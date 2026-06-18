"""
Tests for findAndModify core behavior: update, remove, upsert, new flag,
sort selection, and response structure.
"""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccess, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

NEW_FLAG_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "update-new-false-returns-pre-image",
        docs=[{"_id": 1, "x": 10}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 20}},
            "new": False,
        },
        expected={
            "lastErrorObject": Eq({"n": 1, "updatedExisting": True}),
            "value": Eq({"_id": 1, "x": 10}),
            "ok": Eq(1.0),
        },
        msg="update with new:false returns pre-modification document",
    ),
    CommandTestCase(
        "update-new-true-returns-post-image",
        docs=[{"_id": 1, "x": 10}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 20}},
            "new": True,
        },
        expected={
            "lastErrorObject": Eq({"n": 1, "updatedExisting": True}),
            "value": Eq({"_id": 1, "x": 20}),
            "ok": Eq(1.0),
        },
        msg="update with new:true returns post-modification document",
    ),
    CommandTestCase(
        "new-omitted-defaults-to-pre-image",
        docs=[{"_id": 1, "x": 10}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 20}},
        },
        expected={"value": Eq({"_id": 1, "x": 10})},
        msg="new omitted defaults to returning pre-modification document",
    ),
    CommandTestCase(
        "new-true-noop-update-returns-doc",
        docs=[{"_id": 1, "x": 10}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 10}},
            "new": True,
        },
        expected={
            "lastErrorObject": Eq({"n": 1, "updatedExisting": True}),
            "value": Eq({"_id": 1, "x": 10}),
        },
        msg="new:true on noop update still returns doc with updatedExisting",
    ),
]

REMOVE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "remove-returns-removed-document",
        docs=[{"_id": 1, "x": 10}],
        command={
            "query": {"_id": 1},
            "remove": True,
        },
        expected={
            "lastErrorObject": Eq({"n": 1}),
            "value": Eq({"_id": 1, "x": 10}),
            "ok": Eq(1.0),
        },
        msg="remove returns the removed document",
    ),
    CommandTestCase(
        "remove-no-match-returns-null",
        docs=[{"_id": 1, "x": 10}],
        command={
            "query": {"_id": 999},
            "remove": True,
        },
        expected={
            "lastErrorObject": Eq({"n": 0}),
            "value": Eq(None),
            "ok": Eq(1.0),
        },
        msg="remove with no match returns value:null",
    ),
    CommandTestCase(
        "remove-empty-query-deletes-one",
        docs=[{"_id": 1, "x": 10}, {"_id": 2, "x": 20}],
        command={
            "query": {},
            "remove": True,
        },
        expected={"lastErrorObject": Eq({"n": 1}), "ok": Eq(1.0)},
        msg="remove with empty query deletes one document",
    ),
    CommandTestCase(
        "remove-descending-id-sort",
        docs=[{"_id": 1, "x": 10}, {"_id": 2, "x": 20}, {"_id": 3, "x": 30}],
        command={
            "query": {},
            "remove": True,
            "sort": {"_id": -1},
        },
        expected={"value": Eq({"_id": 3, "x": 30})},
        msg="remove with sort:{_id:-1} removes highest _id",
    ),
    CommandTestCase(
        "remove-ascending-id-sort",
        docs=[{"_id": 1, "x": 10}, {"_id": 2, "x": 20}, {"_id": 3, "x": 30}],
        command={
            "query": {},
            "remove": True,
            "sort": {"_id": 1},
        },
        expected={"value": Eq({"_id": 1, "x": 10})},
        msg="remove with sort:{_id:1} removes lowest _id",
    ),
    CommandTestCase(
        "remove-nested-field-sort",
        docs=[
            {"_id": 1, "a": {"b": 30}},
            {"_id": 2, "a": {"b": 10}},
            {"_id": 3, "a": {"b": 20}},
        ],
        command={
            "query": {},
            "remove": True,
            "sort": {"a.b": -1},
        },
        expected={"value": Eq({"_id": 1, "a": {"b": 30}})},
        msg="remove with sort on nested field path selects correct doc",
    ),
    CommandTestCase(
        "remove-with-query-and-sort",
        docs=[
            {"_id": 1, "x": 5},
            {"_id": 2, "x": 15},
            {"_id": 3, "x": 25},
        ],
        command={
            "query": {"x": {"$gt": 10}},
            "remove": True,
            "sort": {"x": -1},
        },
        expected={"value": Eq({"_id": 3, "x": 25})},
        msg="remove with range query and descending sort selects highest match",
    ),
    CommandTestCase(
        "truthy-numeric-remove",
        docs=[{"_id": 1, "x": 10}],
        command={
            "query": {"_id": 1},
            "remove": 1,
        },
        expected={
            "value": Eq({"_id": 1, "x": 10}),
            "lastErrorObject": Eq({"n": 1}),
        },
        msg="accepts truthy numeric value for remove flag",
    ),
]

UPSERT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "upsert-inserts-new-document",
        docs=[],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 10}},
            "upsert": True,
        },
        expected={
            "lastErrorObject": Eq({"n": 1, "updatedExisting": False, "upserted": 1}),
            "ok": Eq(1.0),
        },
        msg="upsert inserts when no match; lastErrorObject has upserted",
    ),
]

SORT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "sort-ascending-selects-first",
        docs=[{"_id": 1, "x": 30}, {"_id": 2, "x": 10}, {"_id": 3, "x": 20}],
        command={
            "query": {},
            "update": {"$set": {"modified": True}},
            "sort": {"x": 1},
        },
        expected={"value": Eq({"_id": 2, "x": 10})},
        msg="sort:{x:1} selects lowest x value",
    ),
    CommandTestCase(
        "sort-descending-selects-highest",
        docs=[{"_id": 1, "x": 30}, {"_id": 2, "x": 10}, {"_id": 3, "x": 20}],
        command={
            "query": {},
            "update": {"$set": {"modified": True}},
            "sort": {"x": -1},
        },
        expected={"value": Eq({"_id": 1, "x": 30})},
        msg="sort:{x:-1} selects highest x value",
    ),
    CommandTestCase(
        "sort-with-update-returns-pre-image",
        docs=[
            {"_id": 1, "priority": 1, "count": 0},
            {"_id": 2, "priority": 5, "count": 0},
            {"_id": 3, "priority": 3, "count": 0},
        ],
        command={
            "query": {},
            "sort": {"priority": -1},
            "update": {"$inc": {"count": 1}, "$set": {"active": True}},
        },
        expected={"value": Eq({"_id": 2, "priority": 5, "count": 0})},
        msg="sort with multi-operator update returns pre-image by default",
    ),
    CommandTestCase(
        "sort-descending-updates-highest",
        docs=[
            {"_id": 1, "priority": 1},
            {"_id": 2, "priority": 2},
            {"_id": 3, "priority": 3},
        ],
        command={
            "query": {},
            "sort": {"priority": -1},
            "update": {"$set": {"done": True}},
        },
        expected={"value": Eq({"_id": 3, "priority": 3})},
        msg="descending sort updates highest-ranked document",
    ),
    CommandTestCase(
        "compound-sort",
        docs=[
            {"_id": 1, "a": 1, "b": 2},
            {"_id": 2, "a": 1, "b": 1},
            {"_id": 3, "a": 2, "b": 1},
        ],
        command={
            "query": {},
            "sort": {"a": 1, "b": 1},
            "update": {"$set": {"done": True}},
        },
        expected={"value": Eq({"_id": 2, "a": 1, "b": 1})},
        msg="sort with multiple fields (compound sort) selects correctly",
    ),
    CommandTestCase(
        "sort-id-ascending-selects-min",
        docs=[{"_id": 3, "x": 1}, {"_id": 1, "x": 1}, {"_id": 2, "x": 1}],
        command={
            "query": {},
            "sort": {"_id": 1},
            "update": {"$set": {"done": True}},
        },
        expected={"value": Eq({"_id": 1, "x": 1})},
        msg="sort:{_id:1} selects minimum _id",
    ),
    CommandTestCase(
        "sort-id-descending-selects-max",
        docs=[{"_id": 3, "x": 1}, {"_id": 1, "x": 1}, {"_id": 2, "x": 1}],
        command={
            "query": {},
            "sort": {"_id": -1},
            "update": {"$set": {"done": True}},
        },
        expected={"value": Eq({"_id": 3, "x": 1})},
        msg="sort:{_id:-1} selects maximum _id",
    ),
    CommandTestCase(
        "sort-on-field-absent-in-some-docs",
        docs=[
            {"_id": 1, "x": 10},
            {"_id": 2},
            {"_id": 3, "x": 5},
            {"_id": 4},
        ],
        command={
            "query": {},
            "sort": {"x": 1},
            "update": {"$set": {"done": True}},
        },
        expected={"value": Eq({"_id": 2})},
        msg="sort on field absent in some docs: missing field sorts before present values",
    ),
    CommandTestCase(
        "sort-descending-field-absent-selects-highest",
        docs=[
            {"_id": 1, "x": 10},
            {"_id": 2},
            {"_id": 3, "x": 5},
        ],
        command={
            "query": {},
            "sort": {"x": -1},
            "update": {"$set": {"done": True}},
        },
        expected={"value": Eq({"_id": 1, "x": 10})},
        msg="sort descending on field absent in some docs selects highest value",
    ),
    CommandTestCase(
        "sort-mixed-bson-types-ascending",
        docs=[
            {"_id": 1, "x": "hello"},
            {"_id": 2, "x": 10},
            {"_id": 3, "x": None},
            {"_id": 4, "x": True},
        ],
        command={
            "query": {},
            "sort": {"x": 1},
            "update": {"$set": {"done": True}},
        },
        expected={"value": Eq({"_id": 3, "x": None})},
        msg="sort ascending on mixed BSON types follows BSON comparison order",
    ),
]

UPDATE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "update-no-match-returns-null",
        docs=[{"_id": 1, "x": 10}],
        command={
            "query": {"_id": 999},
            "update": {"$set": {"x": 20}},
        },
        expected={
            "lastErrorObject": Eq({"n": 0, "updatedExisting": False}),
            "value": Eq(None),
            "ok": Eq(1.0),
        },
        msg="update with no match returns value:null",
    ),
    CommandTestCase(
        "update-empty-collection-returns-null",
        docs=[],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 1}},
        },
        expected={
            "lastErrorObject": Eq({"n": 0, "updatedExisting": False}),
            "value": Eq(None),
            "ok": Eq(1.0),
        },
        msg="update on empty collection returns null",
    ),
    CommandTestCase(
        "update-operators-inc-push",
        docs=[{"_id": 1, "x": 10, "tags": ["a"]}],
        command={
            "query": {"_id": 1},
            "update": {"$inc": {"x": 5}, "$push": {"tags": "b"}},
            "new": True,
        },
        expected={"value": Eq({"_id": 1, "x": 15, "tags": ["a", "b"]})},
        msg="update operators ($inc/$push) apply correctly",
    ),
]

RESPONSE_STRUCTURE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "response-remove-n-is-1",
        docs=[{"_id": 1, "x": 10}],
        command={
            "query": {"_id": 1},
            "remove": True,
        },
        expected={"lastErrorObject": Eq({"n": 1}), "ok": Eq(1.0)},
        msg="remove response: lastErrorObject.n==1",
    ),
    CommandTestCase(
        "response-no-match-value-null-n-zero",
        docs=[],
        command={
            "query": {"_id": 999},
            "update": {"$set": {"x": 1}},
        },
        expected={
            "lastErrorObject": Eq({"n": 0, "updatedExisting": False}),
            "value": Eq(None),
            "ok": Eq(1.0),
        },
        msg="no-match response: value==null, lastErrorObject.n==0",
    ),
]

ALL_TESTS: list[CommandTestCase] = (
    NEW_FLAG_TESTS
    + REMOVE_TESTS
    + UPSERT_TESTS
    + SORT_TESTS
    + UPDATE_TESTS
    + RESPONSE_STRUCTURE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_findAndModify_core(database_client, collection, test):
    """Test findAndModify core behavior."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    command = {"findAndModify": collection.name, **test.build_command(ctx)}
    result = execute_command(collection, command)
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


def test_findAndModify_remove_actually_deletes_document(collection):
    """Test findAndModify remove deletes the document from the collection."""
    collection.insert_one({"_id": 1, "x": 10})
    execute_command(
        collection,
        {"findAndModify": collection.name, "query": {"_id": 1}, "remove": True},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [])


def test_findAndModify_upsert_new_false_still_inserts(collection):
    """Test findAndModify upsert with new:false still inserts the document."""
    execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": {"$set": {"x": 10}},
            "upsert": True,
            "new": False,
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [{"_id": 1, "x": 10}])


def test_findAndModify_updates_exactly_one_document(collection):
    """Test findAndModify updates only one document when query matches multiple."""
    collection.insert_many([{"_id": i, "status": "active", "x": i} for i in range(1, 6)])
    execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"status": "active"},
            "sort": {"_id": 1},
            "update": {"$set": {"status": "done"}},
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"status": "done"}})
    assertSuccess(result, [{"_id": 1, "status": "done", "x": 1}])


def test_findAndModify_empty_query_no_sort_single_mod(collection):
    """Test findAndModify with empty query and no sort modifies exactly one document."""
    collection.insert_many([{"_id": i, "x": i} for i in range(1, 6)])
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {},
            "update": {"$set": {"done": True}},
        },
    )
    assertSuccessPartial(result, {"lastErrorObject": {"n": 1, "updatedExisting": True}})


def test_findAndModify_remove_nonexistent_collection(database_client, request):
    """Test findAndModify remove on non-existent collection returns null, ok:1."""
    coll = database_client[f"{request.node.name}_nonexistent"]
    result = execute_command(
        coll,
        {
            "findAndModify": coll.name,
            "query": {"_id": 1},
            "remove": True,
        },
    )
    assertSuccess(
        result,
        {"lastErrorObject": {"n": 0}, "value": None, "ok": 1.0},
        raw_res=True,
    )


def test_findAndModify_upsert_creates_collection(database_client, request):
    """Test findAndModify upsert on non-existent collection creates it."""
    coll = database_client[f"{request.node.name}_new"]
    result = execute_command(
        coll,
        {
            "findAndModify": coll.name,
            "query": {"_id": 1},
            "update": {"$set": {"x": 1}},
            "upsert": True,
            "new": True,
        },
    )
    assertResult(
        result,
        expected={"value": Eq({"_id": 1, "x": 1}), "ok": Eq(1.0)},
        raw_res=True,
    )


@pytest.mark.smoke
def test_smoke_findAndModify(collection):
    """Test basic findAndModify command behavior."""
    collection.insert_one({"_id": 1, "name": "Alice", "count": 10})
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": {"$inc": {"count": 5}},
            "new": True,
        },
    )
    assertSuccessPartial(result, {"ok": 1.0, "value": {"_id": 1, "name": "Alice", "count": 15}})
