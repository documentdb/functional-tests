"""Tests for $maxDistance with legacy coordinate pairs ($near and $nearSphere, 2d index)."""

import math

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

NEAR_LEGACY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="basic_legacy_maxDistance",
        filter={"loc": {"$near": [0, 0], "$maxDistance": 5}},
        doc=[
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [1, 1]},
            {"_id": 3, "loc": [50, 50]},
        ],
        expected=[
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [1, 1]},
        ],
        msg="Should filter legacy coordinates with $maxDistance in flat units",
    ),
    QueryTestCase(
        id="legacy_sorted_nearest_first",
        filter={"loc": {"$near": [0, 0], "$maxDistance": 100}},
        doc=[
            {"_id": 1, "loc": [10, 10]},
            {"_id": 2, "loc": [0, 0]},
            {"_id": 3, "loc": [5, 5]},
        ],
        expected=[
            {"_id": 2, "loc": [0, 0]},
            {"_id": 3, "loc": [5, 5]},
            {"_id": 1, "loc": [10, 10]},
        ],
        msg="Should return legacy results sorted nearest first",
    ),
    QueryTestCase(
        id="legacy_zero_maxDistance",
        filter={"loc": {"$near": [0, 0], "$maxDistance": 0}},
        doc=[
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [1, 1]},
        ],
        expected=[
            {"_id": 1, "loc": [0, 0]},
        ],
        msg="Should return only exact match with $maxDistance 0 on legacy",
    ),
    QueryTestCase(
        id="legacy_with_minDistance",
        filter={"loc": {"$near": [0, 0], "$maxDistance": 50, "$minDistance": 5}},
        doc=[
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [10, 10]},
            {"_id": 3, "loc": [40, 40]},
        ],
        expected=[
            {"_id": 2, "loc": [10, 10]},
        ],
        msg="Should return docs in annular region with legacy coordinates",
    ),
    QueryTestCase(
        id="legacy_empty_result",
        filter={"loc": {"$near": [0, 0], "$maxDistance": 0.001}},
        doc=[
            {"_id": 1, "loc": [10, 10]},
        ],
        expected=[],
        msg="Should return empty when no legacy docs within distance",
    ),
]

NEARSPHERE_LEGACY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="nearSphere_2d_with_maxDistance_radians",
        filter={
            "loc": {
                "$nearSphere": [0, 0],
                "$maxDistance": math.radians(5),
            }
        },
        doc=[
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [2, 2]},
            {"_id": 3, "loc": [50, 50]},
        ],
        expected=[
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [2, 2]},
        ],
        msg="Should filter $nearSphere with $maxDistance in radians (2d index)",
    ),
    QueryTestCase(
        id="legacy_coords_radians_with_minDistance",
        filter={
            "loc": {
                "$nearSphere": [0, 0],
                "$minDistance": math.radians(2),
                "$maxDistance": math.radians(20),
            }
        },
        doc=[
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [5, 5]},
            {"_id": 3, "loc": [50, 50]},
        ],
        expected=[
            {"_id": 2, "loc": [5, 5]},
        ],
        msg="Should return $nearSphere legacy docs in annular region (radians)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NEAR_LEGACY_TESTS))
def test_maxDistance_near_legacy(collection, test):
    """Verifies $maxDistance with $near and legacy coordinate pairs (2d index)."""
    collection.create_index([("loc", "2d")])
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(NEARSPHERE_LEGACY_TESTS))
def test_maxDistance_nearSphere_legacy(collection, test):
    """Verifies $maxDistance with $nearSphere and legacy coordinates (radians, 2d index)."""
    collection.create_index([("loc", "2d")])
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg)


def test_maxDistance_nearSphere_2d_annular(collection):
    """Verifies $nearSphere + 2d index with both $minDistance and $maxDistance in radians."""
    collection.create_index([("loc", "2d")])
    collection.insert_many(
        [
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [3, 0]},
            {"_id": 3, "loc": [50, 0]},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {
                "loc": {
                    "$nearSphere": [0, 0],
                    "$minDistance": math.radians(1),
                    "$maxDistance": math.radians(10),
                }
            },
        },
    )
    assertSuccess(
        result,
        [{"_id": 2, "loc": [3, 0]}],
        msg="Should return docs in annular region with $nearSphere + 2d (radians)",
    )


def test_maxDistance_zero_nearSphere_2d_radians(collection):
    """Verifies $maxDistance: 0 with $nearSphere + 2d index returns only exact match."""
    collection.create_index([("loc", "2d")])
    collection.insert_many(
        [
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [1, 0]},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$nearSphere": [0, 0], "$maxDistance": 0}},
        },
    )
    assertSuccess(
        result,
        [{"_id": 1, "loc": [0, 0]}],
        msg="Should return only exact match with $maxDistance: 0 (radians)",
    )
