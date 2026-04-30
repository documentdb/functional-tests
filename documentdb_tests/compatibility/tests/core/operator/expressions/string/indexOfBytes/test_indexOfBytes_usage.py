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

from .utils.indexOfBytes_common import (
    IndexOfBytesTest,
)

# Property [Expression Arguments]: all argument positions accept expressions that resolve to the
# expected type.
INDEXOFBYTES_EXPR_TESTS: list[IndexOfBytesTest] = [
    IndexOfBytesTest(
        "expr_first_arg",
        args=[{"$concat": ["hel", "lo"]}, "lo"],
        expected=3,
        msg="$indexOfBytes should accept expression for string argument",
    ),
    IndexOfBytesTest(
        "expr_second_arg",
        args=["hello", {"$concat": ["l", "o"]}],
        expected=3,
        msg="$indexOfBytes should accept expression for substring argument",
    ),
    IndexOfBytesTest(
        "expr_third_arg",
        args=["hello", "lo", {"$add": [1, 2]}],
        expected=3,
        msg="$indexOfBytes should accept expression for start argument",
    ),
    IndexOfBytesTest(
        "expr_fourth_arg",
        args=["hello", "lo", 0, {"$add": [3, 2]}],
        expected=3,
        msg="$indexOfBytes should accept expression for end argument",
    ),
]

# Property [Dollar Sign Literal]: using $literal to pass a "$" substring avoids field path
# interpretation and finds the dollar sign correctly.
INDEXOFBYTES_DOLLAR_SIGN_SUCCESS_TESTS: list[IndexOfBytesTest] = [
    IndexOfBytesTest(
        "dollar_literal_found",
        args=["hello$world", {"$literal": "$"}],
        expected=5,
        msg="$indexOfBytes should find dollar sign via $literal",
    ),
]


INDEXOFBYTES_USAGE_TESTS = INDEXOFBYTES_EXPR_TESTS + INDEXOFBYTES_DOLLAR_SIGN_SUCCESS_TESTS


@pytest.mark.parametrize("test_case", pytest_params(INDEXOFBYTES_USAGE_TESTS))
def test_indexofbytes_cases(collection, test_case: IndexOfBytesTest):
    """Test $indexOfBytes cases."""
    result = execute_expression(collection, {"$indexOfBytes": test_case.args})
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )


# Property [Document Field References]: $indexOfBytes works with field references
# from inserted documents, not just inline literals.
def test_indexofbytes_document_fields(collection):
    """Test $indexOfBytes reads values from document fields."""
    result = execute_project_with_insert(
        collection,
        {"s": "hello", "sub": "lo"},
        {"result": {"$indexOfBytes": ["$s", "$sub"]}},
    )
    assertSuccess(
        result,
        [{"result": 3}],
        msg="$indexOfBytes should find substring from document field references",
    )


# Property [Nested Field Paths]: $indexOfBytes resolves dotted field paths in nested documents.
def test_indexofbytes_nested_field_paths(collection):
    """Test $indexOfBytes reads values from nested document field paths."""
    result = execute_project_with_insert(
        collection,
        {"a": {"b": "hello"}, "c": {"d": "lo"}},
        {"result": {"$indexOfBytes": ["$a.b", "$c.d"]}},
    )
    assertSuccess(
        result,
        [{"result": 3}],
        msg="$indexOfBytes should find substring from nested field paths",
    )


# Property [Return Type]: the result is int (not float or long) when the expression succeeds.
INDEXOFBYTES_RETURN_TYPE_TESTS: list[IndexOfBytesTest] = [
    IndexOfBytesTest(
        "return_type_two_args",
        args=["hello", "ell"],
        msg="$indexOfBytes should return int type with two args",
    ),
    IndexOfBytesTest(
        "return_type_three_args",
        args=["hello", "lo", 2],
        msg="$indexOfBytes should return int type with three args",
    ),
    IndexOfBytesTest(
        "return_type_four_args",
        args=["hello", "ll", 0, 5],
        msg="$indexOfBytes should return int type with four args",
    ),
    IndexOfBytesTest(
        "return_type_not_found",
        args=["hello", "xyz"],
        msg="$indexOfBytes should return int type when not found",
    ),
    IndexOfBytesTest(
        "return_type_large_index",
        args=["a" * (STRING_SIZE_LIMIT_BYTES - 2) + "b", "b"],
        msg="$indexOfBytes should return int type for large index value",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(INDEXOFBYTES_RETURN_TYPE_TESTS))
def test_indexofbytes_return_type(collection, test_case: IndexOfBytesTest):
    """Test $indexOfBytes result is always type int."""
    result = execute_expression(collection, {"$type": {"$indexOfBytes": test_case.args}})
    assertSuccess(result, [{"result": "int"}], msg=test_case.msg)
