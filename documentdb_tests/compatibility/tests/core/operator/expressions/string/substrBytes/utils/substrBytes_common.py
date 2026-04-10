from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.framework.test_case import BaseTestCase

from ...substr.test_operator_substr import (
    SUBSTR_OPERATOR,
)

# Sentinel for "omit this parameter from the expression." Distinct from None
# (which means pass null).
_OMIT = object()


@dataclass(frozen=True)
class SubstrBytesTest(BaseTestCase):
    """Test case for $substrBytes operator."""

    string: Any = None
    byte_index: Any = None
    byte_count: Any = None
    raw_args: Any = _OMIT  # Raw operator argument override for arity tests.


# $substr is a deprecated alias for $substrBytes; both are tested here.
OPERATORS = [
    pytest.param("$substrBytes", id="substrBytes"),
    SUBSTR_OPERATOR,
]


def _expr(test_case: SubstrBytesTest, op: str) -> dict:
    if test_case.raw_args is not _OMIT:
        return {op: test_case.raw_args}
    return {op: [test_case.string, test_case.byte_index, test_case.byte_count]}
