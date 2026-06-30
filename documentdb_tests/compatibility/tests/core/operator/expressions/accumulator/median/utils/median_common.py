from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class MedianTest(BaseTestCase):
    """Test case for $median operator."""

    args: Any = None
