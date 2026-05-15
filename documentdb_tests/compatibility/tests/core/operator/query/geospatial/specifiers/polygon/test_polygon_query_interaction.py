"""
Tests for $polygon query context interaction.

Validates $polygon in find, aggregation $match, combined with other operators,
and in update/delete filters.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

FIND_QUERY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="basic_find",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        doc=[{"_id": 1, "loc": [5, 5]}, {"_id": 2, "loc": [15, 15]}],
        expected=[{"_id": 1, "loc": [5, 5]}],
        msg="$polygon in find should return matching docs",
    ),
    QueryTestCase(
        id="nested_field_path",
        filter={"address.loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        doc=[
            {"_id": 1, "address": {"loc": [5, 5]}},
            {"_id": 2, "address": {"loc": [15, 15]}},
        ],
        expected=[{"_id": 1, "address": {"loc": [5, 5]}}],
        msg="$polygon on nested field should work",
    ),
    QueryTestCase(
        id="empty_collection",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        expected=[],
        msg="$polygon on empty collection should return empty result",
    ),
    QueryTestCase(
        id="array_location_field",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        doc=[
            {"_id": 1, "loc": [[5, 5], [15, 15]]},
            {"_id": 2, "loc": [[20, 20]]},
        ],
        expected=[{"_id": 1, "loc": [[5, 5], [15, 15]]}],
        msg="Array location field should match if any point is inside",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIND_QUERY_TESTS))
def test_polygon_find_queries(collection, test):
    """Test $polygon in various find query contexts."""
    if test.doc:
        collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected)


COMBINED_OPERATOR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="with_and",
        filter={
            "$and": [
                {"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
                {"status": "active"},
            ]
        },
        doc=[
            {"_id": 1, "loc": [5, 5], "status": "active"},
            {"_id": 2, "loc": [5, 5], "status": "inactive"},
            {"_id": 3, "loc": [15, 15], "status": "active"},
        ],
        expected=[{"_id": 1, "loc": [5, 5], "status": "active"}],
        msg="$polygon with $and should filter correctly",
    ),
    QueryTestCase(
        id="with_or",
        filter={
            "$or": [
                {"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
                {"loc": {"$geoWithin": {"$polygon": [[20, 20], [20, 30], [30, 30], [30, 20]]}}},
            ]
        },
        doc=[
            {"_id": 1, "loc": [5, 5]},
            {"_id": 2, "loc": [15, 15]},
            {"_id": 3, "loc": [25, 25]},
        ],
        expected=[{"_id": 1, "loc": [5, 5]}, {"_id": 3, "loc": [25, 25]}],
        msg="$polygon with $or should match either polygon",
    ),
    QueryTestCase(
        id="with_box_via_or",
        filter={
            "$or": [
                {"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
                {"loc": {"$geoWithin": {"$box": [[20, 20], [30, 30]]}}},
            ]
        },
        doc=[
            {"_id": 1, "loc": [5, 5]},
            {"_id": 2, "loc": [25, 25]},
            {"_id": 3, "loc": [50, 50]},
        ],
        expected=[{"_id": 1, "loc": [5, 5]}, {"_id": 2, "loc": [25, 25]}],
        msg="$polygon and $box via $or should both work",
    ),
    QueryTestCase(
        id="with_center_via_or",
        filter={
            "$or": [
                {"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
                {"loc": {"$geoWithin": {"$center": [[25, 25], 2]}}},
            ]
        },
        doc=[
            {"_id": 1, "loc": [5, 5]},
            {"_id": 2, "loc": [25, 25]},
            {"_id": 3, "loc": [50, 50]},
        ],
        expected=[{"_id": 1, "loc": [5, 5]}, {"_id": 2, "loc": [25, 25]}],
        msg="$polygon and $center via $or should both work",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COMBINED_OPERATOR_TESTS))
def test_polygon_combined_operators(collection, test):
    """Test $polygon combined with other query operators."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)


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
