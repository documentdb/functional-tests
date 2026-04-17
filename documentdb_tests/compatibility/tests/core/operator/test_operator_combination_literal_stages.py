"""
Integration tests for $literal with pipeline stages.

Covers $literal project disambiguation.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params


# ---------------------------------------------------------------------------
# $literal in $project: disambiguation from inclusion/exclusion flags
# ---------------------------------------------------------------------------
def _execute_project_literal(collection, literal_value):
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
    ExpressionTestCase(
        "negative_one_as_value",
        expression=-1,
        expected=-1,
        msg="Should set field to value -1, not exclusion flag",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PROJECT_LITERAL_TESTS))
def test_literal_project_disambiguation(collection, test):
    """Test $literal in $project sets field to value, not inclusion/exclusion."""
    result = _execute_project_literal(collection, test.expression)
    assertSuccess(result, [{"_id": 1, "val": test.expected}], msg=test.msg)
