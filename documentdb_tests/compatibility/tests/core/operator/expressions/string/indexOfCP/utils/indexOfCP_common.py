from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class IndexOfCPTest(BaseTestCase):
    """Test case for $indexOfCP operator."""

    # Uses args because start and end are optional positional parameters.
    # Named fields would be ambiguous about whether an unset optional
    # should be omitted from the array or passed as None.
    args: list[Any] = None  # type: ignore[assignment]
