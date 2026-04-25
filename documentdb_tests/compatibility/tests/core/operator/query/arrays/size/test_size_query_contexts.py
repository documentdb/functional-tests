"""
Tests for $size query contexts.

Covers negation ($not), combination with other array operators ($all, $elemMatch),
logical operators ($and, $or, $nor), query contexts (find, aggregate $match,
find with sort/limit/projection), combination with comparison operators ($exists,
$ne, $type), and $pull context.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

NEGATION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="not_size_2_matches_other_sizes",
        filter={"a": {"$not": {"$size": 2}}},
        doc=[
            {"_id": 1, "a": [1]},
            {"_id": 2, "a": [1, 2]},
            {"_id": 3, "a": [1, 2, 3]},
        ],
        expected=[{"_id": 1, "a": [1]}, {"_id": 3, "a": [1, 2, 3]}],
        msg="$not $size 2 matches arrays of size != 2",
    ),
    QueryTestCase(
        id="not_size_includes_null",
        filter={"a": {"$not": {"$size": 2}}},
        doc=[
            {"_id": 1, "a": [1, 2]},
            {"_id": 2, "a": None},
        ],
        expected=[{"_id": 2, "a": None}],
        msg="$not $size 2 matches docs where field is null",
    ),
    QueryTestCase(
        id="not_size_includes_missing",
        filter={"a": {"$not": {"$size": 2}}},
        doc=[
            {"_id": 1, "a": [1, 2]},
            {"_id": 2, "b": 1},
        ],
        expected=[{"_id": 2, "b": 1}],
        msg="$not $size 2 matches docs where field is missing",
    ),
    QueryTestCase(
        id="not_size_includes_scalar",
        filter={"a": {"$not": {"$size": 2}}},
        doc=[
            {"_id": 1, "a": [1, 2]},
            {"_id": 2, "a": "scalar"},
        ],
        expected=[{"_id": 2, "a": "scalar"}],
        msg="$not $size 2 matches docs where field is scalar",
    ),
    QueryTestCase(
        id="not_size_0_matches_nonempty_and_nonarray",
        filter={"a": {"$not": {"$size": 0}}},
        doc=[
            {"_id": 1, "a": []},
            {"_id": 2, "a": [1]},
            {"_id": 3, "a": "x"},
            {"_id": 4, "b": 1},
        ],
        expected=[
            {"_id": 2, "a": [1]},
            {"_id": 3, "a": "x"},
            {"_id": 4, "b": 1},
        ],
        msg="$not $size 0 matches non-empty arrays and non-array fields",
    ),
]

COMBINATION_ARRAY_OPS_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="size_and_all_exact",
        filter={"a": {"$size": 2, "$all": ["a", "b"]}},
        doc=[
            {"_id": 1, "a": ["a", "b"]},
            {"_id": 2, "a": ["a", "b", "c"]},
            {"_id": 3, "a": ["a"]},
        ],
        expected=[{"_id": 1, "a": ["a", "b"]}],
        msg="$size 2 with $all ['a','b'] matches exact",
    ),
    QueryTestCase(
        id="size_larger_than_all",
        filter={"a": {"$size": 3, "$all": ["a", "b"]}},
        doc=[
            {"_id": 1, "a": ["a", "b", "c"]},
            {"_id": 2, "a": ["a", "b"]},
        ],
        expected=[{"_id": 1, "a": ["a", "b", "c"]}],
        msg="$size 3 with $all ['a','b'] matches size 3 containing both",
    ),
    QueryTestCase(
        id="size_and_elemmatch",
        filter={"a": {"$size": 1, "$elemMatch": {"$gt": 5}}},
        doc=[
            {"_id": 1, "a": [10]},
            {"_id": 2, "a": [3]},
            {"_id": 3, "a": [10, 20]},
        ],
        expected=[{"_id": 1, "a": [10]}],
        msg="$size 1 with $elemMatch {$gt: 5} matches single-element array with condition",
    ),
]

LOGICAL_OPERATOR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="and_size_and_all",
        filter={"$and": [{"a": {"$size": 2}}, {"a": {"$all": ["a"]}}]},
        doc=[
            {"_id": 1, "a": ["a", "b"]},
            {"_id": 2, "a": ["c", "d"]},
            {"_id": 3, "a": ["a"]},
        ],
        expected=[{"_id": 1, "a": ["a", "b"]}],
        msg="$and with $size 2 and $all ['a']",
    ),
    QueryTestCase(
        id="or_size_1_or_2",
        filter={"$or": [{"a": {"$size": 1}}, {"a": {"$size": 2}}]},
        doc=[
            {"_id": 1, "a": [1]},
            {"_id": 2, "a": [1, 2]},
            {"_id": 3, "a": [1, 2, 3]},
        ],
        expected=[{"_id": 1, "a": [1]}, {"_id": 2, "a": [1, 2]}],
        msg="$or with $size 1 or $size 2",
    ),
    QueryTestCase(
        id="nor_size_0",
        filter={"$nor": [{"a": {"$size": 0}}]},
        doc=[
            {"_id": 1, "a": []},
            {"_id": 2, "a": [1]},
            {"_id": 3, "a": "x"},
            {"_id": 4, "b": 1},
        ],
        expected=[
            {"_id": 2, "a": [1]},
            {"_id": 3, "a": "x"},
            {"_id": 4, "b": 1},
        ],
        msg="$nor with $size 0 matches non-empty arrays and non-array fields",
    ),
    QueryTestCase(
        id="multi_field_size",
        filter={"a": {"$size": 2}, "b": {"$size": 1}},
        doc=[
            {"_id": 1, "a": [1, 2], "b": [3]},
            {"_id": 2, "a": [1, 2], "b": [3, 4]},
            {"_id": 3, "a": [1], "b": [3]},
        ],
        expected=[{"_id": 1, "a": [1, 2], "b": [3]}],
        msg="$size on multiple fields matches only when both conditions met",
    ),
    QueryTestCase(
        id="and_contradictory_size",
        filter={"$and": [{"a": {"$size": 1}}, {"a": {"$size": 2}}]},
        doc=[
            {"_id": 1, "a": [1]},
            {"_id": 2, "a": [1, 2]},
        ],
        expected=[],
        msg="$and with contradictory $size values returns no matches",
    ),
]

COMBINATION_COMPARISON_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="size_and_exists",
        filter={"a": {"$size": 2, "$exists": True}},
        doc=[
            {"_id": 1, "a": [1, 2]},
            {"_id": 2, "b": 1},
        ],
        expected=[{"_id": 1, "a": [1, 2]}],
        msg="$size 2 with $exists true",
    ),
    QueryTestCase(
        id="size_and_ne_null",
        filter={"a": {"$size": 2, "$ne": None}},
        doc=[
            {"_id": 1, "a": [1, 2]},
            {"_id": 2, "a": None},
        ],
        expected=[{"_id": 1, "a": [1, 2]}],
        msg="$size 2 with $ne null",
    ),
    QueryTestCase(
        id="size_and_type_array",
        filter={"a": {"$size": 2, "$type": "array"}},
        doc=[
            {"_id": 1, "a": [1, 2]},
            {"_id": 2, "a": "x"},
        ],
        expected=[{"_id": 1, "a": [1, 2]}],
        msg="$size 2 with $type array (redundant but valid)",
    ),
]

SUCCESS_TESTS = (
    NEGATION_TESTS
    + COMBINATION_ARRAY_OPS_TESTS
    + LOGICAL_OPERATOR_TESTS
    + COMBINATION_COMPARISON_TESTS
)


@pytest.mark.parametrize("test", pytest_params(SUCCESS_TESTS))
def test_size_query_contexts(collection, test):
    """Parametrized test for $size query contexts."""
    if test.doc:
        collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)


def test_size_in_aggregate_match(collection):
    """Test $size in aggregate $match stage."""
    collection.insert_many(
        [
            {"_id": 1, "a": [1, 2]},
            {"_id": 2, "a": [1]},
            {"_id": 3, "a": [1, 2, 3]},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$match": {"a": {"$size": 2}}}],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"_id": 1, "a": [1, 2]}])


def test_size_find_with_sort(collection):
    """Test $size in find() with sort."""
    collection.insert_many(
        [
            {"_id": 2, "a": [3, 4]},
            {"_id": 1, "a": [1, 2]},
            {"_id": 3, "a": [5]},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"a": {"$size": 2}},
            "sort": {"_id": 1},
        },
    )
    assertSuccess(result, [{"_id": 1, "a": [1, 2]}, {"_id": 2, "a": [3, 4]}])


def test_size_find_with_limit(collection):
    """Test $size in find() with limit."""
    collection.insert_many(
        [
            {"_id": 1, "a": [1]},
            {"_id": 2, "a": [2]},
            {"_id": 3, "a": [1, 2]},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"a": {"$size": 1}},
            "limit": 1,
        },
    )
    assertSuccess(result, [{"_id": 1, "a": [1]}])


def test_size_find_with_projection(collection):
    """Test $size in find() with projection."""
    collection.insert_many(
        [
            {"_id": 1, "a": [1, 2], "b": "x"},
            {"_id": 2, "a": [1], "b": "y"},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"a": {"$size": 2}},
            "projection": {"a": 1},
        },
    )
    assertSuccess(result, [{"_id": 1, "a": [1, 2]}])


def test_size_in_pull_context(collection):
    """Test $pull with $size condition removes matching array elements."""
    collection.insert_one({"_id": 1, "a": [[1, 2], [3], [4, 5]]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pull": {"a": {"$size": 2}}}}],
        },
    )
    find_result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(find_result, [{"_id": 1, "a": [[3]]}])
