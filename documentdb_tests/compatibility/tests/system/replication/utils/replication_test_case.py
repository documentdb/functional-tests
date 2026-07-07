"""Shared test case for replication command tests."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)


@dataclass(frozen=True)
class ReplicationTestCase(CommandTestCase):
    """Test case for replication command tests.

    Extends CommandTestCase with a ``use_admin`` flag that controls
    whether the command is executed against the admin database.

    The ``expected`` field supports an extended callable signature
    ``(ctx, result) -> dict`` for assertions that reference dynamic
    values from the command result itself.

    Attributes:
        use_admin: If True (the default), execute against the admin
            database via ``execute_admin_command``.  If False, execute
            against the test database via ``execute_command``.
    """

    use_admin: bool = True

    def build_expected(
        self,
        ctx: CommandContext,
        result: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]] | None:
        """Resolve expected, optionally passing the command result.

        If ``expected`` is a callable that accepts two parameters
        (ctx, result), the result is forwarded.  Otherwise, falls
        back to the parent implementation.
        """
        if callable(self.expected) and not isinstance(self.expected, (dict, list)):
            sig = inspect.signature(self.expected)
            if len(sig.parameters) == 2:
                return self.expected(ctx, result)
        return super().build_expected(ctx)
