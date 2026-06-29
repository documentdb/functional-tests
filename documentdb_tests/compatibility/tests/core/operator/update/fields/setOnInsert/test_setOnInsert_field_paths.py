"""
Tests for $setOnInsert update operator - field path handling.

Covers dot notation, embedded documents, and array indices on insert path.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

SETONINSERT_FIELD_PATH_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="deeply_nested_path",
        query={"_id": 1},
        update={"$setOnInsert": {"a.b.c.d.e": 1}},
        upsert=True,
        expected=[{"_id": 1, "a": {"b": {"c": {"d": {"e": 1}}}}}],
        msg="Should create deeply nested path",
    ),
    UpdateTestCase(
        id="numeric_key_path",
        query={"_id": 1},
        update={"$setOnInsert": {"arr.0": "value"}},
        upsert=True,
        # On insert (no existing doc), numeric path components create object keys,
        # not array indices. Arrays are only created when updating an existing array.
        expected=[{"_id": 1, "arr": {"0": "value"}}],
        msg="Should create object with numeric key on insert",
    ),
    UpdateTestCase(
        id="dollar_prefix_field",
        query={"_id": 1},
        # Tests that "$invalid" is treated as a field name inside $setOnInsert,
        # not as an unknown update operator.
        update={"$setOnInsert": {"$invalid": 1}},
        upsert=True,
        expected=[{"_id": 1, "$invalid": 1}],
        msg="Dollar-prefix field should succeed",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SETONINSERT_FIELD_PATH_TESTS))
def test_setOnInsert_field_paths(collection, test):
    """Test $setOnInsert field path handling on insert."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update, "upsert": test.upsert}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, test.expected, msg=test.msg)
