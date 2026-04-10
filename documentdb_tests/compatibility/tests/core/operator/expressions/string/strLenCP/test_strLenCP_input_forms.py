from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
    execute_project_with_insert,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.parametrize import pytest_params

from .utils.strLenCP_common import (
    StrLenCPTest,
    _expr,
)

# Property [Expression Arguments]: the argument accepts any expression that resolves to a string.
STRLENCP_EXPR_TESTS: list[StrLenCPTest] = [
    StrLenCPTest(
        "expr_concat",
        value={"$concat": ["hel", "lo"]},
        expected=5,
        msg="$strLenCP should accept $concat expression as argument",
    ),
    StrLenCPTest(
        "expr_toupper",
        value={"$toUpper": "hello"},
        expected=5,
        msg="$strLenCP should accept $toUpper expression as argument",
    ),
]

# Property [Array Syntax]: a literal single-element array is parsed as one argument.
STRLENCP_ARRAY_SYNTAX_TESTS: list[StrLenCPTest] = [
    StrLenCPTest(
        "expr_array_syntax_ascii",
        value=["hello"],
        expected=5,
        msg="$strLenCP should accept single-element array with ASCII string",
    ),
    StrLenCPTest(
        "expr_array_syntax_multibyte",
        value=["café"],
        expected=4,
        msg="$strLenCP should accept single-element array with multibyte string",
    ),
]


# Property [JSON/BSON-Meaningful Characters]: strings containing JSON/BSON-meaningful characters are
# treated as data and each character is counted as 1 code point.
STRLENCP_JSON_BSON_TESTS: list[StrLenCPTest] = [
    StrLenCPTest(
        "json_bson_double_quote", value='"', expected=1, msg="$strLenCP of double quote should be 1"
    ),
    StrLenCPTest(
        "json_bson_backslash", value="\\", expected=1, msg="$strLenCP of backslash should be 1"
    ),
    StrLenCPTest("json_bson_open_brace", value="{", expected=1, msg="$strLenCP of '{' should be 1"),
    StrLenCPTest(
        "json_bson_close_brace", value="}", expected=1, msg="$strLenCP of '}' should be 1"
    ),
    StrLenCPTest(
        "json_bson_open_bracket", value="[", expected=1, msg="$strLenCP of '[' should be 1"
    ),
    StrLenCPTest(
        "json_bson_close_bracket", value="]", expected=1, msg="$strLenCP of ']' should be 1"
    ),
    StrLenCPTest("json_bson_colon", value=":", expected=1, msg="$strLenCP of colon should be 1"),
    StrLenCPTest("json_bson_comma", value=",", expected=1, msg="$strLenCP of comma should be 1"),
    StrLenCPTest(
        "json_bson_mixed",
        value='{"key": [1, 2]}',
        expected=15,
        msg="$strLenCP of JSON-like string should count each character as 1",
    ),
]


# Property [Dollar Sign Literal]: $literal avoids field path interpretation for dollar-prefixed
# strings.
STRLENCP_DOLLAR_LITERAL_TESTS: list[StrLenCPTest] = [
    StrLenCPTest(
        "dollar_literal_hello",
        value={"$literal": "$hello"},
        expected=6,
        msg="$strLenCP should count dollar-prefixed string via $literal",
    ),
    StrLenCPTest(
        "dollar_literal_bare",
        value={"$literal": "$"},
        expected=1,
        msg="$strLenCP should count bare dollar via $literal as 1",
    ),
]

STRLENCP_INPUT_FORM_TESTS = (
    STRLENCP_EXPR_TESTS
    + STRLENCP_ARRAY_SYNTAX_TESTS
    + STRLENCP_JSON_BSON_TESTS
    + STRLENCP_DOLLAR_LITERAL_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(STRLENCP_INPUT_FORM_TESTS))
def test_strlencp_cases(collection, test_case: StrLenCPTest):
    """Test $strLenCP cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )


# Property [Document Field References]: $strLenCP works with values from document fields.
def test_strlencp_document_fields(collection):
    """Test $strLenCP reads values from document fields."""
    result = execute_project_with_insert(
        collection,
        {"s": "café"},
        {"result": {"$strLenCP": "$s"}},
    )
    assertSuccess(result, [{"result": 4}], msg="$strLenCP should read value from document field")


# Property [Nested Field Paths]: $strLenCP resolves dotted field paths in nested documents.
def test_strlencp_nested_field_paths(collection):
    """Test $strLenCP reads values from nested document field paths."""
    result = execute_expression_with_insert(collection, {"$strLenCP": "$a.b"}, {"a": {"b": "café"}})
    assertSuccess(result, [{"result": 4}], msg="$strLenCP should resolve nested field path")
