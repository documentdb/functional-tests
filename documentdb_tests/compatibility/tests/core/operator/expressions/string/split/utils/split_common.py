from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class SplitTest(BaseTestCase):
    """Test case for $split operator."""

    string: Any = None
    delimiter: Any = None
    expr: Any = None  # Raw expression override for arity/syntax tests


def _expr(test_case: SplitTest) -> dict[str, Any]:
    if test_case.expr is not None:
        return cast(dict[str, Any], test_case.expr)
    return {"$split": [test_case.string, test_case.delimiter]}
