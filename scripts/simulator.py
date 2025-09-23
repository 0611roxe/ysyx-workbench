import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union
import concurrent.futures
import math
from workflow_exceptions import (
    WorkflowEnvError, WorkflowFileNotFound, WorkflowSimBuildError, WorkflowArgumentError, workflow_exception_handler
)

def require_env(var):
    v = os.environ.get(var)
    if v is None:
        raise WorkflowEnvError(f"Required environment variable '{var}' is not set")
    return v

class Simulator:
    _AVAILABLE_TESTS: Dict[str, Dict[str, any]] = {
        "cpu-tests": {
            "path": Path(require_env("AM_KERNELS_HOME")) / "tests" / "cpu-tests",
            "type": "test"
        },
        "coremark": {
            "path": Path(require_env("AM_KERNELS_HOME")) / "benchmarks" / "coremark",
            "type": "benchmark"
        },
        "dhrystone": {
            "path": Path(require_env("AM_KERNELS_HOME")) / "benchmarks" / "dhrystone",
            "type": "benchmark"
        },
        "microbench": {
            "path": Path(require_env("AM_KERNELS_HOME")) / "benchmarks" / "microbench",
            "type": "benchmark"
        },
    }

    def __init__(self, rtl_file: Optional[Union[List[Union[Path, str]], Path, str]] = None, top_name: str = None, max_parallel_jobs: int = 4, stage: str = "D"):
        self.rtl_file = rtl_file
        self.top_name = top_name
        self.max_parallel_jobs = max_parallel_jobs
        self.stage = stage.upper()
        self.CPU_COUNT = 8
        self.ARCH = "minirv-minirv" if self.stage == "D" else "riscv32e-ysyxsoc"
        self.NPC_HOME = Path(require_env("NPC_HOME"))
        self.CROSS_COMPILE = os.environ.get("CROSS_COMPILE", "riscv64-linux-gnu-")
        for name, path in [("NPC_HOME", self.NPC_HOME)]:
            if not path.is_dir():
                raise WorkflowFileNotFound(f"Path for {name} ('{path}') does not exist or is not a directory.")

    @staticmethod
    def _run_command(cmd: List[str], title: str) -> Tuple[str, int, str, str]:
        result = subprocess.run(cmd, capture_output=True, text=True, errors='replace')
        return title, result.returncode, result.stdout, result.stderr

    def _build_simulator(self) -> bool:
        title = "Build Verilator Simulator"
        cmd = ["make", "-C", str(self.NPC_HOME), "all", f"-j{self.CPU_COUNT}"]
        if self.rtl_file:
            if isinstance(self.rtl_file, (list, tuple)):
                rtl_file_arg = " ".join(str(f) for f in self.rtl_file)
            else:
                rtl_file_arg = str(self.rtl_file)
            cmd.append(f"RTL_FILE={rtl_file_arg}")
        build_log = Path(os.environ["RESULT_DIR"]) / "build.log"
        print("[INFO] Building Verilator Simulator...")
        with open(build_log, "w") as logf:
            proc = subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT, text=True)
            rc = proc.wait()
        if rc != 0:     
            return False
        print("[OK]   Build Verilator Simulator finished.")
        return True

    def _discover_available_tests(self) -> List[str]:
        return [name for name, info in self._AVAILABLE_TESTS.items() if info["path"].is_dir()]

    def run_tests(self, tests_to_run: List[str], mainargs: str) -> bool:
        if not tests_to_run:
            return True
        print(f"[INFO] Running tests: {', '.join(tests_to_run)}")
        num_tests = len(tests_to_run)
        num_parallel_jobs = min(num_tests, self.max_parallel_jobs)
        cores_per_job = max(1, math.floor(self.CPU_COUNT / num_parallel_jobs))
        test_results: Dict[str, bool] = {}
        all_passed = True

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_parallel_jobs) as executor:
            futures = []
            for test_name in tests_to_run:
                test_info = self._AVAILABLE_TESTS.get(test_name)
                if not test_info:
                    continue
                test_dir = test_info["path"]
                specific_args = []
                if test_name == "microbench":
                    specific_args.append(f"mainargs={mainargs}")
                common_args = [f"-j{cores_per_job}", f"ARCH={self.ARCH}", f"CROSS_COMPILE={self.CROSS_COMPILE}", "run"]
                if self.rtl_file:
                    if isinstance(self.rtl_file, (list, tuple)):
                        rtl_file_arg = " ".join(str(f) for f in self.rtl_file)
                    else:
                        rtl_file_arg = str(self.rtl_file)
                    common_args.append(f"RTL_FILE={rtl_file_arg}")
                cmd = ["make", "-C", str(test_dir)] + common_args + specific_args
                futures.append(executor.submit(self._run_command, cmd, test_name))
            for future in concurrent.futures.as_completed(futures):
                title, rc, stdout, stderr = future.result()
                if rc == 0:
                    print(f"[OK]   Test {title} finished.")
                    test_results[title] = True
                else:
                    print(f"[ERROR] Test {title} failed. See below:", file=sys.stderr)
                    print(stdout, file=sys.stderr)
                    print(stderr, file=sys.stderr)
                    test_results[title] = False
                    all_passed = False
        return all_passed

@workflow_exception_handler
def main():
    parser = argparse.ArgumentParser(description="Run am-kernels tests. Auto-discovers tests if 'all' is specified.")
    parser.add_argument('--mainargs', default='train', help='mainargs for microbench (default: train)')
    parser.add_argument('--tests', nargs='*', choices=list(Simulator._AVAILABLE_TESTS.keys()) + ['all'], default=['all'])
    parser.add_argument('--rtl_file', type=str, nargs='+', help='RTL file(s), support multiple files separated by space')
    parser.add_argument('--max-parallel-jobs', type=int, default=4, help='Maximum number of tests to run in parallel')
    args = parser.parse_args()
    sim = Simulator(rtl_file=args.rtl_file, max_parallel_jobs=args.max_parallel_jobs)
    if not sim._build_simulator():
        raise WorkflowSimBuildError("Simulator build failure")
    if 'all' in args.tests:
        selected_tests = sim._discover_available_tests()
    else:
        selected_tests = args.tests
    all_tests_passed = sim.run_tests(tests_to_run=selected_tests, mainargs=args.mainargs)
    if not all_tests_passed:
        print("[ERROR] Some tests failed. Please review the error output above.", file=sys.stderr)
        sys.exit(1)
    print("[OK]   All executed tests completed successfully!")

if __name__ == "__main__":
    main()