from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class PercentileTest(BaseTestCase):
    """Test case for the $percentile expression operator."""

    spec: Any = None  # full {input, p, method} document, or a malformed variant
    document: Any = None  # optional doc to insert for field-reference cases


def percentile_spec(input, p=(0.5,), method="approximate"):
    """Build a valid $percentile spec. Pass a raw dict for malformed-spec cases."""
    return {"input": input, "p": list(p), "method": method}
