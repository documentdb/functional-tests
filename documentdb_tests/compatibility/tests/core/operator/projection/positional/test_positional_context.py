"""
Context and interaction tests for positional ($) projection operator.

Tests $ projection with find options, sort, inclusion/exclusion behavior,
multiple arrays, $slice interaction, and batching.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.projection.utils.projection_test_case import (  # noqa: E501
    ProjectionTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

INCLUSION_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "treated_as_inclusion",
        doc=[{"_id": 1, "arr": [10, 20, 30], "other": "value"}],
        filter={"arr": {"$gte": 20}},
        projection={"arr.$": 1},
        expected=[{"_id": 1, "arr": [20]}],
        msg="Other fields excluded unless explicitly included",
    ),
    ProjectionTestCase(
        "with_id_exclusion",
        doc=[{"_id": 1, "arr": [10, 20, 30]}],
        filter={"arr": {"$gte": 20}},
        projection={"arr.$": 1, "_id": 0},
        expected=[{"arr": [20]}],
        msg="_id: 0 exclusion is valid with $",
    ),
    ProjectionTestCase(
        "with_other_inclusions",
        doc=[{"_id": 1, "arr": [10, 20, 30], "name": "test", "extra": "x"}],
        filter={"arr": {"$gte": 20}},
        projection={"arr.$": 1, "name": 1},
        expected=[{"_id": 1, "arr": [20], "name": "test"}],
        msg="Other field inclusions returned alongside matching element",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INCLUSION_TESTS))
def test_positional_inclusion_exclusion(collection, test):
    """Test $ projection inclusion/exclusion behavior."""
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


SORT_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "non_array_sort",
        doc=[
            {"_id": 1, "name": "B", "scores": [70, 85, 90]},
            {"_id": 2, "name": "A", "scores": [60, 88, 95]},
        ],
        filter={"scores": {"$gte": 85}},
        projection={"scores.$": 1},
        expected=[{"_id": 2, "scores": [88]}, {"_id": 1, "scores": [85]}],
        msg="Sort on non-array field orders docs, projection picks first match",
    ),
    ProjectionTestCase(
        "same_array_sort",
        doc=[{"_id": 1, "grades": [90, 85, 70]}, {"_id": 2, "grades": [60, 88, 95]}],
        filter={"grades": {"$gte": 85}},
        projection={"grades.$": 1},
        expected=[{"_id": 2, "grades": [88]}, {"_id": 1, "grades": [90]}],
        msg="Sort on same array field orders docs, projection picks first match",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SORT_TESTS))
def test_positional_with_sort(collection, test):
    """Test $ projection with sort — sort orders documents, projection picks first match."""
    collection.insert_many(test.doc)
    sort = {"name": 1} if test.id == "non_array_sort" else {"grades": 1}
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": test.filter,
            "projection": test.projection,
            "sort": sort,
        },
    )
    assertSuccess(result, test.expected, msg=test.msg)


SLICE_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "positive_slice",
        doc=[{"_id": 1, "a": [1, 2, 3, 4], "b": [10, 20, 30, 40]}],
        filter={"a": {"$gte": 3}},
        projection={"a.$": 1, "b": {"$slice": 2}},
        expected=[{"_id": 1, "a": [3], "b": [10, 20]}],
        msg="$slice positive on different field works with $",
    ),
    ProjectionTestCase(
        "negative_slice",
        doc=[{"_id": 1, "a": [1, 2, 3, 4], "b": [10, 20, 30, 40]}],
        filter={"a": {"$gte": 3}},
        projection={"a.$": 1, "b": {"$slice": -2}},
        expected=[{"_id": 1, "a": [3], "b": [30, 40]}],
        msg="$slice negative on different field works with $",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SLICE_TESTS))
def test_positional_with_slice_on_different_field(collection, test):
    """Test $slice on one array field with $ positional on different array field."""
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


def test_positional_with_limit(collection):
    """Test $ projection with limit applies to documents not array."""
    collection.insert_many([{"_id": 1, "arr": [10, 20, 30]}, {"_id": 2, "arr": [15, 25, 35]}])
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"arr": {"$gte": 20}},
            "projection": {"arr.$": 1},
            "limit": 1,
        },
    )
    assertSuccess(result, [{"_id": 1, "arr": [20]}])


def test_positional_with_skip(collection):
    """Test $ projection with skip applies to documents not array."""
    collection.insert_many([{"_id": 1, "arr": [10, 20, 30]}, {"_id": 2, "arr": [15, 25, 35]}])
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"arr": {"$gte": 20}},
            "projection": {"arr.$": 1},
            "skip": 1,
        },
    )
    assertSuccess(result, [{"_id": 2, "arr": [25]}])


def test_positional_sort_does_not_affect_array_element_selection(collection):
    """Test $ projection picks from original array order regardless of sort direction."""
    collection.insert_one({"_id": 1, "arr": [5, 15, 25, 35]})
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"arr": {"$gt": 10}},
            "projection": {"arr.$": 1},
            "sort": {"_id": -1},
        },
    )
    assertSuccess(result, [{"_id": 1, "arr": [15]}])


def test_positional_consistent_across_batches(collection):
    """Test $ projection returns correct element with batchSize forcing getMore."""
    collection.insert_many(
        [
            {"_id": 1, "arr": [10, 20, 30]},
            {"_id": 2, "arr": [15, 25, 35]},
            {"_id": 3, "arr": [5, 40, 50]},
        ]
    )
    # batchSize: 1 forces getMore for remaining docs
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"arr": {"$gte": 20}},
            "projection": {"arr.$": 1},
            "batchSize": 1,
        },
    )
    first_batch = result["cursor"]["firstBatch"]
    cursor_id = result["cursor"]["id"]

    more = execute_command(
        collection,
        {
            "getMore": cursor_id,
            "collection": collection.name,
            "batchSize": 10,
        },
    )
    next_batch = more["cursor"]["nextBatch"]

    all_docs = sorted(first_batch + next_batch, key=lambda d: d["_id"])
    assertSuccess(
        {"cursor": {"firstBatch": all_docs}, "ok": 1},
        [
            {"_id": 1, "arr": [20]},
            {"_id": 2, "arr": [25]},
            {"_id": 3, "arr": [40]},
        ],
    )
