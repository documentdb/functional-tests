"""Shared test case for administration command tests."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pymongo.collection import Collection

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)


@dataclass(frozen=True)
class AdminTestCase(CommandTestCase):
    """Test case for administration command tests.

    Extends CommandTestCase with fields for admin-specific execution:

    Attributes:
        use_admin: If True (the default), execute the command against
            the admin database via ``execute_admin_command``.  If False,
            execute against the test database via ``execute_command``.
        pre_command: Optional callable ``(collection) -> None`` invoked
            after ``prepare`` completes (docs inserted, indexes created)
            but before the test command executes. Use this for stateful
            setup like enabling a write block.
        partial_success: If True, success assertions use partial matching
            (only checks that expected keys are present in the result).
            Useful for commands that return extra metadata fields.
    """

    use_admin: bool = True
    pre_command: Callable[[Collection], Any] | None = None
    partial_success: bool = False

    def run_pre_command(self, collection: Collection) -> None:
        """Execute the pre_command callable if defined."""
        if self.pre_command is not None:
            self.pre_command(collection)

    def build_expected(self, ctx: CommandContext) -> dict[str, Any] | list[dict[str, Any]] | None:
        """Resolve expected from a callable or plain value."""
        if self.expected is None or isinstance(self.expected, (dict, list)):
            return self.expected
        return self.expected(ctx)
