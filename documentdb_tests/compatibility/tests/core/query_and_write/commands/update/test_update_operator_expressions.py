"""Tests for update command with operator expressions mode."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import CONFLICTING_UPDATE_OPERATORS_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class OperatorTest(BaseTestCase):
    """Test case for update operator expression behavior."""

    setup_docs: Any = None
    updates: Any = None
    expected_docs: Any = None


def run_operator_test(collection, test: OperatorTest):
    """Insert docs, run update, return find result."""
    collection.insert_one(test.setup_docs)
    execute_command(collection, {"update": collection.name, "updates": test.updates})
    return execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})


# Property [Operator Correctness]: each update operator ($inc, $unset, $mul, $min,
# $max, $rename) produces the correct document state.
TESTS: list[OperatorTest] = [
    OperatorTest(
        "inc_increments",
        setup_docs={"_id": 1, "count": 10},
        updates=[{"q": {"_id": 1}, "u": {"$inc": {"count": 5}}}],
        expected_docs=[{"_id": 1, "count": 15}],
        msg="$inc should add the specified value to the field.",
    ),
    OperatorTest(
        "unset_removes_field",
        setup_docs={"_id": 1, "a": 1, "b": 2},
        updates=[{"q": {"_id": 1}, "u": {"$unset": {"b": ""}}}],
        expected_docs=[{"_id": 1, "a": 1}],
        msg="$unset should remove the specified field.",
    ),
    OperatorTest(
        "mul_multiplies",
        setup_docs={"_id": 1, "price": 10},
        updates=[{"q": {"_id": 1}, "u": {"$mul": {"price": 2}}}],
        expected_docs=[{"_id": 1, "price": 20}],
        msg="$mul should multiply the field by the specified value.",
    ),
    OperatorTest(
        "min_updates_if_less",
        setup_docs={"_id": 1, "low": 10},
        updates=[{"q": {"_id": 1}, "u": {"$min": {"low": 5}}}],
        expected_docs=[{"_id": 1, "low": 5}],
        msg="$min should update field when new value is less than current.",
    ),
    OperatorTest(
        "max_updates_if_greater",
        setup_docs={"_id": 1, "high": 10},
        updates=[{"q": {"_id": 1}, "u": {"$max": {"high": 20}}}],
        expected_docs=[{"_id": 1, "high": 20}],
        msg="$max should update field when new value is greater than current.",
    ),
    OperatorTest(
        "rename_field",
        setup_docs={"_id": 1, "old_name": "value"},
        updates=[{"q": {"_id": 1}, "u": {"$rename": {"old_name": "new_name"}}}],
        expected_docs=[{"_id": 1, "new_name": "value"}],
        msg="$rename should move the field to the new name.",
    ),
    OperatorTest(
        "rename_to_nested_path",
        setup_docs={"_id": 1, "x": 5},
        updates=[{"q": {"_id": 1}, "u": {"$rename": {"x": "a.b.c"}}}],
        expected_docs=[{"_id": 1, "a": {"b": {"c": 5}}}],
        msg="$rename should create intermediate documents for nested destination.",
    ),
    OperatorTest(
        "multiple_operators_combined",
        setup_docs={"_id": 1, "a": 1, "b": 10, "c": "remove"},
        updates=[
            {"q": {"_id": 1}, "u": {"$set": {"a": 99}, "$inc": {"b": 5}, "$unset": {"c": ""}}}
        ],
        expected_docs=[{"_id": 1, "a": 99, "b": 15}],
        msg="update should apply multiple operators ($set, $inc, $unset) in one document.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_update_operators(collection, test: OperatorTest):
    """Test update operator expressions produce correct document state."""
    result = run_operator_test(collection, test)
    assertSuccess(result, test.expected_docs, msg=test.msg)


def test_update_set_and_unset_same_field_errors(collection):
    """Test $set and $unset on same field in single update errors."""
    collection.insert_one({"_id": 1, "x": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"x": 2}, "$unset": {"x": ""}}}],
        },
    )
    assertFailureCode(result, CONFLICTING_UPDATE_OPERATORS_ERROR)
