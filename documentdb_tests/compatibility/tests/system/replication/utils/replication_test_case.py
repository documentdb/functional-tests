"""Shared test case for replication command tests."""

from __future__ import annotations

from dataclasses import dataclass

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandTestCase,
)


@dataclass(frozen=True)
class ReplicationTestCase(CommandTestCase):
    """Test case for replication command tests.

    Extends CommandTestCase with a ``use_admin`` flag that controls
    whether the command is executed against the admin database.

    Attributes:
        use_admin: If True (the default), execute against the admin
            database via ``execute_admin_command``.  If False, execute
            against the test database via ``execute_command``.
    """

    use_admin: bool = True
