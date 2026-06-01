"""
Operator and path tests for positional ($) projection operator.

Tests query operator interactions, logical operators, nested path resolution,
cross-array behavior, collation, sort on embedded fields, and index usage.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.projection.utils.projection_test_case import (  # noqa: E501
    ProjectionTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

OPERATOR_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "equality",
        doc=[{"_id": 1, "tags": ["a", "b", "c", "b"]}],
        filter={"tags": "b"},
        projection={"tags.$": 1},
        expected=[{"_id": 1, "tags": ["b"]}],
        msg="Equality match returns first matching element",
    ),
    ProjectionTestCase(
        "gt",
        doc=[{"_id": 1, "scores": [2, 5, 8, 3]}],
        filter={"scores": {"$gt": 4}},
        projection={"scores.$": 1},
        expected=[{"_id": 1, "scores": [5]}],
        msg="$gt returns first element greater than value",
    ),
    ProjectionTestCase(
        "lt",
        doc=[{"_id": 1, "scores": [8, 5, 2, 9]}],
        filter={"scores": {"$lt": 6}},
        projection={"scores.$": 1},
        expected=[{"_id": 1, "scores": [5]}],
        msg="$lt returns first element less than value",
    ),
    ProjectionTestCase(
        "in",
        doc=[{"_id": 1, "vals": [1, 3, 5, 7, 9]}],
        filter={"vals": {"$in": [5, 7]}},
        projection={"vals.$": 1},
        expected=[{"_id": 1, "vals": [5]}],
        msg="$in returns first element in the set",
    ),
    ProjectionTestCase(
        "regex",
        doc=[{"_id": 1, "words": ["apple", "banana", "avocado", "blueberry"]}],
        filter={"words": {"$regex": "^b"}},
        projection={"words.$": 1},
        expected=[{"_id": 1, "words": ["banana"]}],
        msg="Regex returns first matching string",
    ),
    ProjectionTestCase(
        "regex_element_match",
        doc=[{"_id": 1, "arr": ["hello", "world", "wonder"]}],
        filter={"arr": {"$regex": "^w"}},
        projection={"arr.$": 1},
        expected=[{"_id": 1, "arr": ["world"]}],
        msg="Regex matches array element and returns first match",
    ),
    ProjectionTestCase(
        "elemMatch",
        doc=[
            {
                "_id": 1,
                "results": [
                    {"product": "A", "score": 70},
                    {"product": "B", "score": 85},
                    {"product": "C", "score": 90},
                ],
            },
        ],
        filter={"results": {"$elemMatch": {"product": "B", "score": {"$gte": 80}}}},
        projection={"results.$": 1},
        expected=[{"_id": 1, "results": [{"product": "B", "score": 85}]}],
        msg="$elemMatch returns first element matching compound condition",
    ),
    ProjectionTestCase(
        "exists",
        doc=[
            {
                "_id": 1,
                "items": [
                    {"name": "a"},
                    {"name": "b", "qty": 10},
                    {"name": "c", "qty": 20},
                ],
            },
        ],
        filter={"items.qty": {"$exists": True}},
        projection={"items.$": 1},
        expected=[{"_id": 1, "items": [{"name": "b", "qty": 10}]}],
        msg="$exists returns first element with field present",
    ),
    ProjectionTestCase(
        "type",
        doc=[{"_id": 1, "arr": ["hello", 42, "world"]}],
        filter={"arr": {"$type": "int"}},
        projection={"arr.$": 1},
        expected=[{"_id": 1, "arr": [42]}],
        msg="$type returns first element of matching type",
    ),
]


@pytest.mark.parametrize("test", pytest_params(OPERATOR_TESTS))
def test_positional_with_operator(collection, test):
    """Test $ projection with various query operators returns first matching element."""
    collection.insert_many(test.doc)
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": test.filter,
            "projection": test.projection,
        },
    )
    assertSuccess(result, test.expected, msg=test.msg)


NESTED_PATH_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "nested_array",
        doc=[{"_id": 1, "x": {"y": [10, 20, 30]}}],
        filter={"x.y": {"$gte": 20}},
        projection={"x.y.$": 1},
        expected=[{"_id": 1, "x": {"y": [20]}}],
        msg="Nested path returns first matching element",
    ),
    ProjectionTestCase(
        "nonexistent_nested",
        doc=[{"_id": 1, "x": {"other": "val"}}],
        filter={"_id": 1},
        projection={"x.y.$": 1},
        expected=[{"_id": 1, "x": {}}],
        msg="Non-existent nested field returns empty nested object",
    ),
    ProjectionTestCase(
        "no_array_scalar",
        doc=[{"_id": 1, "x": {"y": "scalar"}}],
        filter={"x.y": "scalar"},
        projection={"x.y.$": 1},
        expected=[{"_id": 1, "x": {"y": "scalar"}}],
        msg="Path with no array returns field unchanged",
    ),
    ProjectionTestCase(
        "first_array_on_path",
        doc=[{"_id": 1, "a": [{"b": 1}, {"b": 2}, {"b": 3}]}],
        filter={"a.b": {"$gte": 2}},
        projection={"a.$": 1},
        expected=[{"_id": 1, "a": [{"b": 2}]}],
        msg="Applies to first array encountered on dotted path",
    ),
    ProjectionTestCase(
        "deeply_nested",
        doc=[{"_id": 1, "level1": {"level2": {"items": [100, 200, 300]}}}],
        filter={"level1.level2.items": {"$gt": 150}},
        projection={"level1.level2.items.$": 1},
        expected=[{"_id": 1, "level1": {"level2": {"items": [200]}}}],
        msg="Deeply nested array path works",
    ),
    ProjectionTestCase(
        "nested_array_field_query",
        doc=[
            {
                "_id": 1,
                "items": [
                    {"name": "x", "qty": 5},
                    {"name": "y", "qty": 15},
                    {"name": "z", "qty": 25},
                ],
            },
        ],
        filter={"items.qty": {"$gt": 10}},
        projection={"items.$": 1},
        expected=[{"_id": 1, "items": [{"name": "y", "qty": 15}]}],
        msg="Query on nested array field path returns matching element",
    ),
    ProjectionTestCase(
        "dotted_path_parallel_array",
        doc=[{"_id": 1, "a": {"b": [10, 20, 30], "c": [100, 200, 300]}}],
        filter={"a.c": {"$gte": 200}},
        projection={"a.b.$": 1},
        expected=[{"_id": 1, "a": {"b": [20]}}],
        msg="Nested parallel array uses index from queried sibling",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NESTED_PATH_TESTS))
def test_positional_nested_paths(collection, test):
    """Test $ projection on nested paths."""
    collection.insert_many(test.doc)
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": test.filter,
            "projection": test.projection,
        },
    )
    assertSuccess(result, test.expected, msg=test.msg)


LOGICAL_OPERATOR_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "and_array_and_non_array",
        doc=[
            {"_id": 1, "status": "A", "scores": [70, 85, 90]},
            {"_id": 2, "status": "B", "scores": [60, 88, 95]},
        ],
        filter={"$and": [{"status": "A"}, {"scores": {"$gte": 85}}]},
        projection={"scores.$": 1},
        expected=[{"_id": 1, "scores": [85]}],
        msg="$and combining array and non-array condition works",
    ),
    ProjectionTestCase(
        "and_same_array_uses_first_index",
        doc=[{"_id": 1, "arr": [1, 2, 3, 4, 5]}],
        filter={"$and": [{"arr": {"$gt": 1}}, {"arr": {"$lt": 5}}]},
        projection={"arr.$": 1},
        expected=[{"_id": 1, "arr": [2]}],
        msg="$and on same array uses first array-condition match index",
    ),
    ProjectionTestCase(
        "or_same_array",
        doc=[{"_id": 1, "arr": [1, 2, 3, 4, 5]}],
        # $or succeeds when all branches reference the same array field (can pin index).
        # Errors when branches reference different fields (see or_different_fields in errors).
        filter={"$or": [{"arr": 2}, {"arr": 4}]},
        projection={"arr.$": 1},
        expected=[{"_id": 1, "arr": [2]}],
        msg="$or where both branches match uses first branch index",
    ),
    ProjectionTestCase(
        "or_second_branch_matches",
        doc=[{"_id": 1, "arr": [10, 30, 50]}],
        # First branch (arr: 20) doesn't match, second branch (arr: 30) pins index 1.
        filter={"$or": [{"arr": 20}, {"arr": 30}]},
        projection={"arr.$": 1},
        expected=[{"_id": 1, "arr": [30]}],
        msg="$or falls through to second branch when first doesn't match",
    ),
    ProjectionTestCase(
        "all_returns_last_value_index",
        doc=[{"_id": 1, "arr": [1, 2, 3, 4, 5]}],
        # With $all, the planner pins the index of the LAST $all element matched.
        filter={"arr": {"$all": [3, 5]}},
        projection={"arr.$": 1},
        expected=[{"_id": 1, "arr": [5]}],
        msg="$all returns element at last value's index",
    ),
    ProjectionTestCase(
        # Per the docs, only one array field should appear in the query document;
        # additional array fields may lead to undefined behavior.
        "multiple_array_fields_in_query",
        doc=[{"_id": 1, "a": [1, 2, 3], "b": [4, 5, 6]}],
        filter={"a": 2, "b": 5},
        projection={"a.$": 1},
        expected=[{"_id": 1, "a": [2]}],
        msg="Multiple array fields in query does not error",
    ),
    ProjectionTestCase(
        "query_on_different_array",
        doc=[{"_id": 1, "a": [10, 20, 30], "b": [100, 200, 300]}],
        filter={"b": {"$gte": 200}},
        projection={"a.$": 1},
        expected=[{"_id": 1, "a": [20]}],
        msg="Applies index from queried array to projected array",
    ),
    ProjectionTestCase(
        "elemMatch_on_different_field",
        doc=[
            {
                "_id": 1,
                "tags": [{"k": "a"}, {"k": "b"}],
                "scores": [10, 20, 30],
            },
        ],
        filter={"tags": {"$elemMatch": {"k": "b"}}, "scores": {"$gte": 20}},
        projection={"scores.$": 1},
        expected=[{"_id": 1, "scores": [20]}],
        msg="$elemMatch filter on different field, $ on array with own condition",
    ),
    ProjectionTestCase(
        "matches_elemMatch_projection",
        doc=[
            {
                "_id": 1,
                "items": [
                    {"name": "a", "qty": 5},
                    {"name": "b", "qty": 15},
                    {"name": "c", "qty": 25},
                ],
            },
        ],
        filter={"items.qty": {"$gte": 15}},
        projection={"items.$": 1},
        expected=[{"_id": 1, "items": [{"name": "b", "qty": 15}]}],
        msg="$ projection matches $elemMatch projection for same query",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LOGICAL_OPERATOR_TESTS))
def test_positional_logical_operators(collection, test):
    """Test $ projection with logical operators and multi-array queries."""
    collection.insert_many(test.doc)
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": test.filter,
            "projection": test.projection,
        },
    )
    assertSuccess(result, test.expected, msg=test.msg)


def test_positional_with_collation(collection):
    """Test $ projection with collation for locale-sensitive matching."""
    collection.insert_one({"_id": 1, "arr": ["apple", "Banana", "cherry"]})
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"arr": "banana"},
            "projection": {"arr.$": 1},
            "collation": {"locale": "en", "strength": 2},
        },
    )
    assertSuccess(result, [{"_id": 1, "arr": ["Banana"]}])


def test_positional_with_sort_on_embedded_array_field(collection):
    """Test $ projection with sort on repeating field in embedded doc array.

    Sort orders documents but does not affect which element $ selects —
    $ still returns the first element matching the filter condition.
    """
    collection.insert_one(
        {
            "_id": 1,
            "items": [
                {"name": "b", "qty": 5},
                {"name": "a", "qty": 15},
                {"name": "c", "qty": 25},
            ],
        }
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"items.qty": {"$gte": 10}},
            "projection": {"items.$": 1},
            "sort": {"items.name": 1},
        },
    )
    assertSuccess(result, [{"_id": 1, "items": [{"name": "a", "qty": 15}]}])


def test_positional_with_index(collection):
    """Test $ projection works correctly when array field has an index."""
    collection.insert_one({"_id": 1, "arr": [10, 20, 30]})
    collection.create_index("arr")
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"arr": {"$gte": 20}},
            "projection": {"arr.$": 1},
        },
    )
    assertSuccess(result, [{"_id": 1, "arr": [20]}])
