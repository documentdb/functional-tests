"""
Custom assertion helpers for functional tests.

Provides convenient assertion methods for common test scenarios.
"""

from typing import Dict, List


def assert_document_match(actual: Dict, expected: Dict, ignore_id: bool = True):
    """
    Assert that a document matches the expected structure and values.

    Args:
        actual: The actual document from the database
        expected: The expected document structure
        ignore_id: If True, ignore _id field in comparison (default: True)
    """
    if ignore_id:
        actual = {k: v for k, v in actual.items() if k != "_id"}
        expected = {k: v for k, v in expected.items() if k != "_id"}

    assert actual == expected, f"Document mismatch.\nExpected: {expected}\nActual: {actual}"


def assert_documents_match(
    actual: List[Dict], expected: List[Dict], ignore_id: bool = True, ignore_order: bool = False
):
    """
    Assert that a list of documents matches the expected list.

    Args:
        actual: List of actual documents from the database
        expected: List of expected documents
        ignore_id: If True, ignore _id field in comparison (default: True)
        ignore_order: If True, sort both lists before comparison (default: False)
    """
    if ignore_id:
        actual = [{k: v for k, v in doc.items() if k != "_id"} for doc in actual]
        expected = [{k: v for k, v in doc.items() if k != "_id"} for doc in expected]

    assert len(actual) == len(
        expected
    ), f"Document count mismatch. Expected {len(expected)}, got {len(actual)}"

    if ignore_order:
        # Sort for comparison
        actual = sorted(actual, key=lambda x: str(x))
        expected = sorted(expected, key=lambda x: str(x))

    for i, (act, exp) in enumerate(zip(actual, expected)):
        assert act == exp, f"Document at index {i} does not match.\nExpected: {exp}\nActual: {act}"


def assert_field_exists(document: Dict, field_path: str):
    """
    Assert that a field exists in a document (supports nested paths).

    Args:
        document: The document to check
        field_path: Dot-notation field path (e.g., "user.name")
    """
    parts = field_path.split(".")
    current = document

    for part in parts:
        assert part in current, f"Field '{field_path}' does not exist in document"
        current = current[part]


def assert_field_not_exists(document: Dict, field_path: str):
    """
    Assert that a field does not exist in a document (supports nested paths).

    Args:
        document: The document to check
        field_path: Dot-notation field path (e.g., "user.name")
    """
    parts = field_path.split(".")
    current = document

    for i, part in enumerate(parts):
        if part not in current:
            return  # Field doesn't exist, assertion passes
        if i == len(parts) - 1:
            raise AssertionError(f"Field '{field_path}' exists in document but should not")
        current = current[part]


def assert_count(collection, filter_query: Dict, expected_count: int):
    """
    Assert that a collection contains the expected number of documents matching a filter.

    Args:
        collection: MongoDB collection object
        filter_query: Query filter
        expected_count: Expected number of matching documents
    """
    actual_count = collection.count_documents(filter_query)
    assert actual_count == expected_count, (
        f"Document count mismatch for filter {filter_query}. "
        f"Expected {expected_count}, got {actual_count}"
    )