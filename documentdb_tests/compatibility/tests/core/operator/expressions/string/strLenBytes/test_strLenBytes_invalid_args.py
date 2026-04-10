from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import (
    EXPRESSION_TYPE_MISMATCH_ERROR,
    FAILED_TO_PARSE_ERROR,
    INVALID_DOLLAR_FIELD_PATH,
    STRLENBYTES_TYPE_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

from .utils.strLenBytes_common import (
    StrLenBytesTest,
    _expr,
)

# Property [Null and Missing Errors]: null or missing arguments produce an error.
STRLENBYTES_NULL_ERROR_TESTS: list[StrLenBytesTest] = [
    StrLenBytesTest(
        "null_literal",
        value=None,
        error_code=STRLENBYTES_TYPE_ERROR,
        msg="$strLenBytes should reject null input",
    ),
    StrLenBytesTest(
        "missing_field",
        value=MISSING,
        error_code=STRLENBYTES_TYPE_ERROR,
        msg="$strLenBytes should reject missing field",
    ),
    StrLenBytesTest(
        "null_expr",
        value={"$literal": None},
        error_code=STRLENBYTES_TYPE_ERROR,
        msg="$strLenBytes should reject null from expression",
    ),
    StrLenBytesTest(
        "null_array",
        value=[None],
        error_code=STRLENBYTES_TYPE_ERROR,
        msg="$strLenBytes should reject single-element array containing null",
    ),
]

# Property [Arity Errors]: literal arrays with zero or multiple elements produce an arity error.
STRLENBYTES_ARITY_ERROR_TESTS: list[StrLenBytesTest] = [
    StrLenBytesTest(
        "arity_empty_array",
        value=[],
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$strLenBytes should reject empty array",
    ),
    StrLenBytesTest(
        "arity_two_elements",
        value=["a", "b"],
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$strLenBytes should reject two-element array",
    ),
    StrLenBytesTest(
        "arity_three_elements",
        value=["a", "b", "c"],
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$strLenBytes should reject three-element array",
    ),
]

# Property [Dollar Sign Error]: a bare "$" is interpreted as a field path and "$$" is interpreted
# as an empty variable name.
STRLENBYTES_DOLLAR_ERROR_TESTS: list[StrLenBytesTest] = [
    StrLenBytesTest(
        "dollar_bare_field_path",
        value="$",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$strLenBytes should reject bare '$' as invalid field path",
    ),
    StrLenBytesTest(
        "dollar_double",
        value="$$",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$strLenBytes should reject '$$' as empty variable name",
    ),
]


STRLENBYTES_NON_TYPE_ERROR_TESTS = (
    STRLENBYTES_NULL_ERROR_TESTS + STRLENBYTES_ARITY_ERROR_TESTS + STRLENBYTES_DOLLAR_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(STRLENBYTES_NON_TYPE_ERROR_TESTS))
def test_strlenbytes_cases(collection, test_case: StrLenBytesTest):
    """Test $strLenBytes error cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
