"""Tests for $bucketAuto aggregation stage — 'buckets' parameter validation."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BUCKET_AUTO_BUCKETS_NOT_INT_ERROR,
    BUCKET_AUTO_BUCKETS_NOT_NUMERIC_ERROR,
    BUCKET_AUTO_BUCKETS_NOT_POSITIVE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    FLOAT_INFINITY,
    FLOAT_NAN,
    INT32_OVERFLOW,
)

_DOCS = [{"_id": i, "x": i} for i in range(1, 6)]

# Property [Buckets Accepts Whole Numbers]: 'buckets' accepts any numeric type
# whose value is a whole number in 32-bit integer range.
BUCKET_AUTO_BUCKETS_ACCEPT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "buckets_int32",
        docs=_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 2}}],
        expected=[
            {"_id": {"min": 1, "max": 4}, "count": 3},
            {"_id": {"min": 4, "max": 5}, "count": 2},
        ],
        msg="$bucketAuto should accept an int32 'buckets' value",
    ),
    StageTestCase(
        "buckets_int64_whole",
        docs=_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": Int64(2)}}],
        expected=[
            {"_id": {"min": 1, "max": 4}, "count": 3},
            {"_id": {"min": 4, "max": 5}, "count": 2},
        ],
        msg="$bucketAuto should accept a whole-number int64 'buckets' value",
    ),
    StageTestCase(
        "buckets_double_whole",
        docs=_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 2.0}}],
        expected=[
            {"_id": {"min": 1, "max": 4}, "count": 3},
            {"_id": {"min": 4, "max": 5}, "count": 2},
        ],
        msg="$bucketAuto should accept a whole-number double 'buckets' value",
    ),
    StageTestCase(
        "buckets_decimal128_whole",
        docs=_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": Decimal128("2")}}],
        expected=[
            {"_id": {"min": 1, "max": 4}, "count": 3},
            {"_id": {"min": 4, "max": 5}, "count": 2},
        ],
        msg="$bucketAuto should accept a whole-number Decimal128 'buckets' value",
    ),
    StageTestCase(
        "buckets_one_single_bucket",
        docs=_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 1}}],
        expected=[{"_id": {"min": 1, "max": 5}, "count": 5}],
        msg="$bucketAuto with buckets=1 should return a single bucket spanning all values",
    ),
]

# Property [Buckets Not Positive]: 'buckets' must be greater than 0.
BUCKET_AUTO_BUCKETS_NOT_POSITIVE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "buckets_zero",
        docs=_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 0}}],
        error_code=BUCKET_AUTO_BUCKETS_NOT_POSITIVE_ERROR,
        msg="$bucketAuto should reject buckets=0",
    ),
    StageTestCase(
        "buckets_negative",
        docs=_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": -1}}],
        error_code=BUCKET_AUTO_BUCKETS_NOT_POSITIVE_ERROR,
        msg="$bucketAuto should reject a negative buckets value",
    ),
]

# Property [Buckets Not Integral]: 'buckets' must be representable as a 32-bit
# integer; fractional values, NaN, and overflowing values are rejected.
BUCKET_AUTO_BUCKETS_NOT_INT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "buckets_fractional_double",
        docs=_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 2.5}}],
        error_code=BUCKET_AUTO_BUCKETS_NOT_INT_ERROR,
        msg="$bucketAuto should reject a fractional double buckets value",
    ),
    StageTestCase(
        "buckets_fractional_decimal128",
        docs=_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": Decimal128("2.5")}}],
        error_code=BUCKET_AUTO_BUCKETS_NOT_INT_ERROR,
        msg="$bucketAuto should reject a fractional Decimal128 buckets value",
    ),
    StageTestCase(
        "buckets_nan",
        docs=_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": FLOAT_NAN}}],
        error_code=BUCKET_AUTO_BUCKETS_NOT_INT_ERROR,
        msg="$bucketAuto should reject a NaN buckets value",
    ),
    StageTestCase(
        "buckets_overflow_32bit",
        docs=_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": Int64(INT32_OVERFLOW)}}],
        error_code=BUCKET_AUTO_BUCKETS_NOT_INT_ERROR,
        msg="$bucketAuto should reject a buckets value exceeding 32-bit integer range",
    ),
    StageTestCase(
        "buckets_infinity",
        docs=_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": FLOAT_INFINITY}}],
        error_code=BUCKET_AUTO_BUCKETS_NOT_INT_ERROR,
        msg="$bucketAuto should reject an infinite buckets value",
    ),
]

# Property [Buckets Not Numeric]: 'buckets' must be a numeric value; all
# non-numeric BSON types are rejected.
BUCKET_AUTO_BUCKETS_NOT_NUMERIC_TESTS: list[StageTestCase] = [
    StageTestCase(
        "buckets_string",
        docs=_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": "2"}}],
        error_code=BUCKET_AUTO_BUCKETS_NOT_NUMERIC_ERROR,
        msg="$bucketAuto should reject a string buckets value",
    ),
    StageTestCase(
        "buckets_bool",
        docs=_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": True}}],
        error_code=BUCKET_AUTO_BUCKETS_NOT_NUMERIC_ERROR,
        msg="$bucketAuto should reject a bool buckets value",
    ),
    StageTestCase(
        "buckets_null",
        docs=_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": None}}],
        error_code=BUCKET_AUTO_BUCKETS_NOT_NUMERIC_ERROR,
        msg="$bucketAuto should reject a null buckets value",
    ),
    StageTestCase(
        "buckets_array",
        docs=_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": [2]}}],
        error_code=BUCKET_AUTO_BUCKETS_NOT_NUMERIC_ERROR,
        msg="$bucketAuto should reject an array buckets value",
    ),
    StageTestCase(
        "buckets_object",
        docs=_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": {"n": 2}}}],
        error_code=BUCKET_AUTO_BUCKETS_NOT_NUMERIC_ERROR,
        msg="$bucketAuto should reject an object buckets value",
    ),
    StageTestCase(
        "buckets_objectid",
        docs=_DOCS,
        pipeline=[
            {"$bucketAuto": {"groupBy": "$x", "buckets": ObjectId("000000000000000000000001")}}
        ],
        error_code=BUCKET_AUTO_BUCKETS_NOT_NUMERIC_ERROR,
        msg="$bucketAuto should reject an ObjectId buckets value",
    ),
    StageTestCase(
        "buckets_datetime",
        docs=_DOCS,
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": "$x",
                    "buckets": datetime(2024, 1, 1, tzinfo=timezone.utc),
                }
            }
        ],
        error_code=BUCKET_AUTO_BUCKETS_NOT_NUMERIC_ERROR,
        msg="$bucketAuto should reject a datetime buckets value",
    ),
    StageTestCase(
        "buckets_timestamp",
        docs=_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": Timestamp(1, 1)}}],
        error_code=BUCKET_AUTO_BUCKETS_NOT_NUMERIC_ERROR,
        msg="$bucketAuto should reject a Timestamp buckets value",
    ),
    StageTestCase(
        "buckets_binary",
        docs=_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": Binary(b"x")}}],
        error_code=BUCKET_AUTO_BUCKETS_NOT_NUMERIC_ERROR,
        msg="$bucketAuto should reject a Binary buckets value",
    ),
    StageTestCase(
        "buckets_regex",
        docs=_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": Regex("abc")}}],
        error_code=BUCKET_AUTO_BUCKETS_NOT_NUMERIC_ERROR,
        msg="$bucketAuto should reject a Regex buckets value",
    ),
    StageTestCase(
        "buckets_code",
        docs=_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": Code("function(){}")}}],
        error_code=BUCKET_AUTO_BUCKETS_NOT_NUMERIC_ERROR,
        msg="$bucketAuto should reject a Code buckets value",
    ),
    StageTestCase(
        "buckets_minkey",
        docs=_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": MinKey()}}],
        error_code=BUCKET_AUTO_BUCKETS_NOT_NUMERIC_ERROR,
        msg="$bucketAuto should reject a MinKey buckets value",
    ),
    StageTestCase(
        "buckets_maxkey",
        docs=_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": MaxKey()}}],
        error_code=BUCKET_AUTO_BUCKETS_NOT_NUMERIC_ERROR,
        msg="$bucketAuto should reject a MaxKey buckets value",
    ),
]

BUCKET_AUTO_BUCKETS_TESTS = (
    BUCKET_AUTO_BUCKETS_ACCEPT_TESTS
    + BUCKET_AUTO_BUCKETS_NOT_POSITIVE_TESTS
    + BUCKET_AUTO_BUCKETS_NOT_INT_TESTS
    + BUCKET_AUTO_BUCKETS_NOT_NUMERIC_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(BUCKET_AUTO_BUCKETS_TESTS))
def test_bucketAuto_buckets_validation(collection, test_case: StageTestCase):
    """Test $bucketAuto 'buckets' parameter validation."""
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
