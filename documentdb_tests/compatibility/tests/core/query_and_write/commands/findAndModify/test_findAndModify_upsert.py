"""
Tests for findAndModify upsert behavior: lastErrorObject, $setOnInsert,
id consistency, auto-increment patterns.
"""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import IMMUTABLE_FIELD_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists, IsType, NotExists

EQUALITY_SEEDING_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "equality-query-seeds-field",
        docs=[],
        command={
            "query": {"x": 10},
            "update": {"$set": {"y": 20}},
            "upsert": True,
            "new": True,
        },
        expected={"value": {"_id": Exists(), "x": Eq(10), "y": Eq(20)}},
        msg="upsert with equality predicate seeds field value into inserted doc",
    ),
    CommandTestCase(
        "non-equality-does-not-seed",
        docs=[],
        command={
            "query": {"x": {"$gt": 5}},
            "update": {"$set": {"y": 20}},
            "upsert": True,
            "new": True,
        },
        expected={"value": {"_id": Exists(), "x": NotExists(), "y": Eq(20)}},
        msg="upsert with non-equality operator ($gt) does NOT seed field",
    ),
    CommandTestCase(
        "no-id-auto-creates-id",
        docs=[],
        command={
            "query": {"x": 10},
            "update": {"$set": {"x": 10, "y": 20}},
            "upsert": True,
            "new": True,
        },
        expected={"value": {"_id": IsType("objectId"), "x": Eq(10), "y": Eq(20)}},
        msg="upsert with no _id in query/update auto-creates an ObjectId _id",
    ),
]

REPLACEMENT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "replacement-inserts-replacement",
        docs=[],
        command={
            "query": {"_id": 1},
            "update": {"_id": 1, "z": 99},
            "upsert": True,
            "new": True,
        },
        expected={"value": Eq({"_id": 1, "z": 99})},
        msg="upsert with replacement update inserts the replacement document",
    ),
]

LAST_ERROR_OBJECT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "lastErrorObject-upserted-id",
        docs=[],
        command={
            "query": {"_id": 42},
            "update": {"$set": {"x": 1}},
            "upsert": True,
        },
        expected={
            "lastErrorObject": Eq({"n": 1, "updatedExisting": False, "upserted": 42}),
        },
        msg="lastErrorObject.upserted is the _id of the new document",
    ),
    CommandTestCase(
        "new-false-returns-null-value-key",
        docs=[],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 10}},
            "upsert": True,
            "new": False,
        },
        expected={
            "value": Eq(None),
            "lastErrorObject": Eq({"n": 1, "updatedExisting": False, "upserted": 1}),
        },
        msg="upsert insert with new=false returns value key set to null",
    ),
    CommandTestCase(
        "upsert-false-nonexistent-returns-null",
        docs=[],
        command={
            "query": {"_id": 999},
            "update": {"$set": {"x": 10}},
            "upsert": False,
        },
        expected={
            "lastErrorObject": Eq({"n": 0, "updatedExisting": False}),
            "value": Eq(None),
            "ok": Eq(1.0),
        },
        msg="upsert=false on non-existent document returns null and inserts nothing",
    ),
]

SET_ON_INSERT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "setOnInsert-sets-id-on-upsert",
        docs=[],
        command={
            "query": {"_id": 1},
            "update": {"$setOnInsert": {"x": 10}},
            "upsert": True,
            "new": True,
        },
        expected={"value": Eq({"_id": 1, "x": 10})},
        msg="upsert with $setOnInsert inserts new document using _id from query",
    ),
    CommandTestCase(
        "setOnInsert-noop-when-match-exists",
        docs=[{"_id": 1, "x": 10}],
        command={
            "query": {"_id": 1},
            "update": {"$setOnInsert": {"x": 99}},
            "upsert": True,
            "new": True,
        },
        expected={"value": Eq({"_id": 1, "x": 10})},
        msg="$setOnInsert is a no-op when matching doc already exists",
    ),
    CommandTestCase(
        "setOnInsert-document-id-match-succeeds",
        docs=[],
        command={
            "query": {"_id": {"a": 1, "b": 2}},
            "update": {"$setOnInsert": {"_id": {"a": 1, "b": 2}, "x": 10}},
            "upsert": True,
            "new": True,
        },
        expected={"value": Eq({"_id": {"a": 1, "b": 2}, "x": 10})},
        msg="upsert succeeds when selector and $setOnInsert specify identical document ids",
    ),
    CommandTestCase(
        "setOnInsert-dotted-id-match-succeeds",
        docs=[],
        command={
            "query": {"_id.a": 1},
            "update": {"$setOnInsert": {"x": 10}},
            "upsert": True,
            "new": True,
        },
        expected={"value": Eq({"_id": {"a": 1}, "x": 10})},
        msg="upsert with dotted _id query constructs _id from dotted notation",
    ),
    CommandTestCase(
        "setOnInsert-selector-has-id-setOnInsert-omits",
        docs=[],
        command={
            "query": {"_id": 1},
            "update": {"$setOnInsert": {"x": 10}},
            "upsert": True,
            "new": True,
        },
        expected={"value": Eq({"_id": 1, "x": 10})},
        msg="upsert succeeds when selector specifies _id and $setOnInsert omits it",
    ),
    CommandTestCase(
        "setOnInsert-omits-id-sets-unique",
        docs=[],
        command={
            "query": {"x": 999},
            "update": {"$setOnInsert": {"_id": 42, "y": 1}},
            "upsert": True,
            "new": True,
        },
        expected={"value": Eq({"_id": 42, "x": 999, "y": 1})},
        msg="upsert succeeds when selector omits _id and $setOnInsert sets a unique _id",
    ),
    CommandTestCase(
        "setOnInsert-range-filter-no-match-inserts",
        docs=[],
        command={
            "query": {"_id": {"$gt": 100}},
            "update": {"$setOnInsert": {"x": 10}},
            "upsert": True,
            "new": True,
        },
        expected={"value": {"_id": IsType("objectId"), "x": Eq(10)}},
        msg="upsert with range filter on _id matching no docs inserts using $setOnInsert",
    ),
    CommandTestCase(
        "setOnInsert-range-filter-match-updates",
        docs=[{"_id": 200, "x": 5}],
        command={
            "query": {"_id": {"$gt": 100}},
            "update": {"$setOnInsert": {"x": 99}},
            "upsert": True,
            "new": True,
        },
        expected={"value": Eq({"_id": 200, "x": 5})},
        msg="upsert with range filter matching existing doc is noop for $setOnInsert",
    ),
    CommandTestCase(
        "setOnInsert-subset-id-subfields-consistent",
        docs=[],
        command={
            "query": {"_id": {"a": 1, "b": 2}},
            "update": {"$setOnInsert": {"_id": {"a": 1, "b": 2}, "x": 10}},
            "upsert": True,
            "new": True,
        },
        expected={"value": Eq({"_id": {"a": 1, "b": 2}, "x": 10})},
        msg="upsert with $setOnInsert _id sub-fields consistent with selector succeeds",
    ),
    CommandTestCase(
        "setOnInsert-id-subfields-different-order",
        docs=[],
        command={
            "query": {"_id": {"a": 1, "b": 2}},
            "update": {"$setOnInsert": {"_id": {"b": 2, "a": 1}, "x": 10}},
            "upsert": True,
        },
        error_code=IMMUTABLE_FIELD_ERROR,
        msg="upsert with $setOnInsert _id sub-fields in different order fails",
    ),
]

AUTO_INCREMENT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "auto-increment-pattern",
        docs=[],
        command={
            "query": {"_id": "counter"},
            "update": {"$inc": {"val": 1}},
            "upsert": True,
            "new": True,
        },
        expected={"value": Eq({"_id": "counter", "val": 1})},
        msg="upsert with $inc builds auto-incrementing counter",
    ),
]

UPSERT_PROJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "upsert-new-true-id-exclusion-projection",
        docs=[],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 10, "y": 20}},
            "upsert": True,
            "new": True,
            "fields": {"_id": 0, "x": 1},
        },
        expected={"value": Eq({"x": 10})},
        msg="upsert + new:true + id-exclusion projection returns doc without _id",
    ),
    CommandTestCase(
        "upsert-new-false-excludes-all-returns-null-value",
        docs=[],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 10}},
            "upsert": True,
            "new": False,
            "fields": {"x": 1},
        },
        expected={
            "value": Eq(None),
            "lastErrorObject": Eq({"n": 1, "updatedExisting": False, "upserted": 1}),
        },
        msg="upsert + new:false returns null even with projection (no pre-image)",
    ),
    CommandTestCase(
        "upsert-replacement-new-true-projection",
        docs=[],
        command={
            "query": {"_id": 1},
            "update": {"_id": 1, "a": 1, "b": 2},
            "upsert": True,
            "new": True,
            "fields": {"a": 1},
        },
        expected={"value": Eq({"_id": 1, "a": 1})},
        msg="upsert + replacement + new:true + projection returns projected post-image",
    ),
    CommandTestCase(
        "upsert-replacement-new-false",
        docs=[],
        command={
            "query": {"_id": 1},
            "update": {"_id": 1, "a": 1, "b": 2},
            "upsert": True,
            "new": False,
        },
        expected={
            "value": Eq(None),
            "lastErrorObject": Eq({"n": 1, "updatedExisting": False, "upserted": 1}),
        },
        msg="upsert + replacement + new:false returns null (pre-image of insert is nothing)",
    ),
]

ALL_TESTS: list[CommandTestCase] = (
    EQUALITY_SEEDING_TESTS
    + REPLACEMENT_TESTS
    + LAST_ERROR_OBJECT_TESTS
    + SET_ON_INSERT_TESTS
    + AUTO_INCREMENT_TESTS
    + UPSERT_PROJECTION_TESTS
    + [
        CommandTestCase(
            "upsert-updates-existing-doc",
            docs=[{"_id": 1, "x": 10, "y": 5}],
            command={
                "query": {"_id": 1},
                "update": {"$set": {"x": 99}},
                "upsert": True,
                "new": True,
            },
            expected={
                "value": Eq({"_id": 1, "x": 99, "y": 5}),
                "lastErrorObject": Eq({"n": 1, "updatedExisting": True}),
            },
            msg="upsert with existing match updates doc instead of inserting",
        ),
        CommandTestCase(
            "setOnInsert-combined-with-set",
            docs=[],
            command={
                "query": {"_id": 1},
                "update": {"$set": {"x": 10}, "$setOnInsert": {"y": 99}},
                "upsert": True,
                "new": True,
            },
            expected={"value": Eq({"_id": 1, "x": 10, "y": 99})},
            msg="upsert with $set + $setOnInsert applies both on insert",
        ),
    ]
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_findAndModify_upsert(database_client, collection, test):
    """Test findAndModify upsert behavior."""
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
