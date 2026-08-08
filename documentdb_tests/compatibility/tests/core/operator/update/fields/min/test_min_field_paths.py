"""
Field path tests for $min update field operator.

Tests dot notation, field creation on non-existent fields, and
multiple fields in a single $min expression.
"""

from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

_DATE = datetime(2023, 6, 15, tzinfo=timezone.utc)

# Property [Field Paths]: $min applies via dot notation, creates non-existent fields,
# and evaluates multiple fields independently.
TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "dot_notation_less_updates",
        setup_docs=[{"_id": 1, "embedded": {"field": 20}}],
        query={"_id": 1},
        update={"$min": {"embedded.field": 10}},
        expected={"_id": 1, "embedded": {"field": 10}},
        msg="$min on 'embedded.field' where value is less should update",
    ),
    UpdateTestCase(
        "dot_notation_greater_unchanged",
        setup_docs=[{"_id": 1, "embedded": {"field": 10}}],
        query={"_id": 1},
        update={"$min": {"embedded.field": 20}},
        expected={"_id": 1, "embedded": {"field": 10}},
        msg="$min on 'embedded.field' where value is greater should not update",
    ),
    UpdateTestCase(
        "dot_notation_creates_path",
        setup_docs=[{"_id": 1, "other": "data"}],
        query={"_id": 1},
        update={"$min": {"embedded.field": 100}},
        expected={"_id": 1, "other": "data", "embedded": {"field": 100}},
        msg="$min on non-existent 'embedded.field' should create nested path",
    ),
    UpdateTestCase(
        "array_index_dot_notation",
        setup_docs=[{"_id": 1, "arr": [15, 10, 5]}],
        query={"_id": 1},
        update={"$min": {"arr.0": 3}},
        expected={"_id": 1, "arr": [3, 10, 5]},
        msg="$min on 'arr.0' should update array element at index 0",
    ),
    UpdateTestCase(
        "dotted_past_array_end_pads_with_nulls",
        setup_docs=[{"_id": 1, "a": [10, 20]}],
        query={"_id": 1},
        update={"$min": {"a.10": 5}},
        expected={
            "_id": 1,
            "a": [10, 20, None, None, None, None, None, None, None, None, 5],
        },
        msg="$min past the end of an array should pad with nulls and set the value at the index",
    ),
    UpdateTestCase(
        "nonexistent_field_positive_number",
        setup_docs=[{"_id": 1, "other": "data"}],
        query={"_id": 1},
        update={"$min": {"val": 100}},
        expected={"_id": 1, "other": "data", "val": 100},
        msg="$min on non-existent field with positive number should create field",
    ),
    UpdateTestCase(
        "nonexistent_field_negative_number",
        setup_docs=[{"_id": 1, "other": "data"}],
        query={"_id": 1},
        update={"$min": {"val": -50}},
        expected={"_id": 1, "other": "data", "val": -50},
        msg="$min on non-existent field with negative number should create field",
    ),
    UpdateTestCase(
        "nonexistent_field_null",
        setup_docs=[{"_id": 1, "other": "data"}],
        query={"_id": 1},
        update={"$min": {"val": None}},
        expected={"_id": 1, "other": "data", "val": None},
        msg="$min on non-existent field with null should create field",
    ),
    UpdateTestCase(
        "nonexistent_field_string",
        setup_docs=[{"_id": 1, "other": "data"}],
        query={"_id": 1},
        update={"$min": {"val": "hello"}},
        expected={"_id": 1, "other": "data", "val": "hello"},
        msg="$min on non-existent field with string should create field",
    ),
    UpdateTestCase(
        "nonexistent_field_date",
        setup_docs=[{"_id": 1, "other": "data"}],
        query={"_id": 1},
        update={"$min": {"val": _DATE}},
        expected={"_id": 1, "other": "data", "val": _DATE},
        msg="$min on non-existent field with Date should create field",
    ),
    UpdateTestCase(
        "nonexistent_field_empty_object",
        setup_docs=[{"_id": 1, "other": "data"}],
        query={"_id": 1},
        update={"$min": {"val": {}}},
        expected={"_id": 1, "other": "data", "val": {}},
        msg="$min on non-existent field with empty object should create field",
    ),
    UpdateTestCase(
        "nonexistent_field_empty_array",
        setup_docs=[{"_id": 1, "other": "data"}],
        query={"_id": 1},
        update={"$min": {"val": []}},
        expected={"_id": 1, "other": "data", "val": []},
        msg="$min on non-existent field with empty array should create field",
    ),
    UpdateTestCase(
        "multiple_fields_both_update",
        setup_docs=[{"_id": 1, "a": 50, "b": 60}],
        query={"_id": 1},
        update={"$min": {"a": 10, "b": 20}},
        expected={"_id": 1, "a": 10, "b": 20},
        msg="$min with multiple fields where both are less should update both",
    ),
    UpdateTestCase(
        "multiple_fields_one_updates",
        setup_docs=[{"_id": 1, "a": 50, "b": 5}],
        query={"_id": 1},
        update={"$min": {"a": 10, "b": 100}},
        expected={"_id": 1, "a": 10, "b": 5},
        msg="$min with multiple fields should only update 'a' (10 < 50, 100 > 5)",
    ),
    UpdateTestCase(
        "multiple_fields_none_update",
        setup_docs=[{"_id": 1, "a": 5, "b": 5}],
        query={"_id": 1},
        update={"$min": {"a": 100, "b": 100}},
        expected={"_id": 1, "a": 5, "b": 5},
        msg="$min with multiple fields where none are less should not update",
    ),
    UpdateTestCase(
        "multiple_fields_independent_evaluation",
        setup_docs=[{"_id": 1, "x": 1, "y": 99, "z": 50}],
        query={"_id": 1},
        update={"$min": {"x": 100, "y": 5, "z": 50}},
        expected={"_id": 1, "x": 1, "y": 5, "z": 50},
        msg="$min evaluates each field independently (x stays, y updates, z stays equal)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_min_field_paths(collection, test: UpdateTestCase):
    """Test $min with various field paths and targeting."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )

    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": test.expected["_id"]}}
    )
    assertSuccess(result, [test.expected], msg=test.msg)
