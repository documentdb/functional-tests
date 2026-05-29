"""
Test structure validator to enforce folder organization rules.
"""

from pathlib import Path


def validate_python_files_in_tests(tests_dir: Path) -> list[str]:
    """
    Validate all Python files under tests/ follow structure rules:
    - Test files must match test_{parent_folder}_*.py
    - Utility files belong in utils/ or fixtures/ folders
    """
    errors = []
    allowed_folders = {"utils", "fixtures", "__pycache__"}

    for py_file in tests_dir.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
        if any(folder in py_file.parts for folder in allowed_folders):
            continue

        parent_folder = py_file.parent.name

        if parent_folder == "tests":
            rel_path = py_file.relative_to(tests_dir.parent)
            errors.append(
                f"\n  {rel_path}\n    → Test files should not be placed directly in tests/. "
                f"Move to a feature subfolder."
            )
            continue

        if not py_file.stem.startswith("test_"):
            rel_path = py_file.relative_to(tests_dir.parent)
            errors.append(
                f"\n  {rel_path}\n    → Test file in /{parent_folder}/ should start with 'test_'"
                f" in filename to be picked up by pytest. Non-test utilities should be moved"
                f" to a utils/ or fixtures/ folder."
            )

        if f"{parent_folder}" not in py_file.stem:
            rel_path = py_file.relative_to(tests_dir.parent)
            errors.append(
                f"\n  {rel_path}\n    → Test file name should contain the parent folder name."
            )

    return errors
