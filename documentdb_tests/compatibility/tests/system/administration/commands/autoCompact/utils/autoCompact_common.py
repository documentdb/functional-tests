"""Shared helpers for autoCompact command tests."""

from __future__ import annotations

import time

from documentdb_tests.framework.executor import execute_admin_command


def ensure_autocompact_idle(collection):
    """Disable autoCompact, retrying until it reaches a deterministic idle state.

    autoCompact is a server-wide setting, so a test inherits prior state, and a
    single disable returns before the background wind-down finishes. This sends
    disable repeatedly with a short pause between calls, returns only after
    several consecutive disables succeed (so the async wind-down has time to
    finish), and raises if it never settles within a bounded number of attempts.

    Callers must be marked no_parallel: this only resets state left by a prior
    test, not a concurrent worker mutating the shared setting between settling
    and the command under test.
    """
    consecutive = 0
    for _ in range(200):
        result = execute_admin_command(collection, {"autoCompact": False})
        if isinstance(result, dict) and result.get("ok") == 1.0:
            consecutive += 1
            if consecutive >= 3:
                return
        else:
            consecutive = 0
        time.sleep(0.05)
    raise RuntimeError("autoCompact did not reach an idle state")
