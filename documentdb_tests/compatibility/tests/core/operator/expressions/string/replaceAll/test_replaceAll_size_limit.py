from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import STRING_SIZE_LIMIT_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import STRING_SIZE_LIMIT_BYTES

from .utils.replaceAll_common import (
    ReplaceAllTest,
    _expr,
)

# Property [String Size Limit - Success]: strings one byte under the limit are accepted in all
# parameter positions, and replacement amplification succeeds when the result stays under the
# limit.
REPLACEALL_SIZE_LIMIT_SUCCESS_TESTS: list[ReplaceAllTest] = [
    ReplaceAllTest(
        "size_success_input_max",
        input="a" * (STRING_SIZE_LIMIT_BYTES - 1),
        find="xyz",
        replacement="abc",
        expected="a" * (STRING_SIZE_LIMIT_BYTES - 1),
        msg="$replaceAll size limit: success input max",
    ),
    # Replacement amplification producing result one under the limit.
    ReplaceAllTest(
        "size_success_amplification_max",
        input="a",
        find="a",
        replacement="a" * (STRING_SIZE_LIMIT_BYTES - 1),
        expected="a" * (STRING_SIZE_LIMIT_BYTES - 1),
        msg="$replaceAll size limit: success amplification max",
    ),
    # 4-byte emoji at one character below the byte limit.
    ReplaceAllTest(
        "size_success_4byte_max",
        input="\U0001f600" * ((STRING_SIZE_LIMIT_BYTES - 1) // 4),
        find="xyz",
        replacement="abc",
        expected="\U0001f600" * ((STRING_SIZE_LIMIT_BYTES - 1) // 4),
        msg="$replaceAll size limit: success 4byte max",
    ),
    # Empty find amplification just under the limit.
    ReplaceAllTest(
        "size_success_empty_find_amplification",
        input="a" * ((STRING_SIZE_LIMIT_BYTES - 2) // 2),
        find="",
        replacement="X",
        expected="X" + "aX" * ((STRING_SIZE_LIMIT_BYTES - 2) // 2),
        msg="$replaceAll size limit: success empty find amplification",
    ),
]


# Property [String Size Limit - Errors]: strings at the size limit produce an error, enforced
# per literal and per expression result.
REPLACEALL_SIZE_LIMIT_ERROR_TESTS: list[ReplaceAllTest] = [
    # Exactly at the limit.
    ReplaceAllTest(
        "size_error_input_at_limit",
        input="a" * STRING_SIZE_LIMIT_BYTES,
        find="a",
        replacement="b",
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$replaceAll size limit: error input at limit",
    ),
    # 2-byte chars at the limit.
    ReplaceAllTest(
        "size_error_byte_based_2byte",
        input="\u00e9" * (STRING_SIZE_LIMIT_BYTES // 2),
        find="\u00e9",
        replacement="e",
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$replaceAll size limit: error byte based 2byte",
    ),
    # 4-byte chars at the limit.
    ReplaceAllTest(
        "size_error_byte_based_4byte",
        input="\U0001f600" * (STRING_SIZE_LIMIT_BYTES // 4),
        find="\U0001f600",
        replacement="x",
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$replaceAll size limit: error byte based 4byte",
    ),
    # Input literal rejected even when replacement would shrink the result.
    ReplaceAllTest(
        "size_error_input_shrinking_rejected",
        input="a" * STRING_SIZE_LIMIT_BYTES,
        find="a" * 100,
        replacement="",
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$replaceAll size limit: error input shrinking rejected",
    ),
    # Result amplification: input under limit, replacement grows result to limit.
    ReplaceAllTest(
        "size_error_result_amplification",
        input="a" * (STRING_SIZE_LIMIT_BYTES - 1),
        find="a",
        replacement="aa",
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$replaceAll size limit: error result amplification",
    ),
    # Find parameter at the limit.
    ReplaceAllTest(
        "size_error_find_at_limit",
        input="hello",
        find="a" * STRING_SIZE_LIMIT_BYTES,
        replacement="b",
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$replaceAll size limit: error find at limit",
    ),
    # Replacement parameter at the limit.
    ReplaceAllTest(
        "size_error_replacement_at_limit",
        input="hello",
        find="a",
        replacement="a" * STRING_SIZE_LIMIT_BYTES,
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$replaceAll size limit: error replacement at limit",
    ),
]


REPLACEALL_SIZE_LIMIT_ALL_TESTS = (
    REPLACEALL_SIZE_LIMIT_SUCCESS_TESTS + REPLACEALL_SIZE_LIMIT_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(REPLACEALL_SIZE_LIMIT_ALL_TESTS))
def test_replaceall_size_limit_cases(collection, test_case: ReplaceAllTest):
    """Test $replaceAll size limit cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
