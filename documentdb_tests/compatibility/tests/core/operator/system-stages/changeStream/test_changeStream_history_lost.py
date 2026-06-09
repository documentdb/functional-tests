"""Tests for $changeStream history-lost errors when the start point predates the oplog."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from bson import Timestamp
from utils.changeStream_common import change_stream_command

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import CHANGE_STREAM_HISTORY_LOST_ERROR
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase


# Return the timestamp of the oldest retained oplog entry, used to express the
# history-lost boundary relative to the live oplog rather than as a static value.
def _oldest_oplog_ts(collection) -> Timestamp:
    oldest = (
        collection.database.client["local"]["oplog.rs"]
        .find()
        .sort("$natural", 1)
        .limit(1)
        .next()["ts"]
    )
    return oldest


@dataclass(frozen=True)
class ChangeStreamHistoryLostTestCase(BaseTestCase):
    """Test case for a pre-oplog startAtOperationTime rejected as history lost.

    Attributes:
        compute_start: Receives the timestamp of the oldest retained oplog
            entry captured at run time and returns the startAtOperationTime to
            test, so the boundary case is expressed relative to the live oplog
            rather than as a static value
    """

    compute_start: Any = None


# Property [Timestamp History Lost]: a startAtOperationTime strictly before the
# oldest retained oplog entry is rejected at open with a ChangeStreamHistoryLost
# error, including the boundary five seconds before the oldest retained entry.
# This is verified identically across collection-, database-, and cluster-scoped
# streams.
CHANGESTREAM_HISTORY_LOST_TESTS: list[ChangeStreamHistoryLostTestCase] = [
    ChangeStreamHistoryLostTestCase(
        "zero",
        compute_start=lambda oldest: Timestamp(0, 0),
        error_code=CHANGE_STREAM_HISTORY_LOST_ERROR,
        msg="$changeStream should reject a zero startAtOperationTime as history lost",
    ),
    ChangeStreamHistoryLostTestCase(
        "one_zero",
        compute_start=lambda oldest: Timestamp(1, 0),
        error_code=CHANGE_STREAM_HISTORY_LOST_ERROR,
        msg="$changeStream should reject a pre-oplog startAtOperationTime as history lost",
    ),
    ChangeStreamHistoryLostTestCase(
        "max_increment",
        compute_start=lambda oldest: Timestamp(1, 4_294_967_295),
        error_code=CHANGE_STREAM_HISTORY_LOST_ERROR,
        msg="$changeStream should reject a pre-oplog startAtOperationTime as history lost",
    ),
    ChangeStreamHistoryLostTestCase(
        "oldest_minus_5s",
        compute_start=lambda oldest: Timestamp(oldest.time - 5, oldest.inc),
        error_code=CHANGE_STREAM_HISTORY_LOST_ERROR,
        msg="$changeStream should reject a startAtOperationTime five seconds before"
        " the oldest retained oplog entry as history lost",
    ),
]


@pytest.mark.replica_set
@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(CHANGESTREAM_HISTORY_LOST_TESTS))
def test_changeStream_history_lost_collection_scope(
    collection, test_case: ChangeStreamHistoryLostTestCase
):
    """Test $changeStream rejects a pre-oplog startAtOperationTime on a collection-scoped stream."""
    start = test_case.compute_start(_oldest_oplog_ts(collection))
    result = execute_command(
        collection,
        change_stream_command(
            collection, pipeline=[{"$changeStream": {"startAtOperationTime": start}}]
        ),
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)


@pytest.mark.replica_set
@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(CHANGESTREAM_HISTORY_LOST_TESTS))
def test_changeStream_history_lost_database_scope(
    collection, test_case: ChangeStreamHistoryLostTestCase
):
    """Test $changeStream rejects a pre-oplog startAtOperationTime on a database-scoped stream."""
    start = test_case.compute_start(_oldest_oplog_ts(collection))
    result = execute_command(
        collection,
        change_stream_command(
            collection,
            pipeline=[{"$changeStream": {"startAtOperationTime": start}}],
            aggregate=1,
        ),
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)


@pytest.mark.replica_set
@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(CHANGESTREAM_HISTORY_LOST_TESTS))
def test_changeStream_history_lost_cluster_scope(
    collection, test_case: ChangeStreamHistoryLostTestCase
):
    """Test $changeStream rejects a pre-oplog startAtOperationTime on a cluster-wide stream."""
    start = test_case.compute_start(_oldest_oplog_ts(collection))
    spec = {"startAtOperationTime": start, "allChangesForCluster": True}
    result = execute_admin_command(
        collection,
        change_stream_command(collection, pipeline=[{"$changeStream": spec}], aggregate=1),
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)
