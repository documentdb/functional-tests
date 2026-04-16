from __future__ import annotations

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
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [NaN Handling]: $sum propagates NaN when any input is NaN,
# regardless of other values in the array.
SUM_NAN_TESTS: list[ExpressionTestCase] = [
    # Sole / identity.
    ExpressionTestCase(
        "nan_sole_double",
        expression={"$sum": "$a"},
        doc={"a": FLOAT_NAN},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$sum should return double NaN unchanged",
    ),
    ExpressionTestCase(
        "nan_sole_decimal128",
        expression={"$sum": "$a"},
        doc={"a": DECIMAL128_NAN},
        expected=DECIMAL128_NAN,
        msg="$sum should return Decimal128 NaN unchanged",
    ),
    ExpressionTestCase(
        "nan_sole_decimal128_negative",
        expression={"$sum": "$a"},
        doc={"a": DECIMAL128_NEGATIVE_NAN},
        expected=DECIMAL128_NEGATIVE_NAN,
        msg="$sum should preserve Decimal128 -NaN sign bit",
    ),
    # Propagation over finite.
    ExpressionTestCase(
        "nan_double_with_int",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": FLOAT_NAN, "b": 5},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$sum should return NaN when double NaN is summed with int",
    ),
    ExpressionTestCase(
        "nan_double_with_int64",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": FLOAT_NAN, "b": Int64(5)},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$sum should return NaN when double NaN is summed with int64",
    ),
    ExpressionTestCase(
        "nan_double_with_double",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": FLOAT_NAN, "b": 5.0},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$sum should return NaN when double NaN is summed with double",
    ),
    ExpressionTestCase(
        "nan_double_with_decimal128",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": FLOAT_NAN, "b": Decimal128("5")},
        expected=DECIMAL128_NAN,
        msg="$sum should return Decimal128 NaN when double NaN is summed with Decimal128",
    ),
    ExpressionTestCase(
        "nan_decimal128_with_int",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_NAN, "b": 5},
        expected=DECIMAL128_NAN,
        msg="$sum should return Decimal128 NaN when summed with int",
    ),
    ExpressionTestCase(
        "nan_decimal128_with_int64",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_NAN, "b": Int64(5)},
        expected=DECIMAL128_NAN,
        msg="$sum should return Decimal128 NaN when summed with int64",
    ),
    ExpressionTestCase(
        "nan_decimal128_with_double",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_NAN, "b": 5.0},
        expected=DECIMAL128_NAN,
        msg="$sum should return Decimal128 NaN when summed with double",
    ),
    ExpressionTestCase(
        "nan_decimal128_with_decimal128",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_NAN, "b": Decimal128("5")},
        expected=DECIMAL128_NAN,
        msg="$sum should return Decimal128 NaN when summed with Decimal128",
    ),
    ExpressionTestCase(
        "nan_decimal128_negative_with_int",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_NEGATIVE_NAN, "b": 5},
        expected=DECIMAL128_NEGATIVE_NAN,
        msg="$sum should return Decimal128 -NaN when summed with int",
    ),
    ExpressionTestCase(
        "nan_decimal128_negative_with_int64",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_NEGATIVE_NAN, "b": Int64(5)},
        expected=DECIMAL128_NEGATIVE_NAN,
        msg="$sum should return Decimal128 -NaN when summed with int64",
    ),
    ExpressionTestCase(
        "nan_decimal128_negative_with_double",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_NEGATIVE_NAN, "b": 5.0},
        expected=DECIMAL128_NEGATIVE_NAN,
        msg="$sum should return Decimal128 -NaN when summed with double",
    ),
    ExpressionTestCase(
        "nan_decimal128_negative_with_decimal128",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_NEGATIVE_NAN, "b": Decimal128("5")},
        expected=DECIMAL128_NEGATIVE_NAN,
        msg="$sum should return Decimal128 -NaN when summed with Decimal128",
    ),
    # Dominance over infinity.
    ExpressionTestCase(
        "nan_double_with_double_inf",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": FLOAT_NAN, "b": FLOAT_INFINITY},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$sum should return NaN when double NaN is summed with Infinity",
    ),
    ExpressionTestCase(
        "nan_double_with_double_neg_inf",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": FLOAT_NAN, "b": FLOAT_NEGATIVE_INFINITY},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$sum should return NaN when double NaN is summed with -Infinity",
    ),
    ExpressionTestCase(
        "nan_double_with_decimal128_inf",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": FLOAT_NAN, "b": DECIMAL128_INFINITY},
        expected=DECIMAL128_NAN,
        msg="$sum should return Decimal128 NaN when double NaN is summed with Decimal128 Infinity",
    ),
    ExpressionTestCase(
        "nan_double_with_decimal128_neg_inf",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": FLOAT_NAN, "b": DECIMAL128_NEGATIVE_INFINITY},
        expected=DECIMAL128_NAN,
        msg="$sum should return Decimal128 NaN when double NaN is summed with Decimal128 -Infinity",
    ),
    ExpressionTestCase(
        "nan_decimal128_with_double_inf",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_NAN, "b": FLOAT_INFINITY},
        expected=DECIMAL128_NAN,
        msg="$sum should return Decimal128 NaN when summed with double Infinity",
    ),
    ExpressionTestCase(
        "nan_decimal128_with_double_neg_inf",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_NAN, "b": FLOAT_NEGATIVE_INFINITY},
        expected=DECIMAL128_NAN,
        msg="$sum should return Decimal128 NaN when summed with double -Infinity",
    ),
    ExpressionTestCase(
        "nan_decimal128_with_decimal128_inf",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_NAN, "b": DECIMAL128_INFINITY},
        expected=DECIMAL128_NAN,
        msg="$sum should return Decimal128 NaN when summed with Decimal128 Infinity",
    ),
    ExpressionTestCase(
        "nan_decimal128_with_decimal128_neg_inf",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_NAN, "b": DECIMAL128_NEGATIVE_INFINITY},
        expected=DECIMAL128_NAN,
        msg="$sum should return Decimal128 NaN when summed with Decimal128 -Infinity",
    ),
    ExpressionTestCase(
        "nan_decimal128_neg_with_double_inf",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_NEGATIVE_NAN, "b": FLOAT_INFINITY},
        expected=DECIMAL128_NEGATIVE_NAN,
        msg="$sum should return Decimal128 -NaN when summed with double Infinity",
    ),
    ExpressionTestCase(
        "nan_decimal128_neg_with_double_neg_inf",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_NEGATIVE_NAN, "b": FLOAT_NEGATIVE_INFINITY},
        expected=DECIMAL128_NEGATIVE_NAN,
        msg="$sum should return Decimal128 -NaN when summed with double -Infinity",
    ),
    ExpressionTestCase(
        "nan_decimal128_neg_with_decimal128_inf",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_NEGATIVE_NAN, "b": DECIMAL128_INFINITY},
        expected=DECIMAL128_NEGATIVE_NAN,
        msg="$sum should return Decimal128 -NaN when summed with Decimal128 Infinity",
    ),
    ExpressionTestCase(
        "nan_decimal128_neg_with_decimal128_neg_inf",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_NEGATIVE_NAN, "b": DECIMAL128_NEGATIVE_INFINITY},
        expected=DECIMAL128_NEGATIVE_NAN,
        msg="$sum should return Decimal128 -NaN when summed with Decimal128 -Infinity",
    ),
    # Reverse order: NaN as second operand.
    ExpressionTestCase(
        "nan_int_with_double_nan",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": 5, "b": FLOAT_NAN},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$sum should return NaN when int is summed with double NaN",
    ),
    ExpressionTestCase(
        "nan_int_with_decimal128_nan",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": 5, "b": DECIMAL128_NAN},
        expected=DECIMAL128_NAN,
        msg="$sum should return Decimal128 NaN when int is summed with Decimal128 NaN",
    ),
    ExpressionTestCase(
        "nan_double_inf_with_double_nan",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": FLOAT_INFINITY, "b": FLOAT_NAN},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$sum should return NaN when Infinity is summed with double NaN",
    ),
    ExpressionTestCase(
        "nan_double_inf_with_decimal128_nan",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": FLOAT_INFINITY, "b": DECIMAL128_NAN},
        expected=DECIMAL128_NAN,
        msg="$sum should return Decimal128 NaN when Infinity is summed with Decimal128 NaN",
    ),
    # NaN + NaN.
    ExpressionTestCase(
        "nan_double_pair",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": FLOAT_NAN, "b": FLOAT_NAN},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$sum of two double NaN values should return NaN",
    ),
    ExpressionTestCase(
        "nan_decimal128_pair",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_NAN, "b": DECIMAL128_NAN},
        expected=DECIMAL128_NAN,
        msg="$sum of two Decimal128 NaN values should return Decimal128 NaN",
    ),
    ExpressionTestCase(
        "nan_cross_double_decimal128",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": FLOAT_NAN, "b": DECIMAL128_NAN},
        expected=DECIMAL128_NAN,
        msg="$sum of double NaN and Decimal128 NaN should return Decimal128 NaN",
    ),
    ExpressionTestCase(
        "nan_decimal128_neg_pair",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_NEGATIVE_NAN, "b": DECIMAL128_NEGATIVE_NAN},
        expected=DECIMAL128_NEGATIVE_NAN,
        msg="$sum of two Decimal128 -NaN values should return Decimal128 -NaN",
    ),
    ExpressionTestCase(
        "nan_decimal128_neg_with_decimal128_nan",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_NEGATIVE_NAN, "b": DECIMAL128_NAN},
        expected=DECIMAL128_NEGATIVE_NAN,
        msg="$sum of Decimal128 -NaN and Decimal128 NaN should return Decimal128 -NaN",
    ),
    ExpressionTestCase(
        "nan_decimal128_with_decimal128_neg_nan",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_NAN, "b": DECIMAL128_NEGATIVE_NAN},
        expected=DECIMAL128_NAN,
        msg="$sum of Decimal128 NaN and Decimal128 -NaN should return Decimal128 NaN",
    ),
    ExpressionTestCase(
        "nan_cross_double_decimal128_neg",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": FLOAT_NAN, "b": DECIMAL128_NEGATIVE_NAN},
        expected=DECIMAL128_NEGATIVE_NAN,
        msg="$sum of double NaN and Decimal128 -NaN should return Decimal128 -NaN",
    ),
    ExpressionTestCase(
        "nan_decimal128_neg_with_double_nan",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_NEGATIVE_NAN, "b": FLOAT_NAN},
        expected=DECIMAL128_NEGATIVE_NAN,
        msg="$sum of Decimal128 -NaN and double NaN should return Decimal128 -NaN",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(SUM_NAN_TESTS))
def test_sum_nan(collection, test_case: ExpressionTestCase):
    """Test $sum NaN propagation."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
