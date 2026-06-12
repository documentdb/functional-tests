"""
Tests for $set update operator - argument handling.

Covers empty operand, single field, multiple fields.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import (
    assertSuccess,
    assertSuccessPartial,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

SET_ARGUMENT_SUCCESS_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="single_field",
        setup_docs=[{"_id": 1, "a": 1}],
        query={"_id": 1},
        update={"$set": {"b": 2}},
        expected=[{"_id": 1, "a": 1, "b": 2}],
        msg="Should set single field",
    ),
    UpdateTestCase(
        id="multiple_fields",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$set": {"a": 1, "b": 2, "c": 3}},
        expected=[{"_id": 1, "a": 1, "b": 2, "c": 3}],
        msg="Should set all fields",
    ),
    UpdateTestCase(
        id="multiple_fields_all_applied",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$set": {"z": 1, "a": 2, "m": 3}},
        expected=[{"_id": 1, "a": 2, "m": 3, "z": 1}],
        msg="All fields in $set operand should be applied regardless of order",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SET_ARGUMENT_SUCCESS_TESTS))
def test_set_argument_success(collection, test):
    """Test $set argument handling - success cases."""
    collection.insert_many(test.setup_docs)
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update, "upsert": test.upsert}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, test.expected, msg=test.msg)


def test_set_empty_operand_upsert_creates_from_query(collection):
    """Test upsert with empty $set creates doc from query."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {}}, "upsert": True}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [{"_id": 1}], msg="Upsert with empty $set should create doc from query")


def test_set_empty_operand_noop(collection):
    """Test $set with empty operand {} is a no-op."""
    collection.insert_one({"_id": 1, "a": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {}}}],
        },
    )
    assertSuccessPartial(
        result, {"n": 1, "nModified": 0, "ok": 1.0}, msg="Empty $set should be no-op"
    )
