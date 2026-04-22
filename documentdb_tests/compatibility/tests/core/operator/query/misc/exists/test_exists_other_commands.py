"""
Tests for $exists in non-find command contexts.

Covers aggregate $match, aggregate pipeline interaction ($addFields, $project, $unset),
$exists not supported in expressions, count, deleteMany, updateMany,
and $exists after update operations ($unset, $rename, $setOnInsert).
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import (
    PROJECT_UNKNOWN_EXPRESSION_ERROR,
    UNRECOGNIZED_EXPRESSION_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

DOCS = [
    {"_id": 1, "a": 10},
    {"_id": 2, "a": 5},
    {"_id": 3, "b": 1},
]


AGG_MATCH_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="agg_match_true",
        filter={"a": {"$exists": True}},
        doc=DOCS,
        expected=[{"_id": 1, "a": 10}, {"_id": 2, "a": 5}],
        msg="$exists: true in aggregate $match — parity with find",
    ),
    QueryTestCase(
        id="agg_match_false",
        filter={"a": {"$exists": False}},
        doc=DOCS,
        expected=[{"_id": 3, "b": 1}],
        msg="$exists: false in aggregate $match — parity with find",
    ),
]


@pytest.mark.parametrize("test", pytest_params(AGG_MATCH_TESTS))
def test_exists_aggregate_match(collection, test):
    """Parametrized test for $exists in aggregate $match."""
    collection.insert_many(test.doc)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$match": test.filter}], "cursor": {}},
    )
    assertSuccess(result, test.expected, ignore_doc_order=True)


COUNT_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="count_true",
        filter={"a": {"$exists": True}},
        doc=DOCS,
        expected=2,
        msg="count with $exists: true",
    ),
    QueryTestCase(
        id="count_false",
        filter={"a": {"$exists": False}},
        doc=DOCS,
        expected=1,
        msg="count with $exists: false",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COUNT_TESTS))
def test_exists_count(collection, test):
    """Parametrized test for count with $exists."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"count": collection.name, "query": test.filter})
    assertSuccess(result, {"n": test.expected}, raw_res=True, transform=lambda r: {"n": r["n"]})


def test_exists_match_after_addFields(collection):
    """$exists: true in $match after $addFields creates field."""
    collection.insert_many([{"_id": 1, "b": 1}])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$addFields": {"a": 1}},
                {"$match": {"a": {"$exists": True}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"_id": 1, "a": 1, "b": 1}])


def test_exists_match_after_project_removes(collection):
    """$exists: false in $match after $project removes field."""
    collection.insert_many([{"_id": 1, "a": 1, "b": 2}])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {"a": 0}},
                {"$match": {"a": {"$exists": False}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"_id": 1, "b": 2}])


def test_exists_match_after_unset(collection):
    """$exists: false in $match after $unset removes field."""
    collection.insert_many([{"_id": 1, "a": 1, "b": 2}])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$unset": "a"},
                {"$match": {"a": {"$exists": False}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"_id": 1, "b": 2}])


def test_exists_not_in_project_expression(collection):
    """$exists in $project expression errors with code 31325."""
    collection.insert_many([{"_id": 1, "a": 1}])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {"result": {"$exists": "$a"}}},
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, PROJECT_UNKNOWN_EXPRESSION_ERROR)


def test_exists_not_in_addFields_expression(collection):
    """$exists in $addFields expression errors with code 168."""
    collection.insert_many([{"_id": 1, "a": 1}])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$addFields": {"result": {"$exists": "$a"}}},
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, UNRECOGNIZED_EXPRESSION_ERROR)


def test_exists_not_in_match_expr(collection):
    """$exists in $match $expr errors with code 168."""
    collection.insert_many([{"_id": 1, "a": 1}])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$match": {"$expr": {"$exists": "$a"}}},
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, UNRECOGNIZED_EXPRESSION_ERROR)


def test_exists_delete_many(collection):
    """deleteMany with $exists: false removes docs without field."""
    collection.insert_many(DOCS)
    execute_command(
        collection,
        {"delete": collection.name, "deletes": [{"q": {"a": {"$exists": False}}, "limit": 0}]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {}})
    assertSuccess(result, [{"_id": 1, "a": 10}, {"_id": 2, "a": 5}], ignore_doc_order=True)


def test_exists_update_many(collection):
    """updateMany with $exists: false sets default value."""
    collection.insert_many(DOCS)
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"a": {"$exists": False}}, "u": {"$set": {"a": "default"}}, "multi": True},
            ],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 3}})
    assertSuccess(result, [{"_id": 3, "a": "default", "b": 1}])


def test_exists_after_unset_false(collection):
    """$exists: false matches after $unset removes field."""
    collection.insert_many([{"_id": 1, "a": 1, "b": 2}])
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {}, "u": {"$unset": {"a": ""}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"a": {"$exists": False}}}
    )
    assertSuccess(result, [{"_id": 1, "b": 2}])


def test_exists_after_unset_no_longer_true(collection):
    """$exists: true no longer matches after $unset."""
    collection.insert_many([{"_id": 1, "a": 1, "b": 2}])
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {}, "u": {"$unset": {"a": ""}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"a": {"$exists": True}}}
    )
    assertSuccess(result, [])


def test_exists_after_rename_old_name(collection):
    """$exists: false matches old name after $rename."""
    collection.insert_many([{"_id": 1, "a": 1, "b": 2}])
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {}, "u": {"$rename": {"a": "c"}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"a": {"$exists": False}}}
    )
    assertSuccess(result, [{"_id": 1, "b": 2, "c": 1}])


def test_exists_after_rename_new_name(collection):
    """$exists: true matches new name after $rename."""
    collection.insert_many([{"_id": 1, "a": 1, "b": 2}])
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {}, "u": {"$rename": {"a": "c"}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"c": {"$exists": True}}}
    )
    assertSuccess(result, [{"_id": 1, "b": 2, "c": 1}])


def test_exists_after_setOnInsert_upsert(collection):
    """$exists: true matches after $setOnInsert with upsert."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$setOnInsert": {"a": 1}}, "upsert": True},
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"a": {"$exists": True}}}
    )
    assertSuccess(result, [{"_id": 1, "a": 1}])


def test_exists_update_filter_sets_default(collection):
    """updateMany with $exists: false filter sets default value."""
    collection.insert_many([{"_id": 1, "a": 1}, {"_id": 2, "b": 2}])
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"a": {"$exists": False}}, "u": {"$set": {"a": "default"}}, "multi": True},
            ],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 2}})
    assertSuccess(result, [{"_id": 2, "a": "default", "b": 2}])
