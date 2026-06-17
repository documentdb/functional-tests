"""Tests for $changeStream top-level command option acceptance."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [Cursor and Command Options]: a stream opens when standard aggregate
# cursor and command options are supplied alongside the $changeStream pipeline.
CHANGESTREAM_COMMAND_OPTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "cursor_batch_size_zero",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$changeStream": {}}],
            "cursor": {"batchSize": 0},
        },
        expected={"ok": Eq(1.0)},
        msg="$changeStream should open with cursor.batchSize 0",
    ),
    CommandTestCase(
        "cursor_batch_size_five",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$changeStream": {}}],
            "cursor": {"batchSize": 5},
        },
        expected={"ok": Eq(1.0)},
        msg="$changeStream should open with cursor.batchSize 5",
    ),
    CommandTestCase(
        "max_time_ms",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$changeStream": {}}],
            "cursor": {},
            "maxTimeMS": 1000,
        },
        expected={"ok": Eq(1.0)},
        msg="$changeStream should open with maxTimeMS",
    ),
    CommandTestCase(
        "collation",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$changeStream": {}}],
            "cursor": {},
            "collation": {"locale": "en"},
        },
        expected={"ok": Eq(1.0)},
        msg="$changeStream should open with a top-level collation",
    ),
]


@pytest.mark.requires(change_streams=True)
@pytest.mark.aggregate
@pytest.mark.parametrize("test", pytest_params(CHANGESTREAM_COMMAND_OPTION_TESTS))
def test_changeStream_command_options(database_client, collection, test):
    """Test $changeStream opens with standard aggregate cursor and command options."""
    target = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(target)
    result = execute_command(target, test.build_command(ctx))
    assertResult(result, expected=test.build_expected(ctx), msg=test.msg, raw_res=True)
