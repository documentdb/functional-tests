"""Test case with setup/cleanup lifecycle for settings-based commands.

``SettingsTestCase`` extends ``CommandTestCase`` with ``setup_commands``
and ``cleanup`` hooks for commands that require prerequisite operations
(e.g. creating a query setting before testing removal) and post-test
teardown (e.g. removing cluster-wide query settings).

Results returned by each setup command are appended to
``setup_results`` so that later lambdas (``command``, ``expected``,
etc.) can reference values produced during setup.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)


@dataclass(frozen=True)
class SettingsTestCase(CommandTestCase):
    """CommandTestCase with setup-command and cleanup lifecycle.

    Attributes:
        setup_commands: Optional callable ``(CommandContext) -> list[dict]``
            returning commands to execute **before** the main command.
            Each command's result is appended to
            ``CommandContext.setup_results`` by the runner.
        cleanup: Optional callable ``(CommandContext) -> list[dict]``
            returning commands to run after the test.  Each dict is
            passed to the executor inside a try/except so cleanup
            failures are silently ignored.
    """

    setup_commands: Callable[[CommandContext], list[dict[str, Any]]] | None = None
    cleanup: Callable[[CommandContext], list[dict[str, Any]]] | None = None

    def build_setup(self, ctx: CommandContext) -> list[dict[str, Any]]:
        """Resolve setup commands from the callable, or return empty list."""
        if self.setup_commands is None:
            return []
        return self.setup_commands(ctx)

    def build_cleanup(self, ctx: CommandContext) -> list[dict[str, Any]]:
        """Resolve cleanup commands from the callable, or return empty list."""
        if self.cleanup is None:
            return []
        return self.cleanup(ctx)
