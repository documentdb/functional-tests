"""
Custom assertion helpers for functional tests.

Provides convenient assertion methods for common test scenarios.
"""

import pprint
from typing import Any, Callable, Dict, Optional, Union

from documentdb_tests.framework.infra_exceptions import INFRA_EXCEPTION_TYPES as _INFRA_TYPES


class TestSetupError(AssertionError):
    """Raised when a test has invalid setup (bad arguments, malformed expected values)."""

    pass


def _format_exception_error(result: Exception) -> str:
    """Format a non-infra exception result into an assertion error message."""
    code = getattr(result, "code", None)
    msg = getattr(result, "details", {}).get("errmsg", str(result))
    return (
        f"[UNEXPECTED_ERROR] Expected success but got exception:\n"
        f"{pprint.pformat({'code': code, 'msg': msg}, width=100)}\n"
    )


def assertSuccess(
    result: Union[Any, Exception],
    expected: Any,
    msg: str = None,
    raw_res: bool = False,
    transform: Optional[Callable] = None,
    ignore_doc_order: bool = False,
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
        ignore_doc_order: If True, compare lists as sets (order-independent)
    """
    if isinstance(result, Exception):
        if isinstance(result, _INFRA_TYPES):
            raise result
        raise AssertionError(_format_exception_error(result))

    if not raw_res:
        result = result["cursor"]["firstBatch"]

    if transform:
        result = transform(result)

    error_text = "[RESULT_MISMATCH]"
    if msg:
        error_text += f" {msg}"
    error_text += f"\n\nExpected:\n{pprint.pformat(expected, width=100)}"
    error_text += f"\n\nActual:\n{pprint.pformat(result, width=100)}\n"

    if ignore_doc_order and isinstance(result, list) and isinstance(expected, list):
        assert sorted(result, key=lambda x: str(x)) == sorted(
            expected, key=lambda x: str(x)
        ), error_text
    else:
        assert result == expected, error_text


def assertSuccessPartial(result: Union[Any, Exception], expected: Dict[str, Any], msg: str = None):
    """Assert command succeeded and check only specified fields."""
    assertSuccess(result, expected, msg, raw_res=True, transform=partial_match(expected))


def partial_match(expected: Dict[str, Any]):
    """Create transform function that extracts only expected fields."""
    return lambda r: {k: r[k] for k in expected.keys() if k in r}


def assertFailure(
    result: Union[Any, Exception],
    expected: Dict[str, Any],
    msg: str = None,
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
            f"{pprint.pformat(result, width=100)}\n"
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
        f"Expected:\n{pprint.pformat(expected, width=100)}\n\n"
        f"Actual:\n{pprint.pformat(actual, width=100)}\n"
    )
    assert actual == expected, error_text


def assertFailureCode(result: Union[Any, Exception], expected_code: int, msg: str = None):
    """Assert command failed and check only the code field."""
    expected = {"code": expected_code}
    assertFailure(result, expected, msg, transform=partial_match(expected))


def assertResult(
    result: Union[Any, Exception], expected: Any = None, error_code: int = None, msg: str = None
):
    """
    Universal assertion that handles success and error cases.

    Args:
        result: Result from execute_command
        expected: Expected result value.
        error_code: Expected error code (mutually exclusive with expected)
        msg: Custom assertion message (optional)

    Usage:
        assertResult(result, expected=5)  # Success case
        assertResult(result, error_code=16555)  # Error case
    """
    if error_code is not None:
        # Error case
        assertFailureCode(result, error_code, msg)
    else:
        # Success case
        assertSuccess(result, [{"result": expected}], msg)
