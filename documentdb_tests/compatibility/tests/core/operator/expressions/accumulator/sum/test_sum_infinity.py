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
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [Infinity Handling]: $sum propagates infinity correctly and
# produces NaN when positive and negative infinity are combined.
SUM_INFINITY_TESTS: list[ExpressionTestCase] = [
    # Sole / identity.
    ExpressionTestCase(
        "inf_sole_double_pos",
        expression={"$sum": "$a"},
        doc={"a": FLOAT_INFINITY},
        expected=FLOAT_INFINITY,
        msg="$sum should return double Infinity unchanged",
    ),
    ExpressionTestCase(
        "inf_sole_double_neg",
        expression={"$sum": "$a"},
        doc={"a": FLOAT_NEGATIVE_INFINITY},
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$sum should return double -Infinity unchanged",
    ),
    ExpressionTestCase(
        "inf_sole_decimal128_pos",
        expression={"$sum": "$a"},
        doc={"a": DECIMAL128_INFINITY},
        expected=DECIMAL128_INFINITY,
        msg="$sum should return Decimal128 Infinity unchanged",
    ),
    ExpressionTestCase(
        "inf_sole_decimal128_neg",
        expression={"$sum": "$a"},
        doc={"a": DECIMAL128_NEGATIVE_INFINITY},
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="$sum should return Decimal128 -Infinity unchanged",
    ),
    # Propagation over finite.
    ExpressionTestCase(
        "inf_double_pos_with_int",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": FLOAT_INFINITY, "b": 5},
        expected=FLOAT_INFINITY,
        msg="$sum should return Infinity when double +Inf is summed with int",
    ),
    ExpressionTestCase(
        "inf_double_pos_with_int64",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": FLOAT_INFINITY, "b": Int64(5)},
        expected=FLOAT_INFINITY,
        msg="$sum should return Infinity when double +Inf is summed with int64",
    ),
    ExpressionTestCase(
        "inf_double_pos_with_double",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": FLOAT_INFINITY, "b": 1.0},
        expected=FLOAT_INFINITY,
        msg="$sum should return Infinity when double +Inf is summed with double",
    ),
    ExpressionTestCase(
        "inf_double_pos_with_decimal128",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": FLOAT_INFINITY, "b": Decimal128("5")},
        expected=DECIMAL128_INFINITY,
        msg="$sum should return Decimal128 Infinity when double +Inf is summed with Decimal128",
    ),
    ExpressionTestCase(
        "inf_double_neg_with_int",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": FLOAT_NEGATIVE_INFINITY, "b": 5},
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$sum should return -Infinity when double -Inf is summed with int",
    ),
    ExpressionTestCase(
        "inf_double_neg_with_int64",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": FLOAT_NEGATIVE_INFINITY, "b": Int64(5)},
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$sum should return -Infinity when double -Inf is summed with int64",
    ),
    ExpressionTestCase(
        "inf_double_neg_with_double",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": FLOAT_NEGATIVE_INFINITY, "b": 1.0},
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$sum should return -Infinity when double -Inf is summed with double",
    ),
    ExpressionTestCase(
        "inf_double_neg_with_decimal128",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": FLOAT_NEGATIVE_INFINITY, "b": Decimal128("5")},
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="$sum should return Decimal128 -Infinity when double -Inf is summed with Decimal128",
    ),
    ExpressionTestCase(
        "inf_decimal128_pos_with_int",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_INFINITY, "b": 5},
        expected=DECIMAL128_INFINITY,
        msg="$sum should return Decimal128 Infinity when summed with int",
    ),
    ExpressionTestCase(
        "inf_decimal128_pos_with_int64",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_INFINITY, "b": Int64(5)},
        expected=DECIMAL128_INFINITY,
        msg="$sum should return Decimal128 Infinity when summed with int64",
    ),
    ExpressionTestCase(
        "inf_decimal128_pos_with_double",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_INFINITY, "b": 1.0},
        expected=DECIMAL128_INFINITY,
        msg="$sum should return Decimal128 Infinity when summed with double",
    ),
    ExpressionTestCase(
        "inf_decimal128_pos_with_decimal128",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_INFINITY, "b": Decimal128("5")},
        expected=DECIMAL128_INFINITY,
        msg="$sum should return Decimal128 Infinity when summed with Decimal128",
    ),
    ExpressionTestCase(
        "inf_decimal128_neg_with_int",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_NEGATIVE_INFINITY, "b": 5},
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="$sum should return Decimal128 -Infinity when summed with int",
    ),
    ExpressionTestCase(
        "inf_decimal128_neg_with_int64",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_NEGATIVE_INFINITY, "b": Int64(5)},
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="$sum should return Decimal128 -Infinity when summed with int64",
    ),
    ExpressionTestCase(
        "inf_decimal128_neg_with_double",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_NEGATIVE_INFINITY, "b": 1.0},
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="$sum should return Decimal128 -Infinity when summed with double",
    ),
    ExpressionTestCase(
        "inf_decimal128_neg_with_decimal128",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_NEGATIVE_INFINITY, "b": Decimal128("5")},
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="$sum should return Decimal128 -Infinity when summed with Decimal128",
    ),
    # Reverse order: finite first, infinity second.
    ExpressionTestCase(
        "inf_int_with_double_pos",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": 5, "b": FLOAT_INFINITY},
        expected=FLOAT_INFINITY,
        msg="$sum should return Infinity when int is summed with double +Inf",
    ),
    ExpressionTestCase(
        "inf_int_with_decimal128_pos",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": 5, "b": DECIMAL128_INFINITY},
        expected=DECIMAL128_INFINITY,
        msg="$sum should return Decimal128 Infinity when int is summed with Decimal128 +Inf",
    ),
    ExpressionTestCase(
        "inf_int_with_double_neg",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": 5, "b": FLOAT_NEGATIVE_INFINITY},
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$sum should return -Infinity when int is summed with double -Inf",
    ),
    ExpressionTestCase(
        "inf_int_with_decimal128_neg",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": 5, "b": DECIMAL128_NEGATIVE_INFINITY},
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="$sum should return Decimal128 -Infinity when int is summed with Decimal128 -Inf",
    ),
    # Same-sign pairs.
    ExpressionTestCase(
        "inf_double_pos_pair",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": FLOAT_INFINITY, "b": FLOAT_INFINITY},
        expected=FLOAT_INFINITY,
        msg="$sum should return Infinity when +Inf + +Inf",
    ),
    ExpressionTestCase(
        "inf_double_neg_pair",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": FLOAT_NEGATIVE_INFINITY, "b": FLOAT_NEGATIVE_INFINITY},
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$sum should return -Infinity when -Inf + -Inf",
    ),
    ExpressionTestCase(
        "inf_decimal128_pos_pair",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_INFINITY, "b": DECIMAL128_INFINITY},
        expected=DECIMAL128_INFINITY,
        msg="$sum should return Decimal128 Infinity when +Inf + +Inf",
    ),
    ExpressionTestCase(
        "inf_decimal128_neg_pair",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_NEGATIVE_INFINITY, "b": DECIMAL128_NEGATIVE_INFINITY},
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="$sum should return Decimal128 -Infinity when -Inf + -Inf",
    ),
    # Cross-type same-sign pairs.
    ExpressionTestCase(
        "inf_cross_double_pos_decimal128_pos",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": FLOAT_INFINITY, "b": DECIMAL128_INFINITY},
        expected=DECIMAL128_INFINITY,
        msg="$sum of double +Inf and Decimal128 +Inf should return Decimal128 Infinity",
    ),
    ExpressionTestCase(
        "inf_cross_double_neg_decimal128_neg",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": FLOAT_NEGATIVE_INFINITY, "b": DECIMAL128_NEGATIVE_INFINITY},
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="$sum of double -Inf and Decimal128 -Inf should return Decimal128 -Infinity",
    ),
    ExpressionTestCase(
        "inf_cross_decimal128_pos_double_pos",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_INFINITY, "b": FLOAT_INFINITY},
        expected=DECIMAL128_INFINITY,
        msg="$sum of Decimal128 +Inf and double +Inf should return Decimal128 Infinity",
    ),
    ExpressionTestCase(
        "inf_cross_decimal128_neg_double_neg",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_NEGATIVE_INFINITY, "b": FLOAT_NEGATIVE_INFINITY},
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="$sum of Decimal128 -Inf and double -Inf should return Decimal128 -Infinity",
    ),
    # Opposite-sign pairs (produce NaN).
    ExpressionTestCase(
        "inf_double_pos_neg",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": FLOAT_INFINITY, "b": FLOAT_NEGATIVE_INFINITY},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$sum should return NaN when double +Inf + double -Inf",
    ),
    ExpressionTestCase(
        "inf_double_neg_pos",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": FLOAT_NEGATIVE_INFINITY, "b": FLOAT_INFINITY},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$sum should return NaN when double -Inf + double +Inf",
    ),
    ExpressionTestCase(
        "inf_decimal128_pos_neg",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_INFINITY, "b": DECIMAL128_NEGATIVE_INFINITY},
        expected=DECIMAL128_NAN,
        msg="$sum should return Decimal128 NaN when Decimal128 +Inf + Decimal128 -Inf",
    ),
    ExpressionTestCase(
        "inf_decimal128_neg_pos",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_NEGATIVE_INFINITY, "b": DECIMAL128_INFINITY},
        expected=DECIMAL128_NAN,
        msg="$sum should return Decimal128 NaN when Decimal128 -Inf + Decimal128 +Inf",
    ),
    # Cross-type opposite-sign pairs (produce NaN).
    ExpressionTestCase(
        "inf_cross_double_pos_decimal128_neg",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": FLOAT_INFINITY, "b": DECIMAL128_NEGATIVE_INFINITY},
        expected=DECIMAL128_NAN,
        msg="$sum of double +Inf and Decimal128 -Inf should return Decimal128 NaN",
    ),
    ExpressionTestCase(
        "inf_cross_double_neg_decimal128_pos",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": FLOAT_NEGATIVE_INFINITY, "b": DECIMAL128_INFINITY},
        expected=DECIMAL128_NAN,
        msg="$sum of double -Inf and Decimal128 +Inf should return Decimal128 NaN",
    ),
    ExpressionTestCase(
        "inf_cross_decimal128_pos_double_neg",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_INFINITY, "b": FLOAT_NEGATIVE_INFINITY},
        expected=DECIMAL128_NAN,
        msg="$sum of Decimal128 +Inf and double -Inf should return Decimal128 NaN",
    ),
    ExpressionTestCase(
        "inf_cross_decimal128_neg_double_pos",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_NEGATIVE_INFINITY, "b": FLOAT_INFINITY},
        expected=DECIMAL128_NAN,
        msg="$sum of Decimal128 -Inf and double +Inf should return Decimal128 NaN",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(SUM_INFINITY_TESTS))
def test_sum_infinity(collection, test_case: ExpressionTestCase):
    """Test $sum infinity propagation."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
