from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import INDEXOFCP_SUBSTRING_TYPE_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

from .utils.indexOfCP_common import (
    IndexOfCPTest,
)

# Argument shapes for null/missing first-arg tests. _PLACEHOLDER is replaced with None or MISSING.
_PLACEHOLDER = object()
_NULL_PATTERNS = [
    ([_PLACEHOLDER, "hello"], "first_arg"),
    ([_PLACEHOLDER, "hello", 0], "first_arg_with_start"),
    ([_PLACEHOLDER, "hello", 0, 5], "first_arg_with_start_end"),
    # First arg null/missing takes precedence over second arg null (which would otherwise error).
    ([_PLACEHOLDER, None], "precedence_second_null"),
    # First arg null/missing takes precedence over start null (which would otherwise error).
    ([_PLACEHOLDER, "sub", None], "precedence_start_null"),
    # First arg null/missing takes precedence over end null (which would otherwise error).
    ([_PLACEHOLDER, "sub", 0, None], "precedence_end_null"),
    # First arg null/missing takes precedence over errors from other null args.
    ([_PLACEHOLDER, None, None], "precedence_all_null"),
    ([_PLACEHOLDER, None, None, None], "precedence_all_four_null"),
]


def _build_null_tests(null_value, prefix) -> list[IndexOfCPTest]:
    return [
        IndexOfCPTest(
            f"{prefix}_{suffix}",
            args=[null_value if a is _PLACEHOLDER else a for a in args],
            expected=None,
            msg=f"$indexOfCP should return null when {prefix} {suffix}",
        )
        for args, suffix in _NULL_PATTERNS
    ]


# Property [Null Behavior]: when the first argument is null, the result is null regardless of other
# arguments.
INDEXOFCP_NULL_TESTS = _build_null_tests(None, "null")


# Property [Missing Behavior]: when the first argument references a missing field, the result is
# null regardless of other arguments.
INDEXOFCP_MISSING_TESTS = _build_null_tests(MISSING, "missing")

# Property [Null and Missing Errors - Precedence]: second arg error takes precedence over
# third/fourth arg errors.
INDEXOFCP_NULL_MISSING_PRECEDENCE_TESTS: list[IndexOfCPTest] = [
    IndexOfCPTest(
        "null_err_second_precedes_third",
        args=["hello", None, None],
        error_code=INDEXOFCP_SUBSTRING_TYPE_ERROR,
        msg="$indexOfCP null substring error should precede null start error",
    ),
    IndexOfCPTest(
        "null_err_second_precedes_fourth",
        args=["hello", None, 0, None],
        error_code=INDEXOFCP_SUBSTRING_TYPE_ERROR,
        msg="$indexOfCP null substring error should precede null end error",
    ),
    IndexOfCPTest(
        "null_err_second_precedes_all",
        args=["hello", None, None, None],
        error_code=INDEXOFCP_SUBSTRING_TYPE_ERROR,
        msg="$indexOfCP null substring error should precede all other null errors",
    ),
    IndexOfCPTest(
        "missing_err_second_precedes_third",
        args=["hello", MISSING, None],
        error_code=INDEXOFCP_SUBSTRING_TYPE_ERROR,
        msg="$indexOfCP missing substring error should precede null start error",
    ),
    IndexOfCPTest(
        "missing_err_second_precedes_fourth",
        args=["hello", MISSING, 0, None],
        error_code=INDEXOFCP_SUBSTRING_TYPE_ERROR,
        msg="$indexOfCP missing substring error should precede null end error",
    ),
    IndexOfCPTest(
        "missing_err_second_precedes_all",
        args=["hello", MISSING, None, None],
        error_code=INDEXOFCP_SUBSTRING_TYPE_ERROR,
        msg="$indexOfCP missing substring error should precede all other null errors",
    ),
]

INDEXOFCP_NULL_AND_MISSING_TESTS = (
    INDEXOFCP_NULL_TESTS + INDEXOFCP_MISSING_TESTS + INDEXOFCP_NULL_MISSING_PRECEDENCE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(INDEXOFCP_NULL_AND_MISSING_TESTS))
def test_indexofcp_null(collection, test_case: IndexOfCPTest):
    """Test $indexOfCP null and missing behavior."""
    result = execute_expression(collection, {"$indexOfCP": test_case.args})
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
