import argparse
import sys
import os
import subprocess
from pathlib import Path
from typing import Optional, List
import json

try:
    from file_manager import FileBackupManager
    from simulator import Simulator
    from cpu_test import CpuTestLogParser
    from benchmark import BenchmarkLogParser
    from workflow_utils import (
        require_env, WorkflowEnvError, WorkflowFileNotFound, WorkflowSimBuildError, WorkflowArgumentError, workflow_exception_handler
    )
except ImportError as e:
    raise WorkflowEnvError(f"Could not import a required class. Is the script path configured correctly? Details: {e}")

class MainWorkflow:
    def __init__(self, rtl_file, stage: str, mainargs: str, tests: list[str]):
        self.rtl_file = rtl_file.split()
        self.stage = stage
        self.mainargs = mainargs
        self.tests_to_run = tests

        self.result_dir = Path(require_env('RESULT_DIR'))
        self.file_mgr = FileBackupManager(self.result_dir)

        soc_home = require_env("SOC_HOME")
        self.soc_v_path = Path(soc_home) / "ysyxSoCFull.v"
        self.dstagecpu_sv_path = Path(soc_home) / "DSTAGECPU.sv"

        if not self.soc_v_path.exists():
            raise WorkflowFileNotFound(f"{self.soc_v_path} not found")
        if self.stage.upper() == "D" and not self.dstagecpu_sv_path.exists():
            raise WorkflowFileNotFound(f"{self.dstagecpu_sv_path} not found")

        print("[INFO] Backing up and preparing files...")
        self.soc_v_result_path = self.file_mgr.backup(self.soc_v_path)
        self.dstagecpu_sv_result_path = None
        if self.stage.upper() == "D":
            self.dstagecpu_sv_result_path = self.file_mgr.backup(self.dstagecpu_sv_path)
        self.rtl_file_result_path = self.file_mgr.backup(self.rtl_file)
        print("[OK]   Files backup and replacement done.")

        self.soc_test_json = f"{os.environ.get('TOP_NAME', 'top')}_soc_test.json"
        self.simulator: Optional[Simulator] = None


    def _run_lint_check(self) -> bool:
        npc_home_dir = require_env("NPC_HOME")
        command = ["make", "-C", npc_home_dir, "lint"]
        
        try:
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
            for line in iter(process.stdout.readline, ''):
                sys.stdout.write(line)

            return_code = process.wait()
            if return_code == 0:
                print("[OK]   Lint check passed.")
                return True
            else:
                print(f"[ERROR] Lint check failed with exit code {return_code}.", file=sys.stderr)
                return False

        except FileNotFoundError:
            print("[ERROR] 'make' command not found. Ensure it is in your system's PATH.", file=sys.stderr)
            return False
        except Exception as e:
            print(f"[ERROR] An unexpected error occurred during lint check: {e}", file=sys.stderr)
            return False

    def _replace_files(self):
        top_name = os.environ.get("TOP_NAME", "ysyx_00000000")
        if self.stage.upper() == "D":
            self.file_mgr.replace("DSTAGECPU.sv", r'ysyx_00000000', top_name)
            self.file_mgr.replace("ysyxSoCFull.v", r'ysyx_00000000', "DSTAGECPU")
        else:
            self.file_mgr.replace("ysyxSoCFull.v", r'ysyx_00000000', top_name)

    def _restore_files(self):
        self.file_mgr.restore(["ysyxSoCFull.v", "DSTAGECPU.sv"] if self.stage.upper() == "D" else ["ysyxSoCFull.v"])
        print("[INFO] Files restored to original content.")

    def execute(self) -> bool:
        self._replace_files()
        if not self._run_lint_check():
            raise WorkflowSimBuildError("Lint check failed. Please fix the reported issues before proceeding.")

        try:
            print("[INFO] Building Verilator Simulator...")
            sim_rtl_file = self.rtl_file_result_path
            self.simulator = Simulator(
                rtl_file=sim_rtl_file,
                top_name=os.environ.get("TOP_NAME", "ysyx_00000000"),
                stage=self.stage,
                max_parallel_jobs=8,
                cpu_count=8
            )
            if not self.simulator._build_simulator():
                build_log = Path(os.environ["RESULT_DIR"]) / "build.log"
                try:
                    from verierror import VeriErrorParser
                    parser = VeriErrorParser(str(build_log))
                    parser.parse()
                    parser.write_tracebacks()
                except Exception as e:
                    print(f"[ERROR] Could not parse Verilator errors: {e}", file=sys.stderr)
                raise WorkflowSimBuildError("Simulator build failure")

            print("[OK]   Build Verilator Simulator finished.")

            if 'all' in self.tests_to_run:
                selected_tests = self.simulator._discover_available_tests()
            else:
                selected_tests = self.tests_to_run

            if not selected_tests:
                print("[INFO] No tests were selected or discovered. Workflow finished.")
                self.write_soc_test_json({})
                return True

            print(f"[INFO] Running tests: {', '.join(selected_tests)}")
            tests_passed = self.simulator.run_tests(tests_to_run=selected_tests, mainargs=self.mainargs)
            if tests_passed:
                print("[OK]   All tests finished.")
            else:
                print("[ERROR] Some tests failed. See logs above.", file=sys.stderr)

            self.run_parsers_and_generate_soc_json(selected_tests)
            return tests_passed
        finally:
            self._restore_files()

    def run_parsers_and_generate_soc_json(self, executed_tests: list[str]):
        soc_json_path = self.result_dir / self.soc_test_json

        need_cpu = any(t in executed_tests for t in ["cpu-tests"])
        need_bench = any(t in executed_tests for t in ["coremark", "dhrystone", "microbench"])
        need_all = "all" in executed_tests

        soc_json_data = {}

        if need_cpu or need_all:
            print("[INFO] Parsing cpu-test log...")
            cpu_parser = CpuTestLogParser(log_dir=str(self.result_dir))
            cpu_result = cpu_parser.parse(return_data=True)
            soc_json_data["cpu_test"] = cpu_result if cpu_result is not None else {}
            print("[OK]   cpu-test results saved to", soc_json_path)

        if need_bench or need_all:
            print("[INFO] Parsing benchmark logs...")
            bench_parser = BenchmarkLogParser(log_dir=str(self.result_dir))
            bench_result = bench_parser.parse(return_data=True)
            if bench_result:
                executed = set(t for t in executed_tests if t in ["coremark", "dhrystone", "microbench"])
                for name in executed:
                    if name in bench_result:
                        soc_json_data[name] = bench_result[name]
            print("[OK]   Benchmark results saved to", soc_json_path)

        def check_all_pass(data: dict) -> bool:
            if "cpu_test" in data:
                cpu = data["cpu_test"]
                if isinstance(cpu, dict):
                    summary = cpu.get("summary", {})
                    if summary.get("overall_status", "FAIL") != "PASS":
                        return False
            for k in ["coremark", "dhrystone", "microbench"]:
                v = data.get(k)
                if v is not None and isinstance(v, dict):
                    if v.get("status", "FAIL") != "PASS":
                        return False
            return True

        all_pass = check_all_pass(soc_json_data) and bool(soc_json_data)

        final_data = {}
        if all_pass:
            final_data["result"] = "All Pass"
        final_data.update(soc_json_data)

        self.write_soc_test_json(final_data)

    def write_soc_test_json(self, data):
        soc_json_path = self.result_dir / self.soc_test_json
        try:
            with open(soc_json_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[ERROR] Failed to write SOC test json: {e}", file=sys.stderr)

@workflow_exception_handler
def main():
    parser = argparse.ArgumentParser(description="A unified workflow to run tests and then parse their logs.")
    parser.add_argument('--rtl_file', type=str, required=True, help='RTL files as a single string, e.g. "a.sv b.sv"')
    parser.add_argument('--stage', type=str, required=True, choices=['B', 'D', 'C'])
    parser.add_argument('--tests', nargs='*', default=['all'])
    parser.add_argument('--mainargs', type=str, default='train')

    args = parser.parse_args()

    workflow = MainWorkflow(
        rtl_file=args.rtl_file,
        stage=args.stage,
        mainargs=args.mainargs,
        tests=args.tests
    )

    all_tests_succeeded = workflow.execute()

    if all_tests_succeeded:
        print("[OK]   Workflow completed successfully.")
        sys.exit(0)
    else:
        print("[ERROR] Workflow completed, but some tests failed.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()