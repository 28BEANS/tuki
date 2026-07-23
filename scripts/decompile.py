#!/usr/bin/env python3
"""
Recover .py source files from .pyc bytecode files.

Uses Python's built-in `dis` module to disassemble bytecode, then
reconstructs source from code objects by inspecting constants, names,
and bytecode instructions. This is a best-effort recovery.

For Python 3.11 .pyc files.
"""

import dis
import marshal
import os
import struct
import sys
import types
import re
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "apps" / "backend"

def read_pyc(pyc_path: str) -> types.CodeType:
    """Read a .pyc file and return the code object."""
    with open(pyc_path, "rb") as f:
        magic = f.read(4)
        flags = struct.unpack("<I", f.read(4))[0]
        if flags & 0x1:  # hash-based
            f.read(8)
        else:  # timestamp-based
            f.read(8)  # timestamp + size
        return marshal.load(f)


def code_to_source(code: types.CodeType, indent: int = 0) -> str:
    """
    Best-effort reconstruction of Python source from a code object.
    Uses dis to get the bytecode instructions and reconstructs from there.
    """
    # For simple/empty modules, just return docstring + constants
    instructions = list(dis.get_instructions(code))
    lines = []
    prefix = "    " * indent
    
    # Check if this is a module-level, class, or function code
    # We'll use a simpler approach: extract string constants for docstrings
    # and reconstruct imports, class defs, function defs from nested code objects
    
    # Get docstring if present
    if code.co_consts and isinstance(code.co_consts[0], str):
        doc = code.co_consts[0]
        if "\n" in doc:
            lines.append(f'{prefix}"""')
            for dline in doc.strip().split("\n"):
                lines.append(f"{prefix}{dline}")
            lines.append(f'{prefix}"""')
        else:
            lines.append(f'{prefix}"""{doc}"""')
    
    return "\n".join(lines)


def reconstruct_from_bytecode(pyc_path: str) -> str:
    """
    Use dis.Bytecode to produce a readable reconstruction.
    Falls back to disassembly comments if full reconstruction isn't possible.
    """
    code = read_pyc(pyc_path)
    
    source_lines = []
    
    # Extract all string constants, code objects, etc.
    imports = []
    from_imports = []
    assignments = []
    function_defs = []
    class_defs = []
    
    instructions = list(dis.get_instructions(code))
    
    i = 0
    while i < len(instructions):
        instr = instructions[i]
        
        # Detect: import X
        if instr.opname == "PUSH_NULL" and i + 1 < len(instructions):
            pass
        
        if instr.opname == "IMPORT_NAME":
            module_name = instr.argval
            # Look back for LOAD_CONST (fromlist) and LOAD_CONST (level)
            # Look forward for STORE_NAME or IMPORT_FROM
            if i + 1 < len(instructions):
                next_instr = instructions[i + 1]
                if next_instr.opname == "STORE_NAME":
                    imports.append(f"import {module_name}")
                elif next_instr.opname == "IMPORT_FROM":
                    # Collect all IMPORT_FROM
                    froms = []
                    j = i + 1
                    while j < len(instructions) and instructions[j].opname == "IMPORT_FROM":
                        froms.append(instructions[j].argval)
                        j += 2  # skip STORE_NAME after each IMPORT_FROM
                    from_imports.append(f"from {module_name} import {', '.join(froms)}")
        
        i += 1
    
    # Get all nested code objects (functions, classes)
    nested_codes = []
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            nested_codes.append(const)
    
    # Build source
    # Docstring
    if code.co_consts and isinstance(code.co_consts[0], str) and not code.co_consts[0].startswith(("import", "from")):
        doc = code.co_consts[0]
        if "\n" in doc:
            source_lines.append('"""')
            for dline in doc.strip().split("\n"):
                source_lines.append(dline)
            source_lines.append('"""')
        else:
            source_lines.append(f'"""{doc}"""')
        source_lines.append("")
    
    # Imports
    for imp in imports:
        source_lines.append(imp)
    for imp in from_imports:
        source_lines.append(imp)
    if imports or from_imports:
        source_lines.append("")
    
    return "\n".join(source_lines)


def full_disassembly(pyc_path: str) -> str:
    """Get the full disassembly as a string for manual inspection."""
    code = read_pyc(pyc_path)
    output = []
    output.append(f"# Co-names: {code.co_names}")
    output.append(f"# Co-varnames: {code.co_varnames}")
    output.append(f"# Co-consts (non-code): {[c for c in code.co_consts if not isinstance(c, types.CodeType)]}")
    output.append(f"# Nested code objects: {[c.co_name for c in code.co_consts if isinstance(c, types.CodeType)]}")
    output.append("")
    output.append(dis.Bytecode(code).dis())
    
    # Also disassemble nested code objects
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            output.append(f"\n# === Nested: {const.co_name} ===")
            output.append(f"# Args: {const.co_varnames[:const.co_argcount]}")
            output.append(f"# Co-names: {const.co_names}")
            output.append(f"# Co-consts (non-code): {[c for c in const.co_consts if not isinstance(c, types.CodeType)]}")
            output.append(f"# Nested: {[c.co_name for c in const.co_consts if isinstance(c, types.CodeType)]}")
            output.append(dis.Bytecode(const).dis())
            
            for inner in const.co_consts:
                if isinstance(inner, types.CodeType):
                    output.append(f"\n# === Nested: {const.co_name}.{inner.co_name} ===")
                    output.append(f"# Args: {inner.co_varnames[:inner.co_argcount]}")
                    output.append(f"# Co-names: {inner.co_names}")
                    output.append(f"# Co-consts: {[c for c in inner.co_consts if not isinstance(c, types.CodeType)]}")
                    output.append(dis.Bytecode(inner).dis())
    
    return "\n".join(output)


def main():
    """Process all .pyc files and dump disassembly for manual reconstruction."""
    pyc_dir = BACKEND_DIR
    
    output_dir = Path(__file__).resolve().parent / "disassembly"
    output_dir.mkdir(exist_ok=True)
    
    pyc_files = sorted(pyc_dir.rglob("*.pyc"))
    pyc_files = [p for p in pyc_files if ".venv" not in str(p)]
    
    print(f"Found {len(pyc_files)} .pyc files to process")
    
    for pyc_path in pyc_files:
        # Determine the output path
        # e.g. app/__pycache__/main.cpython-311.pyc -> app/main.dis
        rel = pyc_path.relative_to(pyc_dir)
        parts = list(rel.parts)
        # Remove __pycache__ from path
        parts = [p for p in parts if p != "__pycache__"]
        # Change filename: main.cpython-311.pyc -> main.txt
        fname = parts[-1]
        fname = re.sub(r"\.cpython-\d+\.pyc$", ".txt", fname)
        parts[-1] = fname
        
        out_path = output_dir / Path(*parts)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"  Processing: {pyc_path.relative_to(pyc_dir)} -> {out_path.relative_to(output_dir)}")
        
        try:
            result = full_disassembly(str(pyc_path))
            out_path.write_text(result)
        except Exception as e:
            print(f"    ERROR: {e}")
            out_path.write_text(f"# ERROR: {e}\n")
    
    print(f"\nDisassembly written to: {output_dir}")


if __name__ == "__main__":
    main()
