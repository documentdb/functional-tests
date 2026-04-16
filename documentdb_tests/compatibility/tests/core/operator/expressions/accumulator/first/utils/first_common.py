from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class FirstTest(BaseTestCase):
    """Test case for $first operator."""

    value: Any = None
    document: Any = None
