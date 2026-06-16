"""
Special value tests for $inc update field operator.

Tests NaN, Infinity, negative zero, Decimal128 precision edge cases,
int32/int64 overflow boundaries, and double overflow to Infinity.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessNaN
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_SMALL_EXPONENT,
    DOUBLE_MAX,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MAX_MINUS_1,
    INT32_MIN,
    INT32_MIN_PLUS_1,
    INT64_MAX,
    INT64_MAX_MINUS_1,
    INT64_MIN,
    INT64_MIN_PLUS_1,
)

# Property [NaN Propagation]: any arithmetic involving NaN produces NaN.
NAN_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "nan_field_plus_numeric",
        setup_docs=[{"_id": 1, "val": FLOAT_NAN}],
        query={"_id": 1},
        update={"$inc": {"val": 5}},
        expected={"_id": 1, "val": FLOAT_NAN},
        msg="$inc should produce NaN when NaN field is incremented by a number",
    ),
    UpdateTestCase(
        "numeric_field_plus_nan",
        setup_docs=[{"_id": 1, "val": 10.0}],
        query={"_id": 1},
        update={"$inc": {"val": FLOAT_NAN}},
        expected={"_id": 1, "val": FLOAT_NAN},
        msg="$inc should produce NaN when incrementing a numeric field by NaN",
    ),
    UpdateTestCase(
        "nan_field_plus_nan",
        setup_docs=[{"_id": 1, "val": FLOAT_NAN}],
        query={"_id": 1},
        update={"$inc": {"val": FLOAT_NAN}},
        expected={"_id": 1, "val": FLOAT_NAN},
        msg="$inc should produce NaN when NaN field is incremented by NaN",
    ),
    UpdateTestCase(
        "decimal128_nan_plus_decimal128",
        setup_docs=[{"_id": 1, "val": DECIMAL128_NAN}],
        query={"_id": 1},
        update={"$inc": {"val": Decimal128("1")}},
        expected={"_id": 1, "val": DECIMAL128_NAN},
        msg="$inc should produce Decimal128 NaN when Decimal128 NaN is incremented",
    ),
    UpdateTestCase(
        "decimal128_numeric_plus_nan",
        setup_docs=[{"_id": 1, "val": Decimal128("10")}],
        query={"_id": 1},
        update={"$inc": {"val": DECIMAL128_NAN}},
        expected={"_id": 1, "val": DECIMAL128_NAN},
        msg="$inc should produce Decimal128 NaN when Decimal128 field is incremented by NaN",
    ),
    UpdateTestCase(
        "decimal128_nan_plus_nan",
        setup_docs=[{"_id": 1, "val": DECIMAL128_NAN}],
        query={"_id": 1},
        update={"$inc": {"val": DECIMAL128_NAN}},
        expected={"_id": 1, "val": DECIMAL128_NAN},
        msg="$inc should produce Decimal128 NaN when Decimal128 NaN is incremented by NaN",
    ),
]

# Property [NaN Dominates Infinity]: NaN combined with Infinity produces NaN.
NAN_INFINITY_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "nan_field_plus_infinity",
        setup_docs=[{"_id": 1, "val": FLOAT_NAN}],
        query={"_id": 1},
        update={"$inc": {"val": FLOAT_INFINITY}},
        expected={"_id": 1, "val": FLOAT_NAN},
        msg="$inc should produce NaN when NaN field is incremented by Infinity",
    ),
    UpdateTestCase(
        "infinity_field_plus_nan",
        setup_docs=[{"_id": 1, "val": FLOAT_INFINITY}],
        query={"_id": 1},
        update={"$inc": {"val": FLOAT_NAN}},
        expected={"_id": 1, "val": FLOAT_NAN},
        msg="$inc should produce NaN when Infinity field is incremented by NaN",
    ),
    UpdateTestCase(
        "decimal128_nan_plus_infinity",
        setup_docs=[{"_id": 1, "val": DECIMAL128_NAN}],
        query={"_id": 1},
        update={"$inc": {"val": DECIMAL128_INFINITY}},
        expected={"_id": 1, "val": DECIMAL128_NAN},
        msg="$inc should produce Decimal128 NaN when Decimal128 NaN + Decimal128 Infinity",
    ),
    UpdateTestCase(
        "decimal128_infinity_plus_nan",
        setup_docs=[{"_id": 1, "val": DECIMAL128_INFINITY}],
        query={"_id": 1},
        update={"$inc": {"val": DECIMAL128_NAN}},
        expected={"_id": 1, "val": DECIMAL128_NAN},
        msg="$inc should produce Decimal128 NaN when Decimal128 Infinity + Decimal128 NaN",
    ),
]

# Property [Infinity Arithmetic]: Infinity arithmetic follows IEEE 754 rules.
INFINITY_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "infinity_field_plus_numeric",
        setup_docs=[{"_id": 1, "val": FLOAT_INFINITY}],
        query={"_id": 1},
        update={"$inc": {"val": 5}},
        expected={"_id": 1, "val": FLOAT_INFINITY},
        msg="$inc should produce Infinity when Infinity field is incremented by a number",
    ),
    UpdateTestCase(
        "neg_infinity_field_plus_numeric",
        setup_docs=[{"_id": 1, "val": FLOAT_NEGATIVE_INFINITY}],
        query={"_id": 1},
        update={"$inc": {"val": 5}},
        expected={"_id": 1, "val": FLOAT_NEGATIVE_INFINITY},
        msg="$inc should produce -Infinity when -Infinity field is incremented by a number",
    ),
    UpdateTestCase(
        "numeric_field_plus_infinity",
        setup_docs=[{"_id": 1, "val": 10.0}],
        query={"_id": 1},
        update={"$inc": {"val": FLOAT_INFINITY}},
        expected={"_id": 1, "val": FLOAT_INFINITY},
        msg="$inc should produce Infinity when a numeric field is incremented by Infinity",
    ),
    UpdateTestCase(
        "numeric_field_plus_neg_infinity",
        setup_docs=[{"_id": 1, "val": 10.0}],
        query={"_id": 1},
        update={"$inc": {"val": FLOAT_NEGATIVE_INFINITY}},
        expected={"_id": 1, "val": FLOAT_NEGATIVE_INFINITY},
        msg="$inc should produce -Infinity when a numeric field is incremented by -Infinity",
    ),
    UpdateTestCase(
        "infinity_plus_infinity",
        setup_docs=[{"_id": 1, "val": FLOAT_INFINITY}],
        query={"_id": 1},
        update={"$inc": {"val": FLOAT_INFINITY}},
        expected={"_id": 1, "val": FLOAT_INFINITY},
        msg="$inc should produce Infinity when Infinity + Infinity",
    ),
    UpdateTestCase(
        "neg_infinity_plus_neg_infinity",
        setup_docs=[{"_id": 1, "val": FLOAT_NEGATIVE_INFINITY}],
        query={"_id": 1},
        update={"$inc": {"val": FLOAT_NEGATIVE_INFINITY}},
        expected={"_id": 1, "val": FLOAT_NEGATIVE_INFINITY},
        msg="$inc should produce -Infinity when -Infinity + -Infinity",
    ),
    UpdateTestCase(
        "infinity_plus_neg_infinity",
        setup_docs=[{"_id": 1, "val": FLOAT_INFINITY}],
        query={"_id": 1},
        update={"$inc": {"val": FLOAT_NEGATIVE_INFINITY}},
        expected={"_id": 1, "val": FLOAT_NAN},
        msg="$inc should produce NaN when Infinity + (-Infinity)",
    ),
    UpdateTestCase(
        "decimal128_infinity_plus_numeric",
        setup_docs=[{"_id": 1, "val": DECIMAL128_INFINITY}],
        query={"_id": 1},
        update={"$inc": {"val": Decimal128("1")}},
        expected={"_id": 1, "val": DECIMAL128_INFINITY},
        msg="$inc should produce Decimal128 Infinity when Decimal128 Infinity + numeric",
    ),
    UpdateTestCase(
        "decimal128_neg_infinity_plus_numeric",
        setup_docs=[{"_id": 1, "val": DECIMAL128_NEGATIVE_INFINITY}],
        query={"_id": 1},
        update={"$inc": {"val": Decimal128("1")}},
        expected={"_id": 1, "val": DECIMAL128_NEGATIVE_INFINITY},
        msg="$inc should produce Decimal128 -Infinity when Decimal128 -Infinity + numeric",
    ),
    UpdateTestCase(
        "decimal128_infinity_plus_infinity",
        setup_docs=[{"_id": 1, "val": DECIMAL128_INFINITY}],
        query={"_id": 1},
        update={"$inc": {"val": DECIMAL128_INFINITY}},
        expected={"_id": 1, "val": DECIMAL128_INFINITY},
        msg="$inc should produce Decimal128 Infinity when Decimal128 Infinity + Infinity",
    ),
    UpdateTestCase(
        "decimal128_neg_infinity_plus_neg_infinity",
        setup_docs=[{"_id": 1, "val": DECIMAL128_NEGATIVE_INFINITY}],
        query={"_id": 1},
        update={"$inc": {"val": DECIMAL128_NEGATIVE_INFINITY}},
        expected={"_id": 1, "val": DECIMAL128_NEGATIVE_INFINITY},
        msg="$inc should produce Decimal128 -Infinity when -Infinity + -Infinity",
    ),
    UpdateTestCase(
        "decimal128_infinity_plus_neg_infinity",
        setup_docs=[{"_id": 1, "val": DECIMAL128_INFINITY}],
        query={"_id": 1},
        update={"$inc": {"val": DECIMAL128_NEGATIVE_INFINITY}},
        expected={"_id": 1, "val": DECIMAL128_NAN},
        msg="$inc should produce Decimal128 NaN when Decimal128 Infinity + (-Infinity)",
    ),
]

# Property [Negative Zero]: $inc preserves or normalizes negative zero per IEEE 754.
NEGATIVE_ZERO_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "neg_zero_plus_pos_zero",
        setup_docs=[{"_id": 1, "val": DOUBLE_NEGATIVE_ZERO}],
        query={"_id": 1},
        update={"$inc": {"val": 0.0}},
        expected={"_id": 1, "val": DOUBLE_NEGATIVE_ZERO},
        msg="$inc should preserve -0.0 when incremented by 0.0 (no-op)",
    ),
    UpdateTestCase(
        "pos_zero_plus_neg_zero",
        setup_docs=[{"_id": 1, "val": 0.0}],
        query={"_id": 1},
        update={"$inc": {"val": DOUBLE_NEGATIVE_ZERO}},
        expected={"_id": 1, "val": 0.0},
        msg="$inc should produce 0.0 when 0.0 is incremented by -0.0",
    ),
    UpdateTestCase(
        "neg_zero_plus_neg_zero",
        setup_docs=[{"_id": 1, "val": DOUBLE_NEGATIVE_ZERO}],
        query={"_id": 1},
        update={"$inc": {"val": DOUBLE_NEGATIVE_ZERO}},
        expected={"_id": 1, "val": DOUBLE_NEGATIVE_ZERO},
        msg="$inc should produce -0.0 when -0.0 is incremented by -0.0",
    ),
    UpdateTestCase(
        "decimal128_neg_zero_plus_zero",
        setup_docs=[{"_id": 1, "val": DECIMAL128_NEGATIVE_ZERO}],
        query={"_id": 1},
        update={"$inc": {"val": Decimal128("0")}},
        expected={"_id": 1, "val": DECIMAL128_NEGATIVE_ZERO},
        msg="$inc should preserve Decimal128(-0) when incremented by 0 (no-op)",
    ),
    UpdateTestCase(
        "decimal128_zero_plus_neg_zero",
        setup_docs=[{"_id": 1, "val": Decimal128("0")}],
        query={"_id": 1},
        update={"$inc": {"val": DECIMAL128_NEGATIVE_ZERO}},
        expected={"_id": 1, "val": Decimal128("0")},
        msg="$inc should produce Decimal128(0) when 0 is incremented by -0",
    ),
    UpdateTestCase(
        "decimal128_neg_zero_plus_neg_zero",
        setup_docs=[{"_id": 1, "val": DECIMAL128_NEGATIVE_ZERO}],
        query={"_id": 1},
        update={"$inc": {"val": DECIMAL128_NEGATIVE_ZERO}},
        expected={"_id": 1, "val": DECIMAL128_NEGATIVE_ZERO},
        msg="$inc should produce Decimal128(-0) when -0 is incremented by -0",
    ),
]

# Property [Decimal128 Precision]: $inc preserves Decimal128 precision and exponents.
DECIMAL128_PRECISION_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "decimal128_max_plus_zero",
        setup_docs=[{"_id": 1, "val": DECIMAL128_MAX}],
        query={"_id": 1},
        update={"$inc": {"val": Decimal128("0")}},
        expected={"_id": 1, "val": DECIMAL128_MAX},
        msg="$inc should preserve DECIMAL128_MAX when incremented by zero",
    ),
    UpdateTestCase(
        "decimal128_min_plus_zero",
        setup_docs=[{"_id": 1, "val": DECIMAL128_MIN}],
        query={"_id": 1},
        update={"$inc": {"val": Decimal128("0")}},
        expected={"_id": 1, "val": DECIMAL128_MIN},
        msg="$inc should preserve DECIMAL128_MIN when incremented by zero",
    ),
    UpdateTestCase(
        "decimal128_max_plus_max",
        setup_docs=[{"_id": 1, "val": DECIMAL128_MAX}],
        query={"_id": 1},
        update={"$inc": {"val": DECIMAL128_MAX}},
        expected={"_id": 1, "val": DECIMAL128_INFINITY},
        msg="$inc should produce Decimal128 Infinity when DECIMAL128_MAX + DECIMAL128_MAX",
    ),
    UpdateTestCase(
        "decimal128_small_exponent_plus_zero",
        setup_docs=[{"_id": 1, "val": DECIMAL128_SMALL_EXPONENT}],
        query={"_id": 1},
        update={"$inc": {"val": Decimal128("0")}},
        expected={"_id": 1, "val": DECIMAL128_SMALL_EXPONENT},
        msg="$inc should preserve small exponent Decimal128 when incremented by zero",
    ),
    UpdateTestCase(
        "decimal128_large_exponent_plus_zero",
        setup_docs=[{"_id": 1, "val": DECIMAL128_LARGE_EXPONENT}],
        query={"_id": 1},
        update={"$inc": {"val": Decimal128("0")}},
        expected={"_id": 1, "val": DECIMAL128_LARGE_EXPONENT},
        msg="$inc should preserve large exponent Decimal128 when incremented by zero",
    ),
    UpdateTestCase(
        "decimal128_trailing_zeros_plus_zero",
        setup_docs=[{"_id": 1, "val": Decimal128("1.000")}],
        query={"_id": 1},
        update={"$inc": {"val": Decimal128("0")}},
        expected={"_id": 1, "val": Decimal128("1.000")},
        msg="$inc should preserve Decimal128 trailing zeros when incremented by zero",
    ),
]

# Property [Int32 Overflow]: $inc promotes int32 to int64 when result exceeds int32 range.
INT32_OVERFLOW_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "int32_max_plus_1",
        setup_docs=[{"_id": 1, "val": INT32_MAX}],
        query={"_id": 1},
        update={"$inc": {"val": 1}},
        expected={"_id": 1, "val": Int64(2_147_483_648)},
        msg="$inc should promote INT32_MAX + 1 to int64",
    ),
    UpdateTestCase(
        "int32_max_plus_int32_max",
        setup_docs=[{"_id": 1, "val": INT32_MAX}],
        query={"_id": 1},
        update={"$inc": {"val": INT32_MAX}},
        expected={"_id": 1, "val": Int64(4_294_967_294)},
        msg="$inc should promote INT32_MAX + INT32_MAX to int64",
    ),
    UpdateTestCase(
        "int32_min_minus_1",
        setup_docs=[{"_id": 1, "val": INT32_MIN}],
        query={"_id": 1},
        update={"$inc": {"val": -1}},
        expected={"_id": 1, "val": Int64(-2_147_483_649)},
        msg="$inc should promote INT32_MIN - 1 to int64",
    ),
    UpdateTestCase(
        "int32_min_plus_int32_min",
        setup_docs=[{"_id": 1, "val": INT32_MIN}],
        query={"_id": 1},
        update={"$inc": {"val": INT32_MIN}},
        expected={"_id": 1, "val": Int64(-4_294_967_296)},
        msg="$inc should promote INT32_MIN + INT32_MIN to int64",
    ),
    UpdateTestCase(
        "int32_max_minus_1_plus_1_stays_int32",
        setup_docs=[{"_id": 1, "val": INT32_MAX_MINUS_1}],
        query={"_id": 1},
        update={"$inc": {"val": 1}},
        expected={"_id": 1, "val": INT32_MAX},
        msg="$inc should stay int32 when result is exactly INT32_MAX",
    ),
    UpdateTestCase(
        "int32_min_plus_1_minus_1_stays_int32",
        setup_docs=[{"_id": 1, "val": INT32_MIN_PLUS_1}],
        query={"_id": 1},
        update={"$inc": {"val": -1}},
        expected={"_id": 1, "val": INT32_MIN},
        msg="$inc should stay int32 when result is exactly INT32_MIN",
    ),
]

# Property [Int64 Boundary]: $inc stays int64 when result is at the int64 boundary.
INT64_BOUNDARY_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "int64_max_minus_1_plus_1_stays_int64",
        setup_docs=[{"_id": 1, "val": INT64_MAX_MINUS_1}],
        query={"_id": 1},
        update={"$inc": {"val": 1}},
        expected={"_id": 1, "val": INT64_MAX},
        msg="$inc should stay int64 when result is exactly INT64_MAX",
    ),
    UpdateTestCase(
        "int64_min_plus_1_minus_1_stays_int64",
        setup_docs=[{"_id": 1, "val": INT64_MIN_PLUS_1}],
        query={"_id": 1},
        update={"$inc": {"val": -1}},
        expected={"_id": 1, "val": INT64_MIN},
        msg="$inc should stay int64 when result is exactly INT64_MIN",
    ),
]

# Property [Double Overflow]: $inc produces Infinity when double exceeds max finite value.
DOUBLE_OVERFLOW_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "double_max_plus_double_max",
        setup_docs=[{"_id": 1, "val": DOUBLE_MAX}],
        query={"_id": 1},
        update={"$inc": {"val": DOUBLE_MAX}},
        expected={"_id": 1, "val": float("inf")},
        msg="$inc should produce Infinity when DOUBLE_MAX + DOUBLE_MAX overflows",
    ),
    UpdateTestCase(
        "negative_double_max_plus_negative_double_max",
        setup_docs=[{"_id": 1, "val": -DOUBLE_MAX}],
        query={"_id": 1},
        update={"$inc": {"val": -DOUBLE_MAX}},
        expected={"_id": 1, "val": float("-inf")},
        msg="$inc should produce -Infinity when -DOUBLE_MAX + -DOUBLE_MAX overflows",
    ),
]

ALL_NAN_TESTS = NAN_TESTS + NAN_INFINITY_TESTS + INFINITY_TESTS
ALL_ZERO_PRECISION_TESTS = NEGATIVE_ZERO_TESTS + DECIMAL128_PRECISION_TESTS
ALL_OVERFLOW_TESTS = INT32_OVERFLOW_TESTS + INT64_BOUNDARY_TESTS + DOUBLE_OVERFLOW_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_NAN_TESTS))
def test_inc_nan_and_infinity(collection, test: UpdateTestCase):
    """Test $inc with NaN and Infinity values."""
    collection.insert_many(test.setup_docs)

    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )

    result = execute_command(collection, {"find": collection.name, "filter": test.query})
    assertSuccessNaN(result, [test.expected], msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(ALL_ZERO_PRECISION_TESTS))
def test_inc_negative_zero_and_precision(collection, test: UpdateTestCase):
    """Test $inc negative zero and Decimal128 precision behavior."""
    collection.insert_many(test.setup_docs)

    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )

    result = execute_command(collection, {"find": collection.name, "filter": test.query})
    assertSuccess(result, [test.expected], msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(ALL_OVERFLOW_TESTS))
def test_inc_overflow(collection, test: UpdateTestCase):
    """Test $inc overflow and boundary behavior with successful updates."""
    collection.insert_many(test.setup_docs)

    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )

    result = execute_command(collection, {"find": collection.name, "filter": test.query})
    assertSuccess(result, [test.expected], msg=test.msg)
