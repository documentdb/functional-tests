from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import STRING_SIZE_LIMIT_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import STRING_SIZE_LIMIT_BYTES

from .utils.strcasecmp_common import (
    StrcasecmpTest,
    _expr,
)

# Property [String Size Limit - Success]: large strings near the size limit are accepted.
# Two full-limit strings exceed the BSON document size, so we use half-limit for equal comparison.
STRCASECMP_SIZE_LIMIT_SUCCESS_TESTS: list[StrcasecmpTest] = [
    StrcasecmpTest(
        "size_both_half_limit_equal",
        string1="a" * ((STRING_SIZE_LIMIT_BYTES - 1) // 2),
        string2="a" * ((STRING_SIZE_LIMIT_BYTES - 1) // 2),
        expected=0,
        msg="$strcasecmp should return 0 for identical large strings",
    ),
    StrcasecmpTest(
        "size_one_under_vs_short",
        string1="a" * (STRING_SIZE_LIMIT_BYTES - 1),
        string2="a",
        expected=1,
        msg="$strcasecmp should detect length difference with one string near the size limit",
    ),
]

# Property [String Size Limit - Error]: input at the size limit produces an error.
STRCASECMP_SIZE_LIMIT_ERROR_TESTS: list[StrcasecmpTest] = [
    StrcasecmpTest(
        "size_at_limit",
        string1="a" * STRING_SIZE_LIMIT_BYTES,
        string2="a",
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$strcasecmp should reject a string at the size limit",
    ),
]

STRCASECMP_SIZE_LIMIT_ALL_TESTS = (
    STRCASECMP_SIZE_LIMIT_SUCCESS_TESTS + STRCASECMP_SIZE_LIMIT_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(STRCASECMP_SIZE_LIMIT_ALL_TESTS))
def test_strcasecmp_size_limit_cases(collection, test_case: StrcasecmpTest):
    """Test $strcasecmp size limit cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
