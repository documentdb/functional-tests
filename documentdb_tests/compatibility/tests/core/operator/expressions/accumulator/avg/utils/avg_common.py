from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class AvgTest(BaseTestCase):
    """Test case for $avg operator."""

    args: Any = None
