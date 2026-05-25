"""Shared test cases for diagnostic command tests."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class DiagnosticErrorTest(BaseTestCase):
    """Test case for diagnostic command error conditions.

    Attributes:
        command: The command document to execute.
        use_admin: If True, execute against the admin database.
    """

    command: Optional[Dict[str, Any]] = None
    use_admin: bool = True


@dataclass(frozen=True)
class DiagnosticPropertyTest(BaseTestCase):
    """Test case for diagnostic command response property checks.

    Attributes:
        checks: Mapping of dotted field paths to property check objects.
    """

    checks: Dict[str, Any] = field(default_factory=dict)
