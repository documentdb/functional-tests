from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class ToLowerTest(BaseTestCase):
    """Test case for $toLower operator."""

    value: Any = None


def _expr(test_case: ToLowerTest) -> dict[str, Any]:
    return {"$toLower": test_case.value}
