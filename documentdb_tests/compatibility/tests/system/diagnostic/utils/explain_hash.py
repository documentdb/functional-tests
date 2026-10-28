"""Helpers for comparing the query hashes that explain reports.

The hash tests run explain on two queries and assert that their hashes match
(same shape) or differ (different shape). The helpers here keep the explain
result raw and do every check, including that the hash is present at all,
through a single ``assertProperties`` call. A failed explain or a missing hash
field is therefore reported as an assertion failure instead of an error raised
before the assertion.
"""

from __future__ import annotations

from typing import Any, Union

from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.property_checks import Eq, Ne, NonEmptyStr

PLAN_CACHE_SHAPE_HASH = "queryPlanner.planCacheShapeHash"
"""Dotted path of the plan cache shape hash in a standard explain result."""

QUERY_SHAPE_HASH = "queryShapeHash"
"""Dotted path of the top-level query shape hash in an explain result."""


def _lookup(result: Any, path: str) -> Any:
    """Return the value at a dotted path (dict keys and list indices), or None when absent."""
    value: Any = result
    for part in path.split("."):
        if isinstance(value, list) and part.isdigit() and int(part) < len(value):
            value = value[int(part)]
        elif isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return None
    return value


def assert_hash_relation(
    result_a: Any,
    result_b: Any,
    paths: Union[str, tuple[str, ...]],
    same: bool,
    msg: str,
) -> None:
    """Assert both explain results report a hash, and that the two hashes match or differ.

    Args:
        result_a: Raw explain result (or exception) for the first query.
        result_b: Raw explain result (or exception) for the second query.
        paths: Dotted path of the hash, or several candidate paths tried in
            order (for explain output whose layout depends on the pipeline).
        same: True to assert the hashes are equal, False to assert they differ.
        msg: Failure message.
    """
    candidates = (paths,) if isinstance(paths, str) else paths
    for result in (result_a, result_b):
        if isinstance(result, Exception):
            # The failed explain is the result under test: assert on it and stop,
            # so it is reported once rather than again as two missing hashes.
            assertProperties(result, {candidates[0]: NonEmptyStr()}, msg=msg, raw_res=True)
            return
    hashes: dict[str, str] = {}
    for key, result in (("hash_a", result_a), ("hash_b", result_b)):
        for path in candidates:
            value = _lookup(result, path)
            if value is not None:
                hashes[key] = str(value)
                break
    # Compare only when the second hash exists; its absence is reported on its own.
    checks_a: list[Any] = [NonEmptyStr()]
    if "hash_b" in hashes:
        checks_a.append(Eq(hashes["hash_b"]) if same else Ne(hashes["hash_b"]))
    assertProperties(
        hashes,
        {"hash_a": checks_a, "hash_b": NonEmptyStr()},
        msg=f"{msg} (hash at {' or '.join(candidates)})",
        raw_res=True,
    )
