from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_project_with_insert,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import STRING_SIZE_LIMIT_BYTES

from .utils.indexOfCP_common import (
    IndexOfCPTest,
)

# Property [Expression Arguments]: all argument positions accept expressions that resolve to the
# expected type.
INDEXOFCP_EXPR_TESTS: list[IndexOfCPTest] = [
    IndexOfCPTest(
        "expr_first_arg",
        args=[{"$concat": ["hel", "lo"]}, "lo"],
        expected=3,
        msg="$indexOfCP should accept expression for string argument",
    ),
    IndexOfCPTest(
        "expr_second_arg",
        args=["hello", {"$concat": ["l", "o"]}],
        expected=3,
        msg="$indexOfCP should accept expression for substring argument",
    ),
    IndexOfCPTest(
        "expr_third_arg",
        args=["hello", "lo", {"$add": [1, 2]}],
        expected=3,
        msg="$indexOfCP should accept expression for start argument",
    ),
    IndexOfCPTest(
        "expr_fourth_arg",
        args=["hello", "lo", 0, {"$add": [3, 2]}],
        expected=3,
        msg="$indexOfCP should accept expression for end argument",
    ),
]

# Property [Dollar Sign Handling - Success]: using $literal for a dollar sign substring avoids field
# path interpretation and finds the character correctly.
INDEXOFCP_DOLLAR_SIGN_SUCCESS_TESTS: list[IndexOfCPTest] = [
    IndexOfCPTest(
        "dollar_literal_finds_dollar",
        args=["a$b", {"$literal": "$"}],
        expected=1,
        msg="$indexOfCP should find dollar sign via $literal",
    ),
]


INDEXOFCP_USAGE_TESTS = INDEXOFCP_EXPR_TESTS + INDEXOFCP_DOLLAR_SIGN_SUCCESS_TESTS


@pytest.mark.parametrize("test_case", pytest_params(INDEXOFCP_USAGE_TESTS))
def test_indexofcp_cases(collection, test_case: IndexOfCPTest):
    """Test $indexOfCP cases."""
    result = execute_expression(collection, {"$indexOfCP": test_case.args})
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )


# Property [Document Field References]: $indexOfCP works with field references
# from inserted documents, not just inline literals.
def test_indexofcp_document_fields(collection):
    """Test $indexOfCP reads values from document fields."""
    result = execute_project_with_insert(
        collection,
        {"s": "hello", "sub": "lo"},
        {"result": {"$indexOfCP": ["$s", "$sub"]}},
    )
    assertSuccess(
        result,
        [{"result": 3}],
        msg="$indexOfCP should find substring from document field references",
    )


# Property [Nested Field Paths]: $indexOfCP resolves dotted field paths in nested documents.
def test_indexofcp_nested_field_paths(collection):
    """Test $indexOfCP reads values from nested document field paths."""
    result = execute_project_with_insert(
        collection,
        {"a": {"b": "hello"}, "c": {"d": "lo"}},
        {"result": {"$indexOfCP": ["$a.b", "$c.d"]}},
    )
    assertSuccess(
        result,
        [{"result": 3}],
        msg="$indexOfCP should find substring from nested field paths",
    )


# Property [Return Type]: the result is always type int, including when not found and for large
# indices.
INDEXOFCP_RETURN_TYPE_TESTS: list[IndexOfCPTest] = [
    IndexOfCPTest(
        "return_type_two_args",
        args=["hello", "ell"],
        msg="$indexOfCP should return int type with two args",
    ),
    IndexOfCPTest(
        "return_type_three_args",
        args=["hello", "lo", 2],
        msg="$indexOfCP should return int type with three args",
    ),
    IndexOfCPTest(
        "return_type_four_args",
        args=["hello", "ll", 0, 5],
        msg="$indexOfCP should return int type with four args",
    ),
    IndexOfCPTest(
        "return_type_not_found",
        args=["hello", "xyz"],
        msg="$indexOfCP should return int type when not found",
    ),
    IndexOfCPTest(
        "return_type_large_index",
        args=["a" * (STRING_SIZE_LIMIT_BYTES - 2) + "b", "b"],
        msg="$indexOfCP should return int type for large index value",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(INDEXOFCP_RETURN_TYPE_TESTS))
def test_indexofcp_return_type(collection, test_case: IndexOfCPTest):
    """Test $indexOfCP result is always type int."""
    result = execute_expression(collection, {"$type": {"$indexOfCP": test_case.args}})
    assertSuccess(result, [{"result": "int"}], msg=test_case.msg)
