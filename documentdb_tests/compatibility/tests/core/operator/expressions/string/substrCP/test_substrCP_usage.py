from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertResult, assertSuccess
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.framework.test_constants import MISSING
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
    execute_project_with_insert,
)

from .utils.substrCP_common import SubstrCPTest, _expr

# Property [Expression Arguments]: all three parameters accept expressions that resolve to valid
# types.
SUBSTRCP_EXPRESSION_TESTS: list[SubstrCPTest] = [
    SubstrCPTest(
        "expr_string",
        string={"$concat": ["hel", "lo"]},
        index=0,
        count=5,
        expected="hello",
        msg="$substrCP should accept an expression for the string parameter",
    ),
    SubstrCPTest(
        "expr_index",
        string="hello",
        index={"$add": [1, 1]},
        count=3,
        expected="llo",
        msg="$substrCP should accept an expression for the index parameter",
    ),
    SubstrCPTest(
        "expr_count",
        string="hello",
        index=0,
        count={"$strLenCP": "hel"},
        expected="hel",
        msg="$substrCP should accept an expression for the count parameter",
    ),
    SubstrCPTest(
        "nested_substrCP",
        string={"$substrCP": ["hello world", 0, 5]},
        index=1,
        count=3,
        expected="ell",
        msg="$substrCP should compose with itself (substring of a substring)",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(SUBSTRCP_EXPRESSION_TESTS))
def test_substrcp_expression_cases(collection, test_case: SubstrCPTest):
    """Test $substrCP expression argument cases."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )


# Property [Document Field References]: $substrCP works with field references from inserted
# documents.
def test_substrcp_document_fields(collection):
    """Test $substrCP reads values from document fields."""
    result = execute_project_with_insert(
        collection,
        {"s": "hello world", "i": 6, "c": 5},
        {"result": {"$substrCP": ["$s", "$i", "$c"]}},
    )
    assertSuccess(
        result,
        [{"result": "world"}],
        msg="$substrCP should resolve field references from document",
    )


# Property [Return Type]: $substrCP always returns a BSON string, including when the input was
# coerced from a non-string type or when the result is empty.
SUBSTRCP_RETURN_TYPE_TESTS: list[SubstrCPTest] = [
    SubstrCPTest(
        "return_type_string",
        string="hello",
        index=0,
        count=3,
        msg="$substrCP of string input should return type string",
    ),
    SubstrCPTest(
        "return_type_coerced",
        string=42,
        index=0,
        count=2,
        msg="$substrCP of coerced input should return type string",
    ),
    SubstrCPTest(
        "return_type_null_input",
        string=None,
        index=0,
        count=1,
        msg="$substrCP of null input should return type string",
    ),
    SubstrCPTest(
        "return_type_missing_input",
        string=MISSING,
        index=0,
        count=1,
        msg="$substrCP of missing input should return type string",
    ),
    SubstrCPTest(
        "return_type_empty",
        string="hello",
        index=0,
        count=0,
        msg="$substrCP with count 0 should return type string",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(SUBSTRCP_RETURN_TYPE_TESTS))
def test_substrcp_return_type(collection, test_case: SubstrCPTest):
    """Test $substrCP result is always type string."""
    result = execute_expression(
        collection, {"$type": {"$substrCP": [test_case.string, test_case.index, test_case.count]}}
    )
    assertSuccess(result, [{"result": "string"}], msg=test_case.msg)
