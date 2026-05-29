"""
Tests for $box index interaction.

Validates $box behavior with 2d index, without index, with 2dsphere index,
custom index bounds, and queries outside index bounds.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

NO_INDEX_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="without_index",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}},
        doc=[{"_id": 1, "loc": [5, 5]}, {"_id": 2, "loc": [15, 15]}],
        expected=[{"_id": 1, "loc": [5, 5]}],
        msg="$box should work without index",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NO_INDEX_TESTS))
def test_box_no_index(collection, test):
    """Test $box works without any geospatial index."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertResult(result, expected=test.expected, ignore_doc_order=True, msg=test.msg)


WITH_2D_INDEX_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="basic_2d_index",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}},
        doc=[{"_id": 1, "loc": [5, 5]}, {"_id": 2, "loc": [15, 15]}],
        expected=[{"_id": 1, "loc": [5, 5]}],
        msg="$box with 2d index should return correct results",
    ),
    QueryTestCase(
        id="query_outside_default_bounds",
        filter={"loc": {"$geoWithin": {"$box": [[-200, -200], [200, 200]]}}},
        doc=[{"_id": 1, "loc": [5, 5]}],
        expected=[{"_id": 1, "loc": [5, 5]}],
        msg="$box query outside default bounds should still return items within bounds",
    ),
    QueryTestCase(
        id="index_bounds_clipping",
        filter={"loc": {"$geoWithin": {"$box": [[-200, -200], [200, 200]]}}},
        doc=[{"_id": i, "loc": [i * 10 - 50, 0]} for i in range(11)],
        expected=[{"_id": i, "loc": [i * 10 - 50, 0]} for i in range(11)],
        msg="$box larger than index bounds should clip and return all items",
    ),
    QueryTestCase(
        id="single_dimension_off_bounds",
        filter={"loc": {"$geoWithin": {"$box": [[-200, -10], [200, 10]]}}},
        doc=[{"_id": i, "loc": [i, 0]} for i in range(11)],
        expected=[{"_id": i, "loc": [i, 0]} for i in range(11)],
        msg="$box with single dimension off-bounds should return all items within",
    ),
    QueryTestCase(
        id="close_to_index_bounds",
        filter={"loc": {"$geoWithin": {"$box": [[-179, -179], [179, 179]]}}},
        doc=[{"_id": i, "loc": [i, 0]} for i in range(11)],
        expected=[{"_id": i, "loc": [i, 0]} for i in range(11)],
        msg="$box close to index bounds should return all items",
    ),
    QueryTestCase(
        id="inverted_coordinates_with_2d_index",
        filter={"loc": {"$geoWithin": {"$box": [[179, 179], [-179, -179]]}}},
        doc=[{"_id": i, "loc": [i, 0]} for i in range(11)],
        expected=[{"_id": i, "loc": [i, 0]} for i in range(11)],
        msg="$box with inverted coordinates should return same results with 2d index",
    ),
    QueryTestCase(
        id="mixed_inverted_coordinates_with_2d_index",
        filter={"loc": {"$geoWithin": {"$box": [[179, -179], [-179, 179]]}}},
        doc=[{"_id": i, "loc": [i, 0]} for i in range(11)],
        expected=[{"_id": i, "loc": [i, 0]} for i in range(11)],
        msg="$box with mixed inverted coordinates should return same results with 2d index",
    ),
]


@pytest.mark.parametrize("test", pytest_params(WITH_2D_INDEX_TESTS))
def test_box_with_2d_index(collection, test):
    """Test $box with 2d index."""
    collection.insert_many(test.doc)
    collection.create_index([("loc", "2d")])
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertResult(result, expected=test.expected, ignore_doc_order=True, msg=test.msg)


WITH_2DSPHERE_INDEX_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="basic_2dsphere_index",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}},
        doc=[{"_id": 1, "loc": [5, 5]}, {"_id": 2, "loc": [15, 15]}],
        expected=[{"_id": 1, "loc": [5, 5]}],
        msg="$box with 2dsphere index should still work",
    ),
]


@pytest.mark.parametrize("test", pytest_params(WITH_2DSPHERE_INDEX_TESTS))
def test_box_with_2dsphere_index(collection, test):
    """Test $box with 2dsphere index."""
    collection.insert_many(test.doc)
    collection.create_index([("loc", "2dsphere")])
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertResult(result, expected=test.expected, ignore_doc_order=True, msg=test.msg)


def test_box_custom_2d_bounds_1000(collection):
    """Test $box with 2d index bounds [-1000, 1000]."""
    collection.insert_many([{"_id": 1, "loc": [5, 5]}, {"_id": 2, "loc": [500, 500]}])
    collection.create_index([("loc", "2d")], min=-1000, max=1000)
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$box": [[0, 0], [600, 600]]}}},
        },
    )
    assertResult(
        result,
        expected=[{"_id": 1, "loc": [5, 5]}, {"_id": 2, "loc": [500, 500]}],
        ignore_doc_order=True,
        msg="$box with custom 2d index bounds [-1000, 1000] should return points within box",
    )


def test_box_custom_2d_bounds_10m(collection):
    """Test $box with 2d index bounds [-10M, 10M]."""
    collection.insert_many([{"_id": 1, "loc": [5, 5]}, {"_id": 2, "loc": [500, 500]}])
    collection.create_index([("loc", "2d")], min=-10000000, max=10000000)
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$box": [[0, 0], [600, 600]]}}},
        },
    )
    assertResult(
        result,
        expected=[{"_id": 1, "loc": [5, 5]}, {"_id": 2, "loc": [500, 500]}],
        ignore_doc_order=True,
        msg="$box with custom 2d index bounds [-10M, 10M] should return correct results",
    )


def test_box_custom_2d_bounds_1b(collection):
    """Test $box with 2d index bounds [-1B, 1B]."""
    collection.insert_many([{"_id": 1, "loc": [5, 5]}, {"_id": 2, "loc": [500, 500]}])
    collection.create_index([("loc", "2d")], min=-1000000000, max=1000000000)
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$box": [[0, 0], [600, 600]]}}},
        },
    )
    assertResult(
        result,
        expected=[{"_id": 1, "loc": [5, 5]}, {"_id": 2, "loc": [500, 500]}],
        ignore_doc_order=True,
        msg="$box with custom 2d index bounds [-1B, 1B] should return correct results",
    )


def test_box_non_default_bits_precision(collection):
    """Test $box with 2d index using non-default bits precision."""
    collection.insert_many([{"_id": 1, "loc": [5, 5]}, {"_id": 2, "loc": [15, 15]}])
    collection.create_index([("loc", "2d")], bits=16)
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}}},
    )
    assertResult(
        result,
        expected=[{"_id": 1, "loc": [5, 5]}],
        ignore_doc_order=True,
        msg="$box with non-default bits precision should return correct results",
    )


def test_box_with_compound_2d_index(collection):
    """Test $box with compound 2d index."""
    collection.insert_many(
        [
            {"_id": 1, "loc": [5, 5], "type": "a"},
            {"_id": 2, "loc": [15, 15], "type": "b"},
        ]
    )
    collection.create_index([("loc", "2d"), ("type", 1)])
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}}},
    )
    assertResult(
        result,
        expected=[{"_id": 1, "loc": [5, 5], "type": "a"}],
        ignore_doc_order=True,
        msg="$box with compound 2d index should return correct results",
    )
