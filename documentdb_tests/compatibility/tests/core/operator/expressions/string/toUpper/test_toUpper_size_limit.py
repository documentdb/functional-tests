from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import STRING_SIZE_LIMIT_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import STRING_SIZE_LIMIT_BYTES

from .utils.toUpper_common import (
    ToUpperTest,
    _expr,
)

# Property [String Size Limit Success]: input strings just under the size limit are accepted.
TOUPPER_SIZE_LIMIT_SUCCESS_TESTS: list[ToUpperTest] = [
    ToUpperTest(
        "size_one_under",
        value="a" * (STRING_SIZE_LIMIT_BYTES - 1),
        expected="A" * (STRING_SIZE_LIMIT_BYTES - 1),
        msg="$toUpper should accept input string one byte under the 16 MB limit",
    ),
]

# Property [String Size Limit]: input strings at or above the size limit produce an error.
TOUPPER_SIZE_LIMIT_ERROR_TESTS: list[ToUpperTest] = [
    ToUpperTest(
        "size_at_limit",
        value="a" * STRING_SIZE_LIMIT_BYTES,
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$toUpper should reject input string at the 16 MB byte limit",
    ),
]

TOUPPER_SIZE_LIMIT_TESTS = TOUPPER_SIZE_LIMIT_SUCCESS_TESTS + TOUPPER_SIZE_LIMIT_ERROR_TESTS


@pytest.mark.parametrize("test_case", pytest_params(TOUPPER_SIZE_LIMIT_TESTS))
def test_toupper_size_limit(collection, test_case: ToUpperTest):
    """Test $toUpper string size limit behavior."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
