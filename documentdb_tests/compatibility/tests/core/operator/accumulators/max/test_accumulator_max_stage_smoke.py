"""Tests for $max accumulator via $bucket and $bucketAuto stages."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    FLOAT_INFINITY,
    FLOAT_NAN,
    INT32_MAX,
    INT64_MAX,
    INT64_MIN,
)

# ===========================================================================
# 1. $bucket Smoke Tests
# ===========================================================================

# Property [Bucket Stage Smoke]: $max produces correct results through $bucket
# for representative cases from each property category.
MAX_BUCKET_SMOKE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bucket_null_all",
        docs=[{"v": None}, {"v": None}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$max": "$v"}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$max via $bucket should return null when all values are null",
    ),
    AccumulatorTestCase(
        "bucket_numeric_basic",
        docs=[{"v": 10}, {"v": 30}, {"v": 20}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$max": "$v"}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 30}],
        msg="$max via $bucket should return the largest int32 value",
    ),
    AccumulatorTestCase(
        "bucket_string_basic",
        docs=[{"v": "abc"}, {"v": "abd"}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$max": "$v"}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": "abd"}],
        msg="$max via $bucket should pick the lexicographically larger string",
    ),
    AccumulatorTestCase(
        "bucket_nan_vs_positive",
        docs=[{"v": FLOAT_NAN}, {"v": 5}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$max": "$v"}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 5}],
        msg="$max via $bucket should pick positive number over NaN",
    ),
    AccumulatorTestCase(
        "bucket_infinity",
        docs=[{"v": FLOAT_INFINITY}, {"v": INT32_MAX}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$max": "$v"}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": FLOAT_INFINITY}],
        msg="$max via $bucket should pick Infinity over INT32_MAX",
    ),
    AccumulatorTestCase(
        "bucket_boundary_int64",
        docs=[{"v": INT64_MAX}, {"v": INT64_MIN}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$max": "$v"}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": INT64_MAX}],
        msg="$max via $bucket should pick INT64_MAX over INT64_MIN",
    ),
    AccumulatorTestCase(
        "bucket_edge_single_doc",
        docs=[{"v": 42}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$max": "$v"}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 42}],
        msg="$max via $bucket should handle single document",
    ),
]


# ===========================================================================
# 2. $bucketAuto Smoke Tests
# ===========================================================================

# Property [BucketAuto Stage Smoke]: $max produces correct results through
# $bucketAuto for representative cases from each property category.
MAX_BUCKET_AUTO_SMOKE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bucket_auto_null_all",
        docs=[{"v": None}, {"v": None}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": "$v"}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$max via $bucketAuto should return null when all values are null",
    ),
    AccumulatorTestCase(
        "bucket_auto_numeric_basic",
        docs=[{"v": 10}, {"v": 30}, {"v": 20}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": "$v"}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 30}],
        msg="$max via $bucketAuto should return the largest int32 value",
    ),
    AccumulatorTestCase(
        "bucket_auto_string_basic",
        docs=[{"v": "abc"}, {"v": "abd"}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": "$v"}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": "abd"}],
        msg="$max via $bucketAuto should pick the lexicographically larger string",
    ),
    AccumulatorTestCase(
        "bucket_auto_nan_vs_positive",
        docs=[{"v": FLOAT_NAN}, {"v": 5}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": "$v"}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 5}],
        msg="$max via $bucketAuto should pick positive number over NaN",
    ),
    AccumulatorTestCase(
        "bucket_auto_infinity",
        docs=[{"v": FLOAT_INFINITY}, {"v": INT32_MAX}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": "$v"}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": FLOAT_INFINITY}],
        msg="$max via $bucketAuto should pick Infinity over INT32_MAX",
    ),
    AccumulatorTestCase(
        "bucket_auto_boundary_int64",
        docs=[{"v": INT64_MAX}, {"v": INT64_MIN}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": "$v"}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": INT64_MAX}],
        msg="$max via $bucketAuto should pick INT64_MAX over INT64_MIN",
    ),
    AccumulatorTestCase(
        "bucket_auto_edge_single_doc",
        docs=[{"v": 42}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": "$v"}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 42}],
        msg="$max via $bucketAuto should handle single document",
    ),
]


# ===========================================================================
# Test functions
# ===========================================================================


@pytest.mark.parametrize("test_case", pytest_params(MAX_BUCKET_SMOKE_TESTS))
def test_accumulator_max_bucket(collection, test_case: AccumulatorTestCase):
    """Test $max accumulator via $bucket for representative cases."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)


@pytest.mark.parametrize("test_case", pytest_params(MAX_BUCKET_AUTO_SMOKE_TESTS))
def test_accumulator_max_bucket_auto(collection, test_case: AccumulatorTestCase):
    """Test $max accumulator via $bucketAuto for representative cases."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
