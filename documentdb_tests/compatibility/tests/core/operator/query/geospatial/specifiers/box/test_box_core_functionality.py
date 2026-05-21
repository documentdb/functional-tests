"""
Tests for $box core functionality.

Validates basic $box behavior with $geoWithin, GeoJSON exclusion,
multiple documents, coordinate ordering, and result correctness.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

CORE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="basic_box_returns_points_inside",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}},
        doc=[
            {"_id": 1, "loc": [5, 5]},
            {"_id": 2, "loc": [15, 15]},
        ],
        expected=[{"_id": 1, "loc": [5, 5]}],
        msg="$box should return documents within rectangle bounds",
    ),
    QueryTestCase(
        id="does_not_return_outside",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}},
        doc=[
            {"_id": 1, "loc": [11, 11]},
            {"_id": 2, "loc": [-1, -1]},
        ],
        expected=[],
        msg="$box should NOT return documents outside the rectangle",
    ),
    QueryTestCase(
        id="longitude_first_latitude_second",
        filter={"loc": {"$geoWithin": {"$box": [[-74, 40], [-73, 41]]}}},
        doc=[
            {"_id": 1, "loc": [-73.5, 40.5]},
            {"_id": 2, "loc": [0, 0]},
        ],
        expected=[{"_id": 1, "loc": [-73.5, 40.5]}],
        msg="$box uses longitude first, latitude second ordering",
    ),
    QueryTestCase(
        id="arbitrary_grid_coordinates",
        filter={"loc": {"$geoWithin": {"$box": [[100, 200], [300, 400]]}}},
        doc=[
            {"_id": 1, "loc": [150, 250]},
            {"_id": 2, "loc": [50, 50]},
        ],
        expected=[{"_id": 1, "loc": [150, 250]}],
        msg="$box works with arbitrary grid coordinates",
    ),
    QueryTestCase(
        id="grid_count_4x4",
        filter={"loc": {"$geoWithin": {"$box": [[2, 2], [5, 5]]}}},
        doc=[{"_id": i * 10 + j, "loc": [i, j]} for i in range(10) for j in range(10)],
        expected=[{"_id": i * 10 + j, "loc": [i, j]} for i in range(2, 6) for j in range(2, 6)],
        msg="Grid count should be 16",
    ),
    QueryTestCase(
        id="full_coverage",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [9, 9]]}}},
        doc=[{"_id": i * 10 + j, "loc": [i, j]} for i in range(10) for j in range(10)],
        expected=[{"_id": i * 10 + j, "loc": [i, j]} for i in range(10) for j in range(10)],
        msg="Should return all 100 documents",
    ),
    QueryTestCase(
        id="geojson_point_within_bounds_matched",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}},
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [5, 5]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [5, 5]}}],
        msg="$box matches documents stored as GeoJSON Point within bounds",
    ),
    QueryTestCase(
        id="multiple_inside_all_returned",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}},
        doc=[
            {"_id": 1, "loc": [1, 1]},
            {"_id": 2, "loc": [5, 5]},
            {"_id": 3, "loc": [9, 9]},
        ],
        expected=[
            {"_id": 1, "loc": [1, 1]},
            {"_id": 2, "loc": [5, 5]},
            {"_id": 3, "loc": [9, 9]},
        ],
        msg="$box should return all documents inside the rectangle",
    ),
    QueryTestCase(
        id="mixed_inside_outside",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}},
        doc=[
            {"_id": 1, "loc": [5, 5]},
            {"_id": 2, "loc": [15, 15]},
            {"_id": 3, "loc": [8, 8]},
        ],
        expected=[
            {"_id": 1, "loc": [5, 5]},
            {"_id": 3, "loc": [8, 8]},
        ],
        msg="$box should return only documents inside the rectangle",
    ),
    QueryTestCase(
        id="no_documents_inside",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}},
        doc=[
            {"_id": 1, "loc": [20, 20]},
            {"_id": 2, "loc": [30, 30]},
        ],
        expected=[],
        msg="$box should return empty result when no documents are inside",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CORE_TESTS))
def test_box_core(collection, test):
    """Test $box core functionality with $geoWithin."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertResult(result, expected=test.expected, ignore_doc_order=True, msg=test.msg)


def test_box_empty_collection(collection):
    """Test $box returns empty result on empty collection."""
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}}},
    )
    assertResult(result, expected=[], msg="$box should return empty result on empty collection")
