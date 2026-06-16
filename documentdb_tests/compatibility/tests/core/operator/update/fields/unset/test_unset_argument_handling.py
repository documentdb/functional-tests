"""
Tests for $unset update operator - argument handling.

Covers empty operand, empty operand with upsert, single field, multiple fields,
numeric-string field names, partial field removal, and mixed existing/missing fields.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

UNSET_ARGUMENT_SUCCESS_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="single_field",
        setup_docs=[{"_id": 1, "a": 1, "b": 2}],
        query={"_id": 1},
        update={"$unset": {"a": ""}},
        expected=[{"_id": 1, "b": 2}],
        msg="Should remove single field",
    ),
    UpdateTestCase(
        id="multiple_fields",
        setup_docs=[{"_id": 1, "a": 1, "b": 2, "c": 3}],
        query={"_id": 1},
        update={"$unset": {"a": "", "b": "", "c": ""}},
        expected=[{"_id": 1}],
        msg="Should remove all specified fields",
    ),
    UpdateTestCase(
        id="numeric_string_field_names",
        setup_docs=[{"_id": 1, "10": "ten", "2": "two", "1": "one"}],
        query={"_id": 1},
        update={"$unset": {"10": "", "2": "", "1": ""}},
        expected=[{"_id": 1}],
        msg="Should remove fields with numeric-string names",
    ),
    UpdateTestCase(
        id="subset_of_fields",
        setup_docs=[{"_id": 1, "a": 1, "b": 2, "c": 3, "d": 4}],
        query={"_id": 1},
        update={"$unset": {"a": "", "c": ""}},
        expected=[{"_id": 1, "b": 2, "d": 4}],
        msg="Should remove only specified fields, leaving others intact",
    ),
    UpdateTestCase(
        id="existing_and_missing_field",
        setup_docs=[{"_id": 1, "a": 1, "b": 2}],
        query={"_id": 1},
        update={"$unset": {"a": "", "missing": ""}},
        expected=[{"_id": 1, "b": 2}],
        msg="Should remove existing field and silently ignore missing field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(UNSET_ARGUMENT_SUCCESS_TESTS))
def test_unset_argument_success(collection, test):
    """Test $unset argument handling - success cases."""
    collection.insert_many(test.setup_docs)
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, test.expected, msg=test.msg)


def test_unset_empty_operand_noop(collection):
    """Test $unset with empty operand {} is a no-op."""
    collection.insert_one({"_id": 1, "a": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$unset": {}}}],
        },
    )
    assertSuccessPartial(
        result, {"n": 1, "nModified": 0, "ok": 1.0}, msg="Empty $unset should be no-op"
    )


def test_unset_empty_operand_upsert_creates_from_query(collection):
    """Test upsert with empty $unset creates doc from query."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$unset": {}}, "upsert": True}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [{"_id": 1}], msg="Upsert with empty $unset should create doc from query")
