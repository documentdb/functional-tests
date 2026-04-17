# $convert is the general form behind $toString, $toInt, $toDouble, etc.
# Each to* operator's tests are parametrized over both the native operator
# and the equivalent $convert expression using the helpers below.
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

import pytest

from documentdb_tests.framework.test_case import BaseTestCase

# Public API for to* operator test files.
__all__ = ["convert_expr", "convert_format_auto_expr", "convert_field_expr"]


# Sentinel for "omit this parameter from the expression." Distinct from None
# (which means pass null) and MISSING (which means reference a missing field).
_OMIT = object()


@dataclass(frozen=True)
class ConvertTest(BaseTestCase):
    """Test case for $convert operator."""

    input: Any = None
    to: Any = None
    byte_order: Any = _OMIT
    format: Any = _OMIT
    on_error: Any = _OMIT
    on_null: Any = _OMIT
    expr: Any = None  # Raw expression override (for syntax tests)


def _build_convert(
    input: Any,
    to: Any,
    on_null: Any = _OMIT,
    on_error: Any = _OMIT,
    fmt: Any = _OMIT,
    byte_order: Any = _OMIT,
) -> dict[str, Any]:
    doc: dict[str, Any] = {"input": input, "to": to}
    if byte_order is not _OMIT:
        doc["byteOrder"] = byte_order
    if fmt is not _OMIT:
        doc["format"] = fmt
    if on_error is not _OMIT:
        doc["onError"] = on_error
    if on_null is not _OMIT:
        doc["onNull"] = on_null
    return {"$convert": doc}


def _expr(test_case: ConvertTest) -> dict[str, Any]:
    if test_case.expr is not None:
        return dict(test_case.expr)
    return _build_convert(
        input=test_case.input,
        to=test_case.to,
        on_null=test_case.on_null,
        on_error=test_case.on_error,
        fmt=test_case.format,
        byte_order=test_case.byte_order,
    )


def convert_expr(target_type: str):
    """Return a pytest.param that builds a $convert expression for the given target type."""
    return pytest.param(
        lambda tc: {"$convert": {"input": tc.value, "to": target_type}},
        id="convert",
    )


def convert_format_auto_expr(target_type: str):
    """Return a pytest.param that builds a $convert expression with format: 'auto' (needed for string/binData conversions)."""  # noqa: E501
    return pytest.param(
        lambda tc: {
            "$convert": {
                "input": tc.value,
                "to": target_type,
                "format": "auto",
            }
        },
        id="convert_format_auto",
    )


def convert_field_expr(target_type: str):
    """Return a pytest.param that builds a $convert expression for a field path."""
    return pytest.param(
        lambda field: {"$convert": {"input": field, "to": target_type}},
        id="convert",
    )


# Sentinel for pattern templates; replaced with null/missing.
_PLACEHOLDER = object()


def _build_null_tests(
    patterns: list[ConvertTest], null_value, prefix, field: str = "input"
) -> list[ConvertTest]:
    result: list[ConvertTest] = []
    for t in patterns:
        assert t.msg is not None
        result.append(
            replace(
                t,
                id=f"{prefix}_{t.id}",
                msg=t.msg.format(prefix=prefix),
                **{field: null_value},
            )
        )
    return result
