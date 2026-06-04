import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_MAX,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_FROM_INT64_MAX,
    DOUBLE_MAX,
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_PRECISION_LOSS,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
    INT32_MAX,
    INT32_MIN,
    INT32_OVERFLOW,
    INT64_MAX,
    INT64_MIN,
    INT64_ZERO,
)

from ..utils.round_trip_test_case import RoundTripTestCase

# Property [Numeric Type Equivalence]: numeric values with the same
# mathematical value are equal regardless of whether they are int32, Int64,
# double, or Decimal128.
NUMERIC_EQUIVALENCE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int_long",
        expression={"$eq": [1, Int64(1)]},
        expected=True,
        msg="Numeric equivalence should hold for int32 and Int64",
    ),
    ExpressionTestCase(
        "int_double",
        expression={"$eq": [1, 1.0]},
        expected=True,
        msg="Numeric equivalence should hold for int32 and double",
    ),
    ExpressionTestCase(
        "int_decimal",
        expression={"$eq": [1, Decimal128("1")]},
        expected=True,
        msg="Numeric equivalence should hold for int32 and Decimal128",
    ),
    ExpressionTestCase(
        "long_double",
        expression={"$eq": [Int64(1), 1.0]},
        expected=True,
        msg="Numeric equivalence should hold for Int64 and double",
    ),
    ExpressionTestCase(
        "long_decimal",
        expression={"$eq": [Int64(1), Decimal128("1")]},
        expected=True,
        msg="Numeric equivalence should hold for Int64 and Decimal128",
    ),
    ExpressionTestCase(
        "double_decimal",
        expression={"$eq": [1.0, Decimal128("1")]},
        expected=True,
        msg="Numeric equivalence should hold for double and Decimal128",
    ),
    ExpressionTestCase(
        "negative_cross_type",
        expression={"$eq": [-1, Int64(-1)]},
        expected=True,
        msg="Numeric equivalence should hold for negative int32 and Int64",
    ),
    ExpressionTestCase(
        "negative_int_double",
        expression={"$eq": [-1, -1.0]},
        expected=True,
        msg="Numeric equivalence should hold for negative int32 and double",
    ),
    ExpressionTestCase(
        "negative_int_decimal",
        expression={"$eq": [-1, Decimal128("-1")]},
        expected=True,
        msg="Numeric equivalence should hold for negative int32 and Decimal128",
    ),
]

# Property [Numeric Boundary Equivalence]: cross-type equivalence holds at type
# boundaries where exact representation is possible.
NUMERIC_BOUNDARY_EQUIVALENCE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_max_as_double",
        expression={"$eq": [INT32_MAX, float(INT32_MAX)]},
        expected=True,
        msg="Numeric equivalence should hold for int32 max and its exact double",
    ),
    ExpressionTestCase(
        "int32_max_as_long",
        expression={"$eq": [INT32_MAX, Int64(INT32_MAX)]},
        expected=True,
        msg="Numeric equivalence should hold for int32 max and the same Int64 value",
    ),
    ExpressionTestCase(
        "int32_min_as_long",
        expression={"$eq": [INT32_MIN, Int64(INT32_MIN)]},
        expected=True,
        msg="Numeric equivalence should hold for int32 min and the same Int64 value",
    ),
    ExpressionTestCase(
        "int32_min_as_double",
        expression={"$eq": [INT32_MIN, float(INT32_MIN)]},
        expected=True,
        msg="Numeric equivalence should hold for int32 min and its exact double",
    ),
    ExpressionTestCase(
        "int64_max_as_decimal",
        expression={"$eq": [INT64_MAX, Decimal128(str(INT64_MAX))]},
        expected=True,
        msg="Numeric equivalence should hold for Int64 max and its exact Decimal128",
    ),
    ExpressionTestCase(
        "int64_min_as_decimal",
        expression={"$eq": [INT64_MIN, Decimal128(str(INT64_MIN))]},
        expected=True,
        msg="Numeric equivalence should hold for Int64 min and its exact Decimal128",
    ),
]

# Property [Infinity Equivalence and Ordering]: positive and negative infinity
# are equal across double and Decimal128, distinct from each other, and bound
# all finite values.
INFINITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "positive_infinity_cross_type",
        expression={"$eq": [FLOAT_INFINITY, DECIMAL128_INFINITY]},
        expected=True,
        msg="Double positive infinity should equal Decimal128 positive infinity",
    ),
    ExpressionTestCase(
        "negative_infinity_cross_type",
        expression={"$eq": [FLOAT_NEGATIVE_INFINITY, DECIMAL128_NEGATIVE_INFINITY]},
        expected=True,
        msg="Double negative infinity should equal Decimal128 negative infinity",
    ),
    ExpressionTestCase(
        "positive_ne_negative_infinity_double",
        expression={"$eq": [FLOAT_INFINITY, FLOAT_NEGATIVE_INFINITY]},
        expected=False,
        msg="Double positive infinity should not equal double negative infinity",
    ),
    ExpressionTestCase(
        "positive_ne_negative_infinity_decimal",
        expression={"$eq": [DECIMAL128_INFINITY, DECIMAL128_NEGATIVE_INFINITY]},
        expected=False,
        msg="Decimal128 positive infinity should not equal Decimal128 negative infinity",
    ),
    ExpressionTestCase(
        "max_double_lt_double_infinity",
        expression={"$lt": [DOUBLE_MAX, FLOAT_INFINITY]},
        expected=True,
        msg="The largest finite double should be less than double positive infinity",
    ),
    ExpressionTestCase(
        "max_double_lt_decimal_infinity",
        expression={"$lt": [DOUBLE_MAX, DECIMAL128_INFINITY]},
        expected=True,
        msg="The largest finite double should be less than Decimal128 positive infinity",
    ),
    ExpressionTestCase(
        "double_negative_infinity_lt_negative_max",
        expression={"$lt": [FLOAT_NEGATIVE_INFINITY, -DOUBLE_MAX]},
        expected=True,
        msg="Double negative infinity should be less than the most negative finite double",
    ),
    ExpressionTestCase(
        "decimal_negative_infinity_lt_negative_max",
        expression={"$lt": [DECIMAL128_NEGATIVE_INFINITY, -DOUBLE_MAX]},
        expected=True,
        msg="Decimal128 negative infinity should be less than the most negative finite double",
    ),
]

# Property [Negative Zero Equivalence]: negative zero equals positive zero
# across all numeric types.
NEGATIVE_ZERO_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "double_neg_zero",
        expression={"$eq": [DOUBLE_NEGATIVE_ZERO, DOUBLE_ZERO]},
        expected=True,
        msg="Negative zero should equal positive zero for double",
    ),
    ExpressionTestCase(
        "decimal_neg_zero",
        expression={"$eq": [DECIMAL128_NEGATIVE_ZERO, DECIMAL128_ZERO]},
        expected=True,
        msg="Negative zero should equal positive zero for Decimal128",
    ),
    ExpressionTestCase(
        "neg_zero_int",
        expression={"$eq": [DOUBLE_NEGATIVE_ZERO, 0]},
        expected=True,
        msg="Negative zero should equal int32 zero",
    ),
    ExpressionTestCase(
        "neg_zero_long",
        expression={"$eq": [DOUBLE_NEGATIVE_ZERO, INT64_ZERO]},
        expected=True,
        msg="Negative zero should equal Int64 zero",
    ),
    ExpressionTestCase(
        "neg_zero_cross_decimal",
        expression={"$eq": [DOUBLE_NEGATIVE_ZERO, DECIMAL128_ZERO]},
        expected=True,
        msg="Double negative zero should equal Decimal128 zero",
    ),
]

# Property [NaN Equality and Ordering]: NaN equals NaN (including negative and
# cross-type), is never equal to a non-NaN value, and sorts below all other
# numeric values.
NAN_EQUALITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nan_nan",
        expression={"$eq": [FLOAT_NAN, FLOAT_NAN]},
        expected=True,
        msg="BSON equality should treat NaN as equal to NaN",
    ),
    ExpressionTestCase(
        "nan_negative_nan",
        expression={"$eq": [FLOAT_NAN, FLOAT_NEGATIVE_NAN]},
        expected=True,
        msg="BSON equality should treat NaN as equal to negative NaN",
    ),
    ExpressionTestCase(
        "decimal_nan_decimal_nan",
        expression={"$eq": [DECIMAL128_NAN, DECIMAL128_NAN]},
        expected=True,
        msg="BSON equality should treat Decimal128 NaN as equal to Decimal128 NaN",
    ),
    ExpressionTestCase(
        "decimal_nan_negative_nan",
        expression={"$eq": [DECIMAL128_NAN, DECIMAL128_NEGATIVE_NAN]},
        expected=True,
        msg="BSON equality should treat Decimal128 NaN as equal to Decimal128 negative NaN",
    ),
    ExpressionTestCase(
        "nan_cross_type",
        expression={"$eq": [FLOAT_NAN, DECIMAL128_NAN]},
        expected=True,
        msg="BSON equality should treat double NaN as equal to Decimal128 NaN",
    ),
    ExpressionTestCase(
        "nan_ne_int",
        expression={"$eq": [FLOAT_NAN, 1]},
        expected=False,
        msg="NaN should not equal a number",
    ),
    ExpressionTestCase(
        "nan_ne_null",
        expression={"$eq": [FLOAT_NAN, None]},
        expected=False,
        msg="NaN should not equal null",
    ),
    ExpressionTestCase(
        "double_nan_lt_negative_infinity",
        expression={"$lt": [FLOAT_NAN, FLOAT_NEGATIVE_INFINITY]},
        expected=True,
        msg="Double NaN should sort below negative infinity",
    ),
    ExpressionTestCase(
        "decimal_nan_lt_negative_infinity",
        expression={"$lt": [DECIMAL128_NAN, DECIMAL128_NEGATIVE_INFINITY]},
        expected=True,
        msg="Decimal128 NaN should sort below negative infinity",
    ),
    ExpressionTestCase(
        "double_nan_lt_zero",
        expression={"$lt": [FLOAT_NAN, 0]},
        expected=True,
        msg="Double NaN should sort below zero",
    ),
    ExpressionTestCase(
        "decimal_nan_lt_zero",
        expression={"$lt": [DECIMAL128_NAN, 0]},
        expected=True,
        msg="Decimal128 NaN should sort below zero",
    ),
]

# Property [Decimal128 Precision]: Decimal128 values that represent the same
# mathematical value are equal regardless of trailing zeros, scientific
# notation, or the exponent used to represent zero.
DECIMAL128_PRECISION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "trailing_zeros",
        expression={"$eq": [Decimal128("2.0"), Decimal128("2.00")]},
        expected=True,
        msg="Decimal128 equality should ignore trailing zeros",
    ),
    ExpressionTestCase(
        "scientific_notation",
        expression={"$eq": [Decimal128("3E+2"), Decimal128("300")]},
        expected=True,
        msg="Decimal128 equality should treat scientific notation as equal to standard form",
    ),
    ExpressionTestCase(
        "zero_different_exponents",
        expression={"$eq": [Decimal128("0E-6176"), Decimal128("0E+0")]},
        expected=True,
        msg="Decimal128 equality should treat zeros with different exponents as equal",
    ),
    ExpressionTestCase(
        "zero_extreme_exponents",
        expression={"$eq": [Decimal128("0E-6176"), Decimal128("0E+6111")]},
        expected=True,
        msg="Decimal128 equality should treat zeros across the exponent range as equal",
    ),
]

# Property [Double Precision Boundary]: a double can only exactly represent
# integers up to 2^53, so an Int64 within that range equals its double while an
# Int64 just beyond it does not, and a double cannot exactly represent Int64
# max.
DOUBLE_PRECISION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int64_max_safe_eq_double",
        expression={"$eq": [Int64(DOUBLE_MAX_SAFE_INTEGER), float(DOUBLE_MAX_SAFE_INTEGER)]},
        expected=True,
        msg="An Int64 at the 2^53 boundary should equal its exact double representation",
    ),
    ExpressionTestCase(
        "int64_precision_loss_ne_double",
        expression={"$eq": [Int64(DOUBLE_PRECISION_LOSS), float(DOUBLE_PRECISION_LOSS)]},
        expected=False,
        msg="An Int64 just beyond 2^53 should not equal its rounded double representation",
    ),
    ExpressionTestCase(
        "int64_max_ne_double",
        expression={"$eq": [INT64_MAX, DOUBLE_FROM_INT64_MAX]},
        expected=False,
        msg="Int64 max should not equal the double that cannot exactly represent it",
    ),
    ExpressionTestCase(
        "zero_lt_smallest_subnormal",
        expression={"$lt": [DOUBLE_ZERO, DOUBLE_MIN_SUBNORMAL]},
        expected=True,
        msg="Zero should be less than the smallest positive subnormal double",
    ),
    ExpressionTestCase(
        "double_tenth_ne_decimal_tenth",
        expression={"$eq": [0.1, Decimal128("0.1")]},
        expected=False,
        msg="Double 0.1 should not equal Decimal128 0.1 because of IEEE 754 representation",
    ),
    ExpressionTestCase(
        "decimal_tenth_lt_double_tenth",
        expression={"$lt": [Decimal128("0.1"), 0.1]},
        expected=True,
        msg="Decimal128 0.1 should be less than double 0.1 because the double rounds up",
    ),
]

# Property [Cross-Type Numeric Ordering]: numeric values of different subtypes
# order by mathematical value.
CROSS_TYPE_ORDERING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_max_lt_next_int64",
        expression={"$lt": [INT32_MAX, Int64(INT32_OVERFLOW)]},
        expected=True,
        msg="Cross-type ordering should place int32 max below the next Int64 value",
    ),
    ExpressionTestCase(
        "int64_min_lt_int32_min",
        expression={"$lt": [INT64_MIN, INT32_MIN]},
        expected=True,
        msg="Cross-type ordering should place Int64 min below int32 min",
    ),
    ExpressionTestCase(
        "int64_max_lt_decimal128_max",
        expression={"$lt": [INT64_MAX, DECIMAL128_MAX]},
        expected=True,
        msg="Cross-type ordering should place Int64 max below Decimal128 max",
    ),
]

NUMERIC_COMPARISON_TESTS = (
    NUMERIC_EQUIVALENCE_TESTS
    + NUMERIC_BOUNDARY_EQUIVALENCE_TESTS
    + INFINITY_TESTS
    + NEGATIVE_ZERO_TESTS
    + NAN_EQUALITY_TESTS
    + DECIMAL128_PRECISION_TESTS
    + DOUBLE_PRECISION_TESTS
    + CROSS_TYPE_ORDERING_TESTS
)


@pytest.mark.parametrize("test", pytest_params(NUMERIC_COMPARISON_TESTS))
def test_numeric_comparison(collection, test):
    """Test numeric BSON type comparison semantics."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# Property [Numeric Round-Trip Fidelity]: numeric values at type boundaries
# survive insert and retrieval unchanged.
NUMERIC_ROUND_TRIP_TESTS: list[RoundTripTestCase] = [
    RoundTripTestCase(
        "int32_max",
        value=INT32_MAX,
        expected=INT32_MAX,
        msg="Int32 max should survive round-trip",
    ),
    RoundTripTestCase(
        "int32_min",
        value=INT32_MIN,
        expected=INT32_MIN,
        msg="Int32 min should survive round-trip",
    ),
    RoundTripTestCase(
        "int64_max",
        value=INT64_MAX,
        expected=INT64_MAX,
        msg="Int64 max should survive round-trip",
    ),
    RoundTripTestCase(
        "int64_min",
        value=INT64_MIN,
        expected=INT64_MIN,
        msg="Int64 min should survive round-trip",
    ),
    RoundTripTestCase(
        "double_max",
        value=DOUBLE_MAX,
        expected=DOUBLE_MAX,
        msg="Double max should survive round-trip",
    ),
    RoundTripTestCase(
        "double_min_subnormal",
        value=DOUBLE_MIN_SUBNORMAL,
        expected=DOUBLE_MIN_SUBNORMAL,
        msg="Smallest subnormal double should survive round-trip",
    ),
    RoundTripTestCase(
        "double_infinity",
        value=FLOAT_INFINITY,
        expected=FLOAT_INFINITY,
        msg="Double positive infinity should survive round-trip",
    ),
    RoundTripTestCase(
        "double_negative_infinity",
        value=FLOAT_NEGATIVE_INFINITY,
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="Double negative infinity should survive round-trip",
    ),
    RoundTripTestCase(
        "decimal128_max",
        value=DECIMAL128_MAX,
        expected=DECIMAL128_MAX,
        msg="Decimal128 max should survive round-trip",
    ),
    RoundTripTestCase(
        "decimal128_nan",
        value=DECIMAL128_NAN,
        expected=DECIMAL128_NAN,
        msg="Decimal128 NaN should survive round-trip",
    ),
    RoundTripTestCase(
        "decimal128_infinity",
        value=DECIMAL128_INFINITY,
        expected=DECIMAL128_INFINITY,
        msg="Decimal128 positive infinity should survive round-trip",
    ),
    RoundTripTestCase(
        "decimal128_negative_infinity",
        value=DECIMAL128_NEGATIVE_INFINITY,
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="Decimal128 negative infinity should survive round-trip",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NUMERIC_ROUND_TRIP_TESTS))
def test_numeric_round_trip(collection, test):
    """Test numeric values survive storage and retrieval unchanged."""
    collection.insert_one({"_id": test.id, "v": test.value})
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": test.id}})
    assertSuccess(result, [{"_id": test.id, "v": test.expected}], msg=test.msg)
