from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class StrcasecmpTest(BaseTestCase):
    """Test case for $strcasecmp operator."""

    string1: Any = None
    string2: Any = None
    expr: Any = None  # Raw expression override


def _expr(test_case: StrcasecmpTest) -> dict[str, Any]:
    if test_case.expr is not None:
        return cast(dict[str, Any], test_case.expr)
    return {"$strcasecmp": [test_case.string1, test_case.string2]}
