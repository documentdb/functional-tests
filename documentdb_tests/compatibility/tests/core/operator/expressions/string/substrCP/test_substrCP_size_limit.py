from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import STRING_SIZE_LIMIT_ERROR
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.framework.test_constants import STRING_SIZE_LIMIT_BYTES
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import execute_expression

from .utils.substrCP_common import SubstrCPTest, _expr

# Property [String Size Limit Success]: input strings just under the size limit are accepted.
SUBSTRCP_SIZE_LIMIT_SUCCESS_TESTS: list[SubstrCPTest] = [
    SubstrCPTest(
        "size_long_string",
        string="a" * 10_000,
        index=9_998,
        count=2,
        expected="aa",
        msg="$substrCP should extract from a 10000-character string",
    ),
    SubstrCPTest(
        "size_one_under",
        string="a" * (STRING_SIZE_LIMIT_BYTES - 1),
        index=0,
        count=1,
        expected="a",
        msg="$substrCP should accept input string one byte under the 16 MB limit",
    ),
]


# Property [String Size Limit]: input strings at or above the size limit produce an error.
SUBSTRCP_SIZE_LIMIT_ERROR_TESTS: list[SubstrCPTest] = [
    SubstrCPTest(
        "size_at_limit",
        string="a" * STRING_SIZE_LIMIT_BYTES,
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$substrCP should reject input string at the 16 MB byte limit",
    ),
    # 2-byte chars exceeding 16 MB in bytes.
    SubstrCPTest(
        "size_multibyte_at_limit",
        string="é" * (STRING_SIZE_LIMIT_BYTES // 2),
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$substrCP should reject multi-byte string exceeding 16 MB in bytes",
    ),
    # Eager size check: untaken $cond branch with 16 MB string still errors.
    SubstrCPTest(
        "size_cond_untaken_branch",
        string={"$cond": [True, "hello", "a" * STRING_SIZE_LIMIT_BYTES]},
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$substrCP should reject 16 MB string in untaken $cond branch",
    ),
]


SUBSTRCP_SIZE_LIMIT_ALL_TESTS = SUBSTRCP_SIZE_LIMIT_SUCCESS_TESTS + SUBSTRCP_SIZE_LIMIT_ERROR_TESTS


@pytest.mark.parametrize("test_case", pytest_params(SUBSTRCP_SIZE_LIMIT_ALL_TESTS))
def test_substrcp_size_limit(collection, test_case: SubstrCPTest):
    """Test $substrCP size limit cases."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
