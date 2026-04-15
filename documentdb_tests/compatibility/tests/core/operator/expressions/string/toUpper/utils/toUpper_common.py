from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class ToUpperTest(BaseTestCase):
    """Test case for $toUpper operator."""

    value: Any = None


def _expr(test_case: ToUpperTest) -> dict[str, Any]:
    return {"$toUpper": test_case.value}
