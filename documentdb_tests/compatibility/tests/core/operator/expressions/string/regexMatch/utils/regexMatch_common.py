from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from documentdb_tests.framework.test_case import BaseTestCase

# Sentinel for "omit this parameter from the expression." Distinct from None (which means pass null)
# and MISSING (which means reference a missing field).
_OMIT = object()


@dataclass(frozen=True)
class RegexMatchTest(BaseTestCase):
    """Test case for $regexMatch operator."""

    input: Any = None
    regex: Any = None
    options: Any = _OMIT
    expr: Any = None  # Raw expression override for syntax tests


def _expr(test_case: RegexMatchTest) -> dict[str, Any]:
    if test_case.expr is not None:
        return cast(dict[str, Any], test_case.expr)
    params: dict[str, Any] = {"input": test_case.input, "regex": test_case.regex}
    if test_case.options is not _OMIT:
        params["options"] = test_case.options
    return {"$regexMatch": params}
