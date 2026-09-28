"""
Combination tests for $sortArray composed with other operators.
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

SORT_ARRAY_COMBINATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="sortArray_on_filter",
        expression={
            "$sortArray": {
                "input": {"$filter": {"input": "$arr", "cond": {"$gt": ["$$this", 2]}}},
                "sortBy": 1,
            }
        },
        doc={"arr": [3, 1, 4, 1, 5]},
        expected=[3, 4, 5],
        msg="Should sort $filter result",
    ),
    ExpressionTestCase(
        id="sortArray_on_concatArrays",
        expression={"$sortArray": {"input": {"$concatArrays": ["$a", "$b"]}, "sortBy": 1}},
        doc={"a": [3, 1], "b": [2, 4]},
        expected=[1, 2, 3, 4],
        msg="Should sort $concatArrays result",
    ),
    ExpressionTestCase(
        id="sortArray_on_reverseArray",
        expression={"$sortArray": {"input": {"$reverseArray": "$arr"}, "sortBy": 1}},
        doc={"arr": [3, 1, 2]},
        expected=[1, 2, 3],
        msg="Should sort $reverseArray result",
    ),
    ExpressionTestCase(
        id="sortArray_reverseArray_sortArray",
        expression={
            "$sortArray": {
                "input": {"$reverseArray": {"$sortArray": {"input": "$arr", "sortBy": 1}}},
                "sortBy": 1,
            }
        },
        doc={"arr": [3, 1, 2]},
        expected=[1, 2, 3],
        msg="Should sort $reverseArray of $sortArray result",
    ),
    ExpressionTestCase(
        id="sortArray_on_range",
        expression={"$sortArray": {"input": {"$range": ["$start", "$end", "$step"]}, "sortBy": 1}},
        doc={"start": 5, "end": 0, "step": -1},
        expected=[1, 2, 3, 4, 5],
        msg="Should sort $range result",
    ),
    ExpressionTestCase(
        id="sortArray_on_setUnion",
        expression={"$sortArray": {"input": {"$setUnion": [[3, 1], [2, 1]]}, "sortBy": 1}},
        doc={"x": 0},
        expected=[1, 2, 3],
        msg="Should sort $setUnion result (manual B24)",
    ),
    ExpressionTestCase(
        id="sortArray_result_arrayElemAt",
        expression={"$arrayElemAt": [{"$sortArray": {"input": "$arr", "sortBy": 1}}, 0]},
        doc={"arr": [3, 1, 2]},
        expected=1,
        msg="$arrayElemAt on $sortArray result returns first sorted element",
    ),
    ExpressionTestCase(
        id="sortArray_result_in_eq",
        expression={"$eq": [{"$sortArray": {"input": "$arr", "sortBy": 1}}, [1, 2, 3]]},
        doc={"arr": [3, 1, 2]},
        expected=True,
        msg="$eq on $sortArray result",
    ),
    ExpressionTestCase(
        id="sortArray_objectToArray_by_k",
        expression={"$sortArray": {"input": {"$objectToArray": "$obj"}, "sortBy": {"k": 1}}},
        doc={"obj": {"c": 3, "a": 1, "b": 2}},
        expected=[{"k": "a", "v": 1}, {"k": "b", "v": 2}, {"k": "c", "v": 3}],
        msg="Sort $objectToArray output by key field 'k' (manual B22)",
    ),
    ExpressionTestCase(
        id="sortArray_nested_in_sortArray",
        expression={
            "$sortArray": {
                "input": {"$sortArray": {"input": "$arr", "sortBy": -1}},
                "sortBy": 1,
            }
        },
        doc={"arr": [3, 1, 2]},
        expected=[1, 2, 3],
        msg="Nested $sortArray inside $sortArray — inner desc then outer asc (manual B25)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SORT_ARRAY_COMBINATION_TESTS))
def test_sortArray_combination(collection, test):
    """Test $sortArray composed with other operators."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
