"""Tests for $geoNear pipeline position constraints and stage combinations."""

from __future__ import annotations

import pytest
from pymongo.operations import IndexModel

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    FACET_PIPELINE_INVALID_STAGE_ERROR,
    GEO_NEAR_NOT_FIRST_STAGE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DOUBLE_ZERO

# Property [Stage Constraint - Position and Uniqueness]: $geoNear must be the
# first stage in the main pipeline and is not allowed inside $facet; a second
# $geoNear in the same pipeline is also rejected.
GEONEAR_STAGE_CONSTRAINT_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "not_first_stage",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {"$match": {"_id": 1}},
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                }
            },
        ],
        error_code=GEO_NEAR_NOT_FIRST_STAGE_ERROR,
        msg="$geoNear not as the first stage should fail",
    ),
    StageTestCase(
        "inside_facet",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$facet": {
                    "geo": [
                        {
                            "$geoNear": {
                                "near": {"type": "Point", "coordinates": [0, 0]},
                                "distanceField": "dist",
                                "spherical": True,
                            }
                        },
                    ],
                }
            },
        ],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$geoNear inside $facet should fail",
    ),
    StageTestCase(
        "two_geonear_stages",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                }
            },
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist2",
                    "spherical": True,
                }
            },
        ],
        error_code=GEO_NEAR_NOT_FIRST_STAGE_ERROR,
        msg="Two $geoNear stages in the same pipeline should fail",
    ),
]

# Property [Stage Constraint - Empty Match Optimization]: $geoNear after an
# empty $match succeeds because the optimizer removes the empty $match,
# leaving $geoNear as the effective first stage.
GEONEAR_EMPTY_MATCH_OPTIMIZATION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "after_empty_match",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {"$match": {}},
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                }
            },
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "dist": DOUBLE_ZERO,
            },
        ],
        msg="$geoNear after an empty $match should succeed",
    ),
]

# Property [Pipeline Combination - Match]: $match after $geoNear filters
# results while preserving distance-based ordering.
GEONEAR_MATCH_TESTS: list[StageTestCase] = [
    StageTestCase(
        "match_filter_by_field",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "cat": "a"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "cat": "b"},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 0]}, "cat": "a"},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                }
            },
            {"$match": {"cat": "a"}},
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "cat": "a",
                "dist": DOUBLE_ZERO,
            },
            {
                "_id": 3,
                "loc": {"type": "Point", "coordinates": [2, 0]},
                "cat": "a",
                "dist": 222_637.69004290068,
            },
        ],
        msg="$match after $geoNear should filter by field while preserving distance order",
    ),
    StageTestCase(
        "match_filter_on_computed_dist",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                }
            },
            {"$match": {"dist": {"$lte": 120000}}},
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "dist": DOUBLE_ZERO,
            },
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "dist": 111_318.84502145034,
            },
        ],
        msg="$match after $geoNear should filter on the computed distance field",
    ),
]

# Property [Pipeline Combination - Sort]: $sort after $geoNear re-orders
# results, overriding the default distance-based ordering.
GEONEAR_SORT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "sort_override_distance_order",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "r": 2},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "r": 5},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 0]}, "r": 3},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                }
            },
            {"$sort": {"r": -1}},
        ],
        expected=[
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "r": 5,
                "dist": 111_318.84502145034,
            },
            {
                "_id": 3,
                "loc": {"type": "Point", "coordinates": [2, 0]},
                "r": 3,
                "dist": 222_637.69004290068,
            },
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "r": 2,
                "dist": DOUBLE_ZERO,
            },
        ],
        msg="$sort after $geoNear should re-order results overriding distance-based ordering",
    ),
]

# Property [Pipeline Combination - Limit]: $limit after $geoNear truncates
# results to the N nearest documents.
GEONEAR_LIMIT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "limit_nearest",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                }
            },
            {"$limit": 2},
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "dist": DOUBLE_ZERO,
            },
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "dist": 111_318.84502145034,
            },
        ],
        msg="$limit after $geoNear should return only the N nearest documents",
    ),
]

# Property [Pipeline Combination - Skip]: $skip after $geoNear skips the
# first N nearest documents.
GEONEAR_SKIP_TESTS: list[StageTestCase] = [
    StageTestCase(
        "skip_and_limit_pagination",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                }
            },
            {"$skip": 1},
            {"$limit": 2},
        ],
        expected=[
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "dist": 111_318.84502145034,
            },
            {
                "_id": 3,
                "loc": {"type": "Point", "coordinates": [2, 0]},
                "dist": 222_637.69004290068,
            },
        ],
        msg="$skip + $limit after $geoNear should paginate through distance-ordered results",
    ),
]

# Property [Pipeline Combination - Project]: $project after $geoNear reshapes
# documents and can compute derived fields from the distance.
GEONEAR_PROJECT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "project_derived_field",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "name": "A"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "name": "B"},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                }
            },
            {"$project": {"name": 1, "distKm": {"$divide": ["$dist", 1000]}}},
        ],
        expected=[
            {"_id": 1, "name": "A", "distKm": DOUBLE_ZERO},
            {"_id": 2, "name": "B", "distKm": 111.31884502145034},
        ],
        msg="$project after $geoNear should compute derived fields from distance",
    ),
]

# Property [Pipeline Combination - AddFields]: $addFields after $geoNear
# appends computed fields without removing existing ones.
GEONEAR_ADDFIELDS_TESTS: list[StageTestCase] = [
    StageTestCase(
        "addFields_derived_distance",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                }
            },
            {"$addFields": {"distKm": {"$divide": ["$dist", 1000]}}},
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "dist": DOUBLE_ZERO,
                "distKm": DOUBLE_ZERO,
            },
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "dist": 111_318.84502145034,
                "distKm": 111.31884502145034,
            },
        ],
        msg="$addFields after $geoNear should append computed fields preserving all originals",
    ),
]

# Property [Pipeline Combination - Group]: $group after $geoNear aggregates
# distance-ordered results into groups.
GEONEAR_GROUP_TESTS: list[StageTestCase] = [
    StageTestCase(
        "group_by_category",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "cat": "a"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "cat": "b"},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 0]}, "cat": "a"},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                }
            },
            {
                "$group": {
                    "_id": "$cat",
                    "nearest": {"$first": "$dist"},
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": "a", "nearest": DOUBLE_ZERO, "count": 2},
            {"_id": "b", "nearest": 111_318.84502145034, "count": 1},
        ],
        msg="$group after $geoNear should aggregate with $first reflecting nearest document",
    ),
]

# Property [Pipeline Combination - Unwind]: $unwind after $geoNear expands
# array fields while preserving the computed distance on each expanded document.
GEONEAR_UNWIND_TESTS: list[StageTestCase] = [
    StageTestCase(
        "unwind_preserves_dist",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "tags": ["a", "b"]},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "tags": ["c"]},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                }
            },
            {"$unwind": "$tags"},
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "tags": "a",
                "dist": DOUBLE_ZERO,
            },
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "tags": "b",
                "dist": DOUBLE_ZERO,
            },
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "tags": "c",
                "dist": 111_318.84502145034,
            },
        ],
        msg="$unwind after $geoNear should expand arrays preserving distance on each document",
    ),
]

# Property [Pipeline Combination - Count]: $count after $geoNear counts
# the documents passing through the pipeline.
GEONEAR_COUNT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "count_within_max_distance",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "maxDistance": 150000,
                }
            },
            {"$count": "total"},
        ],
        expected=[{"total": 2}],
        msg="$count after $geoNear should count documents within maxDistance",
    ),
]

# Property [Pipeline Combination - Bucket]: $bucket after $geoNear groups
# documents into distance-based ranges.
GEONEAR_BUCKET_TESTS: list[StageTestCase] = [
    StageTestCase(
        "bucket_by_distance",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                }
            },
            {
                "$bucket": {
                    "groupBy": "$dist",
                    "boundaries": [0, 150000, 300000],
                    "output": {"count": {"$sum": 1}},
                }
            },
        ],
        expected=[
            {"_id": 0, "count": 2},
            {"_id": 150000, "count": 1},
        ],
        msg="$bucket after $geoNear should group documents into distance-based ranges",
    ),
]

# Property [Pipeline Combination - ReplaceRoot]: $replaceRoot after $geoNear
# reshapes documents using the computed distance field.
GEONEAR_REPLACEROOT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "replaceRoot_reshape",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "name": "A"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "name": "B"},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                }
            },
            {"$replaceRoot": {"newRoot": {"place": "$name", "distance": "$dist"}}},
        ],
        expected=[
            {"place": "A", "distance": DOUBLE_ZERO},
            {"place": "B", "distance": 111_318.84502145034},
        ],
        msg="$replaceRoot after $geoNear should reshape documents using computed distance",
    ),
]

# Property [Pipeline Combination - Multi-Stage]: common multi-stage patterns
# combining $geoNear with filtering, re-sorting, and limiting.
GEONEAR_MULTI_STAGE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "match_then_limit",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "cat": "a"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "cat": "b"},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 0]}, "cat": "a"},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                }
            },
            {"$match": {"cat": "a"}},
            {"$limit": 1},
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "cat": "a",
                "dist": DOUBLE_ZERO,
            },
        ],
        msg="$geoNear + $match + $limit should return nearest N of a filtered category",
    ),
    StageTestCase(
        "maxDistance_sort_by_rating_limit",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "r": 3},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "r": 5},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 0]}, "r": 4},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "maxDistance": 250000,
                }
            },
            {"$sort": {"r": -1}},
            {"$limit": 1},
        ],
        expected=[
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "r": 5,
                "dist": 111_318.84502145034,
            },
        ],
        msg=(
            "$geoNear with maxDistance + $sort + $limit should return"
            " top-rated within distance radius"
        ),
    ),
    StageTestCase(
        "unwind_then_group",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "tags": ["x", "y"]},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "tags": ["y"]},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                }
            },
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": "x", "count": 1},
            {"_id": "y", "count": 2},
        ],
        msg="$geoNear + $unwind + $group should aggregate expanded array values",
    ),
]

ALL_TESTS = (
    GEONEAR_STAGE_CONSTRAINT_ERROR_TESTS
    + GEONEAR_EMPTY_MATCH_OPTIMIZATION_TESTS
    + GEONEAR_MATCH_TESTS
    + GEONEAR_SORT_TESTS
    + GEONEAR_LIMIT_TESTS
    + GEONEAR_SKIP_TESTS
    + GEONEAR_PROJECT_TESTS
    + GEONEAR_ADDFIELDS_TESTS
    + GEONEAR_GROUP_TESTS
    + GEONEAR_UNWIND_TESTS
    + GEONEAR_COUNT_TESTS
    + GEONEAR_BUCKET_TESTS
    + GEONEAR_REPLACEROOT_TESTS
    + GEONEAR_MULTI_STAGE_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(ALL_TESTS))
def test_geoNear_position_and_combinations(collection, test_case: StageTestCase):
    """Test $geoNear pipeline position constraints and stage combinations."""
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
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
