"""Shared test case for diagnostic command tests."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class DiagnosticTestCase(BaseTestCase):
    """Test case for diagnostic command tests.

    Attributes:
        command: The command document to execute.
        use_admin: If True, execute against the admin database.
        checks: Mapping of dotted field paths to property check objects.
    """

    command: Optional[Dict[str, Any]] = None
    use_admin: bool = True
    checks: Dict[str, Any] = field(default_factory=dict)
