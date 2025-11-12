import re
import os
from pathlib import Path

VERILATOR_ERROR_DICT = {
    # --- Language-related ---
    'BLKANDNBLK':   {"code": 201, "base_msg": "Blocking and non-blocking assignments in same 'always' block"},
    'CASEINCOMPLETE':{"code": 202, "base_msg": "Case statement is incomplete and lacks a default"},
    'CASEX':        {"code": 203, "base_msg": "Case statement contains 'x' or 'z' in its items"},
    'CMPCONST':     {"code": 204, "base_msg": "Comparison with a constant that can never be true"},
    'IMPLICIT':     {"code": 205, "base_msg": "Signal is implicitly declared"},
    'INITIALDLY':   {"code": 206, "base_msg": "Delay statement found in an 'initial' or 'final' block"},
    'LATCH':        {"code": 207, "base_msg": "Latch inferred from incomplete logic"},
    'REALCVT':      {"code": 208, "base_msg": "Implicit conversion from 'real' to integer, potential precision loss"},
    'SELRANGE':     {"code": 209, "base_msg": "Bit-select or part-select index is out of range"},
    'STATICVAR':    {"code": 210, "base_msg": "Static variable used in an automatic task or function"},
    'STRINGARG':    {"code": 211, "base_msg": "String used as an argument to a non-string-typed format specifier"},
    'SYNCASYNCNET': {"code": 212, "base_msg": "Net is driven by both blocking and non-blocking assignments"},
    'UNDRIVEN':     {"code": 213, "base_msg": "Signal is never driven"},
    'UNSIGNED':     {"code": 214, "base_msg": "Comparison of signed and unsigned numbers"},
    'WIDTHEQ':      {"code": 215, "base_msg": "Width mismatch in equality operator"},
    'WIDTHXOR':     {"code": 216, "base_msg": "Width mismatch in reduction operator"},
    'WIDTHEXPAND':  {"code": 217, "base_msg": "Width mismatch in '{... extend ...}'"},
    'WIDTH':        {"code": 218, "base_msg": "Generic width mismatch in assignment or expression"},
    'SYNTAX':       {"code": 219, "base_msg": "General Verilog syntax error"},
    'UNDEF':        {"code": 220, "base_msg": "Use of an undefined variable, module, or symbol"},
    'REDECL':       {"code": 221, "base_msg": "Symbol has been redeclared"},
    'MULTIDEF':     {"code": 222, "base_msg": "Module has been defined multiple times"},
    'UNSUPPORTED':  {"code": 223, "base_msg": "Use of an unsupported Verilog/SystemVerilog feature"},
    'SYMTYPE':      {"code": 224, "base_msg": "Symbol used with an incorrect type"},

    # --- Structure-related ---
    'ASSIGNDLY':    {"code": 230, "base_msg": "Assignment with a delay in a combinational block"},
    'BLKSEQ':       {"code": 231, "base_msg": "Blocking assignment used in a sequential block"},
    'COMBDLY':      {"code": 232, "base_msg": "Combinational logic loop detected"},
    'DECLFILENAME': {"code": 233, "base_msg": "Module name does not match the filename"},
    'DEFPARAM':     {"code": 234, "base_msg": "Use of deprecated 'defparam' statement"},
    'MULTIDRIVEN':  {"code": 235, "base_msg": "Signal is driven by multiple sources"},
    'PINCONNECTEMPTY': {"code": 236, "base_msg": "Port connected to empty, e.g., .port()"},
    'PINMISSING':   {"code": 237, "base_msg": "Port not connected in module instantiation"},
    'PINNOCONNECT': {"code": 238, "base_msg": "Module port is never connected in any instantiation"},
    'UNOPT':        {"code": 239, "base_msg": "Signal or module is unused and has been optimized away"},
    'UNOPTFLAT':    {"code": 240, "base_msg": "Signal has no source or load in the flattened design"},
    'UNUSED':       {"code": 241, "base_msg": "Signal, parameter, or variable was declared but never used"},
    'MODMISSING':   {"code": 242, "base_msg": "Module definition cannot be found"},
    'PORTCONNECT':  {"code": 243, "base_msg": "Error in port connection"},
    'PORTWIDTH':    {"code": 244, "base_msg": "Signal width does not match port width"},

    # --- Style-related ---
    'BEGINENABLED': {"code": 250, "base_msg": "'begin' block is not named while corresponding 'end' is"},
    'ENDLABEL':     {"code": 251, "base_msg": "'end' label does not match 'begin' label"},
    'IMPLICITSTATIC':{"code": 252, "base_msg": "Variable lifetime is implicitly static"},
    'SYMRSVD':      {"code": 253, "base_msg": "Use of a reserved symbol name (e.g., starts with v_ or vl_)"},
    'VARHIDDEN':    {"code": 254, "base_msg": "Inner variable declaration hides an outer variable of the same name"},

    # --- Verilator-specific & Configuration ---
    'ASSTASKS':     {"code": 260, "base_msg": "Assignment exported from a task or function"},
    'HIERBLOCK':    {"code": 261, "base_msg": "Generate block name conflicts with Verilator's hierarchy scheme"},
    'REDEFMACRO':   {"code": 262, "base_msg": "A macro has been redefined"},
    'SFORMAT':      {"code": 263, "base_msg": "Use of an unsupported $-format code"},
    'UNOPTTHREADS': {"code": 264, "base_msg": "Threading-related code has been optimized away"},
    'UNUSEDPARAM':  {"code": 265, "base_msg": "A parameter's value is overridden but the parameter is never used"},
    'UNUSEDPUBLIC': {"code": 266, "base_msg": "A function marked as public is never called"},
    'VPIINTEGER':   {"code": 267, "base_msg": "64-bit integer passed to a 32-bit VPI call"},
    'FILEOPEN':     {"code": 268, "base_msg": "File cannot be opened or read"},
    'CMDLINE':      {"code": 269, "base_msg": "Invalid command-line arguments"},
    'NEEDTIMINGOPT':{"code": 270, "base_msg": "Code has delay controls, but --timing or --no-timing was not specified"},
    'TIMESCALEMOD': {"code": 271, "base_msg": "Timescale is missing or inconsistent across modules"},
    
    # --- Fatal and Internal Errors ---
    'INTERNAL':     {"code": 280, "base_msg": "Internal Verilator error"},
    'FATAL':        {"code": 281, "base_msg": "A fatal error that prevents Verilator from continuing"},
    
    # --- Other Generic Categories ---
    'COMPILER':     {"code": 290, "base_msg": "C++ compiler error during Verilator model build"},
    'LINKER':       {"code": 291, "base_msg": "Linker error during Verilator model build"},
    'GENERIC':      {"code": 299, "base_msg": "Unknown or generic error"}
}

def get_verilator_error_info(veri_type: str, user_detail: str = None):
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
        error_pat = re.compile(r'^%(Error|Warning)-([A-Z0-9_]+):(?:.+)')
        
        try:
            with open(self.filepath, 'r', encoding="utf-8") as f:
                lines = f.readlines()
        except FileNotFoundError:
            self.errors.append({"error_type": "FILEOPEN", "error_msg": f"Log file '{self.filepath}' not found."})
            return

        for line in lines:
            m = error_pat.match(line)
            if m:
                level, err_subtype = m.groups()
                
                # If the specific error/warning is in our dictionary, use it.
                if err_subtype in VERILATOR_ERROR_DICT:
                    self.errors.append({
                        "error_type": err_subtype,
                        "error_msg": line.strip()
                    })
                elif level == 'Warning':
                    self.errors.append({
                        "error_type": "LINT",
                        "error_msg": line.strip()
                    })
                # Fallback for unknown Errors
                else:
                    self.errors.append({
                        "error_type": "GENERIC",
                        "error_msg": line.strip()
                    })
                break
        
        if not self.errors:
            for line in lines:
                if "error:" in line.lower() or "fatal:" in line.lower() or "undefined reference" in line:
                    self.errors.append({
                        "error_type": "GENERIC",
                        "error_msg": line.strip()
                    })
                    break

    def write_tracebacks(self):
        """Writes the first found error to the VerilatorError.log file."""
        with open(self.output_file, "w", encoding="utf-8") as f:
            if self.errors:
                err = self.errors[0]
                code, msg = get_verilator_error_info(err['error_type'], err['error_msg'])
                f.write(f"[ERROR {code}] {err['error_type']}: {msg}\n")
            else:
                code, msg = get_verilator_error_info("GENERIC", "No Verilator error found in log.")
                f.write(f"[ERROR {code}] GENERIC: {msg}\n")
