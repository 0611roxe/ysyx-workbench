import argparse
import sys
import os
from pathlib import Path
from typing import Optional
import json

try:
    from file_manager import FileBackupManager
    from simulator import Simulator
    from cpu_test import CpuTestLogParser
    from benchmark import BenchmarkLogParser
except ImportError as e:
    print(f"Error: Could not import a required class. Is the script path configured correctly?", file=sys.stderr)
    print(f"Details: {e}", file=sys.stderr)
    sys.exit(1)

class MainWorkflow:
    def __init__(self, rtl_file: Path, stage: str, mainargs: str, tests: list[str], stage_template_file: Optional[Path] = None):
        self.rtl_file = rtl_file
        self.stage = stage
        self.mainargs = mainargs
        self.tests_to_run = tests
        self.stage_template_file = stage_template_file

        try:
            self.result_dir = Path(os.environ['RESULT_DIR'])
        except KeyError as e:
            print(f"Error: Required environment variable {e} is not set.", file=sys.stderr)
            print("The 'step_processor' should have injected this variable. Check your step.yaml.", file=sys.stderr)
            sys.exit(1)

        self.file_mgr = FileBackupManager(self.result_dir)

        soc_home = os.environ.get("SOC_HOME")
        if soc_home is None:
            raise RuntimeError("Environment variable SOC_HOME is not set")
        self.soc_v_path = Path(soc_home) / "ysyxSoCFull.v"
        self.dstagecpu_sv_path = Path(soc_home) / "DSTAGECPU.sv"

        self.soc_v_result_path = self.file_mgr.backup(self.soc_v_path)
        self.dstagecpu_sv_result_path = self.file_mgr.backup(self.dstagecpu_sv_path)
        self.rtl_file_result_path = self.file_mgr.backup(self.rtl_file)

        self.soc_test_json = f"{os.environ.get('TOP_NAME', 'top')}_soc_test.json"
        self.simulator: Optional[Simulator] = None

    def _replace_files(self):
        top_name = os.environ.get("TOP_NAME", "ysyx_00000000")
        if self.stage.upper() == "D":
            self.file_mgr.replace("DSTAGECPU.sv", r'ysyx_00000000', top_name)
            self.file_mgr.replace("ysyxSoCFull.v", r'ysyx_00000000', "DSTAGECPU")
        else:
            self.file_mgr.replace("ysyxSoCFull.v", r'ysyx_00000000', top_name)

    def _restore_files(self):
        if self.stage.upper() == "D":
            self.file_mgr.restore("DSTAGECPU.sv")
        self.file_mgr.restore("ysyxSoCFull.v")

    def execute(self) -> bool:
        self._replace_files()
        try:
            sim_rtl_file = self.rtl_file_result_path if self.rtl_file_result_path.exists() else self.rtl_file
            self.simulator = Simulator(
                rtl_file=sim_rtl_file,
                top_name=os.environ.get("TOP_NAME", "ysyx_00000000")
            )
            if not self.simulator._build_simulator():
                print("\nAborting workflow due to simulator build failure.", file=sys.stderr)
                sys.exit(1)

            if 'all' in self.tests_to_run:
                selected_tests = self.simulator._discover_available_tests()
            else:
                selected_tests = self.tests_to_run

            if not selected_tests:
                print("\nNo tests were selected or discovered. Workflow finished.")
                self.write_soc_test_json({})
                return True

            print(f"\nWorkflow will execute the following tests: {', '.join(selected_tests)}")
            tests_passed = self.simulator.run_tests(tests_to_run=selected_tests, mainargs=self.mainargs)

            if not tests_passed:
                print("\nWarning: Some tests failed. Proceeding with log parsing anyway.", file=sys.stderr)

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
            print("\nRunning parser for: cpu-test")
            cpu_parser = CpuTestLogParser(log_dir=str(self.result_dir))
            cpu_result = cpu_parser.parse(return_data=True)
            soc_json_data["cpu_test"] = cpu_result if cpu_result is not None else {}

        if need_bench or need_all:
            print("\nRunning parser for: benchmark")
            bench_parser = BenchmarkLogParser(log_dir=str(self.result_dir))
            bench_result = bench_parser.parse(return_data=True)
            soc_json_data["benchmark"] = bench_result if bench_result is not None else {}

        if not soc_json_data:
            soc_json_data = {}

        self.write_soc_test_json(soc_json_data)

    def write_soc_test_json(self, data):
        soc_json_path = self.result_dir / self.soc_test_json
        try:
            with open(soc_json_path, "w") as f:
                json.dump(data, f, indent=2)
            print(f"SOC test results written to {soc_json_path}")
        except Exception as e:
            print(f"Failed to write SOC test json: {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description="A unified workflow to run tests and then parse their logs.")
    parser.add_argument('--rtl_file', type=Path, required=True)
    parser.add_argument('--stage', type=str, required=True, choices=['B', 'D'])
    parser.add_argument('--tests', nargs='*', default=['all'])
    parser.add_argument('--mainargs', type=str, default='train')
    parser.add_argument('--Dstage_template', type=Path, default=None, help='Template file for D stage')

    args = parser.parse_args()

    workflow = MainWorkflow(
        rtl_file=args.rtl_file,
        stage=args.stage,
        mainargs=args.mainargs,
        tests=args.tests,
        stage_template_file=args.Dstage_template
    )

    all_tests_succeeded = workflow.execute()

    if all_tests_succeeded:
        print("\nWorkflow completed successfully.")
        sys.exit(0)
    else:
        print("\nWorkflow completed, but some tests failed.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()