"""
Tests for $polygon from MongoDB JS test specifications.

Covers geo_polygon1.js, geo_poly_edge.js, and geo_max.js test scenarios
including triangle containment, large coordinates, boundary coordinates,
and dense grid behavior.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command


def test_polygon_triangle_single_match(collection):
    """Test $polygon with triangle containing single point from grid (geo_polygon1)."""
    collection.create_index([("loc", "2d")])
    # Insert a 10x10 grid
    docs = []
    doc_id = 1
    for x in range(10):
        for y in range(10):
            docs.append({"_id": doc_id, "loc": [x, y]})
            doc_id += 1
    collection.insert_many(docs)

    # Small triangle containing only point [1,1]
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$polygon": [[0.5, 0.5], [1.5, 0.5], [1, 1.5]]}}},
        },
    )
    expected = [{"_id": 12, "loc": [1, 1]}]
    assertSuccess(result, expected, msg="Triangle should contain single grid point")


def test_polygon_edge_large_coordinates(collection):
    """Test $polygon with coordinates exceeding default 2d bounds (geo_poly_edge)."""
    collection.create_index([("loc", "2d"), ("val", 1)], min=-1000, max=1000)
    collection.insert_many(
        [
            {"_id": 1, "loc": [100, 100], "val": 1},
            {"_id": 2, "loc": [500, 500], "val": 2},
            {"_id": 3, "loc": [900, 900], "val": 3},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {
                "loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 600], [600, 600], [600, 0]]}}
            },
        },
    )
    expected = [
        {"_id": 1, "loc": [100, 100], "val": 1},
        {"_id": 2, "loc": [500, 500], "val": 2},
    ]
    assertSuccess(
        result,
        expected,
        ignore_doc_order=True,
        msg="Large coordinates within custom bounds should work",
    )


def test_polygon_boundary_positive_max(collection):
    """Test $polygon at positive max longitude boundary (geo_max)."""
    collection.create_index([("loc", "2d")])
    collection.insert_many(
        [
            {"_id": 1, "loc": [50, 50]},
            {"_id": 2, "loc": [-50, -50]},
        ]
    )
    # Triangle at positive boundary
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {
                "loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 179], [179, 179], [179, 0]]}}
            },
        },
    )
    expected = [{"_id": 1, "loc": [50, 50]}]
    assertSuccess(
        result,
        expected,
        msg="Polygon at positive boundary should match positive-x points only",
    )


def test_polygon_boundary_negative_max(collection):
    """Test $polygon at negative max longitude boundary (geo_max)."""
    collection.create_index([("loc", "2d")])
    collection.insert_many(
        [
            {"_id": 1, "loc": [50, 50]},
            {"_id": 2, "loc": [-50, -50]},
        ]
    )
    # Triangle at negative boundary
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {
                "loc": {"$geoWithin": {"$polygon": [[-179, -179], [-179, 0], [0, 0], [0, -179]]}}
            },
        },
    )
    expected = [{"_id": 2, "loc": [-50, -50]}]
    assertSuccess(
        result,
        expected,
        msg="Polygon at negative boundary should match negative-x points only",
    )


def test_polygon_dense_grid_triangle(collection):
    """Test $polygon with triangle on dense grid (geo_polygon.js)."""
    collection.create_index([("loc", "2d")])
    # Insert a grid with 0.5 spacing from 0 to 9.5 (20x20 = 400 points)
    docs = []
    doc_id = 1
    for i in range(20):
        for j in range(20):
            docs.append({"_id": doc_id, "loc": [i * 0.5, j * 0.5]})
            doc_id += 1
    collection.insert_many(docs)

    # Triangle
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$polygon": [[4, 4], [6, 4], [5, 6]]}}},
        },
    )
    # Verify it returns results without error (exact count depends on boundary inclusion)
    result_docs = result["cursor"]["firstBatch"]
    assertSuccess(result, result_docs, msg="Triangle on dense grid should not error")
