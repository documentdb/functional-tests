"""
Tests for findAndModify update modes: operator updates, replacements, pipelines,
arrayFilters, boundary inputs, and input interactions.
"""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

UPDATE_MODE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "all-dollar-keys-is-update-operator",
        docs=[{"_id": 1, "x": 10, "y": 5}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 20}, "$inc": {"y": 1}},
            "new": True,
        },
        expected={"value": Eq({"_id": 1, "x": 20, "y": 6})},
        msg="update with all dollar-prefixed keys treated as update-operator form",
    ),
    CommandTestCase(
        "no-dollar-keys-is-replacement",
        docs=[{"_id": 1, "x": 10, "y": 20}],
        command={
            "query": {"_id": 1},
            "update": {"z": 30},
            "new": True,
        },
        expected={"value": Eq({"_id": 1, "z": 30})},
        msg="update with no dollar-prefixed keys treated as replacement",
    ),
    CommandTestCase(
        "pipeline-references-existing-fields",
        docs=[{"_id": 1, "a": 3, "b": 7}],
        command={
            "query": {"_id": 1},
            "update": [{"$set": {"total": {"$add": ["$a", "$b"]}}}],
            "new": True,
        },
        expected={"value": Eq({"_id": 1, "a": 3, "b": 7, "total": 10})},
        msg="pipeline update can reference existing field values",
    ),
]

BOUNDARY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "empty-set-is-noop",
        docs=[{"_id": 1, "x": 10}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {}},
            "new": True,
        },
        expected={
            "value": Eq({"_id": 1, "x": 10}),
            "lastErrorObject": Eq({"n": 1, "updatedExisting": True}),
        },
        msg="update {$set:{}} succeeds with no field change",
    ),
    CommandTestCase(
        "empty-replacement",
        docs=[{"_id": 1, "x": 10, "y": 20}],
        command={
            "query": {"_id": 1},
            "update": {},
            "new": True,
        },
        expected={
            "lastErrorObject": Eq({"n": 1, "updatedExisting": True}),
            "value": Eq({"_id": 1}),
            "ok": Eq(1.0),
        },
        msg="replacement with empty document {} leaves only _id",
    ),
    CommandTestCase(
        "unset-removes-field",
        docs=[{"_id": 1, "x": 10, "y": 20}],
        command={
            "query": {"_id": 1},
            "update": {"$unset": {"y": ""}},
            "new": True,
        },
        expected={
            "lastErrorObject": Eq({"n": 1, "updatedExisting": True}),
            "value": Eq({"_id": 1, "x": 10}),
            "ok": Eq(1.0),
        },
        msg="$unset removes field and new:true doc omits it",
    ),
    CommandTestCase(
        "deeply-nested-set-creates-intermediates",
        docs=[{"_id": 1}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"a.b.c.d.e": 1}},
            "new": True,
        },
        expected={"value": Eq({"_id": 1, "a": {"b": {"c": {"d": {"e": 1}}}}})},
        msg="$set with deeply nested path creates intermediate documents",
    ),
]

DOTTED_PATH_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "set-dotted-index-on-array",
        docs=[{"_id": 1, "a": [10, 20, 30]}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"a.0": 99}},
            "new": True,
        },
        expected={"value": Eq({"_id": 1, "a": [99, 20, 30]})},
        msg="$set with dotted numeric index on array updates the element at that index",
    ),
    CommandTestCase(
        "set-dotted-index-on-object",
        docs=[{"_id": 1, "a": {"0": "old", "1": "keep"}}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"a.0": "new"}},
            "new": True,
        },
        expected={"value": Eq({"_id": 1, "a": {"0": "new", "1": "keep"}})},
        msg="$set with dotted numeric key on object updates the field named '0'",
    ),
]

INTERACTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "upsert-with-sort-no-match-still-inserts",
        docs=[],
        command={
            "query": {"_id": 1},
            "sort": {"x": -1},
            "update": {"$set": {"x": 10}},
            "upsert": True,
            "new": True,
        },
        expected={"value": Eq({"_id": 1, "x": 10})},
        msg="upsert:true + sort: when no match, insert still occurs",
    ),
    CommandTestCase(
        "projection-on-removed-field-new-true",
        docs=[{"_id": 1, "x": 10, "y": 20}],
        command={
            "query": {"_id": 1},
            "update": {"$unset": {"x": ""}},
            "fields": {"x": 1},
            "new": True,
        },
        expected={"value": Eq({"_id": 1})},
        msg="fields projection on a field removed by update (new:true) -- absent",
    ),
    CommandTestCase(
        "atomic-pre-image-consistent",
        docs=[{"_id": 1, "x": 10, "y": 20}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 99, "y": 99}},
        },
        expected={"value": Eq({"_id": 1, "x": 10, "y": 20})},
        msg="findAndModify pre-image is self-consistent",
    ),
]

ALL_TESTS: list[CommandTestCase] = (
    UPDATE_MODE_TESTS + BOUNDARY_TESTS + DOTTED_PATH_TESTS + INTERACTION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_findAndModify_update_modes(database_client, collection, test):
    """Test findAndModify update modes."""
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


def test_findAndModify_array_filters_updates_matching_elements(collection):
    """Test arrayFilters restricts update to matching array elements."""
    collection.insert_one({"_id": 1, "grades": [85, 92, 78, 95]})
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": {"$set": {"grades.$[elem]": 100}},
            "arrayFilters": [{"elem": {"$gte": 90}}],
            "new": True,
        },
    )
    assertSuccessPartial(result, {"value": {"_id": 1, "grades": [85, 100, 78, 100]}})


def test_findAndModify_array_filters_multiple_identifiers(collection):
    """Test arrayFilters with multiple identifiers in same update."""
    collection.insert_one({"_id": 1, "scores": [5, 15, 25, 35]})
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": {
                "$set": {"scores.$[low]": 0, "scores.$[high]": 100},
            },
            "arrayFilters": [{"low": {"$lt": 10}}, {"high": {"$gt": 30}}],
            "new": True,
        },
    )
    assertSuccessPartial(result, {"value": {"_id": 1, "scores": [0, 15, 25, 100]}})


def test_findAndModify_positional_operator(collection):
    """Test positional $ operator updates first matching array element."""
    collection.insert_one({"_id": 1, "items": [10, 20, 30]})
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1, "items": 20},
            "update": {"$set": {"items.$": 99}},
            "new": True,
        },
    )
    assertSuccessPartial(result, {"value": {"_id": 1, "items": [10, 99, 30]}})


def test_findAndModify_pipeline_multiple_stages(collection):
    """Test pipeline update with multiple stages."""
    collection.insert_one({"_id": 1, "x": 10, "y": 20, "tmp": "remove_me"})
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": [
                {"$set": {"sum": {"$add": ["$x", "$y"]}}},
                {"$unset": "tmp"},
            ],
            "new": True,
        },
    )
    assertSuccessPartial(result, {"value": {"_id": 1, "x": 10, "y": 20, "sum": 30}})


def test_findAndModify_pull(collection):
    """Test $pull with findAndModify removes matching elements and returns updated doc."""
    collection.insert_one({"_id": 1, "arr": [1, 2, 3, 2]})
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": {"$pull": {"arr": 2}},
            "new": True,
        },
    )
    assertSuccessPartial(result, {"value": {"_id": 1, "arr": [1, 3]}})


def test_findAndModify_addToSet(collection):
    """Test $addToSet with findAndModify adds element and returns updated doc."""
    collection.insert_one({"_id": 1, "arr": ["a"]})
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": {"$addToSet": {"arr": "b"}},
            "new": True,
        },
    )
    assertSuccessPartial(result, {"value": {"_id": 1, "arr": ["a", "b"]}})
