"""Tests for findAndModify argument handling — success cases for valid parameter variants."""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
    IndexModel,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

ALL_TESTS = [
    CommandTestCase(
        "hint-string-existing-index",
        docs=[{"_id": 1, "x": 10}],
        indexes=[IndexModel("x", name="x_1")],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 20}},
            "hint": "x_1",
            "new": True,
        },
        expected={"value": Eq({"_id": 1, "x": 20})},
        msg="findAndModify with hint as index-name string succeeds",
    ),
    CommandTestCase(
        "hint-spec-document",
        docs=[{"_id": 1, "x": 10}],
        indexes=[IndexModel("x")],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 20}},
            "hint": {"x": 1},
            "new": True,
        },
        expected={"value": Eq({"_id": 1, "x": 20})},
        msg="findAndModify with hint as index-specification document succeeds",
    ),
    CommandTestCase(
        "empty-query-selects-document",
        docs=[{"_id": 1, "x": 10}],
        command={
            "query": {},
            "update": {"$set": {"x": 20}},
        },
        expected={"value": Eq({"_id": 1, "x": 10})},
        msg="findAndModify with empty query {} selects a document",
    ),
    CommandTestCase(
        "write-concern-w1",
        docs=[{"_id": 1, "x": 10}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 20}},
            "writeConcern": {"w": 1},
            "new": True,
        },
        expected={"value": Eq({"_id": 1, "x": 20})},
        msg="findAndModify with writeConcern w:1 succeeds",
    ),
    CommandTestCase(
        "comment-string",
        docs=[{"_id": 1, "x": 10}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 20}},
            "comment": "test comment",
        },
        expected={
            "lastErrorObject": Eq({"n": 1, "updatedExisting": True}),
            "value": Eq({"_id": 1, "x": 10}),
        },
        msg="findAndModify with comment as string succeeds",
    ),
    CommandTestCase(
        "maxTimeMS-zero",
        docs=[{"_id": 1, "x": 10}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 20}},
            "maxTimeMS": 0,
        },
        expected={
            "lastErrorObject": Eq({"n": 1, "updatedExisting": True}),
            "value": Eq({"_id": 1, "x": 10}),
        },
        msg="findAndModify with maxTimeMS:0 succeeds (unbounded)",
    ),
    CommandTestCase(
        "sort-empty-document",
        docs=[{"_id": 1, "x": 10}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 20}},
            "sort": {},
        },
        expected={"value": Eq({"_id": 1, "x": 10})},
        msg="findAndModify with sort:{} is accepted (no sort applied)",
    ),
    CommandTestCase(
        "fields-empty-document-returns-full-doc",
        docs=[{"_id": 1, "x": 10, "y": 20}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 99}},
            "fields": {},
        },
        expected={"value": Eq({"_id": 1, "x": 10, "y": 20})},
        msg="findAndModify with fields:{} returns the full document",
    ),
    CommandTestCase(
        "hint-empty-document",
        docs=[{"_id": 1, "x": 10}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 20}},
            "hint": {},
            "new": True,
        },
        expected={"value": Eq({"_id": 1, "x": 20})},
        msg="findAndModify with hint:{} empty document succeeds",
    ),
    CommandTestCase(
        "bypass-validation-as-int",
        docs=[{"_id": 1, "x": 10}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 20}},
            "bypassDocumentValidation": 1,
        },
        expected={
            "lastErrorObject": Eq({"n": 1, "updatedExisting": True}),
            "value": Eq({"_id": 1, "x": 10}),
        },
        msg="findAndModify accepts bypassDocumentValidation as integer",
    ),
    CommandTestCase(
        "bypass-validation-as-null",
        docs=[{"_id": 1, "x": 10}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 20}},
            "bypassDocumentValidation": None,
        },
        expected={
            "lastErrorObject": Eq({"n": 1, "updatedExisting": True}),
            "value": Eq({"_id": 1, "x": 10}),
        },
        msg="findAndModify accepts bypassDocumentValidation as null",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_findAndModify_argument_validation(database_client, collection, test):
    """Test findAndModify argument handling - success cases for valid parameter variants."""
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


def test_findAndModify_bypass_validation_allows_invalid_write(database_client, request):
    """Test bypassDocumentValidation:true allows write that violates validator."""
    db = database_client
    coll_name = f"{request.node.name}_validated"
    db.create_collection(coll_name, validator={"$jsonSchema": {"required": ["name"]}})
    coll = db[coll_name]
    coll.insert_one({"_id": 1, "name": "test"})
    result = execute_command(
        coll,
        {
            "findAndModify": coll.name,
            "query": {"_id": 1},
            "update": {"$unset": {"name": ""}},
            "bypassDocumentValidation": True,
            "new": True,
        },
    )
    assertSuccessPartial(result, {"value": {"_id": 1}})
