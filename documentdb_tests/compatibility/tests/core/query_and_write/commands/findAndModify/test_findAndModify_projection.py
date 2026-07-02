"""
Tests for findAndModify fields projection behavior.
"""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

UPDATE_PROJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "new-true-returns-post-image-projection",
        docs=[{"_id": 1, "x": 10, "y": 20}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 99}},
            "fields": {"x": 1},
            "new": True,
        },
        expected={"value": Eq({"_id": 1, "x": 99})},
        msg="fields projection with new:true returns projection of post-modification doc",
    ),
    CommandTestCase(
        "new-false-returns-pre-image-projection",
        docs=[{"_id": 1, "x": 10, "y": 20}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 99}},
            "fields": {"x": 1},
            "new": False,
        },
        expected={"value": Eq({"_id": 1, "x": 10})},
        msg="fields projection with new:false returns projection of pre-modification doc",
    ),
    CommandTestCase(
        "exclude-id-from-projection",
        docs=[{"_id": 1, "x": 10, "y": 20}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 99}},
            "fields": {"_id": 0, "x": 1},
        },
        expected={"value": Eq({"x": 10})},
        msg="fields projection with _id:0 omits _id from returned value",
    ),
]

REMOVE_PROJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "remove-inclusion-projection",
        docs=[{"_id": 1, "x": 10, "y": 20, "z": 30}],
        command={
            "query": {"_id": 1},
            "remove": True,
            "fields": {"x": 1},
        },
        expected={"value": Eq({"_id": 1, "x": 10})},
        msg="remove with inclusion projection returns _id plus included field",
    ),
    CommandTestCase(
        "remove-exclusion-projection",
        docs=[{"_id": 1, "x": 10, "y": 20}],
        command={
            "query": {"_id": 1},
            "remove": True,
            "fields": {"y": 0},
        },
        expected={"value": Eq({"_id": 1, "x": 10})},
        msg="remove with exclusion projection returns document without excluded field",
    ),
    CommandTestCase(
        "remove-exclude-id-and-field",
        docs=[{"_id": 1, "x": 10, "y": 20}],
        command={
            "query": {"_id": 1},
            "remove": True,
            "fields": {"_id": 0, "x": 0},
        },
        expected={"value": Eq({"y": 20})},
        msg="remove with exclusion of both _id and a field",
    ),
    CommandTestCase(
        "remove-combined-query-sort-projection",
        docs=[
            {"_id": 1, "x": 5, "y": "a"},
            {"_id": 2, "x": 15, "y": "b"},
            {"_id": 3, "x": 25, "y": "c"},
        ],
        command={
            "query": {"x": {"$gt": 10}},
            "remove": True,
            "sort": {"x": -1},
            "fields": {"y": 0},
        },
        expected={"value": Eq({"_id": 3, "x": 25})},
        msg="remove combining range query, exclusion projection, and descending sort",
    ),
]

UPSERT_PROJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "projection-on-upsert-new-true",
        docs=[],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 10, "y": 20}},
            "upsert": True,
            "new": True,
            "fields": {"x": 1},
        },
        expected={"value": Eq({"_id": 1, "x": 10})},
        msg="projection on upserted document returns only projected fields",
    ),
]

COMPUTED_PROJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "computed-expression-new-true",
        docs=[{"_id": 1, "x": 5}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 10}},
            "fields": {"doubled": {"$multiply": ["$x", 2]}, "_id": 0},
            "new": True,
        },
        expected={"value": Eq({"doubled": 20})},
        msg="computed expression in fields evaluates against post-image when new:true",
    ),
    CommandTestCase(
        "computed-expression-new-false",
        docs=[{"_id": 1, "x": 5}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": 10}},
            "fields": {"doubled": {"$multiply": ["$x", 2]}, "_id": 0},
            "new": False,
        },
        expected={"value": Eq({"doubled": 10})},
        msg="computed expression in fields evaluates against pre-image when new:false",
    ),
]

ALL_TESTS: list[CommandTestCase] = (
    UPDATE_PROJECTION_TESTS
    + REMOVE_PROJECTION_TESTS
    + UPSERT_PROJECTION_TESTS
    + COMPUTED_PROJECTION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_findAndModify_projection(database_client, collection, test):
    """Test findAndModify fields projection behavior."""
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
