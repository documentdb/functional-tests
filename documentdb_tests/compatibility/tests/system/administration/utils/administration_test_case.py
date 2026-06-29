from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class AdministrationTestCase(BaseTestCase):
    """Test case for administration command tests.

    Attributes:
        command: The command dict to execute.
        checks: Mapping of dotted field paths to property check objects.
    """

    command: Optional[Dict[str, Any]] = None
    checks: Dict[str, Any] = field(default_factory=dict)
