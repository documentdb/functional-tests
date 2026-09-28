"""Shared fsync-lock state management for fsync and fsyncUnlock tests.

The fsync lock is a server-global count that neither command's collection
fixture manages, so both test directories need a way to return the server to a
known unlocked baseline. The drain helper and the autouse baseline fixture here
are the single source of truth; each command directory's conftest re-exports the
fixture so it applies to that directory's tests.
"""

from __future__ import annotations

import pytest

from documentdb_tests.framework.error_codes import ILLEGAL_OPERATION_ERROR
from documentdb_tests.framework.executor import execute_admin_command


def drain_fsync_lock(collection) -> None:
    """Release outstanding fsync locks until the server-global count reaches 0.

    Loops fsyncUnlock until the reported count is 0, treating the not-locked
    error as "already 0" and re-raising any other error so an unexpected failure
    cannot silently leave the server locked.
    """
    while True:
        result = execute_admin_command(collection, {"fsyncUnlock": 1})
        if isinstance(result, Exception):
            if getattr(result, "code", None) == ILLEGAL_OPERATION_ERROR:
                return
            raise result
        if result.get("lockCount", 0) == 0:
            return


@pytest.fixture(autouse=True)
def unlocked_baseline(collection):
    """Drain the server-global fsync lock before and after every test."""
    drain_fsync_lock(collection)
    yield
    drain_fsync_lock(collection)
