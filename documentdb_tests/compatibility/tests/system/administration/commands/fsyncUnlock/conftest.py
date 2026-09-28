"""Shared fixtures for fsyncUnlock tests.

Re-exports the autouse fsync-lock baseline fixture so it applies to every test
in this directory without each test file importing it.
"""

from documentdb_tests.compatibility.tests.system.administration.utils.fsync_lock import (
    unlocked_baseline,
)

__all__ = ["unlocked_baseline"]
