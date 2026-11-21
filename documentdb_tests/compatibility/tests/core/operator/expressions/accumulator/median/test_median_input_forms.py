from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.accumulator.median.utils.median_common import (  # noqa: E501
    MedianTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_project_with_insert,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.parametrize import pytest_params

# Property [Array Traversal (Single Expression Form)]: when a single
# expression resolves to an array, $median traverses one level into it to
# find the median of its numeric elements. Nested arrays and non-numeric elements are
# ignored.
MEDIAN_ARRAY_TRAVERSAL_TESTS: list[MedianTest] = [
    MedianTest(
        "traversal_basic",
        args={"$literal": [10, 20, 30]},
        expected=20.0,
        msg="$median should traverse a literal array and find the median of its numeric elements",
    ),
    MedianTest(
        "traversal_nested_array_ignored",
        args={"$literal": [10, [20, 30], 40]},
        expected=25.0,
        msg="$median should ignore nested arrays as non-numeric during traversal",
    ),
    MedianTest(
        "traversal_double_nested",
        args={"$literal": [[10, 20, 30]]},
        expected=None,
        msg="$median should return null when the only element is a nested array",
    ),
    MedianTest(
        "traversal_non_numeric_ignored",
        args={"$literal": [10, "hello", Int64(20), None, 30.0, Decimal128("7")]},
        expected=15.0,
        msg="$median should ignore non-numeric elements and null during array traversal",
    ),
    MedianTest(
        "traversal_all_non_numeric",
        args={"$literal": ["hello", True]},
        expected=None,
        msg="$median should return null when all traversed elements are non-numeric",
    ),
    MedianTest(
        "traversal_all_null",
        args={"$literal": [None, None]},
        expected=None,
        msg="$median should return null when all traversed elements are null",
    ),
    MedianTest(
        "traversal_empty_array",
        args={"$literal": []},
        expected=None,
        msg="$median should return null for an empty traversed array",
    ),
]

# Property [Arity]: $median returns null for an empty operand list and
# correctly computes the median of large operand counts.
MEDIAN_ARITY_TESTS: list[MedianTest] = [
    MedianTest(
        "arity_empty_array",
        args=[],
        expected=None,
        msg="$median should return null for an empty operand list",
    ),
    MedianTest(
        "arity_single_element_list",
        args=[42],
        expected=42.0,
        msg="$median of a single-element list should return that value as double",
    ),
    MedianTest(
        "arity_10_000_elements",
        args=list(range(10_000)),
        expected=4999.5,
        msg="$median should correctly compute median of 10000 elements",
    ),
    MedianTest(
        "arity_10_000_identical",
        args=[7] * 10_000,
        expected=7.0,
        msg="$median of 10000 identical values should return that value",
    ),
]

# Property [Expression Arguments]: $median accepts arbitrary expressions as
# operands, evaluating each before computing the median.
MEDIAN_EXPRESSION_ARGS_TESTS: list[MedianTest] = [
    MedianTest(
        "expr_add",
        args={"$literal": [10, 20, {"$add": [15, 15]}]},
        expected=20.0,
        msg="$median should accept $add expression as an operand within the array",
    ),
    MedianTest(
        "expr_returning_null",
        args={"$literal": [10, {"$literal": None}, 20]},
        expected=15.0,
        msg="$median should ignore an expression that returns null within the array",
    ),
    MedianTest(
        "expr_returning_non_numeric",
        args={"$literal": [10, {"$toString": 42}, 20]},
        expected=15.0,
        msg="$median should ignore an expression that returns a non-numeric type",
    ),
]

MEDIAN_INPUT_FORMS_TESTS = (
    MEDIAN_ARRAY_TRAVERSAL_TESTS + MEDIAN_ARITY_TESTS + MEDIAN_EXPRESSION_ARGS_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(MEDIAN_INPUT_FORMS_TESTS))
def test_median_input_form(collection, test_case: MedianTest):
    """Test $median input cases."""
    result = execute_expression(
        collection, {"$median": {"input": test_case.args, "method": "approximate"}}
    )
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )


def test_median_document_fields(collection):
    """Test $median reads values from document fields."""
    result = execute_project_with_insert(
        collection,
        {"arr": [10, 20, 30]},
        {"result": {"$median": {"input": "$arr", "method": "approximate"}}},
    )
    assertSuccess(result, [{"result": 20.0}], msg="$median should read values from document fields")


def test_median_dotted_field_path_traversal(collection):
    """Test $median traverses arrays via dotted field paths."""
    result = execute_project_with_insert(
        collection,
        {"a": [{"b": 10}, {"b": 20}, {"b": 30}]},
        {"result": {"$median": {"input": "$a.b", "method": "approximate"}}},
    )
    assertSuccess(
        result,
        [{"result": 20.0}],
        msg="$median should traverse an array of objects via dotted path and find the median",
    )
