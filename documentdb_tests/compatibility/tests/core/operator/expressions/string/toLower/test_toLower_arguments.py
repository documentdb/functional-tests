from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_project_with_insert,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.error_codes import (
    BSON_TO_STRING_CONVERSION_ERROR,
    EXPRESSION_TYPE_MISMATCH_ERROR,
    FAILED_TO_PARSE_ERROR,
    INVALID_DOLLAR_FIELD_PATH,
)
from documentdb_tests.framework.parametrize import pytest_params

from .utils.toLower_common import (
    ToLowerTest,
    _expr,
)

# Property [Expression Arguments]: the operator accepts expressions, $literal, and coercible
# expression results, resolving and coercing them before lowercasing.
TOLOWER_EXPR_TESTS: list[ToLowerTest] = [
    ToLowerTest(
        "expr_toupper_roundtrip",
        value={"$toUpper": "hello"},
        expected="hello",
        msg="$toLower should reverse $toUpper on ASCII letters",
    ),
    ToLowerTest(
        "expr_literal_dollar_sign",
        value={"$literal": "$HELLO"},
        expected="$hello",
        msg="$toLower should lowercase $literal string preserving dollar sign",
    ),
    ToLowerTest(
        "expr_coercible_numeric_result",
        value={"$add": [1, 2]},
        expected="3",
        msg="$toLower should coerce numeric expression result to string",
    ),
]

# Property [Arity Success]: a single-element array is unwrapped and processed as the argument,
# including null and coercible types.
TOLOWER_ARITY_SUCCESS_TESTS: list[ToLowerTest] = [
    ToLowerTest(
        "arity_single_element",
        value=["HELLO"],
        expected="hello",
        msg="$toLower should unwrap single-element string array",
    ),
    ToLowerTest(
        "arity_single_null",
        value=[None],
        expected="",
        msg="$toLower should unwrap single-element null array to empty string",
    ),
    ToLowerTest(
        "arity_single_coercible",
        value=[42],
        expected="42",
        msg="$toLower should unwrap single-element coercible array",
    ),
]

# Property [Arity Errors]: an empty array or an array with more than one element produces an
# error.
TOLOWER_ARITY_ERROR_TESTS: list[ToLowerTest] = [
    ToLowerTest(
        "arity_empty_array",
        value=[],
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$toLower should reject empty array",
    ),
    ToLowerTest(
        "arity_two_elements",
        value=["a", "b"],
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$toLower should reject two-element array",
    ),
    # Single-element array containing a non-coercible type is unwrapped and errors.
    ToLowerTest(
        "arity_single_bool",
        value=[True],
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$toLower should reject single-element array with boolean",
    ),
]

# Property [Field Path Errors]: bare '$' and '$$' are rejected as invalid field paths.
TOLOWER_FIELD_PATH_ERROR_TESTS: list[ToLowerTest] = [
    ToLowerTest(
        "fieldpath_bare_dollar",
        value="$",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$toLower should reject bare '$' as invalid field path",
    ),
    ToLowerTest(
        "fieldpath_double_dollar",
        value="$$",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$toLower should reject '$$' as empty variable name",
    ),
]

TOLOWER_ARGUMENT_TESTS = (
    TOLOWER_EXPR_TESTS
    + TOLOWER_ARITY_SUCCESS_TESTS
    + TOLOWER_ARITY_ERROR_TESTS
    + TOLOWER_FIELD_PATH_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(TOLOWER_ARGUMENT_TESTS))
def test_tolower_arguments(collection, test_case: ToLowerTest):
    """Test $toLower argument handling."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )


def test_tolower_document_fields(collection):
    """Test $toLower reads values from document fields."""
    result = execute_project_with_insert(
        collection,
        {"val": "HELLO WORLD"},
        {"result": {"$toLower": "$val"}},
    )
    assertSuccess(
        result,
        [{"result": "hello world"}],
        msg="$toLower should read values from document fields",
    )
