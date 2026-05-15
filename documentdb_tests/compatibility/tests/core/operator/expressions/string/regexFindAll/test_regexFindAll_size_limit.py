from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import REGEX_BAD_PATTERN_ERROR, STRING_SIZE_LIMIT_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    REGEX_PATTERN_LIMIT_BYTES,
    STRING_SIZE_LIMIT_BYTES,
)

from .utils.regexFindAll_common import (
    RegexFindAllTest,
    _expr,
)

# Property [String Size Limit - Success]: input one byte under the limit is accepted.
REGEXFINDALL_SIZE_LIMIT_SUCCESS_TESTS: list[RegexFindAllTest] = [
    RegexFindAllTest(
        "size_one_under",
        input="a" * (STRING_SIZE_LIMIT_BYTES - 4) + "XYZ",
        regex="XYZ",
        expected=[{"match": "XYZ", "idx": STRING_SIZE_LIMIT_BYTES - 4, "captures": []}],
        msg="$regexFindAll should accept input one byte under the size limit",
    ),
    RegexFindAllTest(
        "size_regex_at_pattern_limit",
        input="a" * REGEX_PATTERN_LIMIT_BYTES,
        regex="a" * REGEX_PATTERN_LIMIT_BYTES,
        expected=[{"match": "a" * REGEX_PATTERN_LIMIT_BYTES, "idx": 0, "captures": []}],
        msg="$regexFindAll should accept regex at the pattern length limit",
    ),
    RegexFindAllTest(
        "size_two_matches",
        input="XY" + "a" * (STRING_SIZE_LIMIT_BYTES - 5) + "XY",
        regex="XY",
        expected=[
            {"match": "XY", "idx": 0, "captures": []},
            {"match": "XY", "idx": STRING_SIZE_LIMIT_BYTES - 3, "captures": []},
        ],
        msg="$regexFindAll should find matches at start and end of a large string",
    ),
]


# Property [String Size Limit - Error]: input at the size limit or regex over the pattern limit
# produces an error.
REGEXFINDALL_SIZE_LIMIT_ERROR_TESTS: list[RegexFindAllTest] = [
    RegexFindAllTest(
        "size_at_limit",
        input="a" * STRING_SIZE_LIMIT_BYTES,
        regex="a",
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$regexFindAll should reject input at the size limit",
    ),
    RegexFindAllTest(
        "size_regex_over_pattern_limit",
        input="a",
        regex="a" * (REGEX_PATTERN_LIMIT_BYTES + 1),
        error_code=REGEX_BAD_PATTERN_ERROR,
        msg="$regexFindAll should reject regex over the pattern length limit",
    ),
]

REGEXFINDALL_SIZE_LIMIT_ALL_TESTS = (
    REGEXFINDALL_SIZE_LIMIT_SUCCESS_TESTS + REGEXFINDALL_SIZE_LIMIT_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(REGEXFINDALL_SIZE_LIMIT_ALL_TESTS))
def test_regexfindall_size_limit(collection, test_case: RegexFindAllTest):
    """Test $regexFindAll string size limit behavior."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
