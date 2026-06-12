"""Tests for tailable cursor lifecycle with getMore."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertProperties, assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Ne
from documentdb_tests.framework.target_collection import CappedCollection
from documentdb_tests.framework.test_constants import INT64_ZERO

from .utils.capped import create_capped

# Property [Cursor Lifecycle with getMore]: find options like skip, batchSize, and
# limit affect the initial tailable cursor response.
TAILABLE_LIFECYCLE_FIND_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "skip_initial",
        target_collection=CappedCollection(),
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}, {"_id": 3, "x": 3}],
        command=lambda ctx: {
            "find": ctx.collection,
            "tailable": True,
            "skip": 2,
            "batchSize": 100,
        },
        expected={"cursor": {"firstBatch": Eq([{"_id": 3, "x": 3}])}},
        msg="Skip should apply to initial query",
    ),
    CommandTestCase(
        "batchsize_zero_find",
        target_collection=CappedCollection(),
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {"find": ctx.collection, "tailable": True, "batchSize": 0},
        expected={"cursor": {"id": Ne(INT64_ZERO), "firstBatch": Eq([])}},
        msg="batchSize: 0 should establish cursor without returning documents",
    ),
    CommandTestCase(
        "sequential_batches_first",
        target_collection=CappedCollection(),
        docs=[{"_id": i} for i in range(1, 6)],
        command=lambda ctx: {"find": ctx.collection, "tailable": True, "batchSize": 2},
        expected={
            "cursor": {
                "id": Ne(INT64_ZERO),
                "firstBatch": Eq([{"_id": 1}, {"_id": 2}]),
            },
        },
        msg="First batch should contain first 2 documents",
    ),
    CommandTestCase(
        "limit_restricts_results",
        target_collection=CappedCollection(),
        docs=[{"_id": 1}, {"_id": 2}, {"_id": 3}, {"_id": 4}, {"_id": 5}],
        command=lambda ctx: {
            "find": ctx.collection,
            "tailable": True,
            "limit": 2,
            "batchSize": 100,
        },
        expected={
            "cursor": {
                "id": Ne(INT64_ZERO),
                "firstBatch": Eq([{"_id": 1}, {"_id": 2}]),
            },
        },
        msg="Tailable cursor with limit should return at most limit documents",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TAILABLE_LIFECYCLE_FIND_TESTS))
def test_tailable_cursors_lifecycle_find(database_client, collection, test: CommandTestCase):
    """Test single-command tailable cursor lifecycle behavior."""
    resolved = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(resolved)
    result = execute_command(resolved, test.build_command(ctx))
    assertResult(result, expected=test.build_expected(ctx), msg=test.msg, raw_res=True)


# Property [Empty getMore]: getMore at end of data returns an empty batch and the
# cursor stays open.
def test_tailable_cursors_lifecycle_empty_getmore(database_client, collection):
    """Test getMore at end of data returns empty batch, cursor stays open."""
    capped = create_capped(database_client, collection, [{"_id": 1, "x": 1}])
    result = execute_command(capped, {"find": capped.name, "tailable": True, "batchSize": 100})
    cursor_id = result["cursor"]["id"]

    gm_result = execute_command(capped, {"getMore": cursor_id, "collection": capped.name})
    assertProperties(
        gm_result,
        {"cursor": {"id": Ne(INT64_ZERO), "nextBatch": Eq([])}},
        msg="getMore at end of data should return empty batch with cursor open",
        raw_res=True,
    )


# Property [New Insert Visibility]: getMore returns documents inserted after the
# cursor was opened.
def test_tailable_cursors_lifecycle_new_inserts(database_client, collection):
    """Test getMore returns newly inserted documents."""
    capped = create_capped(database_client, collection, [{"_id": 1, "x": 1}])
    result = execute_command(capped, {"find": capped.name, "tailable": True, "batchSize": 100})
    cursor_id = result["cursor"]["id"]

    capped.insert_one({"_id": 2, "x": 2})

    gm_result = execute_command(capped, {"getMore": cursor_id, "collection": capped.name})
    assertProperties(
        gm_result,
        {"cursor": {"id": Ne(INT64_ZERO), "nextBatch": Eq([{"_id": 2, "x": 2}])}},
        msg="getMore should return newly inserted documents",
        raw_res=True,
    )


# Property [Limit with Tailable]: limit caps total documents returned but the cursor
# remains open.
def test_tailable_cursors_lifecycle_limit_cursor_stays_open(database_client, collection):
    """Test tailable cursor stays open after limit is exhausted."""
    capped = create_capped(
        database_client, collection, [{"_id": 1}, {"_id": 2}, {"_id": 3}, {"_id": 4}, {"_id": 5}]
    )
    result = execute_command(
        capped, {"find": capped.name, "tailable": True, "limit": 2, "batchSize": 100}
    )
    cursor_id = result["cursor"]["id"]

    gm_result = execute_command(capped, {"getMore": cursor_id, "collection": capped.name})
    assertProperties(
        gm_result,
        {"cursor": {"id": Ne(INT64_ZERO), "nextBatch": Eq([])}},
        msg="Tailable cursor should stay open after limit is exhausted",
        raw_res=True,
    )


# Property [Limit Blocks New Inserts]: new inserts are not visible via getMore after
# the limit is exhausted.
def test_tailable_cursors_lifecycle_limit_blocks_new_inserts(database_client, collection):
    """Test new inserts are not visible after limit is exhausted."""
    capped = create_capped(
        database_client, collection, [{"_id": 1}, {"_id": 2}, {"_id": 3}, {"_id": 4}, {"_id": 5}]
    )
    result = execute_command(
        capped, {"find": capped.name, "tailable": True, "limit": 2, "batchSize": 100}
    )
    cursor_id = result["cursor"]["id"]

    capped.insert_one({"_id": 6})

    gm_result = execute_command(capped, {"getMore": cursor_id, "collection": capped.name})
    assertProperties(
        gm_result,
        {"cursor": {"id": Ne(INT64_ZERO), "nextBatch": Eq([])}},
        msg="New inserts should not be visible after limit is exhausted",
        raw_res=True,
    )


# Property [Limit Counts Across getMores]: limit counts total documents delivered
# across all getMores, not just the initial batch.
def test_tailable_cursors_lifecycle_limit_counts_across_getmores(database_client, collection):
    """Test limit counts total documents across getMores, not just initial batch."""
    capped = create_capped(database_client, collection, [{"_id": 1}])
    result = execute_command(
        capped, {"find": capped.name, "tailable": True, "limit": 2, "batchSize": 100}
    )
    cursor_id = result["cursor"]["id"]

    capped.insert_many([{"_id": 2}, {"_id": 3}])
    gm1 = execute_command(capped, {"getMore": cursor_id, "collection": capped.name})
    assertProperties(
        gm1,
        {"cursor": {"id": Ne(INT64_ZERO), "nextBatch": Eq([{"_id": 2}])}},
        msg="getMore should return only one doc when limit of 2 allows one more",
        raw_res=True,
    )


# Property [Limit Exhausted Across getMores]: documents beyond the limit are not
# returned even via subsequent getMore calls.
def test_tailable_cursors_lifecycle_limit_exhausted_across_getmores(database_client, collection):
    """Test documents beyond limit are not returned even via getMore."""
    capped = create_capped(database_client, collection, [{"_id": 1}])
    result = execute_command(
        capped, {"find": capped.name, "tailable": True, "limit": 2, "batchSize": 100}
    )
    cursor_id = result["cursor"]["id"]

    capped.insert_one({"_id": 2})
    gm1 = execute_command(capped, {"getMore": cursor_id, "collection": capped.name})

    capped.insert_one({"_id": 3})
    gm2 = execute_command(capped, {"getMore": gm1["cursor"]["id"], "collection": capped.name})
    assertProperties(
        gm2,
        {"cursor": {"id": Ne(INT64_ZERO), "nextBatch": Eq([])}},
        msg="Third doc should not be visible after limit of 2 is exhausted across getMores",
        raw_res=True,
    )
