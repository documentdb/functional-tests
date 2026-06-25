"""Tests for $changeStream startAtOperationTime boundary across scopes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from bson import Timestamp
from utils.changeStream_common import change_stream_command

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class ChangeStreamTimestampTestCase(BaseTestCase):
    """Test case for opening a $changeStream at a startAtOperationTime boundary.

    Attributes:
        compute_start: Receives the current operationTime captured at run time
            and returns the timestamp to pass as startAtOperationTime, so the
            boundary is expressed relative to the live oplog rather than as a
            static value
    """

    compute_start: Any = None


# Property [Timestamp Start Boundary]: a startAtOperationTime at the current
# operationTime, at a zero-increment timestamp for the current second, and at a
# far-future timestamp each opens the stream, identically across collection-,
# database-, and cluster-scoped streams.
CHANGESTREAM_TIMESTAMP_BOUNDARY_TESTS: list[ChangeStreamTimestampTestCase] = [
    ChangeStreamTimestampTestCase(
        "current",
        compute_start=lambda operation_time: operation_time,
        expected={"ok": Eq(1.0)},
        msg="$changeStream should open at the current operationTime",
    ),
    ChangeStreamTimestampTestCase(
        "zero_increment",
        compute_start=lambda operation_time: Timestamp(operation_time.time, 0),
        expected={"ok": Eq(1.0)},
        msg="$changeStream should open at a current-second zero-increment timestamp",
    ),
    ChangeStreamTimestampTestCase(
        "future",
        compute_start=lambda operation_time: Timestamp(operation_time.time + 1_000_000, 0),
        expected={"ok": Eq(1.0)},
        msg="$changeStream should open at a far-future timestamp",
    ),
]


@pytest.mark.requires(change_streams=True)
@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(CHANGESTREAM_TIMESTAMP_BOUNDARY_TESTS))
def test_changeStream_timestamp_boundary_collection_scope(
    collection, test_case: ChangeStreamTimestampTestCase
):
    """Test $changeStream opens a collection-scoped stream at startAtOperationTime boundaries."""
    base = execute_command(
        collection, change_stream_command(collection, pipeline=[{"$changeStream": {}}])
    )
    start = test_case.compute_start(base["operationTime"])
    result = execute_command(
        collection,
        change_stream_command(
            collection, pipeline=[{"$changeStream": {"startAtOperationTime": start}}]
        ),
    )
    assertResult(result, expected=test_case.expected, msg=test_case.msg, raw_res=True)


@pytest.mark.requires(change_streams=True)
@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(CHANGESTREAM_TIMESTAMP_BOUNDARY_TESTS))
def test_changeStream_timestamp_boundary_database_scope(
    collection, test_case: ChangeStreamTimestampTestCase
):
    """Test $changeStream opens a database-scoped stream at startAtOperationTime boundaries."""
    base = execute_command(
        collection, change_stream_command(collection, pipeline=[{"$changeStream": {}}])
    )
    start = test_case.compute_start(base["operationTime"])
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
@pytest.mark.parametrize("test_case", pytest_params(CHANGESTREAM_TIMESTAMP_BOUNDARY_TESTS))
def test_changeStream_timestamp_boundary_cluster_scope(
    collection, test_case: ChangeStreamTimestampTestCase
):
    """Test $changeStream opens a cluster-wide stream at startAtOperationTime boundaries."""
    base = execute_command(
        collection, change_stream_command(collection, pipeline=[{"$changeStream": {}}])
    )
    start = test_case.compute_start(base["operationTime"])
    spec = {"startAtOperationTime": start, "allChangesForCluster": True}
    result = execute_admin_command(
        collection,
        change_stream_command(collection, pipeline=[{"$changeStream": spec}], aggregate=1),
    )
    assertResult(result, expected=test_case.expected, msg=test_case.msg, raw_res=True)
