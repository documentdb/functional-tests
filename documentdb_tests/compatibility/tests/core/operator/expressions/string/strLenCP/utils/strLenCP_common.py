from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class StrLenCPTest(BaseTestCase):
    """Test case for $strLenCP operator."""

    value: Any = None
    expr: Any = None  # Raw expression override


def _expr(test_case: StrLenCPTest) -> dict[str, Any]:
    if test_case.expr is not None:
        return cast(dict[str, Any], test_case.expr)
    return {"$strLenCP": test_case.value}
