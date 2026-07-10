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

# Property [Return Type]: $abs preserves the numeric type of its input, for both negative inputs
# (an actual sign flip) and positive inputs (a no-op).
ABS_RETURN_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "return_type_positive_int32",
        doc={"value": 5},
        expression={"$type": {"$abs": "$value"}},
        expected="int",
        msg="$abs should preserve int32 type for a positive int32",
    ),
    ExpressionTestCase(
        "return_type_negative_int32",
        doc={"value": -5},
        expression={"$type": {"$abs": "$value"}},
        expected="int",
        msg="$abs should preserve int32 type for a negative int32",
    ),
    ExpressionTestCase(
        "return_type_positive_int64",
        doc={"value": Int64(5)},
        expression={"$type": {"$abs": "$value"}},
        expected="long",
        msg="$abs should preserve int64 type for a positive int64",
    ),
    ExpressionTestCase(
        "return_type_negative_int64",
        doc={"value": Int64(-5)},
        expression={"$type": {"$abs": "$value"}},
        expected="long",
        msg="$abs should preserve int64 type for a negative int64",
    ),
    ExpressionTestCase(
        "return_type_positive_double",
        doc={"value": 5.0},
        expression={"$type": {"$abs": "$value"}},
        expected="double",
        msg="$abs should preserve double type for a positive double",
    ),
    ExpressionTestCase(
        "return_type_negative_double",
        doc={"value": -5.0},
        expression={"$type": {"$abs": "$value"}},
        expected="double",
        msg="$abs should preserve double type for a negative double",
    ),
    ExpressionTestCase(
        "return_type_positive_decimal",
        doc={"value": Decimal128("5")},
        expression={"$type": {"$abs": "$value"}},
        expected="decimal",
        msg="$abs should preserve decimal128 type for a positive decimal128",
    ),
    ExpressionTestCase(
        "return_type_negative_decimal",
        doc={"value": Decimal128("-5")},
        expression={"$type": {"$abs": "$value"}},
        expected="decimal",
        msg="$abs should preserve decimal128 type for a negative decimal128",
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
