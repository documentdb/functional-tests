"""Shared fixtures for setParameter tests.

Provides an autouse fixture that snapshots mutable server parameters before
each test and unconditionally restores them after, preventing leaked state
even when a test fails.
"""

import pytest

from documentdb_tests.framework.executor import execute_admin_command


@pytest.fixture(autouse=True)
def restore_server_params(collection):
    """Snapshot mutable server parameters before the test, restore after.

    This runs unconditionally (autouse) so that any test modifying server state
    cannot leak changes into subsequent tests — whether it passes, fails, or errors.
    """
    # Snapshot current values
    snapshot = {}
    for param in ["logLevel", "quiet", "automationServiceDescriptor", "logComponentVerbosity"]:
        result = execute_admin_command(collection, {"getParameter": 1, param: 1})
        if isinstance(result, dict) and param in result:
            snapshot[param] = result[param]

    yield

    # Restore original values unconditionally
    for param, value in snapshot.items():
        execute_admin_command(collection, {"setParameter": 1, param: value})
