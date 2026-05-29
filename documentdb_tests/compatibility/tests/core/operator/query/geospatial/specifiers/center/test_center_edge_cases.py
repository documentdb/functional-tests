"""Tests for $center edge cases — radius boundaries, coordinate boundaries, and planar distance."""

import math

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import FLOAT_INFINITY

TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="radius_zero",
        filter={"loc": {"$geoWithin": {"$center": [[0, 0], 0]}}},
        doc=[{"_id": 1, "loc": [0, 0]}, {"_id": 2, "loc": [0.001, 0]}],
        expected=[{"_id": 1, "loc": [0, 0]}],
        msg="Should return only exact center point with radius=0",
    ),
    QueryTestCase(
        id="infinity_radius",
        filter={"loc": {"$geoWithin": {"$center": [[0, 0], FLOAT_INFINITY]}}},
        doc=[{"_id": 1, "loc": [0, 0]}, {"_id": 2, "loc": [100, 100]}],
        expected=[{"_id": 1, "loc": [0, 0]}, {"_id": 2, "loc": [100, 100]}],
        msg="Should return all documents with Infinity radius",
    ),
    QueryTestCase(
        id="very_small_radius",
        filter={"loc": {"$geoWithin": {"$center": [[0, 0], 0.0001]}}},
        doc=[
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [0.00005, 0]},
            {"_id": 3, "loc": [1, 1]},
        ],
        expected=[{"_id": 1, "loc": [0, 0]}, {"_id": 2, "loc": [0.00005, 0]}],
        msg="Should work with very small radius",
    ),
    QueryTestCase(
        id="negative_coordinates",
        filter={"loc": {"$geoWithin": {"$center": [[-100, -100], 10]}}},
        doc=[
            {"_id": 1, "loc": [-100, -100]},
            {"_id": 2, "loc": [-95, -95]},
            {"_id": 3, "loc": [0, 0]},
        ],
        expected=[{"_id": 1, "loc": [-100, -100]}, {"_id": 2, "loc": [-95, -95]}],
        msg="Should work with negative coordinates",
    ),
    QueryTestCase(
        id="point_at_boundary_included",
        filter={"loc": {"$geoWithin": {"$center": [[0, 0], 1]}}},
        doc=[{"_id": 1, "loc": [1, 0]}, {"_id": 2, "loc": [2, 0]}],
        expected=[{"_id": 1, "loc": [1, 0]}],
        msg="Should include point exactly at boundary (distance=radius)",
    ),
    QueryTestCase(
        id="point_just_outside",
        filter={"loc": {"$geoWithin": {"$center": [[0, 0], 1]}}},
        doc=[{"_id": 1, "loc": [1.001, 0]}],
        expected=[],
        msg="Should not match point just outside boundary",
    ),
    QueryTestCase(
        id="diagonal_outside",
        filter={"loc": {"$geoWithin": {"$center": [[0, 0], 5]}}},
        doc=[{"_id": 1, "loc": [5, 5]}],
        expected=[],
        msg="Should exclude point at corner of bounding box (outside circle)",
    ),
    QueryTestCase(
        id="diagonal_on_boundary",
        filter={"loc": {"$geoWithin": {"$center": [[0, 0], 5]}}},
        doc=[
            {"_id": 1, "loc": [5 / math.sqrt(2), 5 / math.sqrt(2)]},
            {"_id": 2, "loc": [4, 4]},
        ],
        expected=[{"_id": 1, "loc": [5 / math.sqrt(2), 5 / math.sqrt(2)]}],
        msg="Should include point at diagonal boundary",
    ),
    QueryTestCase(
        id="point_on_boundary_of_two_touching_circles",
        filter={
            "$and": [
                {"loc": {"$geoWithin": {"$center": [[0, 0], 5]}}},
                {"loc": {"$geoWithin": {"$center": [[10, 0], 5]}}},
            ]
        },
        doc=[
            {"_id": 1, "loc": [5, 0]},
            {"_id": 2, "loc": [3, 0]},
            {"_id": 3, "loc": [7, 0]},
        ],
        expected=[{"_id": 1, "loc": [5, 0]}],
        msg="Should match point exactly on boundary of two tangent circles",
    ),
    QueryTestCase(
        id="very_large_coordinates",
        filter={"loc": {"$geoWithin": {"$center": [[1e15, 1e15], 1]}}},
        doc=[
            {"_id": 1, "loc": [1e15, 1e15]},
            {"_id": 2, "loc": [1e15 + 0.5, 1e15]},
            {"_id": 3, "loc": [1e15 + 2, 1e15]},
        ],
        expected=[
            {"_id": 1, "loc": [1e15, 1e15]},
            {"_id": 2, "loc": [1e15 + 0.5, 1e15]},
        ],
        msg="Should handle very large coordinates without float precision loss",
    ),
    QueryTestCase(
        id="irrational_boundary_sqrt2",
        filter={"loc": {"$geoWithin": {"$center": [[0, 0], math.sqrt(2)]}}},
        doc=[
            {"_id": 1, "loc": [1, 1]},
            {"_id": 2, "loc": [1.01, 1.01]},
        ],
        expected=[{"_id": 1, "loc": [1, 1]}],
        msg="Should include point at irrational boundary (sqrt(2) from origin)",
    ),
    QueryTestCase(
        id="float_rounding_near_boundary",
        filter={"loc": {"$geoWithin": {"$center": [[0, 0], 5]}}},
        doc=[
            {"_id": 1, "loc": [4.9999999999, 0]},
            {"_id": 2, "loc": [5.0000000001, 0]},
        ],
        expected=[{"_id": 1, "loc": [4.9999999999, 0]}],
        msg="Should distinguish points at near-identical distances around boundary",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_center_edge_cases(collection, test):
    """Verifies $center behavior at radius and coordinate boundaries."""
    if test.doc:
        collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg, ignore_doc_order=True)
