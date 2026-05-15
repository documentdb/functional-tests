"""Tests for $bucket aggregation stage — boundary type and cross-type routing."""

from __future__ import annotations

import math

import pytest
from bson import (
    Decimal128,
    Int64,
)

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_ZERO,
    DOUBLE_MAX,
    DOUBLE_MIN,
    DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
    INT64_ZERO,
)

# Property [Numeric Boundary Types]: boundaries accept Int64, float,
# Decimal128, infinity, and NaN values; the bucket _id preserves the
# boundary type.
BUCKET_NUMERIC_BOUNDARY_TESTS: list[StageTestCase] = [
    StageTestCase(
        docs=[{"_id": 1, "x": Int64(50)}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [INT64_ZERO, Int64(100)]}}],
        expected=[{"_id": INT64_ZERO, "count": 1}],
        msg="$bucket should accept Int64 boundaries",
        id="int64_boundaries",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 5.0}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [DOUBLE_ZERO, 100.0]}}],
        expected=[{"_id": DOUBLE_ZERO, "count": 1}],
        msg="$bucket should accept float boundaries",
        id="float_boundaries",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": Decimal128("5")}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [DECIMAL128_ZERO, Decimal128("100")],
                }
            }
        ],
        expected=[{"_id": DECIMAL128_ZERO, "count": 1}],
        msg="$bucket should accept Decimal128 boundaries",
        id="decimal128_boundaries",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": -5}, {"_id": 2, "x": 5}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [FLOAT_NEGATIVE_INFINITY, 0, FLOAT_INFINITY],
                }
            }
        ],
        expected=[
            {"_id": FLOAT_NEGATIVE_INFINITY, "count": 1},
            {"_id": 0, "count": 1},
        ],
        msg="$bucket should accept float infinity boundaries",
        id="float_infinity_boundaries",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": Decimal128("-5")}, {"_id": 2, "x": Decimal128("5")}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [
                        DECIMAL128_NEGATIVE_INFINITY,
                        DECIMAL128_ZERO,
                        DECIMAL128_INFINITY,
                    ],
                }
            }
        ],
        expected=[
            {"_id": DECIMAL128_NEGATIVE_INFINITY, "count": 1},
            {"_id": DECIMAL128_ZERO, "count": 1},
        ],
        msg="$bucket should accept Decimal128 infinity boundaries",
        id="decimal128_infinity_boundaries",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": FLOAT_NAN}, {"_id": 2, "x": 5}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [FLOAT_NAN, 0, 10]}}],
        expected=[
            {"_id": pytest.approx(math.nan, nan_ok=True), "count": 1},
            {"_id": 0, "count": 1},
        ],
        msg="$bucket should accept float NaN as lowest boundary",
        id="float_nan_boundary",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": FLOAT_NEGATIVE_NAN}, {"_id": 2, "x": 5}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [FLOAT_NEGATIVE_NAN, 0, 10]}}],
        expected=[
            {"_id": pytest.approx(math.nan, nan_ok=True), "count": 1},
            {"_id": 0, "count": 1},
        ],
        msg="$bucket should accept float negative NaN as lowest boundary",
        id="float_negative_nan_boundary",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": DECIMAL128_NAN}, {"_id": 2, "x": Decimal128("5")}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [DECIMAL128_NAN, DECIMAL128_ZERO, Decimal128("10")],
                }
            }
        ],
        expected=[
            {"_id": DECIMAL128_NAN, "count": 1},
            {"_id": DECIMAL128_ZERO, "count": 1},
        ],
        msg="$bucket should accept Decimal128 NaN as lowest boundary",
        id="decimal128_nan_boundary",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": DECIMAL128_NEGATIVE_NAN}, {"_id": 2, "x": Decimal128("5")}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [
                        DECIMAL128_NEGATIVE_NAN,
                        DECIMAL128_ZERO,
                        Decimal128("10"),
                    ],
                }
            }
        ],
        expected=[
            {"_id": DECIMAL128_NEGATIVE_NAN, "count": 1},
            {"_id": DECIMAL128_ZERO, "count": 1},
        ],
        msg="$bucket should accept Decimal128 negative NaN as lowest boundary",
        id="decimal128_negative_nan_boundary",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 0}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [INT32_MIN, INT32_MAX]}}],
        expected=[{"_id": INT32_MIN, "count": 1}],
        msg="$bucket should accept int32 min/max as boundaries",
        id="int32_extreme_boundaries",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": INT64_ZERO}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [INT64_MIN, INT64_MAX]}}],
        expected=[{"_id": INT64_MIN, "count": 1}],
        msg="$bucket should accept int64 min/max as boundaries",
        id="int64_extreme_boundaries",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": DOUBLE_ZERO}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [DOUBLE_MIN, DOUBLE_MAX]}}],
        expected=[{"_id": DOUBLE_MIN, "count": 1}],
        msg="$bucket should accept double min/max as boundaries",
        id="double_extreme_boundaries",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": DOUBLE_ZERO}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [DOUBLE_MIN_NEGATIVE_SUBNORMAL, DOUBLE_MIN_SUBNORMAL],
                }
            }
        ],
        expected=[{"_id": DOUBLE_MIN_NEGATIVE_SUBNORMAL, "count": 1}],
        msg="$bucket should accept subnormal double boundaries",
        id="double_subnormal_boundaries",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": DECIMAL128_ZERO}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [DECIMAL128_MIN, DECIMAL128_MAX]}}],
        expected=[{"_id": DECIMAL128_MIN, "count": 1}],
        msg="$bucket should accept Decimal128 min/max as boundaries",
        id="decimal128_extreme_boundaries",
    ),
]

# Property [Cross-Type Numeric Routing]: documents with a different numeric
# subtype than the boundaries are still routed correctly; the bucket _id
# preserves the boundary type, not the document type.
BUCKET_CROSS_TYPE_NUMERIC_TESTS: list[StageTestCase] = [
    StageTestCase(
        docs=[{"_id": 1, "x": 5.5}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [0, 10]}}],
        expected=[{"_id": 0, "count": 1}],
        msg="$bucket should route float doc into int boundaries",
        id="float_doc_int_boundaries",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": Int64(5)}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [0, 10]}}],
        expected=[{"_id": 0, "count": 1}],
        msg="$bucket should route Int64 doc into int boundaries",
        id="int64_doc_int_boundaries",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": Decimal128("5")}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [0, 10]}}],
        expected=[{"_id": 0, "count": 1}],
        msg="$bucket should route Decimal128 doc into int boundaries",
        id="decimal128_doc_int_boundaries",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 5}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [DOUBLE_ZERO, 10.0]}}],
        expected=[{"_id": DOUBLE_ZERO, "count": 1}],
        msg="$bucket should route int doc into float boundaries preserving float _id",
        id="int_doc_float_boundaries",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 5}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [DECIMAL128_ZERO, Decimal128("10")],
                }
            }
        ],
        expected=[{"_id": DECIMAL128_ZERO, "count": 1}],
        msg="$bucket should route int doc into Decimal128 boundaries preserving Decimal128 _id",
        id="int_doc_decimal128_boundaries",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 10.0}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [0, 10, 20]}}],
        expected=[{"_id": 10, "count": 1}],
        msg="$bucket should route float doc at int boundary edge to correct bucket",
        id="float_doc_at_int_boundary_edge",
    ),
]

BUCKET_BOUNDARY_TESTS = BUCKET_NUMERIC_BOUNDARY_TESTS + BUCKET_CROSS_TYPE_NUMERIC_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(BUCKET_BOUNDARY_TESTS))
def test_bucket_boundaries(collection, test_case: StageTestCase):
    """Test $bucket boundary type and cross-type routing."""
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
