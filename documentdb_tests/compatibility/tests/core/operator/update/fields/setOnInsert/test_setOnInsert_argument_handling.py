"""
Tests for $setOnInsert update operator - argument handling.

Covers empty operand, single field, multiple fields, and field ordering.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

SETONINSERT_ARGUMENT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="empty_operand",
        query={"_id": 1},
        update={"$setOnInsert": {}},
        upsert=True,
        expected=[{"_id": 1}],
        msg="Empty $setOnInsert should create doc from query only",
    ),
    UpdateTestCase(
        id="single_field",
        query={"_id": 1},
        update={"$setOnInsert": {"x": 42}},
        upsert=True,
        expected=[{"_id": 1, "x": 42}],
        msg="Should set single field on insert",
    ),
    UpdateTestCase(
        id="multiple_fields",
        query={"_id": 1},
        update={"$setOnInsert": {"a": 1, "b": 2, "c": 3}},
        upsert=True,
        expected=[{"_id": 1, "a": 1, "b": 2, "c": 3}],
        msg="Should set all fields on insert",
    ),
    UpdateTestCase(
        id="string_keys",
        query={"_id": 1},
        update={"$setOnInsert": {"z": 1, "a": 2, "m": 3}},
        upsert=True,
        expected=[{"_id": 1, "a": 2, "m": 3, "z": 1}],
        msg="Should set all fields on insert (string keys)",
    ),
    UpdateTestCase(
        id="numeric_keys",
        query={"_id": 1},
        update={"$setOnInsert": {"3": "c", "1": "a", "2": "b"}},
        upsert=True,
        expected=[{"_id": 1, "1": "a", "2": "b", "3": "c"}],
        msg="Should set all fields on insert (numeric keys)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SETONINSERT_ARGUMENT_TESTS))
def test_setOnInsert_argument_handling(collection, test):
    """Test $setOnInsert argument handling."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update, "upsert": test.upsert}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, test.expected, msg=test.msg)
