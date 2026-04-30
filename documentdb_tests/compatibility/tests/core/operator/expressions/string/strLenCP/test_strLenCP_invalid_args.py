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
    STRLENCP_TYPE_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

from .utils.strLenCP_common import (
    StrLenCPTest,
    _expr,
)

# Property [Null and Missing Errors]: null or missing arguments produce an error.
STRLENCP_NULL_ERROR_TESTS: list[StrLenCPTest] = [
    StrLenCPTest(
        "null_literal",
        value=None,
        error_code=STRLENCP_TYPE_ERROR,
        msg="$strLenCP should reject null input",
    ),
    StrLenCPTest(
        "missing_field",
        value=MISSING,
        error_code=STRLENCP_TYPE_ERROR,
        msg="$strLenCP should reject missing field",
    ),
    StrLenCPTest(
        "null_expr",
        value={"$literal": None},
        error_code=STRLENCP_TYPE_ERROR,
        msg="$strLenCP should reject null from expression",
    ),
    StrLenCPTest(
        "null_array",
        value=[None],
        error_code=STRLENCP_TYPE_ERROR,
        msg="$strLenCP should reject single-element array containing null",
    ),
]

# Property [Arity Errors]: literal arrays with zero or multiple elements produce an arity error.
STRLENCP_ARITY_ERROR_TESTS: list[StrLenCPTest] = [
    StrLenCPTest(
        "arity_empty_array",
        value=[],
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$strLenCP should reject empty array",
    ),
    StrLenCPTest(
        "arity_two_elements",
        value=["a", "b"],
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$strLenCP should reject two-element array",
    ),
    StrLenCPTest(
        "arity_three_elements",
        value=["a", "b", "c"],
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$strLenCP should reject three-element array",
    ),
]


# Property [Dollar Sign Error]: a bare "$" is interpreted as a field path and "$$" is interpreted
# as an empty variable name.
STRLENCP_DOLLAR_ERROR_TESTS: list[StrLenCPTest] = [
    StrLenCPTest(
        "dollar_bare",
        value="$",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$strLenCP should reject bare '$' as invalid field path",
    ),
    StrLenCPTest(
        "dollar_double",
        value="$$",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$strLenCP should reject '$$' as empty variable name",
    ),
]

STRLENCP_INVALID_ARG_TESTS = (
    STRLENCP_NULL_ERROR_TESTS + STRLENCP_ARITY_ERROR_TESTS + STRLENCP_DOLLAR_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(STRLENCP_INVALID_ARG_TESTS))
def test_strlencp_cases(collection, test_case: StrLenCPTest):
    """Test $strLenCP cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
