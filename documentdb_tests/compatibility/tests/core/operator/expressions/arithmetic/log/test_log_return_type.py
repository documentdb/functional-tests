"""Tests for $log return type across value and base numeric types."""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Return Type]: $log returns double unless either operand is decimal128, in which case it
# returns decimal.
LOG_RETURN_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "return_type_int32",
        doc={"value": 100, "base": 10},
        expression={"$type": {"$log": ["$value", "$base"]}},
        expected="double",
        msg="$log should return a double for int32 value and base",
    ),
    ExpressionTestCase(
        "return_type_int64",
        doc={"value": Int64(1000), "base": Int64(10)},
        expression={"$type": {"$log": ["$value", "$base"]}},
        expected="double",
        msg="$log should return a double for int64 value and base",
    ),
    ExpressionTestCase(
        "return_type_double",
        doc={"value": 10.0, "base": 10.0},
        expression={"$type": {"$log": ["$value", "$base"]}},
        expected="double",
        msg="$log should return a double for double value and base",
    ),
    ExpressionTestCase(
        "return_type_value_decimal",
        doc={"value": Decimal128("100"), "base": 10},
        expression={"$type": {"$log": ["$value", "$base"]}},
        expected="decimal",
        msg="$log should return a decimal for a decimal128 value and int32 base",
    ),
    ExpressionTestCase(
        "return_type_base_decimal",
        doc={"value": 100, "base": Decimal128("10")},
        expression={"$type": {"$log": ["$value", "$base"]}},
        expected="decimal",
        msg="$log should return a decimal for an int32 value and decimal128 base",
    ),
    ExpressionTestCase(
        "return_type_both_decimal",
        doc={"value": Decimal128("100"), "base": Decimal128("10")},
        expression={"$type": {"$log": ["$value", "$base"]}},
        expected="decimal",
        msg="$log should return a decimal for decimal128 value and base",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(LOG_RETURN_TYPE_TESTS))
def test_log_return_type(collection, test_case: ExpressionTestCase):
    """Test $log return type cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
