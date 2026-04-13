from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import STRING_SIZE_LIMIT_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import STRING_SIZE_LIMIT_BYTES

from .utils.ltrim_common import (
    LtrimTest,
    _expr,
)

# Property [String Size Limit - Success]: input one byte under the limit is accepted.
LTRIM_SIZE_LIMIT_SUCCESS_TESTS: list[LtrimTest] = [
    LtrimTest(
        "size_one_under",
        input="a" * (STRING_SIZE_LIMIT_BYTES - 1),
        expected="a" * (STRING_SIZE_LIMIT_BYTES - 1),
        msg="$ltrim should accept input one byte under the size limit",
    ),
    # 2-byte chars: one byte under the limit.
    LtrimTest(
        "size_one_under_2byte",
        input="\u00e9" * ((STRING_SIZE_LIMIT_BYTES - 1) // 2) + "a",
        expected="\u00e9" * ((STRING_SIZE_LIMIT_BYTES - 1) // 2) + "a",
        msg="$ltrim should accept 2-byte character input one byte under the size limit",
    ),
    # Large input with many leading trim characters, just under the limit.
    LtrimTest(
        "size_trim_leading",
        input="a" * (STRING_SIZE_LIMIT_BYTES - 6) + "hello",
        chars="a",
        expected="hello",
        msg="$ltrim should trim many leading characters near the size limit",
    ),
]

# Property [String Size Limit - Error]: input at the BSON string byte limit produces an error.
# Note: These use $concat to avoid parse-time rejection of oversized literals.
LTRIM_SIZE_LIMIT_ERROR_TESTS: list[LtrimTest] = [
    LtrimTest(
        "size_at_limit",
        input="a" * STRING_SIZE_LIMIT_BYTES,
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$ltrim should reject input at the BSON string byte limit",
    ),
    LtrimTest(
        "size_at_limit_2byte",
        input="\u00e9" * (STRING_SIZE_LIMIT_BYTES // 2),
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$ltrim should reject 2-byte character input at the BSON string byte limit",
    ),
]

LTRIM_SIZE_LIMIT_ALL_TESTS = LTRIM_SIZE_LIMIT_SUCCESS_TESTS + LTRIM_SIZE_LIMIT_ERROR_TESTS


@pytest.mark.parametrize("test_case", pytest_params(LTRIM_SIZE_LIMIT_ALL_TESTS))
def test_ltrim_size_limit(collection, test_case: LtrimTest):
    """Test $ltrim string size limit cases."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
