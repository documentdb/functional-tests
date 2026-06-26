"""Shared test case for administration command tests."""

from dataclasses import dataclass
from typing import Any, Optional

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class AdminTestCase(BaseTestCase):
    """Test case for an administration command.

    Attributes:
        command: The command document to execute.
        setup_commands: Commands to run before the test command.
    """

    command: Optional[dict[str, Any]] = None
    setup_commands: tuple[dict[str, Any], ...] = ()
