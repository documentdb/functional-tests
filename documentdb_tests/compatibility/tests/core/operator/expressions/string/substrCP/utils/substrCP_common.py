from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from documentdb_tests.framework.test_case import BaseTestCase

# Sentinel for "omit this parameter from the expression." Distinct from None
# (which means pass null).
_OMIT = object()


@dataclass(frozen=True)
class SubstrCPTest(BaseTestCase):
    """Test case for $substrCP operator."""

    string: Any = None
    index: Any = 0
    count: Any = 1
    raw_args: Any = _OMIT  # Raw operator argument override for arity tests.


def _expr(test_case: SubstrCPTest) -> dict:
    if test_case.raw_args is not _OMIT:
        return {"$substrCP": test_case.raw_args}
    return {"$substrCP": [test_case.string, test_case.index, test_case.count]}
