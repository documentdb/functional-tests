"""Tests for bulkWrite let variables, per-statement constants, and constants override behavior."""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import (
    assertResult,
    assertSuccess,
    assertSuccessPartial,
)
from documentdb_tests.framework.error_codes import LET_UNDEFINED_VARIABLE_ERROR
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

BULKWRITE_LET_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "let_variables_in_filter",
        docs=[{"_id": 1, "x": 10}, {"_id": 2, "x": 20}],
        command={
            "bulkWrite": 1,
            "ops": [
                {
                    "update": 0,
                    "filter": {"$expr": {"$eq": ["$x", "$$target"]}},
                    "updateMods": {"$set": {"matched": True}},
                }
            ],
            "let": {"target": 10},
        },
        expected={"ok": 1.0, "nMatched": 1, "nModified": 1},
        msg="bulkWrite should resolve let variables referenced in filters",
    ),
    CommandTestCase(
        "let_empty_document",
        docs=[{"_id": 1, "x": 1}],
        command={
            "bulkWrite": 1,
            "ops": [{"update": 0, "filter": {"_id": 1}, "updateMods": {"$set": {"x": 2}}}],
            "let": {},
        },
        expected={"ok": 1.0, "nMatched": 1, "nModified": 1},
        msg="bulkWrite should accept an empty let document",
    ),
    CommandTestCase(
        "let_variable_in_delete_filter",
        docs=[{"_id": 1, "x": 10}, {"_id": 2, "x": 20}],
        command={
            "bulkWrite": 1,
            "ops": [{"delete": 0, "filter": {"$expr": {"$eq": ["$x", "$$delTarget"]}}}],
            "let": {"delTarget": 10},
        },
        expected={"ok": 1.0, "nDeleted": 1},
        msg="bulkWrite should resolve let variables referenced in delete filters",
    ),
    CommandTestCase(
        "constants_override_let_in_updateMods",
        docs=[{"_id": 1, "x": 10}],
        command={
            "bulkWrite": 1,
            "ops": [
                {
                    "update": 0,
                    "filter": {"_id": 1},
                    "updateMods": [{"$set": {"x": "$$val"}}],
                    "constants": {"val": 99},
                }
            ],
            "let": {"val": 10},
        },
        expected={"ok": 1.0, "nMatched": 1, "nModified": 1},
        msg="bulkWrite constants should take precedence over let for the same variable",
    ),
    CommandTestCase(
        "let_variable_name_collision_with_field",
        docs=[{"_id": 1, "x": 10, "target": 999}],
        command={
            "bulkWrite": 1,
            "ops": [
                {
                    "update": 0,
                    "filter": {"$expr": {"$eq": ["$x", "$$target"]}},
                    "updateMods": {"$set": {"matched": True}},
                }
            ],
            "let": {"target": 10},
        },
        expected={"ok": 1.0, "nMatched": 1, "nModified": 1},
        msg="bulkWrite let variable should take precedence over a same-named field in $expr",
    ),
]


@pytest.mark.parametrize("test", pytest_params(BULKWRITE_LET_TESTS))
def test_bulkWrite_let_variables(database_client, collection, test):
    """Test bulkWrite let variables, per-statement constants, and constants override behavior."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    command = test.build_command(ctx)
    if "nsInfo" not in command:
        command = {**command, "nsInfo": [{"ns": ctx.namespace}]}
    result = execute_admin_command(collection, command)
    assertSuccessPartial(result, test.build_expected(ctx), msg=test.msg)


def test_bulkWrite_constants_override_let_writes_constants_value(collection):
    """Test constants takes precedence over let: the constants value 99, not let 10, is written."""
    collection.insert_one({"_id": 1, "x": 10})
    ns = f"{collection.database.name}.{collection.name}"
    execute_admin_command(
        collection,
        {
            "bulkWrite": 1,
            "ops": [
                {
                    "update": 0,
                    "filter": {"_id": 1},
                    "updateMods": [{"$set": {"x": "$$val"}}],
                    "constants": {"val": 99},
                }
            ],
            "nsInfo": [{"ns": ns}],
            "let": {"val": 10},
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [{"_id": 1, "x": 99}])


def test_bulkWrite_let_variable_resolved_in_pipeline_updateMods(collection):
    """Test a let $$var in a pipeline updateMods resolves to its value (read-back x==99)."""
    collection.insert_one({"_id": 1, "x": 10})
    ns = f"{collection.database.name}.{collection.name}"
    execute_admin_command(
        collection,
        {
            "bulkWrite": 1,
            "ops": [
                {"update": 0, "filter": {"_id": 1}, "updateMods": [{"$set": {"x": "$$newVal"}}]}
            ],
            "nsInfo": [{"ns": ns}],
            "let": {"newVal": 99},
        },
    )
    assertSuccess(
        execute_command(collection, {"find": collection.name, "filter": {"_id": 1}}),
        [{"_id": 1, "x": 99}],
        msg="bulkWrite should resolve a let variable in a pipeline updateMods to its value",
    )


def test_bulkWrite_constants_resolved_in_pipeline_update(collection):
    """Test a per-statement constant in a pipeline update resolves to x==42 (read-back)."""
    collection.insert_one({"_id": 1, "x": 10})
    ns = f"{collection.database.name}.{collection.name}"
    execute_admin_command(
        collection,
        {
            "bulkWrite": 1,
            "ops": [
                {
                    "update": 0,
                    "filter": {"_id": 1},
                    "updateMods": [{"$set": {"x": "$$myConst"}}],
                    "constants": {"myConst": 42},
                }
            ],
            "nsInfo": [{"ns": ns}],
        },
    )
    assertSuccess(
        execute_command(collection, {"find": collection.name, "filter": {"_id": 1}}),
        [{"_id": 1, "x": 42}],
        msg="bulkWrite should resolve a per-statement constant in a pipeline update to its value",
    )


def test_bulkWrite_let_not_resolved_in_modifier_update(collection):
    """Test a let $$var is stored literally (not resolved) in a non-pipeline $set update."""
    collection.insert_one({"_id": 1, "x": 1})
    ns = f"{collection.database.name}.{collection.name}"
    execute_admin_command(
        collection,
        {
            "bulkWrite": 1,
            "ops": [{"update": 0, "filter": {"_id": 1}, "updateMods": {"$set": {"x": "$$v"}}}],
            "nsInfo": [{"ns": ns}],
            "let": {"v": 99},
        },
    )
    assertSuccess(
        execute_command(collection, {"find": collection.name, "filter": {"_id": 1}}),
        [{"_id": 1, "x": "$$v"}],
        msg="bulkWrite modifier update should store the literal '$$v', not resolve the let var",
    )


def test_bulkWrite_undefined_let_variable_op_error(collection):
    """Test referencing an undefined let variable yields an op-level error (code 17276)."""
    collection.insert_one({"_id": 1, "x": 1})
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_admin_command(
        collection,
        {
            "bulkWrite": 1,
            "ops": [
                {
                    "update": 0,
                    "filter": {"$expr": {"$eq": ["$x", "$$missing"]}},
                    "updateMods": {"$set": {"hit": True}},
                }
            ],
            "nsInfo": [{"ns": ns}],
        },
    )
    assertResult(
        result,
        expected={
            "ok": Eq(1.0),
            "nErrors": Eq(1),
            "cursor.firstBatch.0.code": Eq(LET_UNDEFINED_VARIABLE_ERROR),
        },
        raw_res=True,
        msg="bulkWrite should report an undefined let variable as op error code 17276",
    )
