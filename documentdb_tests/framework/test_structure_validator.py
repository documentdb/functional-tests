"""
Test structure validator to enforce folder organization rules.
"""
from pathlib import Path


def validate_test_file_location(file_path: str) -> tuple[bool, str]:
    """
    Validate that a test file follows naming conventions.
    
    Returns:
        (is_valid, error_message) - error_message is empty if valid
    """
    path = Path(file_path)
    
    # Skip if not in tests directory
    if "tests" not in path.parts:
        return True, ""
    
    # Get path relative to tests directory
    try:
        tests_idx = path.parts.index("tests")
        rel_parts = path.parts[tests_idx + 1:]
    except (ValueError, IndexError):
        return True, ""
    
    if not rel_parts or len(rel_parts) < 2:
        return True, ""
    
    # Extract test file name and parent folder
    test_file = path.stem  # filename without .py
    parent_folder = rel_parts[-2]
    
    # Skip validation for certain folders
    skip_folders = {"operators", "tests"}
    if parent_folder in skip_folders:
        return True, ""
    
    # Rule: Test files in feature subfolders should include feature name in filename
    # Pattern: test_{feature}_*.py or test_pipeline_*.py (for integration tests)
    if not test_file.startswith("test_pipeline") and parent_folder not in test_file:
        return False, (
            f"Test file in /{parent_folder}/ should include feature name in filename. "
            f"Expected pattern: test_{parent_folder}_*.py, got: {path.name}"
        )
    
    return True, ""


def validate_python_files_in_tests(tests_dir: Path) -> list[str]:
    """
    Find Python files in tests directory that don't follow test_*.py pattern.
    
    Returns:
        List of error messages for invalid files
    """
    errors = []
    
    # Folders where non-test Python files are allowed
    allowed_folders = {"utils", "fixtures", "__pycache__"}
    
    for py_file in tests_dir.rglob("*.py"):
        # Skip __init__.py files
        if py_file.name == "__init__.py":
            continue
        
        # Check if file is in an allowed folder
        if any(folder in py_file.parts for folder in allowed_folders):
            continue
        
        # Check if file follows test_*.py pattern
        if not py_file.stem.startswith("test_"):
            rel_path = py_file.relative_to(tests_dir.parent)
            errors.append(
                f"\n  {rel_path}\n    → Python file in tests directory must follow test_*.py pattern. "
                f"Got: {py_file.name}. If this is a utility file, move it to a utils/ or fixtures/ folder."
            )
    
    return errors
