"""Tests for the visibility of a transaction's pending writes before commit.

A write made inside an open transaction must not be visible to readers outside
the transaction until it commits, but must be visible to reads issued within
the same session. Each test observes the pending write before committing, then
commits to end the transaction.
"""

from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = [pytest.mark.admin, pytest.mark.requires(transactions=True)]


def test_pending_write_not_visible_outside_before_commit(collection):
    """A pending insert is not visible to a reader outside the transaction."""
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        collection.insert_one({"_id": 1, "x": 1}, session=session)
        outside = execute_command(collection, {"find": collection.name, "filter": {}})
        session.commit_transaction()
    assertSuccess(outside, [])


def test_pending_write_visible_in_session_before_commit(collection):
    """A pending insert is visible to a read in the same session before commit."""
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        collection.insert_one({"_id": 1, "x": 1}, session=session)
        in_session = execute_command(
            collection, {"find": collection.name, "filter": {}}, session=session
        )
        session.commit_transaction()
    assertSuccess(in_session, [{"_id": 1, "x": 1}])
