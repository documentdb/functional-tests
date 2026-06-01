"""Tests for $minDistance with legacy coordinates (2d index)."""

import math

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

EARTH_RADIUS_KM = 6371


def km_to_radians(km):
    return km / EARTH_RADIUS_KM


LEGACY_DOCS = [
    {"_id": 1, "loc": [40, 0]},
    {"_id": 2, "loc": [41, 0]},
    {"_id": 3, "loc": [42, 0]},
]

NEAR_2D_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="near_2d_no_minDistance",
        filter={"loc": {"$near": [0, 0]}},
        doc=LEGACY_DOCS,
        expected=[
            {"_id": 1, "loc": [40, 0]},
            {"_id": 2, "loc": [41, 0]},
            {"_id": 3, "loc": [42, 0]},
        ],
        msg="Should return all docs sorted by distance without minDistance",
    ),
    QueryTestCase(
        id="near_2d_with_minDistance",
        filter={"loc": {"$near": [0, 0], "$minDistance": 41.5}},
        doc=LEGACY_DOCS,
        expected=[
            {"_id": 3, "loc": [42, 0]},
        ],
        msg="Should exclude docs closer than minDistance=41.5 with 2d index",
    ),
    QueryTestCase(
        id="near_2d_minDistance_zero",
        filter={"loc": {"$near": [0, 0], "$minDistance": 0}},
        doc=LEGACY_DOCS,
        expected=[
            {"_id": 1, "loc": [40, 0]},
            {"_id": 2, "loc": [41, 0]},
            {"_id": 3, "loc": [42, 0]},
        ],
        msg="Should include all docs when minDistance is 0 with 2d index",
    ),
    QueryTestCase(
        id="nearSphere_2d_no_minDistance",
        filter={"loc": {"$nearSphere": [0, 0]}},
        doc=LEGACY_DOCS,
        expected=[
            {"_id": 1, "loc": [40, 0]},
            {"_id": 2, "loc": [41, 0]},
            {"_id": 3, "loc": [42, 0]},
        ],
        msg="Should return all docs sorted by spherical distance without minDistance",
    ),
    QueryTestCase(
        id="nearSphere_2d_with_minDistance_radians",
        filter={
            "loc": {
                "$nearSphere": [0, 0],
                "$minDistance": math.radians(41.5),
            }
        },
        doc=LEGACY_DOCS,
        expected=[
            {"_id": 3, "loc": [42, 0]},
        ],
        msg="Should exclude docs closer than minDistance in radians with $nearSphere + 2d",
    ),
]

NEARSPHERE_LEGACY_DOCS = [
    {"_id": 1, "loc": [0, 0]},
    {"_id": 2, "loc": [1, 0]},
    {"_id": 3, "loc": [5, 5]},
    {"_id": 4, "loc": [10, 10]},
]

NEARSPHERE_LEGACY_COORDS_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="legacy_coords_minDistance_radians",
        filter={
            "loc": {
                "$nearSphere": [0, 0],
                "$minDistance": km_to_radians(200),
            }
        },
        doc=NEARSPHERE_LEGACY_DOCS,
        expected=[
            {"_id": 3, "loc": [5, 5]},
            {"_id": 4, "loc": [10, 10]},
        ],
        msg="Should exclude docs closer than 200km (radians) with $nearSphere + legacy",
    ),
    QueryTestCase(
        id="legacy_coords_minDistance_zero",
        filter={
            "loc": {
                "$nearSphere": [0, 0],
                "$minDistance": 0,
            }
        },
        doc=NEARSPHERE_LEGACY_DOCS,
        expected=[
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [1, 0]},
            {"_id": 3, "loc": [5, 5]},
            {"_id": 4, "loc": [10, 10]},
        ],
        msg="Should include all docs when $minDistance is 0 with legacy coordinates",
    ),
    QueryTestCase(
        id="legacy_coords_annular_region",
        filter={
            "loc": {
                "$nearSphere": [0, 0],
                "$minDistance": km_to_radians(500),
                "$maxDistance": km_to_radians(1000),
            }
        },
        doc=NEARSPHERE_LEGACY_DOCS,
        expected=[
            {"_id": 3, "loc": [5, 5]},
        ],
        msg="Should return docs in annular region with $nearSphere + legacy (radians)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NEAR_2D_TESTS))
def test_minDistance_near_legacy(collection, test):
    """Verifies $minDistance with legacy coordinates (2d index)."""
    collection.create_index([("loc", "2d")])
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(NEARSPHERE_LEGACY_COORDS_TESTS))
def test_minDistance_nearSphere_legacy_coords(collection, test):
    """Verifies $minDistance with $nearSphere and legacy coordinates (radians)."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg)


def test_minDistance_nearSphere_2d_annular(collection):
    """Verifies $nearSphere + 2d index with both $minDistance and $maxDistance."""
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
