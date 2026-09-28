"""Tests for $bucketAuto aggregation stage — boundary semantics and type preservation."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Decimal128,
    Int64,
    ObjectId,
)

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_MAX,
    DECIMAL128_MIN,
)

# Property [Boundary Shape and Sharing]: each bucket _id has exactly min and
# max; min is inclusive, interior max is exclusive, the final max is inclusive,
# consecutive buckets share edges, and the outermost bounds equal the global
# min and max.
BUCKET_AUTO_BOUNDARY_SHAPE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "shared_edges_and_global_bounds",
        docs=[{"_id": i, "x": i} for i in range(1, 7)],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 3}}],
        expected=[
            {"_id": {"min": 1, "max": 3}, "count": 2},
            {"_id": {"min": 3, "max": 5}, "count": 2},
            {"_id": {"min": 5, "max": 6}, "count": 2},
        ],
        msg=(
            "$bucketAuto buckets should share edges, with the first min equal to the"
            " global min and the last max equal to the global max"
        ),
    ),
    StageTestCase(
        "interior_max_exclusive",
        docs=[
            {"_id": 1, "x": 1},
            {"_id": 2, "x": 2},
            {"_id": 3, "x": 3},
            {"_id": 4, "x": 3},
            {"_id": 5, "x": 4},
            {"_id": 6, "x": 5},
        ],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 3}}],
        expected=[
            {"_id": {"min": 1, "max": 3}, "count": 2},
            {"_id": {"min": 3, "max": 4}, "count": 2},
            {"_id": {"min": 4, "max": 5}, "count": 2},
        ],
        msg=(
            "$bucketAuto interior max should be exclusive: a value equal to an interior"
            " boundary lands in the higher bucket"
        ),
    ),
]

# Property [Boundary Type Preservation]: the bucket _id min/max preserve the
# BSON type of the groupBy values.
BUCKET_AUTO_BOUNDARY_TYPE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "int32_boundaries",
        docs=[
            {"_id": 1, "x": 5},
            {"_id": 2, "x": 15},
            {"_id": 3, "x": 25},
            {"_id": 4, "x": 35},
        ],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 2}}],
        expected=[
            {"_id": {"min": 5, "max": 25}, "count": 2},
            {"_id": {"min": 25, "max": 35}, "count": 2},
        ],
        msg="$bucketAuto should produce int32-typed boundaries for int32 values",
    ),
    StageTestCase(
        "int64_boundaries",
        docs=[
            {"_id": 1, "x": Int64(5)},
            {"_id": 2, "x": Int64(15)},
            {"_id": 3, "x": Int64(25)},
            {"_id": 4, "x": Int64(35)},
        ],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 2}}],
        expected=[
            {"_id": {"min": Int64(5), "max": Int64(25)}, "count": 2},
            {"_id": {"min": Int64(25), "max": Int64(35)}, "count": 2},
        ],
        msg="$bucketAuto should produce int64-typed boundaries for int64 values",
    ),
    StageTestCase(
        "double_boundaries",
        docs=[
            {"_id": 1, "x": 5.5},
            {"_id": 2, "x": 15.5},
            {"_id": 3, "x": 25.5},
            {"_id": 4, "x": 35.5},
        ],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 2}}],
        expected=[
            {"_id": {"min": 5.5, "max": 25.5}, "count": 2},
            {"_id": {"min": 25.5, "max": 35.5}, "count": 2},
        ],
        msg="$bucketAuto should produce double-typed boundaries for double values",
    ),
    StageTestCase(
        "decimal128_boundaries",
        docs=[
            {"_id": 1, "x": Decimal128("5")},
            {"_id": 2, "x": Decimal128("15")},
            {"_id": 3, "x": Decimal128("25")},
            {"_id": 4, "x": Decimal128("35")},
        ],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 2}}],
        expected=[
            {"_id": {"min": Decimal128("5"), "max": Decimal128("25")}, "count": 2},
            {"_id": {"min": Decimal128("25"), "max": Decimal128("35")}, "count": 2},
        ],
        msg="$bucketAuto should produce Decimal128-typed boundaries for Decimal128 values",
    ),
    StageTestCase(
        "string_boundaries",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "banana"},
            {"_id": 3, "x": "cherry"},
            {"_id": 4, "x": "date"},
        ],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 2}}],
        expected=[
            {"_id": {"min": "apple", "max": "cherry"}, "count": 2},
            {"_id": {"min": "cherry", "max": "date"}, "count": 2},
        ],
        msg="$bucketAuto should order and bucket string values lexicographically",
    ),
    StageTestCase(
        "date_boundaries",
        docs=[
            {"_id": 1, "x": datetime(2020, 1, 1, tzinfo=timezone.utc)},
            {"_id": 2, "x": datetime(2021, 1, 1, tzinfo=timezone.utc)},
            {"_id": 3, "x": datetime(2022, 1, 1, tzinfo=timezone.utc)},
            {"_id": 4, "x": datetime(2023, 1, 1, tzinfo=timezone.utc)},
        ],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 2}}],
        expected=[
            {
                "_id": {
                    "min": datetime(2020, 1, 1, tzinfo=timezone.utc),
                    "max": datetime(2022, 1, 1, tzinfo=timezone.utc),
                },
                "count": 2,
            },
            {
                "_id": {
                    "min": datetime(2022, 1, 1, tzinfo=timezone.utc),
                    "max": datetime(2023, 1, 1, tzinfo=timezone.utc),
                },
                "count": 2,
            },
        ],
        msg="$bucketAuto should order and bucket date values chronologically",
    ),
    StageTestCase(
        "objectid_boundaries",
        docs=[
            {"_id": 1, "x": ObjectId("000000000000000000000001")},
            {"_id": 2, "x": ObjectId("000000000000000000000002")},
            {"_id": 3, "x": ObjectId("000000000000000000000003")},
            {"_id": 4, "x": ObjectId("000000000000000000000004")},
        ],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 2}}],
        expected=[
            {
                "_id": {
                    "min": ObjectId("000000000000000000000001"),
                    "max": ObjectId("000000000000000000000003"),
                },
                "count": 2,
            },
            {
                "_id": {
                    "min": ObjectId("000000000000000000000003"),
                    "max": ObjectId("000000000000000000000004"),
                },
                "count": 2,
            },
        ],
        msg="$bucketAuto should order and bucket ObjectId values",
    ),
    StageTestCase(
        "bool_boundaries",
        docs=[
            {"_id": 1, "x": False},
            {"_id": 2, "x": False},
            {"_id": 3, "x": True},
            {"_id": 4, "x": True},
        ],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 2}}],
        expected=[
            {"_id": {"min": False, "max": True}, "count": 2},
            {"_id": {"min": True, "max": True}, "count": 2},
        ],
        msg="$bucketAuto should order boolean values with false < true",
    ),
    StageTestCase(
        "decimal128_precision_preserved",
        docs=[
            {"_id": 1, "x": Decimal128("1.5")},
            {"_id": 2, "x": Decimal128("2.5")},
        ],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 1}}],
        expected=[
            {"_id": {"min": Decimal128("1.5"), "max": Decimal128("2.5")}, "count": 2},
        ],
        msg="$bucketAuto should preserve Decimal128 precision in bucket boundaries",
    ),
    StageTestCase(
        "decimal128_extreme_boundaries_preserved",
        docs=[
            {"_id": 1, "x": DECIMAL128_MIN},
            {"_id": 2, "x": DECIMAL128_MAX},
        ],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 1}}],
        expected=[
            {"_id": {"min": DECIMAL128_MIN, "max": DECIMAL128_MAX}, "count": 2},
        ],
        msg="$bucketAuto should preserve extreme high-precision Decimal128 bucket boundaries",
    ),
]

# Property [Numeric Equivalence and Type Distinction]: numerically equivalent
# values across numeric types group together; booleans are distinct from
# numeric 0/1.
BUCKET_AUTO_NUMERIC_EQUIV_TESTS: list[StageTestCase] = [
    StageTestCase(
        "numeric_equivalence_same_bucket",
        docs=[
            {"_id": 1, "x": 1},
            {"_id": 2, "x": Int64(1)},
            {"_id": 3, "x": 1.0},
            {"_id": 4, "x": Decimal128("1")},
        ],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 1}}],
        expected=[{"_id": {"min": 1, "max": Decimal128("1")}, "count": 4}],
        msg="$bucketAuto should group numerically equivalent values across numeric types",
    ),
    StageTestCase(
        "bool_distinct_from_numeric_zero",
        docs=[{"_id": 1, "x": False}, {"_id": 2, "x": 0}],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 2}}],
        expected=[
            {"_id": {"min": 0, "max": False}, "count": 1},
            {"_id": {"min": False, "max": False}, "count": 1},
        ],
        msg="$bucketAuto should treat boolean false as distinct from numeric 0",
    ),
]

# Property [Mixed Type Ordering]: mixed numeric subtypes are ordered
# numerically, and mixed BSON types use canonical BSON type ordering.
BUCKET_AUTO_MIXED_TYPE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "mixed_numeric_types_ordered",
        docs=[
            {"_id": 1, "x": Decimal128("1")},
            {"_id": 2, "x": 5},
            {"_id": 3, "x": Int64(3)},
            {"_id": 4, "x": 2.5},
        ],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 2}}],
        expected=[
            {"_id": {"min": Decimal128("1"), "max": Int64(3)}, "count": 2},
            {"_id": {"min": Int64(3), "max": 5}, "count": 2},
        ],
        msg="$bucketAuto should order mixed numeric subtypes numerically",
    ),
    StageTestCase(
        "mixed_bson_types_canonical_order",
        docs=[
            {"_id": 1, "x": None},
            {"_id": 2, "x": 5},
            {"_id": 3, "x": "str"},
            {"_id": 4, "x": 10},
        ],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 4}}],
        expected=[
            {"_id": {"min": None, "max": 5}, "count": 1},
            {"_id": {"min": 5, "max": 10}, "count": 1},
            {"_id": {"min": 10, "max": "str"}, "count": 1},
            {"_id": {"min": "str", "max": "str"}, "count": 1},
        ],
        msg="$bucketAuto should order mixed BSON types using canonical type ordering",
    ),
]

BUCKET_AUTO_BOUNDARY_TESTS = (
    BUCKET_AUTO_BOUNDARY_SHAPE_TESTS
    + BUCKET_AUTO_BOUNDARY_TYPE_TESTS
    + BUCKET_AUTO_NUMERIC_EQUIV_TESTS
    + BUCKET_AUTO_MIXED_TYPE_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(BUCKET_AUTO_BOUNDARY_TESTS))
def test_bucketAuto_boundaries(collection, test_case: StageTestCase):
    """Test $bucketAuto boundary semantics and type preservation."""
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
