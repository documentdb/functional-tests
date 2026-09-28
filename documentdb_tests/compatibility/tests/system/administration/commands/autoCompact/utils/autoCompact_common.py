"""Shared helpers for autoCompact command tests."""

from __future__ import annotations

from documentdb_tests.framework.error_codes import OBJECT_IS_BUSY_ERROR
from documentdb_tests.framework.executor import execute_admin_with_retry_command


def ensure_autocompact_idle(collection):
    """Reset autoCompact to a disabled baseline before a test runs.

    autoCompact is a server-wide setting, so a test inherits prior state. The
    background compaction winds down asynchronously, so we must try to disable
    until the server stops complaining.

    Callers must be marked no_parallel: this only resets state left by a prior
    test, not a concurrent worker mutating the shared setting between the reset
    and the command under test.
    """
    result = execute_admin_with_retry_command(
        collection, {"autoCompact": False}, retry_code=OBJECT_IS_BUSY_ERROR
    )
    if not (isinstance(result, dict) and result.get("ok") == 1.0):
        raise RuntimeError(f"autoCompact did not reach an idle state: {result!r}")
