"""Tests for $log null and missing propagation across the value and base arguments."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

# Property [Null Propagation]: $log returns null when either the value or the base is null or a
# missing field.
LOG_NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_value",
        doc={"value": None, "base": 10},
        expression={"$log": ["$value", "$base"]},
        expected=None,
        msg="$log should return null for a null value",
    ),
    ExpressionTestCase(
        "null_base",
        doc={"value": 10, "base": None},
        expression={"$log": ["$value", "$base"]},
        expected=None,
        msg="$log should return null for a null base",
    ),
    ExpressionTestCase(
        "both_null",
        doc={"value": None, "base": None},
        expression={"$log": ["$value", "$base"]},
        expected=None,
        msg="$log should return null when both value and base are null",
    ),
    ExpressionTestCase(
        "missing_value",
        doc={"base": 10},
        expression={"$log": [MISSING, "$base"]},
        expected=None,
        msg="$log should return null for a missing value field",
    ),
    ExpressionTestCase(
        "missing_base",
        doc={"value": 10},
        expression={"$log": ["$value", MISSING]},
        expected=None,
        msg="$log should return null for a missing base field",
    ),
    ExpressionTestCase(
        "both_missing",
        doc={},
        expression={"$log": [MISSING, MISSING]},
        expected=None,
        msg="$log should return null when both value and base fields are missing",
    ),
    ExpressionTestCase(
        "null_value_missing_base",
        doc={"value": None},
        expression={"$log": ["$value", MISSING]},
        expected=None,
        msg="$log should return null when the value is null and the base is missing",
    ),
    ExpressionTestCase(
        "missing_value_null_base",
        doc={"base": None},
        expression={"$log": [MISSING, "$base"]},
        expected=None,
        msg="$log should return null when the value is missing and the base is null",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(LOG_NULL_TESTS))
def test_log_null(collection, test_case: ExpressionTestCase):
    """Test $log null and missing propagation cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
