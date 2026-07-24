"""Tests for $exp return type across numeric input types."""

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

# Property [Return Type]: $exp returns double for int32, int64, and double inputs, and decimal for
# decimal128 inputs.
EXP_RETURN_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "return_type_int32",
        doc={"value": 1},
        expression={"$type": {"$exp": "$value"}},
        expected="double",
        msg="$exp should return a double for an int32 input",
    ),
    ExpressionTestCase(
        "return_type_int64",
        doc={"value": Int64(1)},
        expression={"$type": {"$exp": "$value"}},
        expected="double",
        msg="$exp should return a double for an int64 input",
    ),
    ExpressionTestCase(
        "return_type_double",
        doc={"value": 1.0},
        expression={"$type": {"$exp": "$value"}},
        expected="double",
        msg="$exp should return a double for a double input",
    ),
    ExpressionTestCase(
        "return_type_decimal",
        doc={"value": Decimal128("1")},
        expression={"$type": {"$exp": "$value"}},
        expected="decimal",
        msg="$exp should return a decimal for a decimal128 input",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(EXP_RETURN_TYPE_TESTS))
def test_exp_return_type(collection, test_case: ExpressionTestCase):
    """Test $exp return type cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
