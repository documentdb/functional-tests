"""Shared test case for session command tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class SessionCommandTestCase(BaseTestCase):
    """Test case for session command tests.

    Session commands (commitTransaction, abortTransaction, etc.) run against
    the admin database and do not reference a specific collection. The command
    is always a plain dict.

    Attributes:
        command: The command document to execute against the admin database.
    """

    command: Optional[Dict[str, Any]] = None
