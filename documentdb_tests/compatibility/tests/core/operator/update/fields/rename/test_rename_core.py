"""
Core behavioral tests for $rename update operator.

Tests argument handling, null handling, overwrite (including simultaneous
multi-field rename), and field name edge cases. No-op outcomes (missing
source, empty operand, $-prefixed source) are asserted via update-result
metadata in test_rename_update_methods.py; self-rename errors live in
test_rename_errors.py.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

BASIC_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "basic_rename",
        setup_docs=[{"_id": 1, "a": 1}],
        query={"_id": 1},
        update={"$rename": {"a": "b"}},
        expected={"_id": 1, "b": 1},
        msg="$rename should move field a to b",
    ),
    UpdateTestCase(
        "multiple_fields",
        setup_docs=[{"_id": 1, "a": 1, "c": 2, "e": 3}],
        query={"_id": 1},
        update={"$rename": {"a": "b", "c": "d", "e": "f"}},
        expected={"_id": 1, "b": 1, "d": 2, "f": 3},
        msg="$rename should rename multiple fields simultaneously",
    ),
]

NULL_HANDLING_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "null_overwrites_target",
        setup_docs=[{"_id": 1, "a": None, "b": 99}],
        query={"_id": 1},
        update={"$rename": {"a": "b"}},
        expected={"_id": 1, "b": None},
        msg="$rename null source should overwrite target with null",
    ),
]

OVERWRITE_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "overwrite_same_type",
        setup_docs=[{"_id": 1, "a": 1, "b": 2}],
        query={"_id": 1},
        update={"$rename": {"a": "b"}},
        expected={"_id": 1, "b": 1},
        msg="$rename should overwrite existing target (same type)",
    ),
    UpdateTestCase(
        "overwrite_different_type",
        setup_docs=[{"_id": 1, "a": "hello", "b": [1, 2, 3]}],
        query={"_id": 1},
        update={"$rename": {"a": "b"}},
        expected={"_id": 1, "b": "hello"},
        msg="$rename should overwrite existing target (different types)",
    ),
]

FIELD_NAME_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "special_chars",
        setup_docs=[{"_id": 1, "a-b": 1}],
        query={"_id": 1},
        update={"$rename": {"a-b": "c_d"}},
        expected={"_id": 1, "c_d": 1},
        msg="$rename should handle special characters in field names",
    ),
    UpdateTestCase(
        "numeric_field_names",
        setup_docs=[{"_id": 1, "field1": 1}],
        query={"_id": 1},
        update={"$rename": {"field1": "field2"}},
        expected={"_id": 1, "field2": 1},
        msg="$rename should handle numeric field names",
    ),
    UpdateTestCase(
        "purely_numeric_field_names",
        setup_docs=[{"_id": 1, "0": "zero"}],
        query={"_id": 1},
        update={"$rename": {"0": "1"}},
        expected={"_id": 1, "1": "zero"},
        msg="$rename should treat purely numeric keys as field names, not array indices",
    ),
    UpdateTestCase(
        "long_field_name",
        setup_docs=[{"_id": 1, "a" * 50: "value"}],
        query={"_id": 1},
        update={"$rename": {"a" * 50: "b" * 50}},
        expected={"_id": 1, "b" * 50: "value"},
        msg="$rename should handle long field names",
    ),
    UpdateTestCase(
        "unicode_field_names",
        setup_docs=[{"_id": 1, "café": "latte"}],
        query={"_id": 1},
        update={"$rename": {"café": "日本語"}},
        expected={"_id": 1, "日本語": "latte"},
        msg="$rename should handle unicode field names",
    ),
    UpdateTestCase(
        "field_name_with_spaces",
        setup_docs=[{"_id": 1, "a b": "value"}],
        query={"_id": 1},
        update={"$rename": {"a b": "c d"}},
        expected={"_id": 1, "c d": "value"},
        msg="$rename should handle field names with spaces",
    ),
]


ALL_TESTS = BASIC_TESTS + NULL_HANDLING_TESTS + OVERWRITE_TESTS + FIELD_NAME_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_rename_core(collection, test: UpdateTestCase):
    """Test $rename core behavior."""
    collection.insert_many(test.setup_docs)

    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [test.expected], msg=test.msg)
