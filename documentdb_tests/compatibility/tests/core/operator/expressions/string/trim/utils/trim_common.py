from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from documentdb_tests.framework.test_case import BaseTestCase

# Sentinel for "omit this parameter from the expression." Distinct from None (which means pass
# null) and MISSING (which means reference a missing field).
_OMIT = object()


@dataclass(frozen=True)
class TrimTest(BaseTestCase):
    """Test case for $trim operator."""

    input: Any = None
    chars: Any = _OMIT
    expr: Any = None  # Raw expression override for syntax tests


def _expr(test_case: TrimTest) -> dict[str, Any]:
    if test_case.expr is not None:
        return cast(dict[str, Any], test_case.expr)
    params: dict[str, Any] = {"input": test_case.input}
    if test_case.chars is not _OMIT:
        params["chars"] = test_case.chars
    return {"$trim": params}
