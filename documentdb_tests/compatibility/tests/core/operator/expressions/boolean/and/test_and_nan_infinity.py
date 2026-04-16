"""Tests for $and with special numeric values — NaN, Infinity, negative zero, Decimal128."""

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
        "nan_neg_zero",
        expression={"$and": ["$a", -0.0]},
        doc={"a": Decimal128("NaN")},
        expected=False,
        msg="Decimal128 NaN is truthy but -0.0 is falsy",
    ),
    ExpressionTestCase(
        "inf_neg_zero_dec",
        expression={"$and": ["$a", Decimal128("-0")]},
        doc={"a": float("inf")},
        expected=False,
        msg="Infinity is truthy but Decimal128 -0 is falsy",
    ),
    ExpressionTestCase(
        "nan_null",
        expression={"$and": ["$a", None]},
        doc={"a": float("nan")},
        expected=False,
        msg="float NaN is truthy but null is falsy",
    ),
    ExpressionTestCase(
        "neg_zero_nan",
        expression={"$and": ["$a", Decimal128("NaN")]},
        doc={"a": -0.0},
        expected=False,
        msg="-0.0 is falsy even though Decimal128 NaN is truthy",
    ),
    ExpressionTestCase(
        "zero_int64_inf",
        expression={"$and": ["$a", DECIMAL128_INFINITY]},
        doc={"a": Int64(0)},
        expected=False,
        msg="Int64 zero is falsy even though Infinity is truthy",
    ),
    ExpressionTestCase(
        "nan_inf",
        expression={"$and": [FLOAT_NAN, DECIMAL128_INFINITY]},
        doc={"_id": 1},
        expected=True,
        msg="NaN and Infinity are both truthy",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DEC_NAN_INF_TESTS))
def test_and_decimal128_nan_inf_combos(collection, test):
    """Test $and with Decimal128 NaN/Inf and various numeric field values."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
