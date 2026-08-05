from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class BitOrTest(BaseTestCase):
    """Test case for $bitOr operator."""

    args: Any = None
