"""Tests for $changeStream startAtOperationTime at or before the oldest oplog entry.

A startAtOperationTime at or before the oldest retained oplog entry is accepted:
the stream opens and begins from the earliest available event. (It is not
rejected as history lost; that error is reserved for resuming from a point that
was retained and has since been evicted, which a controlled test environment
cannot reliably force.)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

import pytest
from bson import Timestamp
from utils.changeStream_common import change_stream_command

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.test_case import BaseTestCase


# Return the timestamp of the oldest retained oplog entry, so a start point can
# be expressed relative to the live oplog rather than as a static value.
def _oldest_oplog_ts(collection) -> Timestamp:
    oldest = (
        collection.database.client["local"]["oplog.rs"]
        .find()
        .sort("$natural", 1)
        .limit(1)
        .next()["ts"]
    )
    return cast(Timestamp, oldest)


@dataclass(frozen=True)
class ChangeStreamEarlyStartTestCase(BaseTestCase):
    """Test case for a startAtOperationTime at or before the oldest oplog entry.

    Attributes:
        compute_start: Receives the timestamp of the oldest retained oplog entry
            captured at run time and returns the startAtOperationTime to test, so
            the boundary case is expressed relative to the live oplog rather than
            as a static value.
    """

    compute_start: Any = None


# Property [Early Start Accepted]: a startAtOperationTime at or before the oldest
# retained oplog entry opens the stream from the earliest available event rather
# than being rejected, including the boundary five seconds before the oldest
# retained entry. This is verified identically across collection-, database-, and
# cluster-scoped streams.
CHANGESTREAM_EARLY_START_TESTS: list[ChangeStreamEarlyStartTestCase] = [
    ChangeStreamEarlyStartTestCase(
        "zero",
        compute_start=lambda oldest: Timestamp(0, 0),
        expected={"ok": Eq(1.0)},
        msg="$changeStream should accept a zero startAtOperationTime",
    ),
    ChangeStreamEarlyStartTestCase(
        "one_zero",
        compute_start=lambda oldest: Timestamp(1, 0),
        expected={"ok": Eq(1.0)},
        msg="$changeStream should accept a startAtOperationTime before the oldest oplog entry",
    ),
    ChangeStreamEarlyStartTestCase(
        "max_increment",
        compute_start=lambda oldest: Timestamp(1, 4_294_967_295),
        expected={"ok": Eq(1.0)},
        msg="$changeStream should accept a startAtOperationTime before the oldest oplog entry",
    ),
    ChangeStreamEarlyStartTestCase(
        "oldest_minus_5s",
        compute_start=lambda oldest: Timestamp(oldest.time - 5, oldest.inc),
        expected={"ok": Eq(1.0)},
        msg="$changeStream should accept a startAtOperationTime five seconds before"
        " the oldest retained oplog entry",
    ),
]


@pytest.mark.requires(change_streams=True)
@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(CHANGESTREAM_EARLY_START_TESTS))
def test_changeStream_early_start_collection_scope(
    collection, test_case: ChangeStreamEarlyStartTestCase
):
    """Test $changeStream accepts an early startAtOperationTime on a collection-scoped stream."""
    start = test_case.compute_start(_oldest_oplog_ts(collection))
    result = execute_command(
        collection,
        change_stream_command(
            collection, pipeline=[{"$changeStream": {"startAtOperationTime": start}}]
        ),
    )
    assertResult(result, expected=test_case.expected, msg=test_case.msg, raw_res=True)


@pytest.mark.requires(change_streams=True)
@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(CHANGESTREAM_EARLY_START_TESTS))
def test_changeStream_early_start_database_scope(
    collection, test_case: ChangeStreamEarlyStartTestCase
):
    """Test $changeStream accepts an early startAtOperationTime on a database-scoped stream."""
    start = test_case.compute_start(_oldest_oplog_ts(collection))
    result = execute_command(
        collection,
        change_stream_command(
            collection,
            pipeline=[{"$changeStream": {"startAtOperationTime": start}}],
            aggregate=1,
        ),
    )
    assertResult(result, expected=test_case.expected, msg=test_case.msg, raw_res=True)


@pytest.mark.requires(change_streams=True)
@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(CHANGESTREAM_EARLY_START_TESTS))
def test_changeStream_early_start_cluster_scope(
    collection, test_case: ChangeStreamEarlyStartTestCase
):
    """Test $changeStream accepts an early startAtOperationTime on a cluster-wide stream."""
    start = test_case.compute_start(_oldest_oplog_ts(collection))
    spec = {"startAtOperationTime": start, "allChangesForCluster": True}
    result = execute_admin_command(
        collection,
        change_stream_command(collection, pipeline=[{"$changeStream": spec}], aggregate=1),
    )
    assertResult(result, expected=test_case.expected, msg=test_case.msg, raw_res=True)
