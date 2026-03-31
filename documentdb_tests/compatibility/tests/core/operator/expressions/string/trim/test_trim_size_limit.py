from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import STRING_SIZE_LIMIT_ERROR
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.framework.test_constants import STRING_SIZE_LIMIT_BYTES
from documentdb_tests.compatibility.tests.core.operator.expressions.string.trim.utils.trim_common import (
    TrimTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import execute_expression

# Property [String Size Limit - Success]: input one byte under the limit is accepted.
TRIM_SIZE_LIMIT_SUCCESS_TESTS: list[TrimTest] = [
    TrimTest(
        "size_one_under",
        input="a" * (STRING_SIZE_LIMIT_BYTES - 1),
        expected="a" * (STRING_SIZE_LIMIT_BYTES - 1),
        msg="$trim should accept input one byte under the size limit",
    ),
    TrimTest(
        "size_one_under_2byte",
        input="\u00e9" * ((STRING_SIZE_LIMIT_BYTES - 1) // 2) + "a",
        expected="\u00e9" * ((STRING_SIZE_LIMIT_BYTES - 1) // 2) + "a",
        msg="$trim should accept 2-byte character input one byte under the size limit",
    ),
    # Large input with many leading and trailing trim characters, just under the limit.
    TrimTest(
        "size_trim_both_sides",
        input="a" * ((STRING_SIZE_LIMIT_BYTES - 6) // 2)
        + "hello"
        + "a" * ((STRING_SIZE_LIMIT_BYTES - 6) // 2),
        chars="a",
        expected="hello",
        msg="$trim should trim many characters from both sides near the size limit",
    ),
]


# Property [String Size Limit - Error]: input at the BSON string byte limit produces an error.
TRIM_SIZE_LIMIT_ERROR_TESTS: list[TrimTest] = [
    TrimTest(
        "size_at_limit",
        input="a" * STRING_SIZE_LIMIT_BYTES,
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$trim should reject input at the BSON string byte limit",
    ),
    TrimTest(
        "size_at_limit_2byte",
        input="\u00e9" * (STRING_SIZE_LIMIT_BYTES // 2),
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$trim should reject 2-byte character input at the BSON string byte limit",
    ),
]

TRIM_SIZE_LIMIT_ALL_TESTS = TRIM_SIZE_LIMIT_SUCCESS_TESTS + TRIM_SIZE_LIMIT_ERROR_TESTS


@pytest.mark.parametrize("test_case", pytest_params(TRIM_SIZE_LIMIT_ALL_TESTS))
def test_trim_size_limit(collection, test_case: TrimTest):
    """Test $trim string size limit."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
