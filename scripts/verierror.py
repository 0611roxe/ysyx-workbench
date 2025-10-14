import re
import os
from pathlib import Path

# Extended Verilator and compiler/linker error type → error code & default English message
VERILATOR_ERROR_DICT = {
    'MODMISSING': {
        "code": 201,
        "base_msg": "Module definition is missing"
    },
    'FILEOPEN': {
        "code": 202,
        "base_msg": "File cannot be opened or read"
    },
    'FILEWRITE': {
        "code": 203,
        "base_msg": "File cannot be written"
    },
    'INCLDUP': {
        "code": 204,
        "base_msg": "File included multiple times"
    },
    'INCLUDE': {
        "code": 205,
        "base_msg": "Include file not found or error"
    },
    'UNDEF': {
        "code": 206,
        "base_msg": "Undefined symbol"
    },
    'MULTIDEF': {
        "code": 207,
        "base_msg": "Multiple definition of symbol"
    },
    'REDECL': {
        "code": 208,
        "base_msg": "Redeclaration of symbol"
    },
    'SYMTYPE': {
        "code": 209,
        "base_msg": "Symbol type error"
    },
    'SYNERR': {
        "code": 210,
        "base_msg": "Verilog syntax error"
    },
    'SYNTAX': {
        "code": 211,
        "base_msg": "Syntax error"
    },
    'COMPILER': {
        "code": 212,
        "base_msg": "Compiler error"
    },
    'UNSUPPORTED': {
        "code": 213,
        "base_msg": "Unsupported syntax or feature"
    },
    'DEPRECATED': {
        "code": 214,
        "base_msg": "Deprecated syntax used"
    },
    'DEPRECATED_TOOL': {
        "code": 215,
        "base_msg": "Deprecated tool or command used"
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
    'LINKER': {
        "code": 280,
        "base_msg": "Linker error"
    },
    'MEMORY': {
        "code": 281,
        "base_msg": "Memory allocation/access error"
    },
    'SEGFAULT': {
        "code": 282,
        "base_msg": "Segmentation fault"
    },
    'PERMISSION': {
        "code": 283,
        "base_msg": "Permission denied"
    },
    'TIMEOUT': {
        "code": 284,
        "base_msg": "Timeout error"
    },
    'TOOLNOTFOUND': {
        "code": 285,
        "base_msg": "Tool or command not found"
    },
    'GENERIC': {
        "code": 299,
        "base_msg": "Unknown error"
    }
}

def classify_generic_error(err_msg):
    """Classify GENERIC errors to more specific types based on message content."""
    msg_lower = err_msg.lower()

    # Linker errors
    if ("undefined reference to" in err_msg or "ld returned" in err_msg or "multiple definition of" in err_msg):
        return "LINKER"
    if "multiple definition" in err_msg:
        return "MULTIDEF"
    if "redefinition" in err_msg or "redeclaration" in err_msg:
        return "REDECL"
    # Compiler errors
    if ("error: expected" in err_msg or "error: stray" in err_msg or "error: ‘" in err_msg or "error: invalid" in err_msg or "parse error" in msg_lower):
        return "COMPILER"
    if ("syntax error" in msg_lower):
        return "SYNTAX"
    if ("undeclared" in msg_lower or "not declared" in msg_lower):
        return "UNDEF"
    if ("no such file or directory" in err_msg or "included file not found" in msg_lower):
        return "INCLUDE"
    if ("deprecated" in msg_lower and "tool" in msg_lower):
        return "DEPRECATED_TOOL"
    if ("deprecated" in msg_lower):
        return "DEPRECATED"
    # Memory errors
    if ("out of memory" in msg_lower or "cannot allocate memory" in msg_lower):
        return "MEMORY"
    if ("segmentation fault" in msg_lower or "core dumped" in msg_lower):
        return "SEGFAULT"
    # Permission errors
    if ("permission denied" in msg_lower):
        return "PERMISSION"
    # Timeout errors
    if ("timeout" in msg_lower or "timed out" in msg_lower):
        return "TIMEOUT"
    # Tool/command not found
    if ("command not found" in msg_lower or "no such command" in msg_lower or "tool not found" in msg_lower):
        return "TOOLNOTFOUND"
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
                generic_error_patterns = [
                    r"undefined reference to",
                    r"multiple definition of",
                    r"redefinition of",
                    r"error: expected",
                    r"error: stray",
                    r"error: ‘",
                    r"error: invalid",
                    r"parse error",
                    r"syntax error",
                    r"undeclared",
                    r"not declared",
                    r"no such file or directory",
                    r"included file not found",
                    r"deprecated",
                    r"out of memory",
                    r"cannot allocate memory",
                    r"segmentation fault",
                    r"core dumped",
                    r"permission denied",
                    r"timeout",
                    r"timed out",
                    r"command not found",
                    r"tool not found",
                ]
                for pat in generic_error_patterns:
                    if re.search(pat, lines[i], re.IGNORECASE):
                        error_type = classify_generic_error(lines[i])
                        self.errors.append({
                            "error_type": error_type,
                            "error_msg": lines[i].strip()
                        })
                        break
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