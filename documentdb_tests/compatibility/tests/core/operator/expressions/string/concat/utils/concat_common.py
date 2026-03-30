from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class ConcatTest(BaseTestCase):
    args: list[Any] = None  # type: ignore[assignment]
