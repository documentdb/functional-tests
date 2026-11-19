"""Shared helpers for autoCompact command tests."""

from __future__ import annotations

from documentdb_tests.framework.error_codes import (
    COMMAND_NOT_FOUND_ERROR,
    FEATURE_NOT_SUPPORTED_ERROR,
    OBJECT_IS_BUSY_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_with_retry_command

# Codes a server returns when autoCompact is not available at all (command
# unknown, or the feature unsupported). On such an engine there is no
# server-wide compaction state to reset, so the idle baseline is already met.
_UNSUPPORTED_CODES = frozenset({COMMAND_NOT_FOUND_ERROR, FEATURE_NOT_SUPPORTED_ERROR})


def ensure_autocompact_idle(collection):
    """Reset autoCompact to a disabled baseline before a test runs.

    autoCompact is a server-wide setting, so a test inherits prior state. The
    background compaction winds down asynchronously, so we must try to disable
    until the server stops complaining.

    Callers must be marked no_parallel: this only resets state left by a prior
    test, not a concurrent worker mutating the shared setting between the reset
    and the command under test.

    If autoCompact is unsupported, there is no compaction state to reset, so
    return instead of raising and let the test under test run and judge the
    command.
    """
    result = execute_admin_with_retry_command(
        collection, {"autoCompact": False}, retry_code=OBJECT_IS_BUSY_ERROR
    )
    if isinstance(result, Exception) and getattr(result, "code", None) in _UNSUPPORTED_CODES:
        return
    if not (isinstance(result, dict) and result.get("ok") == 1.0):
        raise RuntimeError(f"autoCompact did not reach an idle state: {result!r}")
