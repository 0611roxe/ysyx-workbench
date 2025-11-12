import sys
import os

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
    """A decorator to catch and handle custom workflow exceptions."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except tuple(EXCEPTION_EXIT_CODE.keys()) as e:
            print(f"[{type(e).__name__}] {e}", file=sys.stderr)
            sys.exit(EXCEPTION_EXIT_CODE[type(e)])
        except SystemExit:
            raise
        except Exception as e:
            print(f"[UnknownError] An unexpected error occurred: {e}", file=sys.stderr)
            sys.exit(1)
    return wrapper
    
def require_env(var: str) -> str:
    """
    Gets an environment variable, raising a WorkflowEnvError if it's not set.
    """
    v = os.environ.get(var)
    if v is None:
        raise WorkflowEnvError(f"Required environment variable '{var}' is not set")
    return v