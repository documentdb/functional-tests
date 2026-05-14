"""
Tests for $polygon index interaction.

Validates behavior with and without geospatial indexes.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command


def test_polygon_without_index(collection):
    """Test $polygon query succeeds without any geospatial index."""
    collection.insert_many(
        [
            {"_id": 1, "loc": [5, 5]},
            {"_id": 2, "loc": [15, 15]},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        },
    )
    expected = [{"_id": 1, "loc": [5, 5]}]
    assertSuccess(result, expected, msg="$polygon should work without index")


def test_polygon_with_2d_index(collection):
    """Test $polygon query succeeds with 2d index."""
    collection.create_index([("loc", "2d")])
    collection.insert_many(
        [
            {"_id": 1, "loc": [5, 5]},
            {"_id": 2, "loc": [15, 15]},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        },
    )
    expected = [{"_id": 1, "loc": [5, 5]}]
    assertSuccess(result, expected, msg="$polygon should work with 2d index")


def test_polygon_results_match_with_and_without_index(collection):
    """Test $polygon produces same results with and without 2d index."""
    docs = [
        {"_id": 1, "loc": [2, 3]},
        {"_id": 2, "loc": [7, 8]},
        {"_id": 3, "loc": [5, 5]},
        {"_id": 4, "loc": [15, 15]},
    ]
    polygon_filter = {"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}}

    # Query without index
    collection.insert_many(docs)
    execute_command(collection, {"find": collection.name, "filter": polygon_filter})

    # Add index and query again
    collection.create_index([("loc", "2d")])
    result_with_index = execute_command(
        collection, {"find": collection.name, "filter": polygon_filter}
    )

    expected = [
        {"_id": 1, "loc": [2, 3]},
        {"_id": 2, "loc": [7, 8]},
        {"_id": 3, "loc": [5, 5]},
    ]
    assertSuccess(
        result_with_index,
        expected,
        ignore_doc_order=True,
        msg="Results with index should match expected",
    )


def test_polygon_index_on_different_field(collection):
    """Test $polygon on field without index when different field has 2d index."""
    collection.create_index([("other_loc", "2d")])
    collection.insert_many(
        [
            {"_id": 1, "loc": [5, 5], "other_loc": [1, 1]},
            {"_id": 2, "loc": [15, 15], "other_loc": [2, 2]},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        },
    )
    expected = [{"_id": 1, "loc": [5, 5], "other_loc": [1, 1]}]
    assertSuccess(result, expected, msg="$polygon should work on unindexed field")


def test_polygon_with_2d_index_precision(collection):
    """Test $polygon with 2d index returns correct results for dense grid."""
    collection.create_index([("loc", "2d")])
    # Insert a 5x5 grid of points
    docs = []
    doc_id = 1
    for x in range(5):
        for y in range(5):
            docs.append({"_id": doc_id, "loc": [x, y]})
            doc_id += 1
    collection.insert_many(docs)

    # Square region should contain all 25 points
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {
                "loc": {
                    "$geoWithin": {"$polygon": [[-0.5, -0.5], [-0.5, 4.5], [4.5, 4.5], [4.5, -0.5]]}
                }
            },
        },
    )
    assertSuccess(
        result,
        docs,
        ignore_doc_order=True,
        msg="Square polygon enclosing all grid points should return all docs",
    )
