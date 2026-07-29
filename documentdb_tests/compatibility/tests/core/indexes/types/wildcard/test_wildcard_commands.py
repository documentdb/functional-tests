"""Tests for wildcard index usage across CRUD and write commands: count, update, findAndModify,
and delete."""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index


COMMAND_WIRING_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="count",
        doc=({"_id": 1, "a": 1}, {"_id": 2, "a": None}, {"_id": 3}, {"_id": 4, "a": 3}),
        input="count",
        command_options={"query": {"a": {"$exists": True}}, "hint": "wc_all"},
        expected={"n": 3, "ok": 1.0},
        msg="count hinted to the wildcard index excludes docs missing the field",
    ),
    IndexTestCase(
        id="update",
        doc=({"_id": 1, "a": 1}, {"_id": 2, "a": 2}),
        input="update",
        command_options={"updates": [{"q": {"a": 2}, "u": {"$set": {"a": 99}}, "hint": "wc_all"}]},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="update hinted to the wildcard index modifies the targeted document",
    ),
    IndexTestCase(
        id="upsert",
        doc=(),
        input="update",
        command_options={
            "updates": [
                {"q": {"a": 42}, "u": {"$set": {"a": 42}}, "upsert": True, "hint": "wc_all"}
            ]
        },
        expected={"n": 1, "upserted": [{"index": 0}], "ok": 1.0},
        msg="upsert hinted to the wildcard index inserts the targeted document",
    ),
    IndexTestCase(
        id="findAndModify_update",
        doc=({"_id": 1, "a": 1}, {"_id": 2, "a": 2}),
        input="findAndModify",
        command_options={
            "query": {"a": 2},
            "update": {"$set": {"a": 99}},
            "new": True,
            "hint": "wc_all",
        },
        expected={"value": {"_id": 2, "a": 99}, "ok": 1.0},
        msg="findAndModify hinted to the wildcard index updates and returns the document",
    ),
    IndexTestCase(
        id="findAndModify_remove",
        doc=({"_id": 1, "a": 1}, {"_id": 2, "a": 2}),
        input="findAndModify",
        command_options={"query": {"a": 2}, "remove": True, "hint": "wc_all"},
        expected={"value": {"_id": 2, "a": 2}, "ok": 1.0},
        msg="findAndModify remove hinted to the wildcard index deletes and returns the document",
    ),
    IndexTestCase(
        id="delete",
        doc=({"_id": 1, "a": 1}, {"_id": 2, "a": 2}),
        input="delete",
        command_options={"deletes": [{"q": {"a": 2}, "limit": 1, "hint": "wc_all"}]},
        expected={"n": 1, "ok": 1.0},
        msg="delete hinted to the wildcard index removes the targeted document",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COMMAND_WIRING_TESTS))
def test_wildcard_command_wiring(collection, test):
    """Verify each command that accepts a hint can use a wildcard index."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"$**": 1}, "name": "wc_all"}]},
    )
    if test.doc:
        collection.insert_many(list(test.doc))
    cmd = {test.input: collection.name, **test.command_options}
    result = execute_command(collection, cmd)
    assertSuccessPartial(result, test.expected, msg=test.msg)


def test_wildcard_upsert_indexed_queryable(collection):
    """A document inserted via a hinted upsert is queryable via the wildcard index."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"$**": 1}, "name": "wc_all"}]},
    )
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"a": 42}, "u": {"$set": {"a": 42}}, "upsert": True, "hint": "wc_all"}
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"a": 42}, "hint": "wc_all"}
    )
    assertSuccess(
        result,
        [{"a": 42}],
        transform=lambda batch: [{"a": d["a"]} for d in batch],
        msg="Upserted document is queryable via wildcard index",
    )
