"""
Tests for $box interaction with other query operators.

Validates $box combined with $and, $or, projection, skip, sort,
nested fields, and array fields.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

QUERY_INTERACTION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="combined_with_field_equality",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}, "type": "a"},
        doc=[
            {"_id": 1, "loc": [5, 5], "type": "a"},
            {"_id": 2, "loc": [5, 5], "type": "b"},
            {"_id": 3, "loc": [15, 15], "type": "a"},
        ],
        expected=[{"_id": 1, "loc": [5, 5], "type": "a"}],
        msg="$box combined with field equality should filter both",
    ),
    QueryTestCase(
        id="combined_with_or",
        filter={
            "$or": [
                {"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}},
                {"type": "a"},
            ]
        },
        doc=[
            {"_id": 1, "loc": [5, 5], "type": "a"},
            {"_id": 2, "loc": [5, 5], "type": "b"},
            {"_id": 3, "loc": [15, 15], "type": "a"},
        ],
        expected=[
            {"_id": 1, "loc": [5, 5], "type": "a"},
            {"_id": 2, "loc": [5, 5], "type": "b"},
            {"_id": 3, "loc": [15, 15], "type": "a"},
        ],
        msg="$box combined with $or should union results",
    ),
    QueryTestCase(
        id="on_nested_field",
        filter={"address.loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}},
        doc=[
            {"_id": 1, "address": {"loc": [5, 5]}},
            {"_id": 2, "address": {"loc": [15, 15]}},
        ],
        expected=[{"_id": 1, "address": {"loc": [5, 5]}}],
        msg="$box should work on nested field path",
    ),
    QueryTestCase(
        id="on_array_of_points",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}},
        doc=[
            {"_id": 1, "loc": [[5, 5], [15, 15]]},
            {"_id": 2, "loc": [[20, 20], [25, 25]]},
        ],
        expected=[{"_id": 1, "loc": [[5, 5], [15, 15]]}],
        msg="$box on array of points should match if ANY point is within",
    ),
    QueryTestCase(
        id="on_array_of_points_one_on_boundary",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}},
        doc=[
            {"_id": 1, "loc": [[10, 10], [15, 15]]},
            {"_id": 2, "loc": [[11, 11], [20, 20]]},
        ],
        expected=[{"_id": 1, "loc": [[10, 10], [15, 15]]}],
        msg="$box on array of points should match if one point is on boundary",
    ),
    QueryTestCase(
        id="two_geowithin_same_field",
        filter={
            "$and": [
                {"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}},
                {"loc": {"$geoWithin": {"$box": [[5, 5], [15, 15]]}}},
            ]
        },
        doc=[
            {"_id": 1, "loc": [7, 7]},
            {"_id": 2, "loc": [3, 3]},
            {"_id": 3, "loc": [12, 12]},
        ],
        expected=[{"_id": 1, "loc": [7, 7]}],
        msg="Two $geoWithin $box on same field via $and should intersect results",
    ),
]


@pytest.mark.parametrize("test", pytest_params(QUERY_INTERACTION_TESTS))
def test_box_query_interaction(collection, test):
    """Test $box combined with other query operators."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertResult(result, expected=test.expected, ignore_doc_order=True, msg=test.msg)


def test_box_with_projection(collection):
    """Test $box with projection returns only specified fields."""
    collection.insert_many(
        [
            {"_id": 1, "loc": [5, 5], "type": "a"},
            {"_id": 2, "loc": [5, 5], "type": "b"},
            {"_id": 3, "loc": [15, 15], "type": "a"},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}},
            "projection": {"_id": 1, "type": 1},
        },
    )
    assertResult(
        result,
        expected=[{"_id": 1, "type": "a"}, {"_id": 2, "type": "b"}],
        ignore_doc_order=True,
        msg="$box with projection should return only projected fields",
    )


def test_box_with_skip(collection):
    """Test $box with skip skips the first N results."""
    collection.insert_many(
        [
            {"_id": 1, "loc": [5, 5]},
            {"_id": 2, "loc": [6, 6]},
            {"_id": 3, "loc": [15, 15]},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}},
            "sort": {"_id": 1},
            "skip": 1,
        },
    )
    assertResult(
        result,
        expected=[{"_id": 2, "loc": [6, 6]}],
        msg="$box with skip should skip first result",
    )


def test_box_with_sort(collection):
    """Test $box with sort on a non-geo field."""
    collection.insert_many(
        [
            {"_id": 1, "loc": [5, 5], "val": 10},
            {"_id": 2, "loc": [6, 6], "val": 20},
            {"_id": 3, "loc": [15, 15], "val": 30},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}},
            "sort": {"val": -1},
        },
    )
    assertResult(
        result,
        expected=[
            {"_id": 2, "loc": [6, 6], "val": 20},
            {"_id": 1, "loc": [5, 5], "val": 10},
        ],
        msg="$box with sort should order by specified field",
    )


def test_box_with_limit(collection):
    """Test $box query with limit returns limited number of results."""
    collection.insert_many([{"_id": i, "loc": [i, i]} for i in range(20)])
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$box": [[0, 0], [19, 19]]}}},
            "limit": 5,
            "sort": {"_id": 1},
        },
    )
    assertResult(
        result,
        expected=[{"_id": i, "loc": [i, i]} for i in range(5)],
        msg="$box with limit should return exactly 5 documents",
    )
