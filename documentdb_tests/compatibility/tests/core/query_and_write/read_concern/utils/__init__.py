"""Shared helpers for readConcern tests."""

from documentdb_tests.compatibility.tests.core.utils.command_test_case import CommandTestCase


def is_cursor_command(test: CommandTestCase) -> bool:
    """Return True if the test targets a cursor-returning command (find/aggregate)."""
    return test.id.startswith("find_") or test.id.startswith("aggregate_")
