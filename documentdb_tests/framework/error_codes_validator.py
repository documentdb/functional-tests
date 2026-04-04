"""
Validator to ensure error_codes.py assignments are sorted by value and have no duplicate values.
"""

import ast
from pathlib import Path


def validate_error_codes_sorted() -> list[str]:
    """
    Validate that error code assignments in error_codes.py are sorted by value
    and have no duplicate values.

    Returns:
        List of error messages for violations. Empty if valid.
    """
    file_path = Path(__file__).parent / "error_codes.py"
    if not file_path.exists():
        return ["Error code assignments could not be found."]

    tree = ast.parse(file_path.read_text(), filename=str(file_path))

    codes = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and isinstance(node.value, ast.Constant):
                val = node.value.value
                if not isinstance(val, int):
                    continue
                codes.append((target.id, val, node.lineno))

    errors = []
    for i in range(1, len(codes)):
        prev_name, prev_val, _ = codes[i - 1]
        curr_name, curr_val, curr_line = codes[i]
        if curr_val < prev_val:
            errors.append(
                f"  Line {curr_line}: {curr_name} = {curr_val} is out of order "
                f"(follows {prev_name} = {prev_val}). "
                f"Keep error_codes.py sorted by value."
            )

    # Check for duplicate values. Each numeric code should have exactly one constant.
    seen: dict[int, tuple[str, int]] = {}
    for name, val, lineno in codes:
        if val in seen:
            first_name, first_line = seen[val]
            errors.append(
                f"  Line {lineno}: {name} = {val} duplicates {first_name} "
                f"(line {first_line}). "
                f"Reuse the existing constant or rename it to cover "
                f"the shared scope (e.g., operator family), but do not "
                f"over-generalize without confirming the code is widely shared."
            )
        else:
            seen[val] = (name, lineno)

    return errors
