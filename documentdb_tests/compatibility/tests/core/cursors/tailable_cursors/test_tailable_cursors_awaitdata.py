"""Tests for tailable cursor awaitData behavior and noCursorTimeout."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertProperties, assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    FAILED_TO_PARSE_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Ne
from documentdb_tests.framework.target_collection import CappedCollection
from documentdb_tests.framework.test_constants import INT64_ZERO

from .utils.capped import create_capped

# Property [awaitData Behavior]: awaitData requires tailable and modifies cursor
# blocking behavior.
TAILABLE_AWAITDATA_SINGLE_CMD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "awaitdata_empty_capped_dead_cursor",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {
            "find": ctx.collection,
            "tailable": True,
            "awaitData": True,
            "batchSize": 100,
        },
        expected={"cursor": {"id": Eq(INT64_ZERO), "firstBatch": Eq([])}},
        msg="awaitData on empty capped collection should produce dead cursor",
    ),
    CommandTestCase(
        "awaitdata_requires_tailable",
        target_collection=CappedCollection(),
        docs=[{"_id": 1}],
        command=lambda ctx: {"find": ctx.collection, "awaitData": True},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="awaitData: true without tailable should produce a parse error",
    ),
    CommandTestCase(
        "awaitdata_false_without_tailable",
        target_collection=CappedCollection(),
        docs=[{"_id": 1}],
        command=lambda ctx: {"find": ctx.collection, "awaitData": False},
        expected={"cursor": {"firstBatch": Eq([{"_id": 1}])}},
        msg="awaitData: false without tailable should be accepted",
    ),
    CommandTestCase(
        "nocursortimeout_with_tailable",
        target_collection=CappedCollection(),
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "find": ctx.collection,
            "tailable": True,
            "noCursorTimeout": True,
            "batchSize": 100,
        },
        expected={"cursor": {"id": Ne(INT64_ZERO)}},
        msg="noCursorTimeout with tailable on capped collection should keep cursor open",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TAILABLE_AWAITDATA_SINGLE_CMD_TESTS))
def test_tailable_cursors_awaitdata_single(database_client, collection, test: CommandTestCase):
    """Test single-command awaitData and noCursorTimeout behavior."""
    resolved = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(resolved)
    result = execute_command(resolved, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


# Property [awaitData getMore Behavior]: getMore with maxTimeMS on an awaitData
# cursor returns an empty batch with the cursor still open when no new data exists.
def test_tailable_cursors_awaitdata_getmore_empty(database_client, collection):
    """Test getMore with maxTimeMS on awaitData cursor returns empty batch."""
    capped = create_capped(database_client, collection, [{"_id": 1}])
    result = execute_command(
        capped,
        {"find": capped.name, "tailable": True, "awaitData": True, "batchSize": 100},
    )
    cursor_id = result["cursor"]["id"]

    gm_result = execute_command(
        capped, {"getMore": cursor_id, "collection": capped.name, "maxTimeMS": 200}
    )
    assertProperties(
        gm_result,
        {"cursor": {"id": Ne(INT64_ZERO), "nextBatch": Eq([])}},
        msg="awaitData getMore with maxTimeMS should return empty batch with cursor open",
        raw_res=True,
    )


# Property [Non-awaitData getMore Behavior]: getMore on a tailable cursor without
# awaitData returns an empty batch with the cursor still open when no new data exists.
def test_tailable_cursors_non_awaitdata_getmore_empty(database_client, collection):
    """Test getMore on non-awaitData tailable cursor returns empty batch."""
    capped = create_capped(database_client, collection, [{"_id": 1}])
    result = execute_command(
        capped,
        {"find": capped.name, "tailable": True, "awaitData": False, "batchSize": 100},
    )
    cursor_id = result["cursor"]["id"]

    gm_result = execute_command(capped, {"getMore": cursor_id, "collection": capped.name})
    assertProperties(
        gm_result,
        {"cursor": {"id": Ne(INT64_ZERO), "nextBatch": Eq([])}},
        msg="Non-awaitData getMore should return empty batch with cursor open",
        raw_res=True,
    )


# Property [awaitData maxTimeMS Zero]: maxTimeMS: 0 on getMore causes an awaitData
# cursor to return immediately.
def test_tailable_cursors_awaitdata_maxtime_zero(database_client, collection):
    """Test getMore maxTimeMS: 0 on awaitData cursor returns immediately."""
    capped = create_capped(database_client, collection, [{"_id": 1}])
    result = execute_command(
        capped,
        {"find": capped.name, "tailable": True, "awaitData": True, "batchSize": 100},
    )
    cursor_id = result["cursor"]["id"]

    gm_result = execute_command(
        capped, {"getMore": cursor_id, "collection": capped.name, "maxTimeMS": 0}
    )
    assertProperties(
        gm_result,
        {"cursor": {"id": Ne(INT64_ZERO), "nextBatch": Eq([])}},
        msg="getMore maxTimeMS: 0 on awaitData cursor should return immediately",
        raw_res=True,
    )


# Property [maxTimeMS Requires awaitData]: maxTimeMS on getMore is rejected for
# non-awaitData tailable cursors.
def test_tailable_cursors_awaitdata_maxtime_noawait_error(database_client, collection):
    """Test maxTimeMS on getMore for non-awaitData tailable cursor produces error."""
    capped = create_capped(database_client, collection, [{"_id": 1}])
    result = execute_command(
        capped,
        {"find": capped.name, "tailable": True, "awaitData": False, "batchSize": 100},
    )
    cursor_id = result["cursor"]["id"]

    gm_result = execute_command(
        capped, {"getMore": cursor_id, "collection": capped.name, "maxTimeMS": 100}
    )
    assertFailureCode(
        gm_result,
        BAD_VALUE_ERROR,
        msg="maxTimeMS on getMore for non-awaitData tailable cursor should produce an error",
    )


# Property [getMore Rejects awaitData Field]: the awaitData field is not accepted
# on the getMore command itself.
def test_tailable_cursors_awaitdata_getmore_rejects_awaitdata_field(database_client, collection):
    """Test specifying awaitData on getMore command is rejected."""
    capped = create_capped(database_client, collection, [{"_id": 1}])
    result = execute_command(
        capped,
        {"find": capped.name, "tailable": True, "awaitData": True, "batchSize": 100},
    )
    cursor_id = result["cursor"]["id"]

    gm_result = execute_command(
        capped,
        {"getMore": cursor_id, "collection": capped.name, "awaitData": True},
    )
    assertFailureCode(
        gm_result,
        UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Specifying awaitData on getMore should produce unrecognized command field error",
    )
