from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class ReplaceOneTest(BaseTestCase):
    """Test case for $replaceOne operator."""

    input: Any = None
    find: Any = None
    replacement: Any = None
    expr: Any = None  # Raw expression override for syntax tests


def _expr(test_case: ReplaceOneTest) -> dict[str, Any]:
    if test_case.expr is not None:
        return cast(dict[str, Any], test_case.expr)
    return {
        "$replaceOne": {
            "input": test_case.input,
            "find": test_case.find,
            "replacement": test_case.replacement,
        }
    }
