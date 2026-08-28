"""Fix the indentation error in roman_urdu_generator.py."""

from pathlib import Path

path = Path(__file__).resolve().parent / "roman_urdu_generator.py"
content = path.read_text("utf-8")

# The issue: the _post_process method was inserted with wrong indentation
# Find the broken section and fix it

# The integrate_fixes.py script replaced the method body but left 
# the _fix_special_sounds method header without a proper body.
# We need to remove the empty _fix_special_sounds method and fix the
# _post_process method indentation.

# Strategy: Find the pattern where the file has:
# 1. An incomplete _fix_special_sounds method (empty body)
# 2. A _post_process method that's inside _fix_special_sounds's scope

# Let's find the exact problem and fix it.

lines = content.split('\n')

# Find where the actual issue is
fix_count = 0

for i, line in enumerate(lines):
    stripped = line.lstrip()
    
    # Check for the end of convert_text method
    if 'return word' in stripped and i > 1790:
        # This should be the end of _fix_special_sounds
        # But if the next non-empty, non-indented line is _post_process 
        # at the same indentation, it's fine
        pass

# The simplest fix: just check Python syntax and fix
# The issue might be that the file has a method with no body
# Let's find methods with no body

# Actually, let me take a simpler approach - compile and use the error to guide us
import py_compile
import tempfile
import os

try:
    compile(content, 'test', 'exec')
    print("No syntax errors found!")
except SyntaxError as e:
    print(f"Syntax error at line {e.lineno}: {e.msg}")
    print(f"Text: {e.text}")
    
    if e.lineno:
        linenum = e.lineno - 1  # 0-indexed
        if linenum < len(lines):
            # Show context around the error
            for j in range(max(0, linenum-3), min(len(lines), linenum+4)):
                prefix = ">>>" if j == linenum else "   "
                print(f"{prefix} {j+1}: {lines[j]}")
