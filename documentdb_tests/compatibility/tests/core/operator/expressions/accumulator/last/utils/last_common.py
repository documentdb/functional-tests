from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class LastTest(BaseTestCase):
    """Test case for $last operator."""

    value: Any = None
    document: Any = None
