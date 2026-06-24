"""
readConcern level acceptance tests.

Verifies that each valid readConcern level is accepted by each read command
and returns correct results.
"""

import pytest

from documentdb_tests.compatibility.tests.core.query_and_write.read_concern.utils import (
    is_cursor_command,
)
from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Level Acceptance]: read commands accept valid readConcern levels.
LEVEL_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "find_accepts_local",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {},
            "sort": {"_id": 1},
            "readConcern": {"level": "local"},
        },
        expected=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        msg="find should accept readConcern level 'local'.",
    ),
    CommandTestCase(
        "find_accepts_available",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {},
            "sort": {"_id": 1},
            "readConcern": {"level": "available"},
        },
        expected=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        msg="find should accept readConcern level 'available'.",
    ),
    CommandTestCase(
        "find_accepts_majority",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {},
            "sort": {"_id": 1},
            "readConcern": {"level": "majority"},
        },
        expected=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        msg="find should accept readConcern level 'majority'.",
    ),
    CommandTestCase(
        "aggregate_accepts_local",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"_id": 1}}],
            "cursor": {},
            "readConcern": {"level": "local"},
        },
        expected=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        msg="aggregate should accept readConcern level 'local'.",
    ),
    CommandTestCase(
        "aggregate_accepts_available",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"_id": 1}}],
            "cursor": {},
            "readConcern": {"level": "available"},
        },
        expected=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        msg="aggregate should accept readConcern level 'available'.",
    ),
    CommandTestCase(
        "aggregate_accepts_majority",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"_id": 1}}],
            "cursor": {},
            "readConcern": {"level": "majority"},
        },
        expected=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        msg="aggregate should accept readConcern level 'majority'.",
    ),
    CommandTestCase(
        "count_accepts_local",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {},
            "readConcern": {"level": "local"},
        },
        expected={"n": 2, "ok": 1.0},
        msg="count should accept readConcern level 'local'.",
    ),
    CommandTestCase(
        "count_accepts_available",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {},
            "readConcern": {"level": "available"},
        },
        expected={"n": 2, "ok": 1.0},
        msg="count should accept readConcern level 'available'.",
    ),
    CommandTestCase(
        "count_accepts_majority",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {},
            "readConcern": {"level": "majority"},
        },
        expected={"n": 2, "ok": 1.0},
        msg="count should accept readConcern level 'majority'.",
    ),
    CommandTestCase(
        "distinct_accepts_local",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "readConcern": {"level": "local"},
        },
        expected={"ok": 1.0, "values": [1, 2]},
        msg="distinct should accept readConcern level 'local'.",
    ),
    CommandTestCase(
        "distinct_accepts_available",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "readConcern": {"level": "available"},
        },
        expected={"ok": 1.0, "values": [1, 2]},
        msg="distinct should accept readConcern level 'available'.",
    ),
    CommandTestCase(
        "distinct_accepts_majority",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "readConcern": {"level": "majority"},
        },
        expected={"ok": 1.0, "values": [1, 2]},
        msg="distinct should accept readConcern level 'majority'.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LEVEL_ACCEPTANCE_TESTS))
def test_read_concern_level_acceptance(collection, test: CommandTestCase):
    """Test readConcern level is accepted by the command."""
    collection = test.prepare(collection.database, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        msg=test.msg,
        raw_res=not is_cursor_command(test),
    )


# Property [Empty readConcern Document]: empty readConcern uses the implicit default.
EMPTY_READ_CONCERN_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "find_accepts_empty_read_concern",
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {"find": ctx.collection, "filter": {}, "readConcern": {}},
        expected=[{"_id": 1, "x": 1}],
        msg="find should accept empty readConcern document.",
    ),
    CommandTestCase(
        "aggregate_accepts_empty_read_concern",
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {},
        },
        expected=[{"_id": 1, "x": 1}],
        msg="aggregate should accept empty readConcern document.",
    ),
    CommandTestCase(
        "count_accepts_empty_read_concern",
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {"count": ctx.collection, "query": {}, "readConcern": {}},
        expected={"n": 1, "ok": 1.0},
        msg="count should accept empty readConcern document.",
    ),
    CommandTestCase(
        "distinct_accepts_empty_read_concern",
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x", "readConcern": {}},
        expected={"ok": 1.0, "values": [1]},
        msg="distinct should accept empty readConcern document.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(EMPTY_READ_CONCERN_TESTS))
def test_read_concern_empty_document(collection, test: CommandTestCase):
    """Test readConcern with empty document uses implicit default."""
    collection = test.prepare(collection.database, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        msg=test.msg,
        raw_res=not is_cursor_command(test),
    )


_EQUIVALENCE_PARAMS = [
    pytest.param("local", id="equivalence_local"),
    pytest.param("available", id="equivalence_available"),
    pytest.param("majority", id="equivalence_majority"),
]


@pytest.mark.parametrize("level", _EQUIVALENCE_PARAMS)
def test_read_concern_functional_equivalence(collection, level):
    """Test all levels return the same results on a single node."""
    collection.insert_many([{"_id": 1, "x": 1}, {"_id": 2, "x": 2}])
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {},
            "sort": {"_id": 1},
            "readConcern": {"level": level},
        },
    )
    assertSuccess(
        result,
        [{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        msg=f"find with readConcern '{level}' should return same results on single node.",
    )
