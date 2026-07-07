"""
Combination tests for $zip composed with other operators.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import FLOAT_NAN

ZIP_COMBINATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="zip_on_sortArray",
        expression={"$zip": {"inputs": [{"$sortArray": {"input": "$a", "sortBy": 1}}, "$b"]}},
        doc={"a": [3, 1, 2], "b": [10, 20, 30]},
        expected=[[1, 10], [2, 20], [3, 30]],
        msg="Should zip $sortArray result with array",
    ),
    ExpressionTestCase(
        id="zip_on_concatArrays",
        expression={"$zip": {"inputs": [{"$concatArrays": ["$a", "$b"]}, "$c"]}},
        doc={"a": [1], "b": [2], "c": [10, 20]},
        expected=[[1, 10], [2, 20]],
        msg="Should zip $concatArrays result with array",
    ),
    ExpressionTestCase(
        id="zip_on_range",
        expression={"$zip": {"inputs": [{"$range": [0, 3]}, {"$range": [10, 13]}]}},
        doc={"x": 1},
        expected=[[0, 10], [1, 11], [2, 12]],
        msg="Should zip two $range results",
    ),
    ExpressionTestCase(
        id="arrayElemAt_on_zip",
        expression={"$arrayElemAt": [{"$zip": {"inputs": ["$a", "$b"]}}, 1]},
        doc={"a": [1, 2, 3], "b": [10, 20, 30]},
        expected=[2, 20],
        msg="$arrayElemAt on $zip result",
    ),
    ExpressionTestCase(
        id="zip_matrix_transpose_2x3",
        expression={
            "$zip": {
                "inputs": [
                    {"$arrayElemAt": ["$matrix", 0]},
                    {"$arrayElemAt": ["$matrix", 1]},
                ]
            }
        },
        doc={"matrix": [[0, 1, 2], [3, 4, 5]]},
        expected=[[0, 3], [1, 4], [2, 5]],
        msg="2x3 matrix transposed to 3x2",
    ),
    ExpressionTestCase(
        id="zip_index_preservation",
        expression={"$zip": {"inputs": ["$arr", {"$range": [0, {"$size": "$arr"}]}]}},
        doc={"arr": ["a", "b", "c"]},
        expected=[["a", 0], ["b", 1], ["c", 2]],
        msg="Elements paired with indices",
    ),
    ExpressionTestCase(
        id="zip_reduce_on_output",
        expression={
            "$reduce": {
                "input": {"$zip": {"inputs": ["$a", "$b"]}},
                "initialValue": 0,
                "in": {"$add": ["$$value", {"$arrayElemAt": ["$$this", 1]}]},
            }
        },
        doc={"a": [1, 2, 3], "b": [10, 20, 30]},
        expected=60,
        msg="$reduce sums second elements of zipped pairs",
    ),
    ExpressionTestCase(
        id="zip_output_is_array",
        expression={"$isArray": {"$zip": {"inputs": ["$a", "$b"]}}},
        doc={"a": [1, 2], "b": ["a", "b"]},
        expected=True,
        msg="Output is an array",
    ),
    ExpressionTestCase(
        id="float_nan_preserved",
        expression={"$arrayElemAt": [{"$arrayElemAt": [{"$zip": {"inputs": ["$a", "$b"]}}, 0]}, 0]},
        doc={"a": [FLOAT_NAN], "b": [1]},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="Float NaN element preserved after zipping",
    ),
    ExpressionTestCase(
        id="default_float_nan",
        expression={
            "$arrayElemAt": [
                {
                    "$arrayElemAt": [
                        {
                            "$zip": {
                                "inputs": ["$a", "$b"],
                                "useLongestLength": True,
                                "defaults": [0, FLOAT_NAN],
                            }
                        },
                        1,
                    ]
                },
                1,
            ]
        },
        doc={"a": [1, 2], "b": [10]},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="Should use float NaN as default value",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ZIP_COMBINATION_TESTS))
def test_zip_combination(collection, test):
    """Test $zip composed with other operators."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
