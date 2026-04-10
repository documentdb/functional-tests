from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import STRING_SIZE_LIMIT_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import STRING_SIZE_LIMIT_BYTES

from .utils.substrBytes_common import (
    OPERATORS,
    SubstrBytesTest,
    _expr,
)

# Property [String Size Limit Success]: input strings just under the size limit are accepted.
SUBSTRBYTES_SIZE_LIMIT_SUCCESS_TESTS: list[SubstrBytesTest] = [
    SubstrBytesTest(
        "size_one_under_first",
        string="a" * (STRING_SIZE_LIMIT_BYTES - 1),
        byte_index=0,
        byte_count=1,
        expected="a",
        msg="$substrBytes should extract first byte from string one byte under the 16 MB limit",
    ),
    SubstrBytesTest(
        "size_one_under_full",
        string="a" * (STRING_SIZE_LIMIT_BYTES - 1),
        byte_index=0,
        byte_count=STRING_SIZE_LIMIT_BYTES - 1,
        expected="a" * (STRING_SIZE_LIMIT_BYTES - 1),
        msg="$substrBytes should extract full string one byte under the 16 MB limit",
    ),
    SubstrBytesTest(
        "size_one_under_last",
        string="a" * (STRING_SIZE_LIMIT_BYTES - 1),
        byte_index=STRING_SIZE_LIMIT_BYTES - 2,
        byte_count=1,
        expected="a",
        msg="$substrBytes should extract last byte from string one byte under the 16 MB limit",
    ),
]


# Property [String Size Limit]: input strings at or above the size limit produce an error.
SUBSTRBYTES_SIZE_LIMIT_ERROR_TESTS: list[SubstrBytesTest] = [
    SubstrBytesTest(
        "size_at_limit",
        string="a" * STRING_SIZE_LIMIT_BYTES,
        byte_index=0,
        byte_count=1,
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$substrBytes should reject input string at the 16 MB byte limit",
    ),
    # 2-byte chars exceeding 16 MB in bytes.
    SubstrBytesTest(
        "size_multibyte_at_limit",
        string="é" * (STRING_SIZE_LIMIT_BYTES // 2),
        byte_index=0,
        byte_count=1,
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$substrBytes should reject multi-byte string exceeding 16 MB in bytes",
    ),
]


SUBSTRBYTES_SIZE_LIMIT_ALL_TESTS = (
    SUBSTRBYTES_SIZE_LIMIT_SUCCESS_TESTS + SUBSTRBYTES_SIZE_LIMIT_ERROR_TESTS
)


@pytest.mark.parametrize("op", OPERATORS)
@pytest.mark.parametrize("test_case", pytest_params(SUBSTRBYTES_SIZE_LIMIT_ALL_TESTS))
def test_substrbytes_size_limit(collection, op, test_case: SubstrBytesTest):
    """Test $substrBytes cases."""
    result = execute_expression(collection, _expr(test_case, op))
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
