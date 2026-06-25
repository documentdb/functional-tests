"""
Tests for $setOnInsert update operator - errors.

Covers conflicting paths, conflict with $set, _id immutability, and conflicting
$and values.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import (
    assertFailureCode,
)
from documentdb_tests.framework.error_codes import (
    CONFLICTING_UPDATE_OPERATORS_ERROR,
    IMMUTABLE_FIELD_ERROR,
    NOT_EXACT_VALUE_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

SETONINSERT_ERROR_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="conflicting_paths",
        query={"_id": 1},
        update={"$setOnInsert": {"a": 1, "a.b": 2}},
        upsert=True,
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="Conflicting paths should fail",
    ),
    UpdateTestCase(
        id="id_conflict_with_query",
        query={"_id": 1},
        update={"$setOnInsert": {"_id": 2}},
        upsert=True,
        error_code=IMMUTABLE_FIELD_ERROR,
        msg="$setOnInsert _id conflicting with query-derived _id should error",
    ),
    UpdateTestCase(
        id="id_dotted_subfield",
        query={"_id.a": 1},
        update={"$setOnInsert": {"_id.b": 2}},
        upsert=True,
        error_code=IMMUTABLE_FIELD_ERROR,
        msg="Cannot modify _id subfield with $setOnInsert",
    ),
    UpdateTestCase(
        id="id_replace_different_structure",
        query={"_id.a": 1},
        update={"$setOnInsert": {"_id": "plain_string"}},
        upsert=True,
        error_code=IMMUTABLE_FIELD_ERROR,
        msg="Replacing _id structure should error",
    ),
    UpdateTestCase(
        id="id_add_subfield_when_query_dotted",
        query={"_id.x": 1},
        update={"$setOnInsert": {"_id.y": 2}},
        upsert=True,
        error_code=IMMUTABLE_FIELD_ERROR,
        msg="Adding _id subfield when query uses dotted _id should error",
    ),
    UpdateTestCase(
        id="and_conflicting_values",
        query={"$and": [{"a": 1}, {"a": 2}]},
        update={"$setOnInsert": {"x": 10}},
        upsert=True,
        error_code=NOT_EXACT_VALUE_FIELD_ERROR,
        msg="Conflicting values in $and should error",
    ),
    UpdateTestCase(
        id="set_conflict_same_field",
        query={"_id": 1},
        update={"$set": {"a": 1}, "$setOnInsert": {"a": 2}},
        upsert=True,
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$set and $setOnInsert on same field should conflict",
    ),
    UpdateTestCase(
        id="set_conflict_nested_path",
        query={"_id": 1},
        update={"$set": {"a.b": 1}, "$setOnInsert": {"a.b": 2}},
        upsert=True,
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$set and $setOnInsert on same nested path should conflict",
    ),
    UpdateTestCase(
        id="set_conflict_parent_child",
        query={"_id": 1},
        update={"$set": {"a": 1}, "$setOnInsert": {"a.b": 2}},
        upsert=True,
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$set on parent and $setOnInsert on child path should conflict",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SETONINSERT_ERROR_TESTS))
def test_setOnInsert_errors(collection, test):
    """Test $setOnInsert error cases."""
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update, "upsert": test.upsert}],
        },
    )
    assertFailureCode(result, test.error_code, msg=test.msg)
