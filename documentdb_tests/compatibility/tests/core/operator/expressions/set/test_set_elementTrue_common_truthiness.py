"""
Common truthiness tests for $allElementsTrue and $anyElementTrue.

Single-element arrays produce identical results for both operators.
This file tests the shared truthiness engine once, covering falsy values,
truthy values, NaN, Infinity, negative zero, Decimal128 zero variants,
numeric boundaries, per-type coverage, and duplicates.

Divergent behavior (multi-element arrays, empty arrays) is tested
in each operator's own truthiness file.
"""

from datetime import datetime

import pytest
from bson import Binary, Code, Decimal128, Int64, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MAX,
    DECIMAL128_MAX_NEGATIVE,
    DECIMAL128_MIN,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_SMALL_EXPONENT,
    DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEAR_MIN,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
    NUMERIC,
    ZERO_NUMERIC,
)

OPERATORS = ["$allElementsTrue", "$anyElementTrue"]


def _build_expr(op, array):
    return {op: [array]}


def _id(op):
    return "all" if op == "$allElementsTrue" else "any"


# ---------------------------------------------------------------------------
# Falsy values — sole element returns false for both operators
# ---------------------------------------------------------------------------
FALSY_VALUES = [
    ("false", [False]),
    ("int_zero", [0]),
    ("long_zero", [Int64(0)]),
    ("double_zero", [0.0]),
    ("decimal_zero", [Decimal128("0")]),
    ("null", [None]),
]


@pytest.mark.parametrize("op", OPERATORS)
@pytest.mark.parametrize("name,array", FALSY_VALUES, ids=[f[0] for f in FALSY_VALUES])
def test_set_common_falsy(collection, op, name, array):
    """Test both set operators return false for sole falsy element."""
    result = execute_expression(collection, _build_expr(op, array))
    assert_expression_result(result, expected=False, msg=f"{op} {name} should be false")


# ---------------------------------------------------------------------------
# Truthy values — sole element returns true for both operators
# ---------------------------------------------------------------------------
TRUTHY_VALUES = [
    ("true", [True]),
    ("int_1", [1]),
    ("int_neg1", [-1]),
    ("long_1", [Int64(1)]),
    ("long_neg1", [Int64(-1)]),
    ("double_1_5", [1.5]),
    ("double_neg1_5", [-1.5]),
    ("decimal_1", [Decimal128("1")]),
    ("decimal_neg1", [Decimal128("-1")]),
    ("empty_string", [""]),
    ("string", ["hello"]),
    ("empty_nested_array", [[]]),
    ("empty_object", [{}]),
    ("object", [{"a": 1}]),
    ("objectid", [ObjectId("507f1f77bcf86cd799439011")]),
    ("date", [datetime(2017, 1, 1)]),
    ("timestamp", [Timestamp(1, 1)]),
    ("bindata", [Binary(b"", 0)]),
    ("regex", [Regex("pattern")]),
    ("javascript", [Code("function(){}")]),
    ("timestamp_zero", [Timestamp(0, 0)]),
]


@pytest.mark.parametrize("op", OPERATORS)
@pytest.mark.parametrize("name,array", TRUTHY_VALUES, ids=[t[0] for t in TRUTHY_VALUES])
def test_set_common_truthy(collection, op, name, array):
    """Test both set operators return true for sole truthy element."""
    result = execute_expression(collection, _build_expr(op, array))
    assert_expression_result(result, expected=True, msg=f"{op} {name} should be true")


# ---------------------------------------------------------------------------
# MinKey/MaxKey truthy — must use field reference
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("op", OPERATORS)
def test_set_common_minkey_truthy(collection, op):
    """Test both set operators treat MinKey as truthy."""
    from bson import MinKey

    result = execute_expression_with_insert(collection, {op: ["$arr"]}, {"arr": [MinKey()]})
    assert_expression_result(result, expected=True, msg=f"{op} MinKey should be true")


@pytest.mark.parametrize("op", OPERATORS)
def test_set_common_maxkey_truthy(collection, op):
    """Test both set operators treat MaxKey as truthy."""
    from bson import MaxKey

    result = execute_expression_with_insert(collection, {op: ["$arr"]}, {"arr": [MaxKey()]})
    assert_expression_result(result, expected=True, msg=f"{op} MaxKey should be true")


# ---------------------------------------------------------------------------
# NaN is truthy (sole element)
# ---------------------------------------------------------------------------
NAN_VALUES = [
    ("nan_double", [FLOAT_NAN]),
    ("nan_decimal", [DECIMAL128_NAN]),
]


@pytest.mark.parametrize("op", OPERATORS)
@pytest.mark.parametrize("name,array", NAN_VALUES, ids=[n[0] for n in NAN_VALUES])
def test_set_common_nan_truthy(collection, op, name, array):
    """Test both set operators treat NaN as truthy."""
    result = execute_expression(collection, _build_expr(op, array))
    assert_expression_result(result, expected=True, msg=f"{op} {name} should be true")


# ---------------------------------------------------------------------------
# Infinity is truthy (sole element)
# ---------------------------------------------------------------------------
INF_VALUES = [
    ("inf_double", [FLOAT_INFINITY]),
    ("neg_inf_double", [FLOAT_NEGATIVE_INFINITY]),
    ("inf_decimal", [DECIMAL128_INFINITY]),
    ("neg_inf_decimal", [DECIMAL128_NEGATIVE_INFINITY]),
]


@pytest.mark.parametrize("op", OPERATORS)
@pytest.mark.parametrize("name,array", INF_VALUES, ids=[i[0] for i in INF_VALUES])
def test_set_common_infinity_truthy(collection, op, name, array):
    """Test both set operators treat Infinity as truthy."""
    result = execute_expression(collection, _build_expr(op, array))
    assert_expression_result(result, expected=True, msg=f"{op} {name} should be true")


# ---------------------------------------------------------------------------
# Negative zero is falsy (sole element)
# ---------------------------------------------------------------------------
NEG_ZERO_VALUES = [
    ("neg_zero_double", [DOUBLE_NEGATIVE_ZERO]),
    ("neg_zero_decimal", [DECIMAL128_NEGATIVE_ZERO]),
    ("neg_zero_decimal_0_0", [Decimal128("-0.0")]),
    ("neg_zero_decimal_E1", [Decimal128("-0E+1")]),
    ("neg_zero_decimal_E_1", [Decimal128("-0E-1")]),
]


@pytest.mark.parametrize("op", OPERATORS)
@pytest.mark.parametrize("name,array", NEG_ZERO_VALUES, ids=[n[0] for n in NEG_ZERO_VALUES])
def test_set_common_negative_zero_falsy(collection, op, name, array):
    """Test both set operators treat negative zero as falsy."""
    result = execute_expression(collection, _build_expr(op, array))
    assert_expression_result(result, expected=False, msg=f"{op} {name} should be false")


# ---------------------------------------------------------------------------
# Decimal128 zero variants are falsy
# ---------------------------------------------------------------------------
DECIMAL_ZERO_VALUES = [
    ("decimal_0_0", [Decimal128("0.0")]),
    ("decimal_0_many_zeros", [Decimal128("0.00000000000000000000000000000000")]),
    ("decimal_0E6144", [Decimal128("0E+6144")]),
    ("decimal_neg0E_6143", [Decimal128("-0E-6143")]),
]


@pytest.mark.parametrize("op", OPERATORS)
@pytest.mark.parametrize("name,array", DECIMAL_ZERO_VALUES, ids=[d[0] for d in DECIMAL_ZERO_VALUES])
def test_set_common_decimal_zero_falsy(collection, op, name, array):
    """Test both set operators treat Decimal128 zero variants as falsy."""
    result = execute_expression(collection, _build_expr(op, array))
    assert_expression_result(result, expected=False, msg=f"{op} {name} should be false")


# ---------------------------------------------------------------------------
# Numeric boundary values from NUMERIC dataset
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("op", OPERATORS)
@pytest.mark.parametrize("value", NUMERIC)
def test_set_common_numeric_boundary(collection, op, value):
    """Test both set operators with each NUMERIC boundary value."""
    expected = value not in ZERO_NUMERIC
    result = execute_expression_with_insert(collection, {op: ["$arr"]}, {"arr": [value]})
    assert_expression_result(result, expected=expected, msg=f"{op} {repr(value)} truthiness")


# ---------------------------------------------------------------------------
# Non-zero boundary values are truthy
# ---------------------------------------------------------------------------
BOUNDARY_VALUES = [
    ("int32_min", [INT32_MIN]),
    ("int32_max", [INT32_MAX]),
    ("int64_min", [INT64_MIN]),
    ("int64_max", [INT64_MAX]),
    ("double_near_max", [DOUBLE_NEAR_MAX]),
    ("double_min_subnormal", [DOUBLE_MIN_SUBNORMAL]),
    ("double_min_neg_subnormal", [DOUBLE_MIN_NEGATIVE_SUBNORMAL]),
    ("double_near_min", [DOUBLE_NEAR_MIN]),
    ("decimal_max", [DECIMAL128_MAX]),
    ("decimal_min", [DECIMAL128_MIN]),
    ("decimal_large_exp", [DECIMAL128_LARGE_EXPONENT]),
    ("decimal_small_exp", [DECIMAL128_SMALL_EXPONENT]),
    ("decimal_min_positive", [DECIMAL128_MIN_POSITIVE]),
    ("decimal_max_negative", [DECIMAL128_MAX_NEGATIVE]),
]


@pytest.mark.parametrize("op", OPERATORS)
@pytest.mark.parametrize("name,array", BOUNDARY_VALUES, ids=[b[0] for b in BOUNDARY_VALUES])
def test_set_common_boundary_truthy(collection, op, name, array):
    """Test both set operators with non-zero numeric boundary values."""
    result = execute_expression(collection, _build_expr(op, array))
    assert_expression_result(result, expected=True, msg=f"{op} {name} should be true")


# ---------------------------------------------------------------------------
# Per-type coverage — double
# ---------------------------------------------------------------------------
DOUBLE_VALUES = [
    ("double_zero", [0.0], False),
    ("double_neg_zero", [-0.0], False),
    ("double_small_pos", [0.0000001], True),
    ("double_small_neg", [-0.0000001], True),
]


@pytest.mark.parametrize("op", OPERATORS)
@pytest.mark.parametrize("name,array,expected", DOUBLE_VALUES, ids=[d[0] for d in DOUBLE_VALUES])
def test_set_common_double(collection, op, name, array, expected):
    """Test both set operators with double values."""
    result = execute_expression(collection, _build_expr(op, array))
    assert_expression_result(result, expected=expected, msg=f"{op} {name}")


# ---------------------------------------------------------------------------
# Per-type coverage — int
# ---------------------------------------------------------------------------
INT_VALUES = [
    ("int_zero", [0], False),
    ("int_1", [1], True),
    ("int_neg1", [-1], True),
    ("int_max", [INT32_MAX], True),
    ("int_min", [INT32_MIN], True),
]


@pytest.mark.parametrize("op", OPERATORS)
@pytest.mark.parametrize("name,array,expected", INT_VALUES, ids=[i[0] for i in INT_VALUES])
def test_set_common_int(collection, op, name, array, expected):
    """Test both set operators with int values."""
    result = execute_expression(collection, _build_expr(op, array))
    assert_expression_result(result, expected=expected, msg=f"{op} {name}")


# ---------------------------------------------------------------------------
# Per-type coverage — long
# ---------------------------------------------------------------------------
LONG_VALUES = [
    ("long_zero", [Int64(0)], False),
    ("long_1", [Int64(1)], True),
    ("long_neg1", [Int64(-1)], True),
    ("long_max", [INT64_MAX], True),
    ("long_min", [INT64_MIN], True),
]


@pytest.mark.parametrize("op", OPERATORS)
@pytest.mark.parametrize("name,array,expected", LONG_VALUES, ids=[v[0] for v in LONG_VALUES])
def test_set_common_long(collection, op, name, array, expected):
    """Test both set operators with long values."""
    result = execute_expression(collection, _build_expr(op, array))
    assert_expression_result(result, expected=expected, msg=f"{op} {name}")


# ---------------------------------------------------------------------------
# Per-type coverage — decimal128
# ---------------------------------------------------------------------------
DECIMAL_VALUES = [
    ("decimal_zero", [Decimal128("0")], False),
    ("decimal_neg_zero", [Decimal128("-0")], False),
    ("decimal_small_pos", [Decimal128("0.0000001")], True),
    ("decimal_small_neg", [Decimal128("-0.0000001")], True),
]


@pytest.mark.parametrize("op", OPERATORS)
@pytest.mark.parametrize("name,array,expected", DECIMAL_VALUES, ids=[d[0] for d in DECIMAL_VALUES])
def test_set_common_decimal128(collection, op, name, array, expected):
    """Test both set operators with Decimal128 values."""
    result = execute_expression(collection, _build_expr(op, array))
    assert_expression_result(result, expected=expected, msg=f"{op} {name}")


# ---------------------------------------------------------------------------
# undefined/null in array is falsy
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("op", OPERATORS)
def test_set_common_undefined_falsy(collection, op):
    """Test both set operators with array containing null returns false."""
    result = execute_expression_with_insert(collection, {op: ["$arr"]}, {"arr": [None]})
    assert_expression_result(result, expected=False, msg=f"{op} null should be false")


# ---------------------------------------------------------------------------
# Duplicates (all same value)
# ---------------------------------------------------------------------------
DUPLICATE_VALUES = [
    ("all_true", [True, True, True], True),
    ("all_false", [False, False, False], False),
    ("all_ones", [1, 1, 1, 1], True),
    ("all_zeros", [0, 0, 0], False),
    ("all_nulls", [None, None], False),
]


@pytest.mark.parametrize("op", OPERATORS)
@pytest.mark.parametrize(
    "name,array,expected", DUPLICATE_VALUES, ids=[d[0] for d in DUPLICATE_VALUES]
)
def test_set_common_duplicates(collection, op, name, array, expected):
    """Test both set operators with duplicate elements."""
    result = execute_expression(collection, _build_expr(op, array))
    assert_expression_result(result, expected=expected, msg=f"{op} {name}")
