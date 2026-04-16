"""Tests for $or with special numeric values — NaN, Infinity, negative zero, Decimal128."""

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
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    FLOAT_NAN,
)

DEC_NAN_INF_TESTS = [
    ExpressionTestCase(
        "neg_zero_or_neg_zero_dec",
        expression={"$or": ["$a", Decimal128("-0")]},
        doc={"a": -0.0},
        expected=False,
        msg="Double -0.0 or Decimal128 -0 — both falsy",
    ),
    ExpressionTestCase(
        "zero_or_neg_zero",
        expression={"$or": ["$a", -0.0]},
        doc={"a": Decimal128("0")},
        expected=False,
        msg="Decimal128 0 or double -0.0 — both falsy",
    ),
    ExpressionTestCase(
        "neg_zero_or_nan",
        expression={"$or": ["$a", Decimal128("NaN")]},
        doc={"a": -0.0},
        expected=True,
        msg="-0.0 is falsy but Decimal128 NaN is truthy",
    ),
    ExpressionTestCase(
        "neg_zero_or_inf",
        expression={"$or": ["$a", DECIMAL128_INFINITY]},
        doc={"a": Decimal128("-0")},
        expected=True,
        msg="Decimal128 -0 is falsy but Infinity is truthy",
    ),
    ExpressionTestCase(
        "zero_int64_or_nan",
        expression={"$or": ["$a", FLOAT_NAN]},
        doc={"a": Int64(0)},
        expected=True,
        msg="Int64 zero is falsy but float NaN is truthy",
    ),
    ExpressionTestCase(
        "null_or_inf",
        expression={"$or": ["$a", Decimal128("Infinity")]},
        doc={"a": None},
        expected=True,
        msg="null is falsy but Infinity is truthy",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DEC_NAN_INF_TESTS))
def test_or_decimal128_nan_inf_combos(collection, test):
    """Test $or with Decimal128 NaN/Inf and various numeric field values."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
