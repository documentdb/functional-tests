"""
Tests for $literal in $project disambiguation.

Verifies $literal distinguishes computed values from $project inclusion/exclusion
flags, and handles dollar-sign string comparisons.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command


def execute_project_literal(collection, literal_value):
    """Insert a doc and project a $literal value."""
    collection.insert_one({"_id": 1, "a": 10})
    return execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"_id": 1, "val": {"$literal": literal_value}}}],
            "cursor": {},
        },
    )


# ---------------------------------------------------------------------------
# $project inclusion/exclusion vs $literal value
# ---------------------------------------------------------------------------
PROJECT_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "one_as_value",
        expression=1,
        expected=1,
        msg="Should set field to value 1, not inclusion flag",
    ),
    ExpressionTestCase(
        "zero_as_value",
        expression=0,
        expected=0,
        msg="Should set field to value 0, not exclusion flag",
    ),
    ExpressionTestCase(
        "true_as_value",
        expression=True,
        expected=True,
        msg="Should set field to value true, not inclusion flag",
    ),
    ExpressionTestCase(
        "false_as_value",
        expression=False,
        expected=False,
        msg="Should set field to value false, not exclusion flag",
    ),
]


@pytest.mark.parametrize("test", PROJECT_LITERAL_TESTS, ids=lambda t: t.id)
def test_literal_project_disambiguation(collection, test):
    """Test $literal in $project sets field to value, not inclusion/exclusion."""
    result = execute_project_literal(collection, test.expression)
    assertSuccess(result, [{"_id": 1, "val": test.expected}], msg=test.msg)


# ---------------------------------------------------------------------------
# Dollar-sign string comparison
# ---------------------------------------------------------------------------
def test_literal_dollar_string_eq_match(collection):
    """Test $literal '$1' compared via $eq to field containing '$1' returns true."""
    collection.insert_one({"_id": 1, "price": "$1"})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {"_id": 0, "result": {"$eq": ["$price", {"$literal": "$1"}]}}}
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result, [{"result": True}], msg="$literal '$1' should match field containing '$1'"
    )


def test_literal_dollar_string_eq_no_match(collection):
    """Test $literal '$1' compared via $eq to field not containing '$1' returns false."""
    collection.insert_one({"_id": 1, "price": "$2.50"})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {"_id": 0, "result": {"$eq": ["$price", {"$literal": "$1"}]}}}
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result, [{"result": False}], msg="$literal '$1' should not match field containing '$2.50'"
    )
