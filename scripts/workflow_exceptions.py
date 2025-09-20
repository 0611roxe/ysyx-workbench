import sys

class WorkflowError(Exception): pass
class WorkflowEnvError(WorkflowError): pass
class WorkflowFileNotFound(WorkflowError): pass
class WorkflowSimBuildError(WorkflowError): pass
class WorkflowTestNotFound(WorkflowError): pass
class WorkflowLogParseError(WorkflowError): pass
class WorkflowArgumentError(WorkflowError): pass

EXCEPTION_EXIT_CODE = {
    WorkflowEnvError: 101,
    WorkflowFileNotFound: 102,
    WorkflowSimBuildError: 103,
    WorkflowTestNotFound: 104,
    WorkflowLogParseError: 105,
    WorkflowArgumentError: 106,
}

def workflow_exception_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except tuple(EXCEPTION_EXIT_CODE.keys()) as e:
            print(f"[{type(e).__name__}] {e}", file=sys.stderr)
            sys.exit(EXCEPTION_EXIT_CODE[type(e)])
        except SystemExit:
            raise
        except Exception as e:
            print(f"[UnknownError] {e}", file=sys.stderr)
            sys.exit(1)
    return wrapper