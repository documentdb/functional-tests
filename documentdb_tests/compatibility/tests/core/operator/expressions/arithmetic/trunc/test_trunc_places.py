"""
Place argument, nested-expression, and field-lookup tests for $trunc expression.

Covers positive/negative place values, place types (int64, decimal128,
whole double), decimal128 zero-padding, single-element array form,
null/missing short-circuiting, NaN/Infinity with place, nested $trunc,
and field-path resolution.
"""

import math

import pytest
from bson import (
    Decimal128,
    Int64,
)

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    MISSING,
)

TRUNC_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "double_place_0",
        expression={"$trunc": [1.12345678901234, 0]},
        expected=1.0,
        msg="Should truncate a double to 0 decimal places",
    ),
    ExpressionTestCase(
        "double_place_2",
        expression={"$trunc": [1.12345678901234, 2]},
        expected=1.12,
        msg="Should truncate a double to 2 decimal places",
    ),
    ExpressionTestCase(
        "double_place_10",
        expression={"$trunc": [1.12345678901234, 10]},
        expected=1.1234567890,
        msg="Should truncate a double to 10 decimal places",
    ),
    ExpressionTestCase(
        "double_place_13",
        expression={"$trunc": [1.12345678901234, 13]},
        expected=1.1234567890123,
        msg="Should truncate a double to 13 decimal places",
    ),
    ExpressionTestCase(
        "double_place_14",
        expression={"$trunc": [1.12345678901234, 14]},
        expected=pytest.approx(1.12345678901234),
        msg="Should preserve full double precision at place 14",
    ),
    ExpressionTestCase(
        "double_place_20",
        expression={"$trunc": [1.12345678901234, 20]},
        expected=pytest.approx(1.12345678901234),
        msg="Should preserve full double precision when place exceeds available digits",
    ),
    ExpressionTestCase(
        "double_ieee754_divergence",
        expression={"$trunc": [0.29, 2]},
        expected=0.28,
        msg=(
            "IEEE-754 double 0.29 is stored as ~0.28999999999999998, so truncating to 2 places "
            "drops below its literal spelling to 0.28"
        ),
    ),
    ExpressionTestCase(
        "double_ieee754_divergence_2",
        expression={"$trunc": [1.005, 2]},
        expected=1.00,
        msg=(
            "IEEE-754 double 1.005 is stored as ~1.00499999999999989, so truncating to 2 places "
            "drops to 1.00 instead of 1.01"
        ),
    ),
    ExpressionTestCase(
        "decimal128_no_ieee754_divergence",
        expression={"$trunc": [Decimal128("0.29"), 2]},
        expected=Decimal128("0.29"),
        msg=(
            "Decimal128 has exact base-10 representation, so truncating 0.29 to 2 places "
            "stays 0.29 (contrast with the double_ieee754_divergence case)"
        ),
    ),
    ExpressionTestCase(
        "place_0",
        expression={"$trunc": [Decimal128("1.123456789012345678901234567890123"), 0]},
        expected=Decimal128("1"),
        msg="Should truncate a high-precision Decimal128 to 0 decimal places",
    ),
    ExpressionTestCase(
        "place_2",
        expression={"$trunc": [Decimal128("1.123456789012345678901234567890123"), 2]},
        expected=Decimal128("1.12"),
        msg="Should truncate a high-precision Decimal128 to 2 decimal places",
    ),
    ExpressionTestCase(
        "place_10",
        expression={"$trunc": [Decimal128("1.123456789012345678901234567890123"), 10]},
        expected=Decimal128("1.1234567890"),
        msg="Should truncate a high-precision Decimal128 to 10 decimal places",
    ),
    ExpressionTestCase(
        "place_32",
        expression={"$trunc": [Decimal128("1.123456789012345678901234567890123"), 32]},
        expected=Decimal128("1.12345678901234567890123456789012"),
        msg="Should truncate a Decimal128 to 32 decimal places",
    ),
    ExpressionTestCase(
        "place_33",
        expression={"$trunc": [Decimal128("1.123456789012345678901234567890123"), 33]},
        expected=Decimal128("1.123456789012345678901234567890123"),
        msg="Should preserve a Decimal128 unchanged at its natural 33-digit precision",
    ),
    ExpressionTestCase(
        "place_34",
        expression={"$trunc": [Decimal128("1.123456789012345678901234567890123"), 34]},
        expected=Decimal128("1.1234567890123456789012345678901230"),
        msg="Should zero-pad a Decimal128 to 34 decimal places",
    ),
    ExpressionTestCase(
        "place_99",
        expression={"$trunc": [Decimal128("1.123456789012345678901234567890123"), 99]},
        expected=Decimal128("1.1234567890123456789012345678901230"),
        msg="Should cap Decimal128 truncation at 34 decimal places for place 99",
    ),
    ExpressionTestCase(
        "place_100",
        expression={"$trunc": [Decimal128("1.123456789012345678901234567890123"), 100]},
        expected=Decimal128("1.1234567890123456789012345678901230"),
        msg="Should cap Decimal128 truncation at 34 decimal places for place 100",
    ),
    ExpressionTestCase(
        "zero_pad_place_2",
        expression={"$trunc": [Decimal128("1.1"), 2]},
        expected=Decimal128("1.10"),
        msg="Should zero-pad Decimal128(1.1) to 2 decimal places",
    ),
    ExpressionTestCase(
        "zero_pad_place_10",
        expression={"$trunc": [Decimal128("1.1"), 10]},
        expected=Decimal128("1.1000000000"),
        msg="Should zero-pad Decimal128(1.1) to 10 decimal places",
    ),
    ExpressionTestCase(
        "zero_pad_place_33",
        expression={"$trunc": [Decimal128("1.1"), 33]},
        expected=Decimal128("1.100000000000000000000000000000000"),
        msg="Should zero-pad Decimal128(1.1) to 33 decimal places",
    ),
    ExpressionTestCase(
        "place_int64",
        expression={"$trunc": [1.12345, Int64(2)]},
        expected=1.12,
        msg="Should accept an Int64 place argument",
    ),
    ExpressionTestCase(
        "place_decimal",
        expression={"$trunc": [1.12345, Decimal128("2")]},
        expected=1.12,
        msg="Should accept a Decimal128 place argument",
    ),
    ExpressionTestCase(
        "place_double_whole",
        expression={"$trunc": [1.2345, 2.0]},
        expected=1.23,
        msg="Should accept a whole-number double as the place argument",
    ),
    ExpressionTestCase(
        "single_element_array",
        expression={"$trunc": [1.9]},
        expected=1.0,
        msg="Should default place to 0 for single-element array form",
    ),
    ExpressionTestCase(
        "int32_with_place",
        expression={"$trunc": [5, 3]},
        expected=5,
        msg="Should leave an int32 with no fractional part unchanged when given a place",
    ),
    ExpressionTestCase(
        "int64_with_place",
        expression={"$trunc": [Int64(5), 3]},
        expected=Int64(5),
        msg="Should leave an int64 with no fractional part unchanged when given a place",
    ),
    ExpressionTestCase(
        "neg_place_-1",
        expression={"$trunc": [123456789012345.123, -1]},
        expected=123456789012340.0,
        msg="Should truncate to the tens place with place -1",
    ),
    ExpressionTestCase(
        "neg_place_-2",
        expression={"$trunc": [123456789012345.123, -2]},
        expected=123456789012300.0,
        msg="Should truncate to the hundreds place with place -2",
    ),
    ExpressionTestCase(
        "neg_place_-10",
        expression={"$trunc": [123456789012345.123, -10]},
        expected=123450000000000.0,
        msg="Should truncate to the ten-billions place with place -10",
    ),
    ExpressionTestCase(
        "neg_place_-14",
        expression={"$trunc": [123456789012345.123, -14]},
        expected=100000000000000.0,
        msg="Should truncate to the highest digit with place -14",
    ),
    ExpressionTestCase(
        "neg_place_-15",
        expression={"$trunc": [123456789012345.123, -15]},
        expected=0.0,
        msg="Should truncate to 0.0 when place exceeds the value's magnitude",
    ),
    ExpressionTestCase(
        "neg_place_-19",
        expression={"$trunc": [123456789012345.123, -19]},
        expected=0.0,
        msg="Should truncate to 0.0 for a large negative place",
    ),
    ExpressionTestCase(
        "neg_place_-20",
        expression={"$trunc": [123456789012345.123, -20]},
        expected=0.0,
        msg="Should truncate to 0.0 at the minimum allowed negative place",
    ),
    ExpressionTestCase(
        "neg_place_int64",
        expression={"$trunc": [Int64(1234), Int64(-2)]},
        expected=Int64(1200),
        msg="Should truncate an Int64 value using a negative Int64 place",
    ),
    ExpressionTestCase(
        "neg_place_decimal",
        expression={"$trunc": [Decimal128("23.298"), Decimal128("-1")]},
        expected=Decimal128("2E+1"),
        msg="Should truncate a Decimal128 value using a negative Decimal128 place",
    ),
    ExpressionTestCase(
        "place_null",
        expression={"$trunc": [5.7, None]},
        expected=None,
        msg="Should return null when place is null",
    ),
    ExpressionTestCase(
        "nan_with_place_0",
        expression={"$trunc": [FLOAT_NAN, 0]},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for NaN with place",
    ),
    ExpressionTestCase(
        "infinity_with_place_0",
        expression={"$trunc": [FLOAT_INFINITY, 0]},
        expected=FLOAT_INFINITY,
        msg="Should return Infinity for Infinity with place",
    ),
    ExpressionTestCase(
        "neg_infinity_with_place_0",
        expression={"$trunc": [FLOAT_NEGATIVE_INFINITY, 0]},
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="Should return -Infinity for -Infinity with place",
    ),
    ExpressionTestCase(
        "decimal_nan_with_place_0",
        expression={"$trunc": [DECIMAL128_NAN, 0]},
        expected=DECIMAL128_NAN,
        msg="Should return decimal NaN for decimal NaN with place",
    ),
    ExpressionTestCase(
        "decimal_infinity_with_place_0",
        expression={"$trunc": [DECIMAL128_INFINITY, 0]},
        expected=DECIMAL128_INFINITY,
        msg="Should return decimal Infinity for decimal Infinity with place",
    ),
    ExpressionTestCase(
        "neg_value_neg_place_-1",
        expression={"$trunc": [-1234.5678, -1]},
        expected=-1230.0,
        msg="Should truncate negative value with negative place -1",
    ),
    ExpressionTestCase(
        "neg_value_neg_place_-20",
        expression={"$trunc": [-1234.5678, -20]},
        expected=-0.0,
        msg="Should truncate negative value with negative place -20",
    ),
    ExpressionTestCase(
        "missing_value",
        expression={"$trunc": MISSING},
        expected=None,
        msg="Should return null for a missing field value",
    ),
]


TRUNC_INSERT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "double_place_0",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": 1.12345678901234, "place": 0},
        expected=1.0,
        msg="Should truncate a double to 0 decimal places",
    ),
    ExpressionTestCase(
        "double_place_2",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": 1.12345678901234, "place": 2},
        expected=1.12,
        msg="Should truncate a double to 2 decimal places",
    ),
    ExpressionTestCase(
        "double_place_10",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": 1.12345678901234, "place": 10},
        expected=1.1234567890,
        msg="Should truncate a double to 10 decimal places",
    ),
    ExpressionTestCase(
        "double_place_13",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": 1.12345678901234, "place": 13},
        expected=1.1234567890123,
        msg="Should truncate a double to 13 decimal places",
    ),
    ExpressionTestCase(
        "double_place_14",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": 1.12345678901234, "place": 14},
        expected=pytest.approx(1.12345678901234),
        msg="Should preserve full double precision at place 14",
    ),
    ExpressionTestCase(
        "double_place_20",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": 1.12345678901234, "place": 20},
        expected=pytest.approx(1.12345678901234),
        msg="Should preserve full double precision when place exceeds available digits",
    ),
    ExpressionTestCase(
        "double_ieee754_divergence",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": 0.29, "place": 2},
        expected=0.28,
        msg=(
            "IEEE-754 double 0.29 is stored as ~0.28999999999999998, so truncating to 2 places "
            "drops below its literal spelling to 0.28"
        ),
    ),
    ExpressionTestCase(
        "double_ieee754_divergence_2",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": 1.005, "place": 2},
        expected=1.00,
        msg=(
            "IEEE-754 double 1.005 is stored as ~1.00499999999999989, so truncating to 2 places "
            "drops to 1.00 instead of 1.01"
        ),
    ),
    ExpressionTestCase(
        "decimal128_no_ieee754_divergence",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": Decimal128("0.29"), "place": 2},
        expected=Decimal128("0.29"),
        msg=(
            "Decimal128 has exact base-10 representation, so truncating 0.29 to 2 places "
            "stays 0.29 (contrast with the double_ieee754_divergence case)"
        ),
    ),
    ExpressionTestCase(
        "place_0",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": Decimal128("1.123456789012345678901234567890123"), "place": 0},
        expected=Decimal128("1"),
        msg="Should truncate a high-precision Decimal128 to 0 decimal places",
    ),
    ExpressionTestCase(
        "place_2",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": Decimal128("1.123456789012345678901234567890123"), "place": 2},
        expected=Decimal128("1.12"),
        msg="Should truncate a high-precision Decimal128 to 2 decimal places",
    ),
    ExpressionTestCase(
        "place_10",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": Decimal128("1.123456789012345678901234567890123"), "place": 10},
        expected=Decimal128("1.1234567890"),
        msg="Should truncate a high-precision Decimal128 to 10 decimal places",
    ),
    ExpressionTestCase(
        "place_32",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": Decimal128("1.123456789012345678901234567890123"), "place": 32},
        expected=Decimal128("1.12345678901234567890123456789012"),
        msg="Should truncate a Decimal128 to 32 decimal places",
    ),
    ExpressionTestCase(
        "place_33",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": Decimal128("1.123456789012345678901234567890123"), "place": 33},
        expected=Decimal128("1.123456789012345678901234567890123"),
        msg="Should preserve a Decimal128 unchanged at its natural 33-digit precision",
    ),
    ExpressionTestCase(
        "place_34",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": Decimal128("1.123456789012345678901234567890123"), "place": 34},
        expected=Decimal128("1.1234567890123456789012345678901230"),
        msg="Should zero-pad a Decimal128 to 34 decimal places",
    ),
    ExpressionTestCase(
        "place_99",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": Decimal128("1.123456789012345678901234567890123"), "place": 99},
        expected=Decimal128("1.1234567890123456789012345678901230"),
        msg="Should cap Decimal128 truncation at 34 decimal places for place 99",
    ),
    ExpressionTestCase(
        "place_100",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": Decimal128("1.123456789012345678901234567890123"), "place": 100},
        expected=Decimal128("1.1234567890123456789012345678901230"),
        msg="Should cap Decimal128 truncation at 34 decimal places for place 100",
    ),
    ExpressionTestCase(
        "zero_pad_place_2",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": Decimal128("1.1"), "place": 2},
        expected=Decimal128("1.10"),
        msg="Should zero-pad Decimal128(1.1) to 2 decimal places",
    ),
    ExpressionTestCase(
        "zero_pad_place_10",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": Decimal128("1.1"), "place": 10},
        expected=Decimal128("1.1000000000"),
        msg="Should zero-pad Decimal128(1.1) to 10 decimal places",
    ),
    ExpressionTestCase(
        "zero_pad_place_33",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": Decimal128("1.1"), "place": 33},
        expected=Decimal128("1.100000000000000000000000000000000"),
        msg="Should zero-pad Decimal128(1.1) to 33 decimal places",
    ),
    ExpressionTestCase(
        "place_int64",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": 1.12345, "place": Int64(2)},
        expected=1.12,
        msg="Should accept an Int64 place argument",
    ),
    ExpressionTestCase(
        "place_decimal",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": 1.12345, "place": Decimal128("2")},
        expected=1.12,
        msg="Should accept a Decimal128 place argument",
    ),
    ExpressionTestCase(
        "place_double_whole",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": 1.2345, "place": 2.0},
        expected=1.23,
        msg="Should accept a whole-number double as the place argument",
    ),
    ExpressionTestCase(
        "int32_with_place",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": 5, "place": 3},
        expected=5,
        msg="Should leave an int32 with no fractional part unchanged when given a place",
    ),
    ExpressionTestCase(
        "int64_with_place",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": Int64(5), "place": 3},
        expected=Int64(5),
        msg="Should leave an int64 with no fractional part unchanged when given a place",
    ),
    ExpressionTestCase(
        "neg_place_-1",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": 123456789012345.123, "place": -1},
        expected=123456789012340.0,
        msg="Should truncate to the tens place with place -1",
    ),
    ExpressionTestCase(
        "neg_place_-2",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": 123456789012345.123, "place": -2},
        expected=123456789012300.0,
        msg="Should truncate to the hundreds place with place -2",
    ),
    ExpressionTestCase(
        "neg_place_-10",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": 123456789012345.123, "place": -10},
        expected=123450000000000.0,
        msg="Should truncate to the ten-billions place with place -10",
    ),
    ExpressionTestCase(
        "neg_place_-14",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": 123456789012345.123, "place": -14},
        expected=100000000000000.0,
        msg="Should truncate to the highest digit with place -14",
    ),
    ExpressionTestCase(
        "neg_place_-15",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": 123456789012345.123, "place": -15},
        expected=0.0,
        msg="Should truncate to 0.0 when place exceeds the value's magnitude",
    ),
    ExpressionTestCase(
        "neg_place_-19",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": 123456789012345.123, "place": -19},
        expected=0.0,
        msg="Should truncate to 0.0 for a large negative place",
    ),
    ExpressionTestCase(
        "neg_place_-20",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": 123456789012345.123, "place": -20},
        expected=0.0,
        msg="Should truncate to 0.0 at the minimum allowed negative place",
    ),
    ExpressionTestCase(
        "neg_place_int64",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": Int64(1234), "place": Int64(-2)},
        expected=Int64(1200),
        msg="Should truncate an Int64 value using a negative Int64 place",
    ),
    ExpressionTestCase(
        "neg_place_decimal",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": Decimal128("23.298"), "place": Decimal128("-1")},
        expected=Decimal128("2E+1"),
        msg="Should truncate a Decimal128 value using a negative Decimal128 place",
    ),
    ExpressionTestCase(
        "place_null",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": 5.7, "place": None},
        expected=None,
        msg="Should return null when place is null",
    ),
    ExpressionTestCase(
        "nonexistent_place_field",
        expression={"$trunc": ["$value", "$nonexistent"]},
        doc={"value": 5.678},
        expected=None,
        msg="Should return null when place field does not exist",
    ),
    ExpressionTestCase(
        "nan_with_place_0",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": FLOAT_NAN, "place": 0},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for NaN with place",
    ),
    ExpressionTestCase(
        "infinity_with_place_0",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": FLOAT_INFINITY, "place": 0},
        expected=FLOAT_INFINITY,
        msg="Should return Infinity for Infinity with place",
    ),
    ExpressionTestCase(
        "neg_infinity_with_place_0",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": FLOAT_NEGATIVE_INFINITY, "place": 0},
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="Should return -Infinity for -Infinity with place",
    ),
    ExpressionTestCase(
        "decimal_nan_with_place_0",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": DECIMAL128_NAN, "place": 0},
        expected=DECIMAL128_NAN,
        msg="Should return decimal NaN for decimal NaN with place",
    ),
    ExpressionTestCase(
        "decimal_infinity_with_place_0",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": DECIMAL128_INFINITY, "place": 0},
        expected=DECIMAL128_INFINITY,
        msg="Should return decimal Infinity for decimal Infinity with place",
    ),
    ExpressionTestCase(
        "neg_value_neg_place_-1",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": -1234.5678, "place": -1},
        expected=-1230.0,
        msg="Should truncate negative value with negative place -1",
    ),
    ExpressionTestCase(
        "neg_value_neg_place_-20",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": -1234.5678, "place": -20},
        expected=-0.0,
        msg="Should truncate negative value with negative place -20",
    ),
]


TRUNC_NESTED_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_trunc_2",
        expression={"$trunc": {"$trunc": 4.6}},
        expected=4.0,
        msg="Should evaluate nested $trunc",
    ),
    ExpressionTestCase(
        "nested_trunc_2_large",
        expression={"$trunc": {"$trunc": 9.99}},
        expected=9.0,
        msg="Should evaluate nested $trunc with larger input",
    ),
    ExpressionTestCase(
        "nested_trunc_3_with_place",
        expression={"$trunc": [{"$trunc": [{"$trunc": [9.876, 2]}, 1]}]},
        expected=9.0,
        msg="Should evaluate triple-nested $trunc with place",
    ),
]


TRUNC_FIELD_LOOKUP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_field",
        expression={"$trunc": "$a.b"},
        doc={"a": {"b": 4.6}},
        expected=4.0,
        msg="Should resolve nested field path",
    ),
    ExpressionTestCase(
        "nonexistent_field",
        expression={"$trunc": "$a.nonexistent"},
        doc={"a": {"missing": 1}},
        expected=None,
        msg="Should return null for nonexistent field path",
    ),
    ExpressionTestCase(
        "array_index",
        expression={"$trunc": {"$arrayElemAt": ["$arr", 0]}},
        doc={"arr": [4.6, 3.2, 1.8]},
        expected=4.0,
        msg="Should resolve value from array index",
    ),
    ExpressionTestCase(
        "deeply_nested_field",
        expression={"$trunc": "$a.b.c.d"},
        doc={"a": {"b": {"c": {"d": 5.9}}}},
        expected=5.0,
        msg="Should resolve deeply nested field path",
    ),
]


TRUNC_LITERAL_ALL_TESTS: list[ExpressionTestCase] = TRUNC_LITERAL_TESTS + TRUNC_NESTED_TESTS
TRUNC_INSERT_ALL_TESTS: list[ExpressionTestCase] = TRUNC_INSERT_TESTS + TRUNC_FIELD_LOOKUP_TESTS


@pytest.mark.parametrize("test", pytest_params(TRUNC_LITERAL_ALL_TESTS))
def test_trunc_literal(collection, test):
    """Test $trunc with literal values and nested expressions."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(TRUNC_INSERT_ALL_TESTS))
def test_trunc_insert(collection, test):
    """Test $trunc with inserted document values and field-path lookups."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
