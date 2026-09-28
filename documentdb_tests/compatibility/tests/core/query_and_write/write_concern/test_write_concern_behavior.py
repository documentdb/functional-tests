"""writeConcern behavior: w:0 unacknowledged writes, j:true overriding w:0,
findAndModify return semantics, and ordered interaction.

The "still performs the write" checks are hand-written (not CommandTestCase
rows) because they verify the effect with a second find command.
"""

from typing import Any, Dict, cast

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import CommandTestCase
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, NotExists

BEHAVIOR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "update_j_true_overrides_w0",
        docs=[{"_id": 1}],
        command={
            "verb": "update",
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": 0, "j": True},
        },
        expected={"ok": Eq(1.0)},
        msg="update with j:true should override w:0.",
    ),
    CommandTestCase(
        "delete_j_true_overrides_w0",
        docs=[{"_id": 99}],
        command={
            "verb": "delete",
            "deletes": [{"q": {"_id": 99}, "limit": 1}],
            "writeConcern": {"w": 0, "j": True},
        },
        expected={"ok": Eq(1.0)},
        msg="delete with j:true should override w:0.",
    ),
    CommandTestCase(
        "findAndModify_j_true_overrides_w0",
        docs=[{"_id": 1}],
        command={
            "verb": "findAndModify",
            "query": {"_id": 1},
            "update": {"$set": {"a": 1}},
            "writeConcern": {"w": 0, "j": True},
        },
        expected={"ok": Eq(1.0)},
        msg="findAndModify with j:true should override w:0.",
    ),
    CommandTestCase(
        "findAndModify_w0_accepts_and_performs_write",
        docs=[{"_id": 1, "a": 0}],
        command={
            "verb": "findAndModify",
            "query": {"_id": 1},
            "update": {"$set": {"a": 99}},
            "new": True,
            "writeConcern": {"w": 0},
        },
        expected={"value": {"_id": Eq(1), "a": Eq(99)}},
        msg="findAndModify with w:0 should still perform the write.",
    ),
    CommandTestCase(
        "findAndModify_new_true",
        docs=[{"_id": 1, "a": 0}],
        command={
            "verb": "findAndModify",
            "query": {"_id": 1},
            "update": {"$set": {"a": 99}},
            "new": True,
            "writeConcern": {"w": 1},
        },
        expected={"value": {"_id": Eq(1), "a": Eq(99)}},
        msg="findAndModify new:true should return modified doc.",
    ),
    CommandTestCase(
        "findAndModify_new_false",
        docs=[{"_id": 1, "a": 0}],
        command={
            "verb": "findAndModify",
            "query": {"_id": 1},
            "update": {"$set": {"a": 99}},
            "new": False,
            "writeConcern": {"w": 1},
        },
        expected={"value": {"_id": Eq(1), "a": Eq(0)}},
        msg="findAndModify new:false should return original doc.",
    ),
    CommandTestCase(
        "findAndModify_remove",
        docs=[{"_id": 1, "a": 0}],
        command={
            "verb": "findAndModify",
            "query": {"_id": 1},
            "remove": True,
            "writeConcern": {"w": 1},
        },
        expected={"value": {"_id": Eq(1), "a": Eq(0)}},
        msg="findAndModify remove:true should return removed doc.",
    ),
    CommandTestCase(
        "update_ordered_true",
        docs=[{"_id": 1}],
        command={
            "verb": "update",
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a": 1}}}],
            "ordered": True,
            "writeConcern": {"w": 1},
        },
        expected={"ok": Eq(1.0)},
        msg="update with ordered:true and writeConcern should succeed.",
    ),
    CommandTestCase(
        "update_ordered_false",
        docs=[{"_id": 1}],
        command={
            "verb": "update",
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a": 1}}}],
            "ordered": False,
            "writeConcern": {"w": 1},
        },
        expected={"ok": Eq(1.0)},
        msg="update with ordered:false and writeConcern should succeed.",
    ),
    # w:0 suppresses the per-operation error that w:1 surfaces. The w:1 "surfaces"
    # counterpart lives in test_write_concern_errors.py (w1_surfaces_operation_error).
    # multi:true with a replacement doc is the invalid operation under test.
    CommandTestCase(
        "w0_suppresses_operation_error",
        docs=[{"_id": 1, "a": 1}],
        command={
            "verb": "update",
            "updates": [{"q": {}, "u": {"a": 2}, "multi": True}],
            "writeConcern": {"w": 0},
        },
        expected={"writeErrors": NotExists()},
        msg="update with w:0 should suppress the operation error.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(BEHAVIOR_TESTS))
def test_write_concern_behavior(collection, test: CommandTestCase):
    """Test single-command writeConcern behaviors."""
    collection = test.prepare(collection.database, collection)
    body = dict(cast(Dict[str, Any], test.command))
    verb = body.pop("verb")
    result = execute_command(collection, {verb: collection.name, **body})
    assertResult(result, expected=test.expected, msg=test.msg, raw_res=True)


def test_update_w0_performs_write(collection):
    """Test update with w:0 still performs the write."""
    collection.insert_one({"_id": 1, "a": 0})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a": 99}}}],
            "writeConcern": {"w": 0},
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertResult(
        result,
        expected=[{"_id": 1, "a": 99}],
        msg="update with w:0 should still perform the write.",
    )


def test_delete_w0_performs_delete(collection):
    """Test delete with w:0 still performs the delete."""
    collection.insert_one({"_id": 1})
    execute_command(
        collection,
        {
            "delete": collection.name,
            "deletes": [{"q": {"_id": 1}, "limit": 1}],
            "writeConcern": {"w": 0},
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertResult(result, expected=[], msg="delete with w:0 should still perform the delete.")
