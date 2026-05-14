"""
Tests for $polygon query context interaction.

Validates $polygon in find, aggregation $match, combined with other operators,
and in update/delete filters.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command


def test_polygon_in_find(collection):
    """Test $polygon in basic find query."""
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
    assertSuccess(result, expected, msg="$polygon in find should return matching docs")


def test_polygon_in_aggregate_match(collection):
    """Test $polygon in aggregation $match stage."""
    collection.insert_many(
        [
            {"_id": 1, "loc": [5, 5]},
            {"_id": 2, "loc": [15, 15]},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$match": {
                        "loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}
                    }
                },
            ],
            "cursor": {},
        },
    )
    expected = [{"_id": 1, "loc": [5, 5]}]
    assertSuccess(result, expected, msg="$polygon in $match should return matching docs")


def test_polygon_combined_with_and(collection):
    """Test $polygon combined with $and operator."""
    collection.insert_many(
        [
            {"_id": 1, "loc": [5, 5], "status": "active"},
            {"_id": 2, "loc": [5, 5], "status": "inactive"},
            {"_id": 3, "loc": [15, 15], "status": "active"},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {
                "$and": [
                    {"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
                    {"status": "active"},
                ]
            },
        },
    )
    expected = [{"_id": 1, "loc": [5, 5], "status": "active"}]
    assertSuccess(result, expected, msg="$polygon with $and should filter correctly")


def test_polygon_combined_with_or(collection):
    """Test $polygon combined with $or operator."""
    collection.insert_many(
        [
            {"_id": 1, "loc": [5, 5]},
            {"_id": 2, "loc": [15, 15]},
            {"_id": 3, "loc": [25, 25]},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {
                "$or": [
                    {"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
                    {"loc": {"$geoWithin": {"$polygon": [[20, 20], [20, 30], [30, 30], [30, 20]]}}},
                ]
            },
        },
    )
    expected = [{"_id": 1, "loc": [5, 5]}, {"_id": 3, "loc": [25, 25]}]
    assertSuccess(
        result, expected, ignore_doc_order=True, msg="$polygon with $or should match either polygon"
    )


def test_polygon_with_projection(collection):
    """Test $polygon with field projection."""
    collection.insert_many(
        [
            {"_id": 1, "loc": [5, 5], "name": "A", "value": 100},
            {"_id": 2, "loc": [15, 15], "name": "B", "value": 200},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
            "projection": {"name": 1},
        },
    )
    expected = [{"_id": 1, "name": "A"}]
    assertSuccess(
        result, expected, msg="$polygon with projection should return only projected fields"
    )


def test_polygon_with_sort(collection):
    """Test $polygon results with sort."""
    collection.insert_many(
        [
            {"_id": 1, "loc": [5, 5], "val": 30},
            {"_id": 2, "loc": [3, 3], "val": 10},
            {"_id": 3, "loc": [7, 7], "val": 20},
            {"_id": 4, "loc": [15, 15], "val": 5},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
            "sort": {"val": 1},
        },
    )
    expected = [
        {"_id": 2, "loc": [3, 3], "val": 10},
        {"_id": 3, "loc": [7, 7], "val": 20},
        {"_id": 1, "loc": [5, 5], "val": 30},
    ]
    assertSuccess(result, expected, msg="$polygon with sort should return sorted results")


def test_polygon_with_limit(collection):
    """Test $polygon results with limit."""
    collection.insert_many(
        [
            {"_id": 1, "loc": [2, 2]},
            {"_id": 2, "loc": [5, 5]},
            {"_id": 3, "loc": [8, 8]},
            {"_id": 4, "loc": [15, 15]},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
            "limit": 2,
        },
    )
    # Should return exactly 2 documents
    result_docs = result["cursor"]["firstBatch"]
    assertSuccess(
        result, result_docs[:2], raw_res=False, msg="$polygon with limit should limit results"
    )


def test_polygon_in_update_filter(collection):
    """Test $polygon as filter in updateMany."""
    collection.insert_many(
        [
            {"_id": 1, "loc": [5, 5], "updated": False},
            {"_id": 2, "loc": [15, 15], "updated": False},
        ]
    )
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {
                        "loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}
                    },
                    "u": {"$set": {"updated": True}},
                    "multi": True,
                }
            ],
        },
    )
    assertSuccess(
        result,
        {"n": 1, "nModified": 1, "ok": 1.0},
        raw_res=True,
        msg="$polygon in update should match correct docs",
    )


def test_polygon_in_delete_filter(collection):
    """Test $polygon as filter in delete."""
    collection.insert_many(
        [
            {"_id": 1, "loc": [5, 5]},
            {"_id": 2, "loc": [15, 15]},
        ]
    )
    result = execute_command(
        collection,
        {
            "delete": collection.name,
            "deletes": [
                {
                    "q": {
                        "loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}
                    },
                    "limit": 0,
                }
            ],
        },
    )
    assertSuccess(
        result,
        {"n": 1, "ok": 1.0},
        raw_res=True,
        msg="$polygon in delete should match correct docs",
    )


def test_polygon_count_documents(collection):
    """Test countDocuments with $polygon filter."""
    collection.insert_many(
        [
            {"_id": 1, "loc": [5, 5]},
            {"_id": 2, "loc": [3, 3]},
            {"_id": 3, "loc": [15, 15]},
        ]
    )
    result = execute_command(
        collection,
        {
            "count": collection.name,
            "query": {"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        },
    )
    assertSuccess(
        result,
        {"n": 2, "ok": 1.0},
        raw_res=True,
        msg="count with $polygon should return correct count",
    )


def test_polygon_distinct(collection):
    """Test distinct with $polygon filter."""
    collection.insert_many(
        [
            {"_id": 1, "loc": [5, 5], "category": "A"},
            {"_id": 2, "loc": [3, 3], "category": "B"},
            {"_id": 3, "loc": [15, 15], "category": "C"},
        ]
    )
    result = execute_command(
        collection,
        {
            "distinct": collection.name,
            "key": "category",
            "query": {"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        },
    )
    assertSuccess(
        result,
        {"values": ["A", "B"], "ok": 1.0},
        raw_res=True,
        msg="distinct with $polygon should return correct values",
    )


def test_polygon_nested_field_path(collection):
    """Test $polygon on nested field path."""
    collection.insert_many(
        [
            {"_id": 1, "address": {"loc": [5, 5]}},
            {"_id": 2, "address": {"loc": [15, 15]}},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {
                "address.loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}
            },
        },
    )
    expected = [{"_id": 1, "address": {"loc": [5, 5]}}]
    assertSuccess(result, expected, msg="$polygon on nested field should work")


def test_polygon_empty_collection(collection):
    """Test $polygon on empty collection returns empty result."""
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        },
    )
    assertSuccess(result, [], msg="$polygon on empty collection should return empty result")


def test_polygon_combined_with_box_via_or(collection):
    """Test $polygon combined with $box in same query via $or."""
    collection.insert_many(
        [
            {"_id": 1, "loc": [5, 5]},
            {"_id": 2, "loc": [25, 25]},
            {"_id": 3, "loc": [50, 50]},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {
                "$or": [
                    {"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
                    {"loc": {"$geoWithin": {"$box": [[20, 20], [30, 30]]}}},
                ]
            },
        },
    )
    expected = [{"_id": 1, "loc": [5, 5]}, {"_id": 2, "loc": [25, 25]}]
    assertSuccess(
        result, expected, ignore_doc_order=True, msg="$polygon and $box via $or should both work"
    )


def test_polygon_combined_with_center_via_or(collection):
    """Test $polygon combined with $center in same query via $or."""
    collection.insert_many(
        [
            {"_id": 1, "loc": [5, 5]},
            {"_id": 2, "loc": [25, 25]},
            {"_id": 3, "loc": [50, 50]},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {
                "$or": [
                    {"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
                    {"loc": {"$geoWithin": {"$center": [[25, 25], 2]}}},
                ]
            },
        },
    )
    expected = [{"_id": 1, "loc": [5, 5]}, {"_id": 2, "loc": [25, 25]}]
    assertSuccess(
        result, expected, ignore_doc_order=True, msg="$polygon and $center via $or should both work"
    )


def test_polygon_vs_geometry_polygon_different(collection):
    """Test $polygon (legacy) and $geometry Polygon match different document types."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_many(
        [
            {"_id": 1, "loc": [5, 5]},  # legacy coordinate pair
            {"_id": 2, "loc": {"type": "Point", "coordinates": [5, 5]}},  # GeoJSON
        ]
    )
    # $polygon (legacy) - matches both legacy pairs and GeoJSON points
    result_polygon = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        },
    )
    expected = [
        {"_id": 1, "loc": [5, 5]},
        {"_id": 2, "loc": {"type": "Point", "coordinates": [5, 5]}},
    ]
    assertSuccess(
        result_polygon,
        expected,
        ignore_doc_order=True,
        msg="$polygon should match both legacy and GeoJSON point formats",
    )


def test_polygon_on_array_location_field(collection):
    """Test $polygon on field that is an array of coordinate pairs."""
    collection.insert_many(
        [
            {"_id": 1, "loc": [[5, 5], [15, 15]]},
            {"_id": 2, "loc": [[20, 20]]},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        },
    )
    # Array of coordinate pairs matches if any sub-pair is inside the polygon
    expected = [{"_id": 1, "loc": [[5, 5], [15, 15]]}]
    assertSuccess(result, expected, msg="Array location field should match if any point is inside")


def test_polygon_on_capped_collection(database_client):
    """Test $polygon on capped collection."""
    coll_name = "test_polygon_capped"
    database_client.create_collection(coll_name, capped=True, size=4096)
    coll = database_client[coll_name]
    try:
        coll.insert_many(
            [
                {"_id": 1, "loc": [5, 5]},
                {"_id": 2, "loc": [15, 15]},
            ]
        )
        result = execute_command(
            coll,
            {
                "find": coll.name,
                "filter": {
                    "loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}
                },
            },
        )
        expected = [{"_id": 1, "loc": [5, 5]}]
        assertSuccess(result, expected, msg="$polygon should work on capped collection")
    finally:
        database_client.drop_collection(coll_name)
