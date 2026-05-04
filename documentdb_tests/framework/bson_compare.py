"""Strict equality for BSON values."""

from __future__ import annotations

import math
from typing import Any

from bson import Decimal128, Int64

# BSON numeric types that must match exactly during comparison.
_NUMERIC_BSON_TYPES = (int, float, Int64, Decimal128)


def strict_equal(a: Any, b: Any) -> bool:
    """Equality with stricter semantics for BSON numeric types.

    Standard == considers -0.0 and 0.0 equal per IEEE 754, but the sign
    of zero is preserved through arithmetic and operators like $toString.
    A sign mismatch would cause downstream behavior differences that
    these tests exist to detect, so we compare the sign bit explicitly
    when both values are zero floats.

    Python's == also considers int and Int64 equal, but they are distinct
    BSON types. We reject cross-type numeric comparisons so that test
    expectations must specify the exact BSON type returned by the server.
    """
    # Recurse into containers.
    if isinstance(a, dict) and isinstance(b, dict):
        if a.keys() != b.keys():
            return False
        return all(strict_equal(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            return False
        return all(strict_equal(x, y) for x, y in zip(a, b))

    # Reject cross-type numeric comparisons.
    if type(a) is not type(b):
        if isinstance(a, _NUMERIC_BSON_TYPES) and isinstance(b, _NUMERIC_BSON_TYPES):
            return False
        return bool(a == b)

    # Distinguish -0.0 from 0.0.
    if isinstance(a, float) and a == 0.0 and a == b:
        return math.copysign(1.0, a) == math.copysign(1.0, b)
    return bool(a == b)
