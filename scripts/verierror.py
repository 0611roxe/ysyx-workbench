import re
import os
from pathlib import Path

# Extended Verilator error type → error code & default English message
VERILATOR_ERROR_DICT = {
    'MODMISSING': {
        "code": 201,
        "base_msg": "Module definition is missing"
    },
    'FILEOPEN': {
        "code": 202,
        "base_msg": "File cannot be opened or read"
    },
    'INCLDUP': {
        "code": 203,
        "base_msg": "File included multiple times"
    },
    'UNDEF': {
        "code": 204,
        "base_msg": "Undefined symbol"
    },
    'SYMTYPE': {
        "code": 205,
        "base_msg": "Symbol type error"
    },
    'SYNERR': {
        "code": 210,
        "base_msg": "Verilog syntax error"
    },
    'SYNTAX': {
        "code": 211,
        "base_msg": "Verilog syntax error"
    },
    'UNSUPPORTED': {
        "code": 212,
        "base_msg": "Unsupported syntax or feature"
    },
    'DEPRECATED': {
        "code": 213,
        "base_msg": "Deprecated syntax used"
    },
    'PORTCONNECT': {
        "code": 220,
        "base_msg": "Port connection error"
    },
    'PORTCOUNT': {
        "code": 221,
        "base_msg": "Port count error"
    },
    'PORTWIDTH': {
        "code": 222,
        "base_msg": "Port width error"
    },
    'PORTTYPE': {
        "code": 223,
        "base_msg": "Port type error"
    },
    'PARAM': {
        "code": 224,
        "base_msg": "Parameter definition or reference error"
    },
    'UNDRIVEN': {
        "code": 225,
        "base_msg": "Signal not driven"
    },
    'PORTUNDEF': {
        "code": 226,
        "base_msg": "Port undefined or not found"
    },
    'CONST': {
        "code": 230,
        "base_msg": "Constant definition or reference error"
    },
    'WIDTH': {
        "code": 231,
        "base_msg": "Width mismatch"
    },
    'RANGE': {
        "code": 232,
        "base_msg": "Range error"
    },
    'ASSIGN': {
        "code": 233,
        "base_msg": "Assignment error"
    },
    'TYPE': {
        "code": 234,
        "base_msg": "Type error"
    },
    'UNOPTFLAT': {
        "code": 240,
        "base_msg": "Optimization-related warning"
    },
    'UNOPTFLATVAR': {
        "code": 241,
        "base_msg": "Variable optimization-related warning"
    },
    'MULTIDRIVEN': {
        "code": 242,
        "base_msg": "Signal is driven by multiple sources"
    },
    'ORDER': {
        "code": 243,
        "base_msg": "Statement order related error"
    },
    'CLOCK': {
        "code": 250,
        "base_msg": "Clock signal related error"
    },
    'RESET': {
        "code": 251,
        "base_msg": "Reset signal related error"
    },
    'TIMING': {
        "code": 252,
        "base_msg": "Timing error"
    },
    'ASSERT': {
        "code": 260,
        "base_msg": "Assertion failed"
    },
    'FATAL': {
        "code": 261,
        "base_msg": "Fatal error"
    },
    'INTERNAL': {
        "code": 262,
        "base_msg": "Internal Verilator error"
    },
    'VARIANT': {
        "code": 263,
        "base_msg": "Variant-related error"
    },
    'PERF': {
        "code": 264,
        "base_msg": "Performance-related warning"
    },
    'WARNING': {
        "code": 265,
        "base_msg": "General warning"
    },
    'GENERIC': {
        "code": 299,
        "base_msg": "Unknown Verilator error"
    }
}

def classify_generic_error(err_msg):
    """Classify GENERIC errors to more specific types based on message content."""
    # Port connection/undefined errors
    if ("Instance attempts to connect to" in err_msg and "but it is a variable" in err_msg) or \
       ("Instance port" in err_msg and "does not exist" in err_msg):
        return "PORTCONNECT"
    if "Unknown parameter" in err_msg or "Unknown port" in err_msg:
        return "PORTUNDEF"
    if "Port" in err_msg and "is not connected" in err_msg:
        return "PORTCONNECT"
    return "GENERIC"

def get_verilator_error_info(veri_type: str, user_detail: str = None):
    """
    Returns (error_code, message) for the given Verilator error type and detail.
    If user_detail is provided, it is appended to the base message.
    """
    info = VERILATOR_ERROR_DICT.get(veri_type, VERILATOR_ERROR_DICT['GENERIC'])
    code = info["code"]
    base_msg = info["base_msg"]
    if user_detail:
        msg = f"{base_msg}: {user_detail}"
    else:
        msg = base_msg
    return code, msg

class VeriErrorParser:
    def __init__(self, filepath, result_dir_env="RESULT_DIR"):
        self.filepath = filepath
        self.errors = []
        self.result_dir = os.environ.get(result_dir_env, ".")
        self.output_file = Path(self.result_dir) / "VerilatorError.log"

    def parse(self):
        error_pat = re.compile(r'^%Error(?:-([A-Z0-9_]+))?: ([^:]+):(\d+):(?:\d+:)? (.*)')
        with open(self.filepath, encoding="utf-8") as f:
            lines = f.readlines()
        i = 0
        while i < len(lines):
            m = error_pat.match(lines[i])
            if m:
                err_subtype, filename, lineno, err_msg = m.groups()
                error_type = err_subtype or "GENERIC"
                # Try to refine GENERIC errors
                if error_type == "GENERIC":
                    error_type = classify_generic_error(err_msg)
                self.errors.append({
                    "error_type": error_type,
                    "error_msg": err_msg
                })
                break
            else:
                i += 1

    def get_error_code(self, error_type):
        info = VERILATOR_ERROR_DICT.get(error_type, VERILATOR_ERROR_DICT['GENERIC'])
        return info["code"]

    def write_tracebacks(self):
        # Writes only the first error found, with error code, type, and detailed message.
        with open(self.output_file, "w", encoding="utf-8") as f:
            if self.errors:
                err = self.errors[0]
                code, msg = get_verilator_error_info(err['error_type'], err['error_msg'])
                f.write(f"[ERROR {code}] {err['error_type']}: {msg}\n")
            else:
                code, msg = get_verilator_error_info("GENERIC", "No Verilator error found")
                f.write(f"[ERROR {code}] GENERIC: {msg}\n")

    def get_first_error_info(self):
        if not self.errors:
            code, msg = get_verilator_error_info("GENERIC", "No Verilator error found")
            return code, "GENERIC", msg
        err = self.errors[0]
        code, msg = get_verilator_error_info(err['error_type'], err['error_msg'])
        return code, err['error_type'], msg