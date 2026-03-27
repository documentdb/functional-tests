from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertResult, assertSuccess
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.compatibility.tests.core.operator.expressions.string.regexFindAll.utils.regexFindAll_common import (
    RegexFindAllTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
    execute_project_with_insert,
)

# Property [Expression Arguments]: input, regex, and options accept expressions that resolve to the
# appropriate type.
REGEXFINDALL_EXPR_TESTS: list[RegexFindAllTest] = [
    RegexFindAllTest(
        "expr_input",
        input={"$concat": ["hel", "lo"]},
        regex="hello",
        expected=[{"match": "hello", "idx": 0, "captures": []}],
        msg="$regexFindAll should accept expression resolving to string for input",
    ),
    RegexFindAllTest(
        "expr_regex",
        input="hello",
        regex={"$concat": ["hel", "lo"]},
        expected=[{"match": "hello", "idx": 0, "captures": []}],
        msg="$regexFindAll should accept expression resolving to string for regex",
    ),
    RegexFindAllTest(
        "expr_options",
        input="HELLO",
        regex="hello",
        options={"$concat": ["", "i"]},
        expected=[{"match": "HELLO", "idx": 0, "captures": []}],
        msg="$regexFindAll should accept expression resolving to string for options",
    ),
    # $literal for dollar sign in regex.
    RegexFindAllTest(
        "expr_literal_dollar_regex",
        input="price: $100",
        regex={"$literal": "\\$[0-9]+"},
        expected=[{"match": "$100", "idx": 7, "captures": []}],
        msg="$regexFindAll should accept $literal expression for regex with dollar sign",
    ),
]


# Property [Edge Cases - string literal]: a string starting with "$" in the input field is
# treated as a field path reference, not a literal string. When the referenced field is missing,
# the input resolves to null and null propagation applies.
REGEXFINDALL_LITERAL_INPUT_TESTS: list[RegexFindAllTest] = [
    RegexFindAllTest(
        "edge_dollar_input_is_field_ref",
        input="$nonexistent",
        regex="\\$nonexistent",
        expected=[],
        msg="$regexFindAll should treat dollar-prefixed input as field path reference, not literal",
    ),
]

REGEXFINDALL_USAGE_ALL_TESTS = REGEXFINDALL_EXPR_TESTS + REGEXFINDALL_LITERAL_INPUT_TESTS


@pytest.mark.parametrize("test_case", pytest_params(REGEXFINDALL_USAGE_ALL_TESTS))
def test_regexfindall_usage(collection, test_case: RegexFindAllTest):
    """Test $regexFindAll expression arguments and field reference behavior."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )


# Property [Document Field References]: $regexFindAll works with field references
# from inserted documents, not just inline literals.
def test_regexfindall_document_fields(collection):
    """Test $regexFindAll reads values from document fields."""
    result = execute_project_with_insert(
        collection,
        {"s": "abc123def456"},
        {"result": {"$regexFindAll": {"input": "$s", "regex": "[0-9]+"}}},
    )
    assertSuccess(
        result,
        [
            {
                "result": [
                    {"match": "123", "idx": 3, "captures": []},
                    {"match": "456", "idx": 9, "captures": []},
                ]
            }
        ],
        msg="$regexFindAll should find all digit-sequence matches from a document field",
    )
