from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

from .utils.split_common import (
    SplitTest,
    _expr,
)

# Property [Null Propagation]: if either argument is null or missing, the result
# is null.
SPLIT_NULL_TESTS: list[SplitTest] = [
    SplitTest(
        "null_string",
        string=None,
        delimiter="-",
        expected=None,
        msg="$split should return null when string is null",
    ),
    SplitTest(
        "null_delimiter",
        string="hello-world",
        delimiter=None,
        expected=None,
        msg="$split should return null when delimiter is null",
    ),
    SplitTest(
        "null_both",
        string=None,
        delimiter=None,
        expected=None,
        msg="$split should return null when both arguments are null",
    ),
    SplitTest(
        "missing_string",
        string=MISSING,
        delimiter="-",
        expected=None,
        msg="$split should return null when string is missing",
    ),
    SplitTest(
        "missing_delimiter",
        string="hello-world",
        delimiter=MISSING,
        expected=None,
        msg="$split should return null when delimiter is missing",
    ),
    SplitTest(
        "missing_both",
        string=MISSING,
        delimiter=MISSING,
        expected=None,
        msg="$split should return null when both arguments are missing",
    ),
    SplitTest(
        "null_string_missing_delimiter",
        string=None,
        delimiter=MISSING,
        expected=None,
        msg="$split should return null when string is null and delimiter is missing",
    ),
    SplitTest(
        "missing_string_null_delimiter",
        string=MISSING,
        delimiter=None,
        expected=None,
        msg="$split should return null when string is missing and delimiter is null",
    ),
]

# Property [Null Precedence over Type Error]: null in either position takes
# precedence over a type error in the other position.
SPLIT_NULL_PRECEDENCE_TESTS: list[SplitTest] = [
    SplitTest(
        "null_precedes_type_error_in_delimiter",
        string=None,
        delimiter=42,
        expected=None,
        msg="$split should return null when string is null even if delimiter has wrong type",
    ),
    SplitTest(
        "null_precedes_type_error_in_string",
        string=42,
        delimiter=None,
        expected=None,
        msg="$split should return null when delimiter is null even if string has wrong type",
    ),
    SplitTest(
        "missing_precedes_type_error_in_delimiter",
        string=MISSING,
        delimiter=42,
        expected=None,
        msg="$split should return null when string is missing even if delimiter has wrong type",
    ),
    SplitTest(
        "missing_precedes_type_error_in_string",
        string=42,
        delimiter=MISSING,
        expected=None,
        msg="$split should return null when delimiter is missing even if string has wrong type",
    ),
]

# Property [Null Precedence over Empty Delimiter Error]: null in either position
# takes precedence over the empty delimiter error.
SPLIT_NULL_EMPTY_DELIM_PRECEDENCE_TESTS: list[SplitTest] = [
    SplitTest(
        "null_precedes_empty_delim",
        string=None,
        delimiter="",
        expected=None,
        msg="$split should return null when string is null even with empty delimiter",
    ),
    SplitTest(
        "missing_precedes_empty_delim",
        string=MISSING,
        delimiter="",
        expected=None,
        msg="$split should return null when string is missing even with empty delimiter",
    ),
]

SPLIT_NULL_ALL_TESTS = (
    SPLIT_NULL_TESTS + SPLIT_NULL_PRECEDENCE_TESTS + SPLIT_NULL_EMPTY_DELIM_PRECEDENCE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SPLIT_NULL_ALL_TESTS))
def test_split_null_cases(collection, test_case: SplitTest):
    """Test $split null propagation and null precedence cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
