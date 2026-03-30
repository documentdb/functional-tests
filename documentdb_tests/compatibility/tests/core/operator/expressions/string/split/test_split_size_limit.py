from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import STRING_SIZE_LIMIT_ERROR
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.framework.test_constants import STRING_SIZE_LIMIT_BYTES
from documentdb_tests.compatibility.tests.core.operator.expressions.string.split.utils.split_common import (
    SplitTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import execute_expression

# Property [String Size Limit - Success]: input one byte under the limit is accepted.
SPLIT_SIZE_LIMIT_SUCCESS_TESTS: list[SplitTest] = [
    SplitTest(
        "size_string_one_under",
        string="a" * (STRING_SIZE_LIMIT_BYTES - 1),
        delimiter="-",
        expected=["a" * (STRING_SIZE_LIMIT_BYTES - 1)],
        msg="$split should accept input string one byte under the size limit",
    ),
    SplitTest(
        "size_delim_one_under",
        string="hello",
        delimiter="a" * (STRING_SIZE_LIMIT_BYTES - 1),
        expected=["hello"],
        msg="$split should accept delimiter one byte under the size limit",
    ),
]


# Property [String Size Limit Error]: an input string or delimiter of
# Property [String Size Limit - Error]: input or delimiter at the size limit produces an error.
SPLIT_SIZE_LIMIT_ERROR_TESTS: list[SplitTest] = [
    SplitTest(
        "size_limit_input_at_boundary",
        string="a" * STRING_SIZE_LIMIT_BYTES,
        delimiter="-",
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$split should reject input string at the size limit",
    ),
    SplitTest(
        "size_limit_delim_at_boundary",
        string="hello",
        delimiter="a" * STRING_SIZE_LIMIT_BYTES,
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$split should reject delimiter at the size limit",
    ),
    SplitTest(
        "size_limit_input_2byte",
        string="\u00e9" * (STRING_SIZE_LIMIT_BYTES // 2),
        delimiter="-",
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$split should reject 2-byte char input totaling the size limit",
    ),
    # Sub-expression producing oversized result is caught before $split runs.
    SplitTest(
        "size_limit_input_subexpr",
        string={
            "$concat": ["a" * (STRING_SIZE_LIMIT_BYTES // 2), "a" * (STRING_SIZE_LIMIT_BYTES // 2)]
        },
        delimiter="-",
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$split should reject sub-expression producing oversized string",
    ),
]

SPLIT_SIZE_LIMIT_TESTS = SPLIT_SIZE_LIMIT_SUCCESS_TESTS + SPLIT_SIZE_LIMIT_ERROR_TESTS


@pytest.mark.parametrize("test_case", pytest_params(SPLIT_SIZE_LIMIT_TESTS))
def test_split_size_limit_cases(collection, test_case: SplitTest):
    """Test $split string size limit cases."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
