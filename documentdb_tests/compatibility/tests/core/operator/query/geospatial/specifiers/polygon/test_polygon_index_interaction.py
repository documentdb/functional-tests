"""
Tests for $polygon index interaction.

Validates behavior with and without geospatial indexes, including
dense grid queries with 2d indexes.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command


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


def test_polygon_dense_grid_triangle(collection):
    """Test $polygon with triangle on dense grid with 2d index."""
    collection.create_index([("loc", "2d")])
    # Insert a grid with 0.5 spacing from 0 to 9.5 (20x20 = 400 points)
    docs = []
    doc_id = 1
    for i in range(20):
        for j in range(20):
            docs.append({"_id": doc_id, "loc": [i * 0.5, j * 0.5]})
            doc_id += 1
    collection.insert_many(docs)

    # Triangle: vertices [4,4], [6,4], [5,6]
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$polygon": [[4, 4], [6, 4], [5, 6]]}}},
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 169, "loc": [4.0, 4.0]},
            {"_id": 189, "loc": [4.5, 4.0]},
            {"_id": 190, "loc": [4.5, 4.5]},
            {"_id": 209, "loc": [5.0, 4.0]},
            {"_id": 210, "loc": [5.0, 4.5]},
            {"_id": 211, "loc": [5.0, 5.0]},
            {"_id": 212, "loc": [5.0, 5.5]},
            {"_id": 213, "loc": [5.0, 6.0]},
            {"_id": 229, "loc": [5.5, 4.0]},
            {"_id": 230, "loc": [5.5, 4.5]},
            {"_id": 231, "loc": [5.5, 5.0]},
            {"_id": 249, "loc": [6.0, 4.0]},
        ],
        ignore_doc_order=True,
        msg="Triangle on dense grid should return 12 points (interior + boundary)",
    )
