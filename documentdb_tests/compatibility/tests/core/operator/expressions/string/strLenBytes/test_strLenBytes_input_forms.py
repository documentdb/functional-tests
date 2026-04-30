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

from .utils.strLenBytes_common import (
    StrLenBytesTest,
    _expr,
)

# Property [Expression Arguments]: the argument accepts any expression that resolves to a string.
STRLENBYTES_EXPR_TESTS: list[StrLenBytesTest] = [
    StrLenBytesTest(
        "expr_concat",
        value={"$concat": ["hel", "lo"]},
        expected=5,
        msg="$strLenBytes should accept $concat expression as argument",
    ),
    StrLenBytesTest(
        "expr_toupper",
        value={"$toUpper": "hello"},
        expected=5,
        msg="$strLenBytes should accept $toUpper expression as argument",
    ),
]

# Property [Array Syntax]: a literal single-element array is parsed as one argument.
STRLENBYTES_ARRAY_SYNTAX_TESTS: list[StrLenBytesTest] = [
    StrLenBytesTest(
        "expr_array_syntax_ascii",
        value=["hello"],
        expected=5,
        msg="$strLenBytes should accept single-element array with ASCII string",
    ),
    StrLenBytesTest(
        "expr_array_syntax_multibyte",
        value=["café"],
        expected=5,
        msg="$strLenBytes should accept single-element array with multibyte string",
    ),
]

# Property [JSON/BSON-Meaningful Characters]: strings containing JSON/BSON structural characters are
# treated as data and each character is counted as 1 byte.
STRLENBYTES_JSON_BSON_TESTS: list[StrLenBytesTest] = [
    StrLenBytesTest(
        "json_bson_open_brace", value="{", expected=1, msg="$strLenBytes of '{' should be 1"
    ),
    StrLenBytesTest(
        "json_bson_close_brace", value="}", expected=1, msg="$strLenBytes of '}' should be 1"
    ),
    StrLenBytesTest(
        "json_bson_open_bracket", value="[", expected=1, msg="$strLenBytes of '[' should be 1"
    ),
    StrLenBytesTest(
        "json_bson_close_bracket", value="]", expected=1, msg="$strLenBytes of ']' should be 1"
    ),
    StrLenBytesTest(
        "json_bson_double_quote",
        value='"',
        expected=1,
        msg="$strLenBytes of double quote should be 1",
    ),
    StrLenBytesTest(
        "json_bson_backslash", value="\\", expected=1, msg="$strLenBytes of backslash should be 1"
    ),
    StrLenBytesTest(
        "json_bson_mixed",
        value='{"key": [1]}',
        expected=12,
        msg="$strLenBytes of JSON-like string should count each ASCII char as 1 byte",
    ),
]

# Property [Dollar Sign Handling]: $literal prevents dollar-prefixed strings from being interpreted
# as field paths.
STRLENBYTES_DOLLAR_SIGN_TESTS: list[StrLenBytesTest] = [
    StrLenBytesTest(
        "dollar_literal_hello",
        value={"$literal": "$hello"},
        expected=6,
        msg="$strLenBytes should count dollar-prefixed string via $literal",
    ),
    StrLenBytesTest(
        "dollar_literal_bare",
        value={"$literal": "$"},
        expected=1,
        msg="$strLenBytes should count bare dollar via $literal as 1 byte",
    ),
]


STRLENBYTES_INPUT_FORM_TESTS = (
    STRLENBYTES_EXPR_TESTS
    + STRLENBYTES_ARRAY_SYNTAX_TESTS
    + STRLENBYTES_JSON_BSON_TESTS
    + STRLENBYTES_DOLLAR_SIGN_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(STRLENBYTES_INPUT_FORM_TESTS))
def test_strlenbytes_cases(collection, test_case: StrLenBytesTest):
    """Test $strLenBytes input form cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )


# Property [Document Field References]: $strLenBytes works with values from document fields.
def test_strlenbytes_document_fields(collection):
    """Test $strLenBytes reads values from document fields."""
    result = execute_project_with_insert(
        collection,
        {"s": "café"},
        {"result": {"$strLenBytes": "$s"}},
    )
    assertSuccess(result, [{"result": 5}], msg="$strLenBytes should read value from document field")


# Property [Nested Field Paths]: $strLenBytes resolves dotted field paths in nested documents.
def test_strlenbytes_nested_field_paths(collection):
    """Test $strLenBytes reads values from nested document field paths."""
    result = execute_expression_with_insert(
        collection, {"$strLenBytes": "$a.b"}, {"a": {"b": "café"}}
    )
    assertSuccess(result, [{"result": 5}], msg="$strLenBytes should resolve nested field path")
