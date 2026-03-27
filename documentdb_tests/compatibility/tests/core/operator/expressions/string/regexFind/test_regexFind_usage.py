from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.framework.assertions import assertResult, assertSuccess
from documentdb_tests.framework.test_case import BaseTestCase, pytest_params
from documentdb_tests.compatibility.tests.core.operator.expressions.string.regexFind.utils.regexFind_common import (
    RegexFindTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
    execute_project,
    execute_project_with_insert,
)


# Property [Document Field References]: $regexFind works with field references
# from inserted documents, not just inline literals.
def test_regexfind_document_fields(collection):
    """Test $regexFind reads values from document fields."""
    result = execute_project_with_insert(
        collection,
        {"s": "hello world"},
        {"result": {"$regexFind": {"input": "$s", "regex": "world"}}},
    )
    assertSuccess(
        result,
        [{"result": {"match": "world", "idx": 6, "captures": []}}],
        msg="$regexFind should find match from document field references",
    )


# Property [Return Type]: match result has match (string), idx (int), and captures (array of
# strings).
@dataclass(frozen=True)
class RegexFindReturnTypeTest(BaseTestCase):
    """Test case for $regexFind return type verification."""

    input: Any = None
    regex: Any = None
    capture_element_types: list[str] | None = None


REGEXFIND_RETURN_TYPE_TESTS: list[RegexFindReturnTypeTest] = [
    RegexFindReturnTypeTest(
        "return_type_no_captures",
        input="hello",
        regex="hello",
        capture_element_types=[],
        msg="$regexFind should return correct types with no captures",
    ),
    RegexFindReturnTypeTest(
        "return_type_captures",
        input="abc 123",
        regex="([a-z]+) ([0-9]+)",
        capture_element_types=["string", "string"],
        msg="$regexFind should return string type for capture elements",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(REGEXFIND_RETURN_TYPE_TESTS))
def test_regexfind_return_type(collection, test_case: RegexFindReturnTypeTest):
    """Test $regexFind match result field types."""
    expr = {"$regexFind": {"input": test_case.input, "regex": test_case.regex}}
    captures = {"$getField": {"field": "captures", "input": expr}}
    result = execute_project(
        collection,
        {
            "matchType": {"$type": {"$getField": {"field": "match", "input": expr}}},
            "idxType": {"$type": {"$getField": {"field": "idx", "input": expr}}},
            "capturesType": {"$type": captures},
            "captureElementTypes": {"$map": {"input": captures, "as": "c", "in": {"$type": "$$c"}}},
        },
    )
    assertSuccess(
        result,
        [
            {
                "matchType": "string",
                "idxType": "int",
                "capturesType": "array",
                "captureElementTypes": test_case.capture_element_types,
            }
        ],
        msg=test_case.msg,
    )


# Property [Expression Arguments]: input, regex, and options accept expressions that resolve to
# the appropriate type.
REGEXFIND_EXPR_TESTS: list[RegexFindTest] = [
    RegexFindTest(
        "expr_input",
        input={"$concat": ["hel", "lo"]},
        regex="hello",
        expected={"match": "hello", "idx": 0, "captures": []},
        msg="$regexFind should accept expression for input",
    ),
    RegexFindTest(
        "expr_regex",
        input="hello",
        regex={"$concat": ["hel", "lo"]},
        expected={"match": "hello", "idx": 0, "captures": []},
        msg="$regexFind should accept expression for regex",
    ),
    RegexFindTest(
        "expr_options",
        input="HELLO",
        regex="hello",
        options={"$concat": ["", "i"]},
        expected={"match": "HELLO", "idx": 0, "captures": []},
        msg="$regexFind should accept expression for options",
    ),
    RegexFindTest(
        "expr_literal_dollar_regex",
        input="price: $100",
        regex={"$literal": "\\$[0-9]+"},
        expected={"match": "$100", "idx": 7, "captures": []},
        msg="$regexFind should accept $literal for dollar in regex",
    ),
]

# Property [Edge Cases - string literal]: a string starting with "$" in the input field is
# treated as a field path reference, not a literal string. When the referenced field is missing,
# the input resolves to null and null propagation applies.
REGEXFIND_LITERAL_INPUT_TESTS: list[RegexFindTest] = [
    RegexFindTest(
        "edge_dollar_input_is_field_ref",
        input="$nonexistent",
        regex="\\$nonexistent",
        expected=None,
        msg="$regexFind should treat dollar-prefixed input as field ref",
    ),
]

REGEXFIND_USAGE_PARAM_TESTS = REGEXFIND_EXPR_TESTS + REGEXFIND_LITERAL_INPUT_TESTS


@pytest.mark.parametrize("test_case", pytest_params(REGEXFIND_USAGE_PARAM_TESTS))
def test_regexfind_cases(collection, test_case: RegexFindTest):
    """Test $regexFind usage cases."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
