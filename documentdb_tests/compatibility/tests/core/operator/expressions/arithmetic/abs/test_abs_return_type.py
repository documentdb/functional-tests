"""Tests for $abs return type preservation."""

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

# Property [Return Type]: $abs preserves the numeric type of its input.
ABS_RETURN_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "return_type_int32",
        doc={"value": -5},
        expression={"$type": {"$abs": "$value"}},
        expected="int",
        msg="$abs should preserve int32 type",
    ),
    ExpressionTestCase(
        "return_type_int64",
        doc={"value": Int64(-5)},
        expression={"$type": {"$abs": "$value"}},
        expected="long",
        msg="$abs should preserve int64 type",
    ),
    ExpressionTestCase(
        "return_type_double",
        doc={"value": -5.0},
        expression={"$type": {"$abs": "$value"}},
        expected="double",
        msg="$abs should preserve double type",
    ),
    ExpressionTestCase(
        "return_type_decimal",
        doc={"value": Decimal128("-5")},
        expression={"$type": {"$abs": "$value"}},
        expected="decimal",
        msg="$abs should preserve decimal128 type",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(ABS_RETURN_TYPE_TESTS))
def test_abs_return_type(collection, test_case: ExpressionTestCase):
    """Test $abs return type preservation cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
