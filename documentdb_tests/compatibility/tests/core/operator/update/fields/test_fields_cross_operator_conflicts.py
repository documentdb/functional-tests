"""
Tests for cross-operator interactions at the update/fields level.

Covers same-path conflict detection (engine rejects conflicting operators on
identical paths) and realistic multi-operator updates on different paths.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import CONFLICTING_UPDATE_OPERATORS_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

CROSS_OPERATOR_CONFLICT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="set_inc_same_path",
        setup_docs=[{"_id": 1, "a": 1}],
        query={"_id": 1},
        update={"$set": {"a": 1}, "$inc": {"a": 1}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="Same-path $set + $inc should conflict",
    ),
    UpdateTestCase(
        id="set_unset_same_path",
        setup_docs=[{"_id": 1, "a": 1}],
        query={"_id": 1},
        update={"$set": {"a": 1}, "$unset": {"a": ""}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="Same-path $set + $unset should conflict",
    ),
    UpdateTestCase(
        id="set_unset_same_dot_path",
        setup_docs=[{"_id": 1, "a": {"b": 1}}],
        query={"_id": 1},
        update={"$set": {"a.b": 2}, "$unset": {"a.b": ""}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="Same dot-path $set + $unset should conflict",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CROSS_OPERATOR_CONFLICT_TESTS))
def test_cross_operator_same_path_conflict(collection, test):
    """Same-path updates with different operators should produce a conflict error."""
    collection.insert_many(test.setup_docs)
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update}],
        },
    )
    assertFailureCode(result, test.error_code, msg=test.msg)


CROSS_OPERATOR_SUCCESS_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="set_and_inc_different_fields",
        setup_docs=[{"_id": 1, "status": "pending", "version": 1}],
        query={"_id": 1},
        update={"$set": {"status": "shipped"}, "$inc": {"version": 1}},
        expected=[{"_id": 1, "status": "shipped", "version": 2}],
        msg="$set status + $inc version should both apply",
    ),
    UpdateTestCase(
        id="unset_and_set_different_fields",
        setup_docs=[{"_id": 1, "a": 1, "b": 2}],
        query={"_id": 1},
        update={"$unset": {"a": ""}, "$set": {"c": 3}},
        expected=[{"_id": 1, "b": 2, "c": 3}],
        msg="$unset and $set should both apply",
    ),
    UpdateTestCase(
        id="set_nested_and_unset_sibling",
        setup_docs=[{"_id": 1, "a": {"b": 1, "c": 2}}],
        query={"_id": 1},
        update={"$set": {"a.b": 10}, "$unset": {"a.c": ""}},
        expected=[{"_id": 1, "a": {"b": 10}}],
        msg="$set nested path + $unset sibling path should both apply",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CROSS_OPERATOR_SUCCESS_TESTS))
def test_cross_operator_different_paths_success(collection, test):
    """Different-path updates with multiple operators should both apply."""
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
