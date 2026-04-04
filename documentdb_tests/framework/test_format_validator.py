"""
Test format validator to enforce test writing conventions.
"""

from __future__ import annotations

import ast


def validate_test_format(file_path: str) -> list[str]:
    """
    Validate that test functions follow format conventions.

    Returns:
        List of error messages for violations
    """
    errors: list[str] = []

    try:
        with open(file_path, "r") as f:
            tree = ast.parse(f.read(), filename=file_path)
    except Exception:
        return errors  # Skip files that can't be parsed

    # First pass: collect helper functions that call execute_command
    helper_functions_with_execute = set()

    # Add known helper functions from documentdb_tests.framework.utils that call execute_command
    helper_functions_with_execute.update(
        [
            "execute_project",
            "execute_project_with_insert",
            "execute_expression",
            "execute_expression_with_insert",
        ]
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("test_"):
            # Check if this helper function calls execute_command
            has_execute = any(
                isinstance(n, ast.Call)
                and isinstance(n.func, ast.Name)
                and n.func.id in ("execute_command", "execute_admin_command")
                for n in ast.walk(node)
            )
            if has_execute:
                helper_functions_with_execute.add(node.name)

    # Second pass: validate test functions
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            # Check for docstring
            if not ast.get_docstring(node):
                errors.append(f"  Function '{node.name}' at line {node.lineno}: Missing docstring")

            # Check for plain assert statements
            for n in ast.walk(node):
                if isinstance(n, ast.Assert):
                    errors.append(
                        f"  Function '{node.name}' at line {n.lineno}: "
                        f"Don't use plain 'assert'. Use assertSuccess(), assertFailure(),"
                        f" or assertResult() instead."
                    )

            # Check for multiple assertion helper calls
            call_count = sum(
                1
                for n in ast.walk(node)
                if isinstance(n, ast.Call)
                and isinstance(n.func, ast.Name)
                and n.func.id
                in (
                    "assertSuccess",
                    "assertFailure",
                    "assertResult",
                    "assertFailureCode",
                    "assertNaN",
                )
            )

            if call_count > 1:
                errors.append(
                    f"  Function '{node.name}' at line {node.lineno}: "
                    f"Multiple assertions ({call_count}). Use one assertion per test."
                )

            # Check for execute_command or execute_admin_command usage
            has_execute_command = any(
                isinstance(n, ast.Call)
                and isinstance(n.func, ast.Name)
                and n.func.id in ("execute_command", "execute_admin_command")
                for n in ast.walk(node)
            )

            # Also check if test calls helper functions that use execute_command
            has_helper_with_execute = any(
                isinstance(n, ast.Call)
                and isinstance(n.func, ast.Name)
                and n.func.id in helper_functions_with_execute
                for n in ast.walk(node)
            )

            # Check if test has a parameter that could be an executor function
            # Look for parametrize decorators that pass executor functions
            has_executor_param = False
            for decorator in node.decorator_list:
                if (
                    isinstance(decorator, ast.Call)
                    and isinstance(decorator.func, ast.Attribute)
                    and decorator.func.attr == "parametrize"
                ):
                    # Check if any argument is a list containing helper functions
                    for arg in decorator.args:
                        if isinstance(arg, ast.List):
                            for elt in arg.elts:
                                if (
                                    isinstance(elt, ast.Name)
                                    and elt.id in helper_functions_with_execute
                                ):
                                    has_executor_param = True
                                    break

            if not has_execute_command and not has_helper_with_execute and not has_executor_param:
                errors.append(
                    f"  Function '{node.name}' at line {node.lineno}: "
                    f"Must use execute_command(), execute_admin_command(), or helper"
                    f" functions from documentdb_tests.framework.utils for MongoDB operations"
                )

    return errors
