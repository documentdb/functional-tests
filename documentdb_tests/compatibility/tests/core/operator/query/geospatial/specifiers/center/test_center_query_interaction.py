"""Tests for $center query interaction — combination with other operators, field paths,
and comparison with $centerSphere."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="two_geoWithin_same_field",
        filter={
            "$and": [
                {"loc": {"$geoWithin": {"$center": [[0, 0], 5]}}},
                {"loc": {"$geoWithin": {"$center": [[1, 1], 5]}}},
            ]
        },
        doc=[{"_id": 1, "loc": [0, 0]}],
        expected=[{"_id": 1, "loc": [0, 0]}],
        msg="Should handle two $geoWithin on same field",
    ),
    QueryTestCase(
        id="combined_with_equality",
        filter={
            "loc": {"$geoWithin": {"$center": [[0, 0], 2]}},
            "status": "active",
        },
        doc=[
            {"_id": 1, "loc": [0, 0], "status": "active"},
            {"_id": 2, "loc": [1, 0], "status": "inactive"},
            {"_id": 3, "loc": [0, 1], "status": "active"},
            {"_id": 4, "loc": [10, 10], "status": "active"},
        ],
        expected=[
            {"_id": 1, "loc": [0, 0], "status": "active"},
            {"_id": 3, "loc": [0, 1], "status": "active"},
        ],
        msg="Should combine $center with equality filter",
    ),
    QueryTestCase(
        id="combined_with_or",
        filter={
            "$or": [
                {"loc": {"$geoWithin": {"$center": [[0, 0], 2]}}},
                {"type": "a"},
            ]
        },
        doc=[
            {"_id": 1, "loc": [0, 0], "type": "a"},
            {"_id": 2, "loc": [1, 0], "type": "b"},
            {"_id": 3, "loc": [10, 10], "type": "a"},
        ],
        expected=[
            {"_id": 1, "loc": [0, 0], "type": "a"},
            {"_id": 2, "loc": [1, 0], "type": "b"},
            {"_id": 3, "loc": [10, 10], "type": "a"},
        ],
        msg="Should combine $center with $or operator",
    ),
    QueryTestCase(
        id="nested_field",
        filter={"address.loc": {"$geoWithin": {"$center": [[0, 0], 5]}}},
        doc=[
            {"_id": 1, "address": {"loc": [0, 0]}},
            {"_id": 2, "address": {"loc": [10, 10]}},
        ],
        expected=[{"_id": 1, "address": {"loc": [0, 0]}}],
        msg="Should work on nested field path",
    ),
    QueryTestCase(
        id="array_of_points",
        filter={"locs": {"$geoWithin": {"$center": [[0, 0], 5]}}},
        doc=[
            {"_id": 1, "locs": [[0, 0], [10, 10]]},
            {"_id": 2, "locs": [[20, 20], [30, 30]]},
        ],
        expected=[{"_id": 1, "locs": [[0, 0], [10, 10]]}],
        msg="Should match if ANY point in array is within circle",
    ),
    QueryTestCase(
        id="uses_planar_geometry",
        filter={"loc": {"$geoWithin": {"$center": [[0, 0], 0.15]}}},
        doc=[
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [0.1, 0]},
            {"_id": 3, "loc": [0, 0.1]},
        ],
        expected=[
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [0.1, 0]},
            {"_id": 3, "loc": [0, 0.1]},
        ],
        msg="$center should use planar geometry and return points within Euclidean distance",
    ),
    QueryTestCase(
        id="combined_with_not",
        filter={"loc": {"$not": {"$geoWithin": {"$center": [[0, 0], 2]}}}},
        doc=[
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [1, 1]},
            {"_id": 3, "loc": [10, 10]},
        ],
        expected=[{"_id": 3, "loc": [10, 10]}],
        msg="Should return documents outside circle when using $not",
    ),
    QueryTestCase(
        id="combined_with_nor",
        filter={
            "$nor": [
                {"loc": {"$geoWithin": {"$center": [[0, 0], 2]}}},
            ]
        },
        doc=[
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [5, 5]},
        ],
        expected=[{"_id": 2, "loc": [5, 5]}],
        msg="Should return documents not matching any $nor condition",
    ),
    QueryTestCase(
        id="planar_vs_spherical_divergence",
        filter={"loc": {"$geoWithin": {"$center": [[0, 89], 10]}}},
        doc=[
            {"_id": 1, "loc": [10, 89]},
            {"_id": 2, "loc": [0, 79]},
            {"_id": 3, "loc": [11, 89]},
        ],
        expected=[{"_id": 1, "loc": [10, 89]}, {"_id": 2, "loc": [0, 79]}],
        msg="$center uses planar distance — points at 10 units match regardless of latitude",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_center_query_interaction(collection, test):
    """Verifies $center works correctly combined with other query operators."""
    if test.doc:
        collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg, ignore_doc_order=True)


def test_center_with_projection(collection):
    """Test $center with projection."""
    collection.insert_many(
        [
            {"_id": 1, "loc": [0, 0], "name": "A"},
            {"_id": 2, "loc": [10, 10], "name": "B"},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$center": [[0, 0], 5]}}},
            "projection": {"name": 1},
        },
    )
    assertSuccess(result, [{"_id": 1, "name": "A"}], msg="Should work with projection")


def test_center_with_limit(collection):
    """Test $center with limit."""
    collection.insert_many(
        [
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [1, 0]},
            {"_id": 3, "loc": [0, 1]},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$center": [[0, 0], 5]}}},
            "limit": 2,
        },
    )
    assertSuccess(
        result,
        [{"_id": 1, "loc": [0, 0]}, {"_id": 2, "loc": [1, 0]}],
        msg="Should respect limit",
    )


def test_center_with_sort(collection):
    """Test $center with sort on a non-geo field."""
    collection.insert_many(
        [
            {"_id": 1, "loc": [0, 0], "val": 3},
            {"_id": 2, "loc": [1, 0], "val": 1},
            {"_id": 3, "loc": [0, 1], "val": 2},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$center": [[0, 0], 5]}}},
            "sort": {"val": 1},
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 2, "loc": [1, 0], "val": 1},
            {"_id": 3, "loc": [0, 1], "val": 2},
            {"_id": 1, "loc": [0, 0], "val": 3},
        ],
        msg="Should respect sort on non-geo field",
    )


def test_center_with_skip(collection):
    """Test $center with skip."""
    collection.insert_many(
        [
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [1, 0]},
            {"_id": 3, "loc": [0, 1]},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$center": [[0, 0], 5]}}},
            "skip": 1,
        },
    )
    assertSuccess(
        result,
        [{"_id": 2, "loc": [1, 0]}, {"_id": 3, "loc": [0, 1]}],
        msg="Should respect skip",
    )
