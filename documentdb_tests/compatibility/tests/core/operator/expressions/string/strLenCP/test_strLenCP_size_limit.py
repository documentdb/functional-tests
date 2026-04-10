from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import STRING_SIZE_LIMIT_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import STRING_SIZE_LIMIT_BYTES

from .utils.strLenCP_common import (
    StrLenCPTest,
    _expr,
)

# Property [String Size Limit - Success]: inputs just under the size limit succeed.
STRLENCP_SIZE_LIMIT_SUCCESS_TESTS: list[StrLenCPTest] = [
    StrLenCPTest(
        "size_one_under",
        value="a" * (STRING_SIZE_LIMIT_BYTES - 1),
        expected=STRING_SIZE_LIMIT_BYTES - 1,
        msg="$strLenCP should handle a string one byte under the size limit",
    ),
    StrLenCPTest(
        "size_one_under_3byte",
        value="寿" * ((STRING_SIZE_LIMIT_BYTES - 1) // 3),
        expected=(STRING_SIZE_LIMIT_BYTES - 1) // 3,
        msg="$strLenCP should count 3-byte chars as code points near the size limit",
    ),
]


# Property [String Size Limit - Error]: inputs at or above the size limit produce an error.
STRLENCP_SIZE_LIMIT_ERROR_TESTS: list[StrLenCPTest] = [
    StrLenCPTest(
        "size_at_limit",
        value="a" * STRING_SIZE_LIMIT_BYTES,
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$strLenCP should reject a string at the size limit",
    ),
]

STRLENCP_SIZE_LIMIT_TESTS = STRLENCP_SIZE_LIMIT_SUCCESS_TESTS + STRLENCP_SIZE_LIMIT_ERROR_TESTS


@pytest.mark.parametrize("test_case", pytest_params(STRLENCP_SIZE_LIMIT_TESTS))
def test_strlencp_cases(collection, test_case: StrLenCPTest):
    """Test $strLenCP cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
