"""
Custom assertion helpers for functional tests.

Provides convenient assertion methods for common test scenarios.
"""

import math
import pprint
from typing import Any, Callable, Dict, Optional, Union

from bson import Decimal128, Int64

from documentdb_tests.framework.infra_exceptions import INFRA_EXCEPTION_TYPES as _INFRA_TYPES

_MAX_REPR_LEN = 1000


def _truncate_repr(obj: Any) -> str:
    """Format an object for error output, truncating if too long."""
    text = pprint.pformat(obj, width=100)
    if len(text) > _MAX_REPR_LEN:
        return text[:_MAX_REPR_LEN] + f"... (truncated, {len(text)} chars total)"
    return text


# BSON numeric types that must match exactly during comparison. Python's == operator
# treats some of these as equal (e.g. int and Int64) but they are distinct BSON types.
_NUMERIC_BSON_TYPES = (int, float, Int64, Decimal128)


def _strict_equal(a: Any, b: Any) -> bool:
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
        return all(_strict_equal(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            return False
        return all(_strict_equal(x, y) for x, y in zip(a, b))

    # Reject cross-type numeric comparisons.
    if type(a) is not type(b):
        if isinstance(a, _NUMERIC_BSON_TYPES) and isinstance(b, _NUMERIC_BSON_TYPES):
            return False
        return bool(a == b)

    # Distinguish -0.0 from 0.0.
    if isinstance(a, float) and a == 0.0 and a == b:
        return math.copysign(1.0, a) == math.copysign(1.0, b)
    return bool(a == b)


def _sort_if_list(value):
    """Return a sorted copy if value is a list, otherwise return unchanged."""
    if not isinstance(value, list):
        return value
    return sorted(value, key=lambda x: (type(x).__name__, repr(x)))


def _sort_fields(docs, fields):
    """Sort list values for the named fields in each document."""
    sorted_docs = []
    for doc in docs:
        doc = dict(doc)
        for field in fields:
            if field in doc:
                doc[field] = _sort_if_list(doc[field])
        sorted_docs.append(doc)
    return sorted_docs


class TestSetupError(AssertionError):
    """Raised when a test has invalid setup (bad arguments, malformed expected values)."""

    pass


def _format_exception_error(result: Exception) -> str:
    """Format a non-infra exception result into an assertion error message."""
    code = getattr(result, "code", None)
    msg = getattr(result, "details", {}).get("errmsg", str(result))
    return (
        f"[UNEXPECTED_ERROR] Expected success but got exception:\n"
        f"{_truncate_repr({'code': code, 'msg': msg})}\n"
    )


def assertSuccess(
    result: Union[Any, Exception],
    expected: Any,
    msg: Optional[str] = None,
    raw_res: bool = False,
    transform: Optional[Callable] = None,
    ignore_doc_order: bool = False,
    ignore_order_in: Optional[list[str]] = None,
):
    """
    Assert command succeeded and optionally check result.

    Args:
        result: Result from execute_command
        expected: Expected result value (required)
        msg: Custom assertion message (optional)
        raw_res: If asserting raw result. False by default,
            only compare content of ["cursor"]["firstBatch"]
        transform: Optional callback to transform result before comparison
        ignore_doc_order: If True, compare lists ignoring order (duplicates still matter)
    """
    if isinstance(result, Exception):
        if isinstance(result, _INFRA_TYPES):
            raise result
        raise AssertionError(_format_exception_error(result))

    if not raw_res:
        result = result["cursor"]["firstBatch"]

    if transform:
        result = transform(result)

    if ignore_order_in:
        expected = _sort_fields(expected, ignore_order_in)
        result = _sort_fields(result, ignore_order_in)

    error_text = "[RESULT_MISMATCH]"
    if msg:
        error_text += f" {msg}"
    error_text += f"\n\nExpected:\n{_truncate_repr(expected)}"
    error_text += f"\n\nActual:\n{_truncate_repr(result)}\n"

    _large = len(repr(result)) > _MAX_REPR_LEN or len(repr(expected)) > _MAX_REPR_LEN

    if ignore_doc_order:
        result = _sort_if_list(result)
        expected = _sort_if_list(expected)

    if _large:
        if not _strict_equal(result, expected):
            raise AssertionError(error_text)
    else:
        assert _strict_equal(result, expected), error_text


def assertSuccessPartial(
    result: Union[Any, Exception], expected: Dict[str, Any], msg: Optional[str] = None
):
    """Assert command succeeded and check only specified fields."""
    assertSuccess(result, expected, msg, raw_res=True, transform=partial_match(expected))


def partial_match(expected: Dict[str, Any]):
    """Create transform function that extracts only expected fields."""
    return lambda r: {k: r[k] for k in expected.keys() if k in r}


def assertFailure(
    result: Union[Any, Exception],
    expected: Dict[str, Any],
    msg: Optional[str] = None,
    transform: Optional[Callable] = None,
):
    """
    Assert command failed with expected error.

    Args:
        result: Result from execute_command
        expected: Expected error dict with 'code' and 'msg' keys
            (required unless transform is provided)
        msg: Custom assertion message (optional)
        transform: Optional callback to transform actual error before comparison
    """
    custom_msg = f" {msg}" if msg else ""

    # Check if error is in writeErrors field
    if isinstance(result, dict) and "writeErrors" in result:
        actual = {
            "code": result["writeErrors"][0]["code"],
            "msg": result["writeErrors"][0]["errmsg"],
        }
    elif isinstance(result, Exception):
        if isinstance(result, _INFRA_TYPES):
            raise result
        actual = {
            "code": getattr(result, "code", None),
            "msg": getattr(result, "details", {}).get("errmsg", str(result)),
        }
    else:
        error_text = (
            f"[UNEXPECTED_SUCCESS]{custom_msg} Expected error but got result:\n"
            f"{_truncate_repr(result)}\n"
        )
        raise AssertionError(error_text)

    if transform:
        actual = transform(actual)

    # Validate expected format only if no transform
    if not transform and (
        not isinstance(expected, dict) or "code" not in expected or "msg" not in expected
    ):
        raise TestSetupError(
            f"[TEST_EXCEPTION] Expected must be dict with 'code' and 'msg' keys, got: {expected}"
        )

    error_text = (
        f"[ERROR_MISMATCH]{custom_msg}\n\n"
        f"Expected:\n{_truncate_repr(expected)}\n\n"
        f"Actual:\n{_truncate_repr(actual)}\n"
    )
    if len(repr(actual)) > _MAX_REPR_LEN or len(repr(expected)) > _MAX_REPR_LEN:
        if not _strict_equal(actual, expected):
            raise AssertionError(error_text)
    else:
        assert _strict_equal(actual, expected), error_text


def assertFailureCode(result: Union[Any, Exception], expected_code: int, msg: Optional[str] = None):
    """Assert command failed and check only the code field."""
    expected = {"code": expected_code}
    assertFailure(result, expected, msg, transform=partial_match(expected))


def assertResult(
    result: Union[Any, Exception],
    expected: Any = None,
    error_code: Optional[int] = None,
    msg: Optional[str] = None,
    ignore_order_in: Optional[list[str]] = None,
    ignore_doc_order: bool = False,
    raw_res: bool = False,
):
    """
    Universal assertion that handles success and error cases.

    Args:
        result: Result from execute_command
        expected: Expected result documents (for success cases)
        error_code: Expected error code (for error cases)
        msg: Custom assertion message (optional)
        ignore_order_in: Field names whose list values should be sorted before
            comparison (for fields like set operation results where element
            order is unspecified)
        ignore_doc_order: If True, compare lists ignoring order (duplicates still matter)
        raw_res: If True, compare the raw result dict instead of
            extracting cursor.firstBatch

    Usage:
        assertResult(result, expected=[{"_id": 1}])  # Success case
        assertResult(result, error_code=16555)  # Error case
        assertResult(result, expected=[{"r": [3, 1, 2]}], ignore_order_in=["r"])
        assertResult(result, expected={"ok": 1.0}, raw_res=True)  # Raw command result
    """
    if error_code is not None:
        assertFailureCode(result, error_code, msg)
    else:
        assertSuccess(
            result,
            expected,
            msg,
            raw_res=raw_res,
            ignore_order_in=ignore_order_in,
            ignore_doc_order=ignore_doc_order,
        )


def assertExceptionType(
    result: Union[Any, Exception], expected_type: type, msg: Optional[str] = None
):
    """Assert that the result is an exception of the expected type.

    Useful for client-side errors (e.g. InvalidBSON) that don't carry a
    server error code.
    """
    custom_msg = f" {msg}" if msg else ""
    error_text = (
        f"[EXCEPTION_TYPE_MISMATCH]{custom_msg}\n"
        f"Expected exception type: {expected_type.__name__}\n"
        f"Actual: {type(result).__name__}: {result}\n"
    )
    if not isinstance(result, expected_type):
        raise AssertionError(error_text)


def _replace_nan(val: Any) -> Any:
    """Recursively replace NaN (float or Decimal128) with __NAN__ so that == works."""
    if isinstance(val, float) and math.isnan(val):
        return "__NaN__"
    if isinstance(val, Decimal128) and val.to_decimal().is_nan():
        return "__NaN__"
    if isinstance(val, dict):
        return {k: _replace_nan(v) for k, v in val.items()}
    if isinstance(val, list):
        return [_replace_nan(v) for v in val]
    return val


def assertSuccessNaN(
    result: Union[Any, Exception],
    expected: Any,
    msg: Optional[str] = None,
    ignore_doc_order: bool = False,
):
    """Assert command succeeded, treating NaN == NaN as True."""
    assertSuccess(
        result,
        _replace_nan(expected),
        msg=msg,
        ignore_doc_order=ignore_doc_order,
        transform=_replace_nan,
    )
