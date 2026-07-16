"""Utility for expanding ExpressionTestCase lists with $convert parity variants.

$convert is the general form behind $toInt, $toBool, $toString, etc.
Use ``with_convert_variants`` to add a $convert-equivalent test case alongside
each native-operator test case, without changing ExpressionTestCase or test
functions.
"""

from __future__ import annotations

from dataclasses import replace

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.framework.lazy_payload import Lazy


def with_convert_variants(
    tests: list[ExpressionTestCase],
    operator_key: str,
    target_type: str,
) -> list[ExpressionTestCase]:
    """Return *tests* interleaved with a $convert-equivalent for each eligible case.

    For each test case whose ``expression`` is a plain dict containing
    ``operator_key`` (e.g. ``"$toBool"``), a sibling case is appended
    immediately after it with::

        expression={"$convert": {"input": <original input>, "to": target_type}}

    The sibling inherits all other fields (``expected``, ``error_code``,
    ``msg``, ``marks``) unchanged, and its ``id`` is prefixed with
    ``"convert_"``.

    Cases are skipped when:

    - ``expression`` is a ``Lazy`` payload (size-limit tests — the large value
      is the point, not type-conversion parity).
    - ``expression`` is not a dict or does not contain ``operator_key`` (e.g.
      arity tests that pass an array as the whole argument).

    Callers should not pass arity test lists to this function, since arity is
    operator-specific behaviour that $convert does not share.
    """
    result: list[ExpressionTestCase] = []
    for t in tests:
        result.append(t)
        expr = t.expression
        if isinstance(expr, Lazy) or not isinstance(expr, dict):
            continue
        if operator_key not in expr:
            continue
        result.append(
            replace(
                t,
                id=f"convert_{t.id}",
                expression={"$convert": {"input": expr[operator_key], "to": target_type}},
            )
        )
    return result
