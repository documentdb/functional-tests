from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.accumulator.avg.utils.avg_common import (  # noqa: E501
    AvgTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_project_with_insert,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.error_codes import FAILED_TO_PARSE_ERROR, INVALID_DOLLAR_FIELD_PATH
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF

# Property [Array Traversal (Single Expression Form)]: when a single
# expression resolves to an array, $avg traverses one level into it to
# average its numeric elements. Nested arrays and non-numeric elements are
# ignored. Single-element array syntax behaves identically.
AVG_ARRAY_TRAVERSAL_TESTS: list[AvgTest] = [
    AvgTest(
        "traversal_basic",
        args={"$literal": [1, 2, 3]},
        expected=2.0,
        msg="$avg should traverse a literal array and average its numeric elements",
    ),
    AvgTest(
        "traversal_nested_array_ignored",
        args={"$literal": [1, [2, 3], 4]},
        expected=2.5,
        msg="$avg should ignore nested arrays as non-numeric during traversal",
    ),
    AvgTest(
        "traversal_double_nested",
        args={"$literal": [[1, 2, 3]]},
        expected=None,
        msg="$avg should return null when the only element is a nested array",
    ),
    AvgTest(
        "traversal_triple_nested",
        args={"$literal": [[[1, 2, 3]]]},
        expected=None,
        msg="$avg should return null when the only element is a doubly nested array",
    ),
    AvgTest(
        "traversal_non_numeric_ignored",
        args={"$literal": [1, "hello", Int64(2), None, 3.0, Decimal128("7")]},
        expected=Decimal128("3.25"),
        msg="$avg should ignore non-numeric elements and null during array traversal",
    ),
    AvgTest(
        "traversal_all_non_numeric",
        args={"$literal": ["hello", True]},
        expected=None,
        msg="$avg should return null when all traversed elements are non-numeric",
    ),
    AvgTest(
        "traversal_all_null",
        args={"$literal": [None, None]},
        expected=None,
        msg="$avg should return null when all traversed elements are null",
    ),
    AvgTest(
        "traversal_decimal128_return_type",
        args={"$literal": [1, Decimal128("2")]},
        expected=DECIMAL128_ONE_AND_HALF,
        msg="$avg should return Decimal128 when traversed array contains Decimal128",
    ),
    AvgTest(
        "traversal_empty_array",
        args={"$literal": []},
        expected=None,
        msg="$avg should return null for an empty traversed array",
    ),
    AvgTest(
        "traversal_single_element_array_syntax",
        args=[{"$literal": [1, 2, 3]}],
        expected=2.0,
        msg="$avg with single-element array syntax should traverse like single expression form",
    ),
]

# Property [Array Traversal (List of Expressions Form)]: when a list of
# expressions is provided, arrays resolved by any expression are treated as
# non-numeric and not traversed.
AVG_ARRAY_TRAVERSAL_LIST_TESTS: list[AvgTest] = [
    AvgTest(
        "traversal_list_array_ignored",
        args=[{"$literal": [1, 2, 3]}, 10],
        expected=10.0,
        msg="$avg should treat an array as non-numeric in list-of-expressions form",
    ),
    AvgTest(
        "traversal_list_all_arrays",
        args=[{"$literal": [1, 2, 3]}, {"$literal": [4, 5]}],
        expected=None,
        msg="$avg should return null when all list expressions resolve to arrays",
    ),
]

# Property [Arity]: $avg returns null for an empty operand list and
# correctly averages large operand counts.
AVG_ARITY_TESTS: list[AvgTest] = [
    AvgTest(
        "arity_empty_array",
        args=[],
        expected=None,
        msg="$avg should return null for an empty operand list",
    ),
    AvgTest(
        "arity_single_element_list",
        args=[42],
        expected=42.0,
        msg="$avg of a single-element list should return that value as double",
    ),
    AvgTest(
        "arity_10_000_elements",
        args=list(range(10_000)),
        expected=4999.5,
        msg="$avg should correctly average 10000 elements",
    ),
    AvgTest(
        "arity_10_000_identical",
        args=[7] * 10_000,
        expected=7.0,
        msg="$avg of 10000 identical values should return that value",
    ),
]

# Property [Expression Arguments]: $avg accepts arbitrary expressions as
# operands, evaluating each before averaging. Nested $avg is evaluated as a
# scalar, not flattened.
AVG_EXPRESSION_ARGS_TESTS: list[AvgTest] = [
    AvgTest(
        "expr_add",
        args=[{"$add": [3, 7]}, 20],
        expected=15.0,
        msg="$avg should accept $add expression as an operand",
    ),
    AvgTest(
        "expr_returning_null",
        args=[{"$literal": None}, 10],
        expected=10.0,
        msg="$avg should ignore an expression that returns null",
    ),
    AvgTest(
        "expr_returning_non_numeric",
        args=[{"$toString": 42}, 10],
        expected=10.0,
        msg="$avg should ignore an expression that returns a non-numeric type",
    ),
    AvgTest(
        "expr_nested_avg",
        args=[1, 3, {"$avg": [4, 6]}],
        expected=3.0,
        msg="$avg should evaluate nested $avg as a scalar, not flatten it",
    ),
]

# Property [Field Path Errors]: bare "$" and empty variable name "$$"
# produce errors rather than being treated as valid field references.
AVG_FIELD_PATH_ERROR_TESTS: list[AvgTest] = [
    AvgTest(
        "fieldpath_bare_dollar",
        args="$",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$avg should reject bare '$' as an invalid field path",
    ),
    AvgTest(
        "fieldpath_double_dollar",
        args="$$",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$avg should reject '$$' as an empty variable name",
    ),
]

AVG_INPUT_FORMS_TESTS = (
    AVG_ARRAY_TRAVERSAL_TESTS
    + AVG_ARRAY_TRAVERSAL_LIST_TESTS
    + AVG_ARITY_TESTS
    + AVG_EXPRESSION_ARGS_TESTS
    + AVG_FIELD_PATH_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(AVG_INPUT_FORMS_TESTS))
def test_avg_input_form(collection, test_case: AvgTest):
    """Test $avg cases."""
    result = execute_expression(collection, {"$avg": test_case.args})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )


def test_avg_document_fields(collection):
    """Test $avg reads values from document fields."""
    result = execute_project_with_insert(
        collection,
        {"a": 10, "b": 20, "c": 30},
        {"result": {"$avg": ["$a", "$b", "$c"]}},
    )
    assertSuccess(result, [{"result": 20.0}], msg="$avg should read values from document fields")


def test_avg_document_field_array_traversal(collection):
    """Test $avg traverses an array field reference in single expression form."""
    result = execute_project_with_insert(
        collection,
        {"arr": [10, 20, 30]},
        {"result": {"$avg": "$arr"}},
    )
    assertSuccess(
        result,
        [{"result": 20.0}],
        msg="$avg should traverse an array field reference in single expression form",
    )


def test_avg_dotted_field_path_traversal(collection):
    """Test $avg traverses arrays via dotted field paths."""
    result = execute_project_with_insert(
        collection,
        {"a": [{"b": 1}, {"b": 2}, {"b": 3}]},
        {"result": {"$avg": "$a.b"}},
    )
    assertSuccess(
        result,
        [{"result": 2.0}],
        msg="$avg should traverse an array of objects via dotted path and average extracted values",
    )
