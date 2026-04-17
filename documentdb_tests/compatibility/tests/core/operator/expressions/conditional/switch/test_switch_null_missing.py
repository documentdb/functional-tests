"""
Tests for $switch null and $missing propagation.

Covers null/missing behavior in case, then, and default positions.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.parametrize import pytest_params

# --- Tests that produce a result value (including null) ---
RESULT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_case_falls_through",
        expression={
            "$switch": {"branches": [{"case": None, "then": "matched"}], "default": "default_val"}
        },
        expected="default_val",
        msg="null case should fall through",
    ),
    ExpressionTestCase(
        "literal_null_case_falls_through",
        expression={
            "$switch": {
                "branches": [{"case": {"$literal": None}, "then": "matched"}],
                "default": "default_val",
            }
        },
        expected="default_val",
        msg="$literal null case should fall through",
    ),
    ExpressionTestCase(
        "missing_field_case_falls_through",
        expression={
            "$switch": {
                "branches": [{"case": "$nonexistent", "then": "matched"}],
                "default": "default_val",
            }
        },
        doc={"_id": 1},
        expected="default_val",
        msg="Missing field case should fall through",
    ),
    ExpressionTestCase(
        "null_then_returns_null",
        expression={"$switch": {"branches": [{"case": True, "then": None}]}},
        expected=None,
        msg="null then should return null",
    ),
    ExpressionTestCase(
        "null_default_returns_null",
        expression={"$switch": {"branches": [{"case": None, "then": "x"}], "default": None}},
        expected=None,
        msg="null default should return null",
    ),
    ExpressionTestCase(
        "all_null_cases_with_default",
        expression={
            "$switch": {
                "branches": [
                    {"case": None, "then": "a"},
                    {"case": None, "then": "b"},
                ],
                "default": "default_val",
            }
        },
        expected="default_val",
        msg="All null cases should fall through to default",
    ),
]

# --- Tests where missing field in then/default excludes field from output ---
MISSING_FIELD_OUTPUT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_field_then",
        expression={"$switch": {"branches": [{"case": True, "then": "$nonexistent"}]}},
        doc={"_id": 1},
        expected=[{}],
        msg="Missing field in then should exclude field from output",
    ),
    ExpressionTestCase(
        "missing_field_default",
        expression={
            "$switch": {
                "branches": [{"case": False, "then": "x"}],
                "default": "$nonexistent",
            }
        },
        doc={"_id": 1},
        expected=[{}],
        msg="Missing field in default should exclude field from output",
    ),
]


@pytest.mark.parametrize("test", pytest_params(RESULT_TESTS))
def test_switch_null_missing_result(collection, test):
    """Test $switch null/missing propagation returning a value or error."""
    if test.doc:
        result = execute_expression_with_insert(collection, test.expression, test.doc)
    else:
        result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(MISSING_FIELD_OUTPUT_TESTS))
def test_switch_null_missing_field_output(collection, test):
    """Test $switch with missing field reference excludes field from output."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assertSuccess(result, test.expected, test.msg)
