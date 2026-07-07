"""Shared test case for administration command tests."""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class AdminTestCase(BaseTestCase):
    """Test case for administration command tests.

    Inherits ``id``, ``expected``, ``error_code``, ``msg``, and ``marks`` from
    ``BaseTestCase``.

    Attributes:
        command: The command document to execute.
        use_admin: If True, execute against the admin database.
    """

    command: Optional[Dict[str, Any]] = None
    use_admin: bool = True
