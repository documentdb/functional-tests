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

        if not py_file.stem.startswith(f"test_{parent_folder}"):
            rel_path = py_file.relative_to(tests_dir.parent)
            errors.append(
                f"\n  {rel_path}\n    → Expected pattern: test_{parent_folder}_*.py, got: {py_file.name}. "
                f"Test file in /{parent_folder}/ should include feature name in filename. Non-test utilities should be moved to a utils/ or fixtures/ folder."
            )

    return errors
