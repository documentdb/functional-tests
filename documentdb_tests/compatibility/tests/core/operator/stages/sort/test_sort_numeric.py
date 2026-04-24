from __future__ import annotations

import math

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_INT64_OVERFLOW,
    DECIMAL128_INT64_UNDERFLOW,
    DECIMAL128_MAX,
    DECIMAL128_MAX_NEGATIVE,
    DECIMAL128_MIN,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_TRAILING_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_MAX,
    DOUBLE_MIN,
    DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    DOUBLE_MIN_NORMAL,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_PRECISION_LOSS,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MAX_MINUS_1,
    INT32_OVERFLOW,
    INT64_MAX,
    INT64_MIN,
    INT64_ZERO,
)

# Property [Numeric Ordering]: all numeric BSON types are interleaved by numeric
# value rather than grouped by subtype, with NaN sorting before negative
# infinity, all zero variants sorting equivalently, and Decimal128 preserving
# exact precision where double and int64 cannot.
SORT_NUMERIC_ORDERING_TESTS: list[StageTestCase] = [
    StageTestCase(
        "numeric_interleaved_by_value",
        docs=[
            {"_id": 1, "v": 10},
            {"_id": 2, "v": Int64(5)},
            {"_id": 3, "v": 7.5},
            {"_id": 4, "v": Decimal128("3")},
            {"_id": 5, "v": Int64(15)},
            {"_id": 6, "v": 1.5},
        ],
        pipeline=[{"$sort": {"v": 1, "_id": 1}}],
        expected=[
            {"_id": 6, "v": 1.5},
            {"_id": 4, "v": Decimal128("3")},
            {"_id": 2, "v": Int64(5)},
            {"_id": 3, "v": 7.5},
            {"_id": 1, "v": 10},
            {"_id": 5, "v": Int64(15)},
        ],
        msg="$sort should interleave numeric types by value, not group by subtype",
    ),
    StageTestCase(
        "numeric_int32_int64_boundary",
        docs=[
            {"_id": 1, "v": INT32_MAX},
            {"_id": 2, "v": Int64(INT32_OVERFLOW)},
            {"_id": 3, "v": INT32_MAX_MINUS_1},
        ],
        pipeline=[{"$sort": {"v": 1}}],
        expected=[
            {"_id": 3, "v": INT32_MAX_MINUS_1},
            {"_id": 1, "v": INT32_MAX},
            {"_id": 2, "v": Int64(INT32_OVERFLOW)},
        ],
        msg="$sort should order int32 max before Int64 value just above int32 range",
    ),
    StageTestCase(
        "numeric_int64_extremes",
        docs=[
            {"_id": 1, "v": INT64_MAX},
            {"_id": 2, "v": INT64_MIN},
            {"_id": 3, "v": INT64_ZERO},
            {"_id": 4, "v": Int64(-1)},
            {"_id": 5, "v": Int64(1)},
        ],
        pipeline=[{"$sort": {"v": 1}}],
        expected=[
            {"_id": 2, "v": INT64_MIN},
            {"_id": 4, "v": Int64(-1)},
            {"_id": 3, "v": INT64_ZERO},
            {"_id": 5, "v": Int64(1)},
            {"_id": 1, "v": INT64_MAX},
        ],
        msg="$sort should correctly order Int64 extreme boundary values",
    ),
    StageTestCase(
        "numeric_double_extremes",
        docs=[
            {"_id": 1, "v": FLOAT_INFINITY},
            {"_id": 2, "v": FLOAT_NEGATIVE_INFINITY},
            {"_id": 3, "v": DOUBLE_MAX},
            {"_id": 4, "v": DOUBLE_MIN},
            {"_id": 5, "v": DOUBLE_MIN_SUBNORMAL},
            {"_id": 6, "v": DOUBLE_MIN_NEGATIVE_SUBNORMAL},
            {"_id": 7, "v": DOUBLE_MIN_NORMAL},
            {"_id": 8, "v": DOUBLE_ZERO},
        ],
        pipeline=[{"$sort": {"v": 1}}],
        expected=[
            {"_id": 2, "v": FLOAT_NEGATIVE_INFINITY},
            {"_id": 4, "v": DOUBLE_MIN},
            {"_id": 6, "v": DOUBLE_MIN_NEGATIVE_SUBNORMAL},
            {"_id": 8, "v": DOUBLE_ZERO},
            {"_id": 5, "v": DOUBLE_MIN_SUBNORMAL},
            {"_id": 7, "v": DOUBLE_MIN_NORMAL},
            {"_id": 3, "v": DOUBLE_MAX},
            {"_id": 1, "v": FLOAT_INFINITY},
        ],
        msg="$sort should correctly order double extreme values",
    ),
    StageTestCase(
        "numeric_decimal128_extremes",
        docs=[
            {"_id": 1, "v": DECIMAL128_INFINITY},
            {"_id": 2, "v": DECIMAL128_NEGATIVE_INFINITY},
            {"_id": 3, "v": DECIMAL128_MAX},
            {"_id": 4, "v": DECIMAL128_MIN},
            {"_id": 5, "v": DECIMAL128_MIN_POSITIVE},
            {"_id": 6, "v": DECIMAL128_MAX_NEGATIVE},
            {"_id": 7, "v": DECIMAL128_ZERO},
        ],
        pipeline=[{"$sort": {"v": 1}}],
        expected=[
            {"_id": 2, "v": DECIMAL128_NEGATIVE_INFINITY},
            {"_id": 4, "v": DECIMAL128_MIN},
            {"_id": 6, "v": DECIMAL128_MAX_NEGATIVE},
            {"_id": 7, "v": DECIMAL128_ZERO},
            {"_id": 5, "v": DECIMAL128_MIN_POSITIVE},
            {"_id": 3, "v": DECIMAL128_MAX},
            {"_id": 1, "v": DECIMAL128_INFINITY},
        ],
        msg="$sort should correctly order Decimal128 extreme exponent values",
    ),
    StageTestCase(
        "numeric_nan_and_infinity_cross_type",
        docs=[
            {"_id": 2, "v": FLOAT_NAN},
            {"_id": 1, "v": DECIMAL128_NAN},
            {"_id": 4, "v": FLOAT_NEGATIVE_INFINITY},
            {"_id": 3, "v": DECIMAL128_NEGATIVE_INFINITY},
            {"_id": 5, "v": 0},
            {"_id": 7, "v": FLOAT_INFINITY},
            {"_id": 6, "v": DECIMAL128_INFINITY},
        ],
        pipeline=[{"$sort": {"v": 1, "_id": 1}}],
        expected=[
            {"_id": 1, "v": DECIMAL128_NAN},
            {"_id": 2, "v": pytest.approx(math.nan, nan_ok=True)},
            {"_id": 3, "v": DECIMAL128_NEGATIVE_INFINITY},
            {"_id": 4, "v": FLOAT_NEGATIVE_INFINITY},
            {"_id": 5, "v": 0},
            {"_id": 6, "v": DECIMAL128_INFINITY},
            {"_id": 7, "v": FLOAT_INFINITY},
        ],
        msg=(
            "$sort should treat float and Decimal128 NaN as equivalent,"
            " and float and Decimal128 infinity as equivalent"
        ),
    ),
    StageTestCase(
        "numeric_zero_variants_equivalent",
        docs=[
            {"_id": 6, "v": 0},
            {"_id": 5, "v": DOUBLE_ZERO},
            {"_id": 4, "v": DOUBLE_NEGATIVE_ZERO},
            {"_id": 3, "v": INT64_ZERO},
            {"_id": 2, "v": DECIMAL128_ZERO},
            {"_id": 1, "v": DECIMAL128_NEGATIVE_ZERO},
            {"_id": 7, "v": -1},
            {"_id": 8, "v": 1},
        ],
        pipeline=[{"$sort": {"v": 1, "_id": 1}}],
        expected=[
            {"_id": 7, "v": -1},
            {"_id": 1, "v": DECIMAL128_NEGATIVE_ZERO},
            {"_id": 2, "v": DECIMAL128_ZERO},
            {"_id": 3, "v": INT64_ZERO},
            {"_id": 4, "v": DOUBLE_NEGATIVE_ZERO},
            {"_id": 5, "v": DOUBLE_ZERO},
            {"_id": 6, "v": 0},
            {"_id": 8, "v": 1},
        ],
        msg="$sort should sort all zero variants equivalently, interleaved by _id",
    ),
    StageTestCase(
        "cross_int32_decimal128",
        docs=[
            {"_id": 2, "v": 5},
            {"_id": 1, "v": Decimal128("5")},
            {"_id": 3, "v": Decimal128("3")},
            {"_id": 4, "v": 10},
        ],
        pipeline=[{"$sort": {"v": 1, "_id": 1}}],
        expected=[
            {"_id": 3, "v": Decimal128("3")},
            {"_id": 1, "v": Decimal128("5")},
            {"_id": 2, "v": 5},
            {"_id": 4, "v": 10},
        ],
        msg=(
            "$sort should interleave int32 and Decimal128 by numeric value"
            " with equal values tiebroken by _id"
        ),
    ),
    StageTestCase(
        "cross_int64_decimal128_beyond_range",
        docs=[
            {"_id": 1, "v": INT64_MAX},
            {"_id": 2, "v": DECIMAL128_INT64_OVERFLOW},
            {"_id": 3, "v": INT64_MIN},
            {"_id": 4, "v": DECIMAL128_INT64_UNDERFLOW},
        ],
        pipeline=[{"$sort": {"v": 1, "_id": 1}}],
        expected=[
            {"_id": 4, "v": DECIMAL128_INT64_UNDERFLOW},
            {"_id": 3, "v": INT64_MIN},
            {"_id": 1, "v": INT64_MAX},
            {"_id": 2, "v": DECIMAL128_INT64_OVERFLOW},
        ],
        msg="$sort should place Decimal128 values beyond int64 range correctly at the extremes",
    ),
    StageTestCase(
        "cross_double_decimal128_precision",
        docs=[
            {"_id": 1, "v": 0.1},
            {"_id": 2, "v": Decimal128("0.1")},
        ],
        pipeline=[{"$sort": {"v": 1, "_id": 1}}],
        expected=[
            {"_id": 2, "v": Decimal128("0.1")},
            {"_id": 1, "v": 0.1},
        ],
        msg=(
            "$sort should place double 0.1 after Decimal128 0.1"
            " because IEEE 754 double is slightly greater"
        ),
    ),
    StageTestCase(
        "cross_int64_double_precision_boundary",
        docs=[
            {"_id": 1, "v": Int64(DOUBLE_PRECISION_LOSS)},
            {"_id": 2, "v": float(DOUBLE_PRECISION_LOSS)},
        ],
        pipeline=[{"$sort": {"v": 1, "_id": 1}}],
        expected=[
            {"_id": 2, "v": float(DOUBLE_PRECISION_LOSS)},
            {"_id": 1, "v": Int64(DOUBLE_PRECISION_LOSS)},
        ],
        msg=(
            "$sort should place int64 after its double representation"
            " at the precision loss boundary"
        ),
    ),
    StageTestCase(
        "cross_decimal128_equivalent_representations",
        docs=[
            {"_id": 5, "v": Decimal128("1")},
            {"_id": 3, "v": DECIMAL128_TRAILING_ZERO},
            {"_id": 1, "v": Decimal128("10E-1")},
            {"_id": 4, "v": Decimal128("1E0")},
            {"_id": 2, "v": Decimal128("100E-2")},
        ],
        pipeline=[{"$sort": {"v": 1, "_id": 1}}],
        expected=[
            {"_id": 1, "v": Decimal128("10E-1")},
            {"_id": 2, "v": Decimal128("100E-2")},
            {"_id": 3, "v": DECIMAL128_TRAILING_ZERO},
            {"_id": 4, "v": Decimal128("1E0")},
            {"_id": 5, "v": Decimal128("1")},
        ],
        msg=(
            "$sort should sort Decimal128 equivalent representations"
            " of the same value equivalently by _id"
        ),
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(SORT_NUMERIC_ORDERING_TESTS))
def test_sort_numeric(collection, test_case: StageTestCase):
    """Test $sort numeric type ordering."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
