from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import STRING_SIZE_LIMIT_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import STRING_SIZE_LIMIT_BYTES

from .utils.rtrim_common import (
    RtrimTest,
    _expr,
)

# Property [String Size Limit - Success]: input one byte under the limit is accepted.
RTRIM_SIZE_LIMIT_SUCCESS_TESTS: list[RtrimTest] = [
    RtrimTest(
        "size_one_under",
        input="a" * (STRING_SIZE_LIMIT_BYTES - 1),
        expected="a" * (STRING_SIZE_LIMIT_BYTES - 1),
        msg="$rtrim should accept input one byte under the size limit",
    ),
    # 2-byte chars: one byte under the limit.
    RtrimTest(
        "size_one_under_2byte",
        input="\u00e9" * ((STRING_SIZE_LIMIT_BYTES - 1) // 2) + "a",
        expected="\u00e9" * ((STRING_SIZE_LIMIT_BYTES - 1) // 2) + "a",
        msg="$rtrim should accept 2-byte character input one byte under the size limit",
    ),
    # Large input with many trailing trim characters, just under the limit.
    RtrimTest(
        "size_trim_trailing",
        input="hello" + "a" * (STRING_SIZE_LIMIT_BYTES - 6),
        chars="a",
        expected="hello",
        msg="$rtrim should trim many trailing characters near the size limit",
    ),
]


# Property [String Size Limit - Error]: input at the BSON string byte limit produces an error.
RTRIM_SIZE_LIMIT_ERROR_TESTS: list[RtrimTest] = [
    RtrimTest(
        "size_at_limit",
        input="a" * STRING_SIZE_LIMIT_BYTES,
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$rtrim should reject input at the BSON string byte limit",
    ),
    RtrimTest(
        "size_at_limit_2byte",
        input="\u00e9" * (STRING_SIZE_LIMIT_BYTES // 2),
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$rtrim should reject 2-byte character input at the BSON string byte limit",
    ),
]

RTRIM_SIZE_LIMIT_ALL_TESTS = RTRIM_SIZE_LIMIT_SUCCESS_TESTS + RTRIM_SIZE_LIMIT_ERROR_TESTS


@pytest.mark.parametrize("test_case", pytest_params(RTRIM_SIZE_LIMIT_ALL_TESTS))
def test_rtrim_size_limit(collection, test_case: RtrimTest):
    """Test $rtrim string size limit."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
