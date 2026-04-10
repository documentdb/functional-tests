from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import STRING_SIZE_LIMIT_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import STRING_SIZE_LIMIT_BYTES

from .utils.indexOfCP_common import (
    IndexOfCPTest,
)

# Property [String Size Limit - Success]: string and substring arguments just under the size limit
# are accepted.
INDEXOFCP_SIZE_LIMIT_SUCCESS_TESTS: list[IndexOfCPTest] = [
    IndexOfCPTest(
        "size_string_one_under",
        args=["a" * (STRING_SIZE_LIMIT_BYTES - 1), "a"],
        expected=0,
        msg="$indexOfCP should accept string one byte under the size limit",
    ),
    IndexOfCPTest(
        "size_substr_one_under",
        args=["hello", "a" * (STRING_SIZE_LIMIT_BYTES - 1)],
        expected=-1,
        msg="$indexOfCP should accept substring one byte under the size limit",
    ),
    # 2-byte chars: one byte under the limit. Limit is byte-based, not code-point-based.
    IndexOfCPTest(
        "size_string_one_under_2byte",
        args=["é" * ((STRING_SIZE_LIMIT_BYTES - 1) // 2) + "a", "a"],
        expected=(STRING_SIZE_LIMIT_BYTES - 1) // 2,
        msg="$indexOfCP should accept 2-byte char string one byte under limit",
    ),
    # Found at end of a large string.
    IndexOfCPTest(
        "size_found_at_end",
        args=["a" * (STRING_SIZE_LIMIT_BYTES - 2) + "b", "b"],
        expected=STRING_SIZE_LIMIT_BYTES - 2,
        msg="$indexOfCP should find match at end of a large string",
    ),
    # Not found in a large string.
    IndexOfCPTest(
        "size_not_found",
        args=["a" * (STRING_SIZE_LIMIT_BYTES - 1), "b"],
        expected=-1,
        msg="$indexOfCP should return -1 for no match in a large string",
    ),
]


# Property [String Size Limit - Error]: a string or substring argument at or above the size limit
# produces an error.
INDEXOFCP_SIZE_LIMIT_ERROR_TESTS: list[IndexOfCPTest] = [
    IndexOfCPTest(
        "size_string_at_limit",
        args=["a" * STRING_SIZE_LIMIT_BYTES, "b"],
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$indexOfCP should reject string at the size limit",
    ),
    IndexOfCPTest(
        "size_substr_at_limit",
        args=["hello", "a" * STRING_SIZE_LIMIT_BYTES],
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$indexOfCP should reject substring at the size limit",
    ),
    # 2-byte chars: exactly at the limit. Limit is byte-based, not code-point-based.
    IndexOfCPTest(
        "size_string_at_limit_2byte",
        args=["é" * (STRING_SIZE_LIMIT_BYTES // 2), "b"],
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$indexOfCP should reject 2-byte char string at the byte size limit",
    ),
]

INDEXOFCP_SIZE_LIMIT_TESTS = INDEXOFCP_SIZE_LIMIT_SUCCESS_TESTS + INDEXOFCP_SIZE_LIMIT_ERROR_TESTS


@pytest.mark.parametrize("test_case", pytest_params(INDEXOFCP_SIZE_LIMIT_TESTS))
def test_indexofcp_size_limit(collection, test_case: IndexOfCPTest):
    """Test $indexOfCP size limit behavior."""
    result = execute_expression(collection, {"$indexOfCP": test_case.args})
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
