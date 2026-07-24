"""Detection of oversized test payloads.

A test's parametrized data is kept by pytest for the whole session and copied
onto every xdist worker, so a large value embedded there is a heavy, needless
footprint. This measures a value's size so the collection guardrail can reject
such tests and point them at ``lazy``, which defers construction to test time.
"""

from __future__ import annotations

import sys
from typing import Any

from documentdb_tests.framework.lazy_payload import Lazy

# A test's parametrized data should not embed a payload larger than this.
PARAM_SIZE_LIMIT_BYTES = 1_000_000


def _deep_size(value: Any, seen: set[int], budget: int) -> int:
    """Sum the byte size of ``value``, stopping early once it exceeds ``budget``.

    A ``Lazy`` is treated as its small placeholder, not the value it would build,
    so deferred payloads count as tiny.
    """
    if isinstance(value, Lazy) or id(value) in seen:
        return 0
    seen.add(id(value))
    total = sys.getsizeof(value, 0)
    if isinstance(value, (str, bytes, bytearray)):
        return total
    if isinstance(value, dict):
        for key, item in value.items():
            total += _deep_size(key, seen, budget) + _deep_size(item, seen, budget)
            if total > budget:
                return total
    elif isinstance(value, (list, tuple, set, frozenset)):
        for item in value:
            total += _deep_size(item, seen, budget)
            if total > budget:
                return total
    elif hasattr(value, "__dict__"):
        total += _deep_size(vars(value), seen, budget)
    return total


def exceeds_size_limit(value: Any) -> bool:
    """Return whether ``value``'s byte size exceeds ``PARAM_SIZE_LIMIT_BYTES``.

    Sizing stops as soon as the limit is passed, so ordinary small values cost
    only a shallow walk.
    """
    return _deep_size(value, set(), PARAM_SIZE_LIMIT_BYTES) > PARAM_SIZE_LIMIT_BYTES
