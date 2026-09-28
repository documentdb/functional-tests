"""
Combination tests for $concatArrays composed with other operators.
"""

import math

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression_with_insert,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import FLOAT_NAN

CONCAT_ARRAYS_COMBINATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="concatArrays_on_range",
        expression={"$concatArrays": [{"$range": [0, 3]}, {"$range": [3, 6]}]},
        doc={"x": 1},
        expected=[0, 1, 2, 3, 4, 5],
        msg="Should concatenate two $range results",
    ),
    ExpressionTestCase(
        id="size_of_concatArrays",
        expression={"$size": {"$concatArrays": ["$a", "$b"]}},
        doc={"a": [1, 2], "b": [3, 4, 5]},
        expected=5,
        msg="$size on $concatArrays result",
    ),
    ExpressionTestCase(
        id="size_of_empty_concatArrays",
        expression={"$size": {"$concatArrays": ["$a", "$b"]}},
        doc={"a": [], "b": []},
        expected=0,
        msg="Size of empty concatenation",
    ),
    ExpressionTestCase(
        id="concatArrays_reverseArray_concatArrays",
        expression={
            "$concatArrays": [
                {"$reverseArray": {"$concatArrays": ["$a", "$b"]}},
                "$c",
            ]
        },
        doc={"a": [1, 2], "b": [3], "c": [4]},
        expected=[3, 2, 1, 4],
        msg="Should concatenate reversed concat result with another array",
    ),
    ExpressionTestCase(
        id="isArray_on_concatArrays",
        expression={"$isArray": {"$concatArrays": ["$a", "$b"]}},
        doc={"a": [1], "b": [2]},
        expected=True,
        msg="$isArray on $concatArrays result should return true",
    ),
    ExpressionTestCase(
        id="in_found_in_concatArrays",
        expression={"$in": [3, {"$concatArrays": ["$a", "$b"]}]},
        doc={"a": [1, 2], "b": [3, 4]},
        expected=True,
        msg="Element found in concatenated array",
    ),
    ExpressionTestCase(
        id="isArray_null_concatArrays",
        expression={"$isArray": {"$concatArrays": ["$a", "$b"]}},
        doc={"a": None, "b": [1]},
        expected=False,
        msg="Null result is not array",
    ),
    ExpressionTestCase(
        id="float_nan_preserved",
        expression={"$arrayElemAt": [{"$concatArrays": ["$a", "$b"]}, 0]},
        doc={"a": [FLOAT_NAN], "b": [1]},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Float NaN element preserved after concatenation",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CONCAT_ARRAYS_COMBINATION_TESTS))
def test_concatArrays_combination(collection, test):
    """Test $concatArrays composed with other operators."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    expected = [{"result": test.expected}] if test.error_code is None else None
    assertResult(result, expected=expected, error_code=test.error_code, msg=test.msg)
