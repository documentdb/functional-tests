"""
Combination tests for $reverseArray composed with other operators.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

REVERSE_ARRAY_COMBINATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="reverseArray_on_concatArrays",
        expression={"$reverseArray": {"$concatArrays": ["$a", "$b"]}},
        doc={"a": [1, 2], "b": [3, 4]},
        expected=[4, 3, 2, 1],
        msg="Reverse concatenated arrays",
    ),
    ExpressionTestCase(
        id="reverseArray_on_sortArray",
        expression={"$reverseArray": {"$sortArray": {"input": "$arr", "sortBy": 1}}},
        doc={"arr": [3, 1, 2]},
        expected=[3, 2, 1],
        msg="Reverse sorted array",
    ),
    ExpressionTestCase(
        id="reverseArray_then_slice_last_n_reversed_order",
        expression={"$slice": [{"$reverseArray": "$arr"}, 2]},
        doc={"arr": [1, 2, 3, 4, 5]},
        expected=[5, 4],
        msg="reverse then $slice yields the last N elements in reversed order",
    ),
    ExpressionTestCase(
        id="reverseArray_on_objectToArray",
        expression={"$reverseArray": {"$objectToArray": "$obj"}},
        doc={"obj": {"a": 1, "b": 2, "c": 3}},
        expected=[{"k": "c", "v": 3}, {"k": "b", "v": 2}, {"k": "a", "v": 1}],
        msg="Reverse objectToArray",
    ),
    ExpressionTestCase(
        id="reverseArray_concat_reversed",
        expression={"$concatArrays": [{"$reverseArray": "$a"}, {"$reverseArray": "$b"}]},
        doc={"a": [1, 2], "b": [3, 4]},
        expected=[2, 1, 4, 3],
        msg="Concat of two reversed arrays",
    ),
    ExpressionTestCase(
        id="reverseArray_map_subarrays",
        expression={"$map": {"input": "$arr", "in": {"$reverseArray": "$$this"}}},
        doc={"arr": [[1, 2], [3, 4]]},
        expected=[[2, 1], [4, 3]],
        msg="$map reverses each subarray",
    ),
    ExpressionTestCase(
        id="reverseArray_inside_reduce",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": [],
                "in": {"$concatArrays": ["$$value", {"$reverseArray": "$$this"}]},
            }
        },
        doc={"arr": [[1, 2], [3, 4]]},
        expected=[2, 1, 4, 3],
        msg="$reverseArray used inside $reduce reverses each subarray while accumulating",
    ),
    ExpressionTestCase(
        id="reverseArray_slice_last_n_original_order",
        expression={"$reverseArray": {"$slice": [{"$reverseArray": "$arr"}, 2]}},
        doc={"arr": [1, 2, 3, 4, 5]},
        expected=[4, 5],
        msg="reverse + $slice + reverse yields last N elements in original order",
    ),
]


@pytest.mark.parametrize("test", pytest_params(REVERSE_ARRAY_COMBINATION_TESTS))
def test_reverseArray_combination(collection, test):
    """Test $reverseArray composed with other operators."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
