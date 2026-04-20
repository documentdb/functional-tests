"""
Common tests for comparison operators.

Covers behaviors shared across $eq, $ne, $gt, $gte, $lt, $lte, $cmp —
such as array index path resolution in aggregation expressions.
"""

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

ARRAY_INDEX_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "eq_arr_dot_0_resolves_empty",
        expression={"$eq": ["$arr.0", 10]},
        doc={"arr": [10, 20, 30]},
        expected=False,
        msg="$eq: $arr.0 resolves to [] not index 0, [] != 10",
    ),
    ExpressionTestCase(
        "ne_arr_dot_0_resolves_empty",
        expression={"$ne": ["$arr.0", 10]},
        doc={"arr": [10, 20, 30]},
        expected=True,
        msg="$ne: $arr.0 resolves to [] not index 0, [] != 10",
    ),
    ExpressionTestCase(
        "gt_arr_dot_0_resolves_empty",
        expression={"$gt": ["$arr.0", 10]},
        doc={"arr": [10, 20, 30]},
        expected=True,
        msg="$gt: $arr.0 resolves to [] not index 0, array > number in BSON order",
    ),
    ExpressionTestCase(
        "gte_arr_dot_0_resolves_empty",
        expression={"$gte": ["$arr.0", 10]},
        doc={"arr": [10, 20, 30]},
        expected=True,
        msg="$gte: $arr.0 resolves to [] not index 0, array >= number in BSON order",
    ),
    ExpressionTestCase(
        "lt_arr_dot_0_resolves_empty",
        expression={"$lt": ["$arr.0", 10]},
        doc={"arr": [10, 20, 30]},
        expected=False,
        msg="$lt: $arr.0 resolves to [] not index 0, array not < number in BSON order",
    ),
    ExpressionTestCase(
        "lte_arr_dot_0_resolves_empty",
        expression={"$lte": ["$arr.0", 10]},
        doc={"arr": [10, 20, 30]},
        expected=False,
        msg="$lte: $arr.0 resolves to [] not index 0, array not <= number in BSON order",
    ),
    ExpressionTestCase(
        "cmp_arr_dot_0_resolves_empty",
        expression={"$cmp": ["$arr.0", 10]},
        doc={"arr": [10, 20, 30]},
        expected=1,
        msg="$cmp: $arr.0 resolves to [] not index 0, array > number in BSON order",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ARRAY_INDEX_PATH_TESTS))
def test_comparisons_array_index_path(collection, test):
    """Test that numeric path components don't index arrays in aggregation expressions."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


DECIMAL128_CROSS_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "dec_nan_cmp_dec_neg_nan",
        expression={"$cmp": [Decimal128("NaN"), Decimal128("-NaN")]},
        expected=0,
        msg="Decimal128 NaN and -NaN are equal",
    ),
    ExpressionTestCase(
        "dec_inf_eq_double_inf",
        expression={"$eq": [Decimal128("Infinity"), float("inf")]},
        expected=True,
        msg="Decimal128 Infinity == double Infinity",
    ),
    ExpressionTestCase(
        "dec_inf_cmp_double_inf",
        expression={"$cmp": [Decimal128("Infinity"), float("inf")]},
        expected=0,
        msg="Decimal128 Infinity and double Infinity are equal",
    ),
    ExpressionTestCase(
        "dec_neg_inf_eq_double_neg_inf",
        expression={"$eq": [Decimal128("-Infinity"), float("-inf")]},
        expected=True,
        msg="Decimal128 -Infinity == double -Infinity",
    ),
    ExpressionTestCase(
        "dec_nan_cmp_float_nan",
        expression={"$cmp": [Decimal128("NaN"), float("nan")]},
        expected=0,
        msg="Decimal128 NaN and float NaN are equal",
    ),
    ExpressionTestCase(
        "dec_nan_lt_int",
        expression={"$lt": [Decimal128("NaN"), 1]},
        expected=True,
        msg="Decimal128 NaN < int",
    ),
    ExpressionTestCase(
        "int_gt_dec_nan",
        expression={"$gt": [1, Decimal128("NaN")]},
        expected=True,
        msg="int > Decimal128 NaN",
    ),
    ExpressionTestCase(
        "int_gte_dec_nan",
        expression={"$gte": [1, Decimal128("NaN")]},
        expected=True,
        msg="int >= Decimal128 NaN",
    ),
    ExpressionTestCase(
        "dec_nan_lte_int",
        expression={"$lte": [Decimal128("NaN"), 1]},
        expected=True,
        msg="Decimal128 NaN <= int",
    ),
    ExpressionTestCase(
        "dec_nan_ne_int",
        expression={"$ne": [Decimal128("NaN"), 1]},
        expected=True,
        msg="Decimal128 NaN != int",
    ),
    ExpressionTestCase(
        "dec_nan_lt_dec_inf",
        expression={"$lt": [Decimal128("NaN"), Decimal128("Infinity")]},
        expected=True,
        msg="Decimal128 NaN < Decimal128 Infinity",
    ),
    ExpressionTestCase(
        "dec_inf_gt_dec_nan",
        expression={"$gt": [Decimal128("Infinity"), Decimal128("NaN")]},
        expected=True,
        msg="Decimal128 Infinity > Decimal128 NaN",
    ),
    ExpressionTestCase(
        "dec_inf_gte_dec_nan",
        expression={"$gte": [Decimal128("Infinity"), Decimal128("NaN")]},
        expected=True,
        msg="Decimal128 Infinity >= Decimal128 NaN",
    ),
    ExpressionTestCase(
        "dec_nan_lte_dec_inf",
        expression={"$lte": [Decimal128("NaN"), Decimal128("Infinity")]},
        expected=True,
        msg="Decimal128 NaN <= Decimal128 Infinity",
    ),
    ExpressionTestCase(
        "dec_nan_ne_dec_inf",
        expression={"$ne": [Decimal128("NaN"), Decimal128("Infinity")]},
        expected=True,
        msg="Decimal128 NaN != Decimal128 Infinity",
    ),
    ExpressionTestCase(
        "dec_nan_lt_double_neg_inf",
        expression={"$lt": [Decimal128("NaN"), float("-inf")]},
        expected=True,
        msg="Decimal128 NaN < double -Infinity",
    ),
    ExpressionTestCase(
        "double_neg_inf_gt_dec_nan",
        expression={"$gt": [float("-inf"), Decimal128("NaN")]},
        expected=True,
        msg="double -Infinity > Decimal128 NaN",
    ),
    ExpressionTestCase(
        "double_neg_inf_gte_dec_nan",
        expression={"$gte": [float("-inf"), Decimal128("NaN")]},
        expected=True,
        msg="double -Infinity >= Decimal128 NaN",
    ),
    ExpressionTestCase(
        "dec_nan_lte_double_neg_inf",
        expression={"$lte": [Decimal128("NaN"), float("-inf")]},
        expected=True,
        msg="Decimal128 NaN <= double -Infinity",
    ),
    ExpressionTestCase(
        "dec_nan_ne_double_neg_inf",
        expression={"$ne": [Decimal128("NaN"), float("-inf")]},
        expected=True,
        msg="Decimal128 NaN != double -Infinity",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DECIMAL128_CROSS_TYPE_TESTS))
def test_comparisons_decimal128_cross_type(collection, test):
    """Test Decimal128 NaN/Infinity cross-type comparisons."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
