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

from .utils.toUpper_common import (
    ToUpperTest,
    _expr,
)

# Property [Expression Arguments]: the operator accepts expressions, $literal, and operator
# composition as arguments.
TOUPPER_EXPR_TESTS: list[ToUpperTest] = [
    ToUpperTest(
        "expr_operator_composition",
        value={"$concat": ["hello", " world"]},
        expected="HELLO WORLD",
        msg="$toUpper should uppercase result of $concat expression",
    ),
    ToUpperTest(
        "expr_literal_dollar",
        value={"$literal": "$hello"},
        expected="$HELLO",
        msg="$toUpper should uppercase $literal string preserving dollar sign",
    ),
    ToUpperTest(
        "expr_coercible_result",
        value={"$add": [1, 2]},
        expected="3",
        msg="$toUpper should coerce numeric expression result to string",
    ),
]

# Property [Arity Success]: a single-element array is unwrapped and processed as the argument.
TOUPPER_ARITY_SUCCESS_TESTS: list[ToUpperTest] = [
    ToUpperTest(
        "arity_single_string",
        value=["hello"],
        expected="HELLO",
        msg="$toUpper should unwrap single-element string array",
    ),
    ToUpperTest(
        "arity_single_null",
        value=[None],
        expected="",
        msg="$toUpper should unwrap single-element null array to empty string",
    ),
    ToUpperTest(
        "arity_single_coercible",
        value=[42],
        expected="42",
        msg="$toUpper should unwrap single-element coercible array",
    ),
]

# Property [Arity Errors]: an empty array or an array with more than one element produces an
# error; a single-element array containing a non-coercible type produces a type error.
TOUPPER_ARITY_ERROR_TESTS: list[ToUpperTest] = [
    ToUpperTest(
        "arity_empty_array",
        value=[],
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$toUpper should reject empty array",
    ),
    ToUpperTest(
        "arity_two_elements",
        value=["a", "b"],
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$toUpper should reject two-element array",
    ),
    ToUpperTest(
        "arity_single_non_coercible",
        value=[True],
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$toUpper should reject single-element array with non-coercible type",
    ),
]

# Property [Field Path Errors]: bare '$' and '$$' are rejected as invalid field paths.
TOUPPER_FIELD_PATH_ERROR_TESTS: list[ToUpperTest] = [
    ToUpperTest(
        "fieldpath_bare_dollar",
        value="$",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$toUpper should reject bare '$' as invalid field path",
    ),
    ToUpperTest(
        "fieldpath_double_dollar",
        value="$$",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$toUpper should reject '$$' as empty variable name",
    ),
]

TOUPPER_ARGUMENT_TESTS = (
    TOUPPER_EXPR_TESTS
    + TOUPPER_ARITY_SUCCESS_TESTS
    + TOUPPER_ARITY_ERROR_TESTS
    + TOUPPER_FIELD_PATH_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(TOUPPER_ARGUMENT_TESTS))
def test_toupper_arguments(collection, test_case: ToUpperTest):
    """Test $toUpper argument handling."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )


# Property [Document Field References]: field references and nested field references are resolved
# before conversion.
def test_toupper_document_fields(collection):
    """Test $toUpper reads values from document fields."""
    result = execute_project_with_insert(
        collection,
        {"val": "hello"},
        {"result": {"$toUpper": "$val"}},
    )
    assertSuccess(
        result,
        [{"result": "HELLO"}],
        msg="$toUpper should read values from document fields",
    )
