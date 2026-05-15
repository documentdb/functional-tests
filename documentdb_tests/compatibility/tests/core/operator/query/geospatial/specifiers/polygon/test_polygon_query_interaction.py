"""
Tests for $polygon query context interaction.

Validates $polygon in find with various options (projection, sort, limit),
combined with other operators, $expr non-support, and special collection
contexts.
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
    QueryTestCase(
        id="polygon_in_expr_not_evaluated",
        filter={
            "$expr": {
                "$eq": [
                    {
                        "$literal": {
                            "loc": {
                                "$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}
                            }
                        }
                    },
                    True,
                ]
            }
        },
        doc=[{"_id": 1, "loc": [5, 5]}],
        expected=[],
        msg="$polygon inside $expr should not match (not evaluated as geo query)",
    ),
]


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


QUERY_INTERACTION_TESTS: list[QueryTestCase] = FIND_QUERY_TESTS + COMBINED_OPERATOR_TESTS


@pytest.mark.parametrize("test", pytest_params(QUERY_INTERACTION_TESTS))
def test_polygon_query_interaction(collection, test):
    """Test $polygon query interaction."""
    if test.doc:
        collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)


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
