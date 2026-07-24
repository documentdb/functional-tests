"""
Combination tests for $size composed with other operators.
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

SIZE_COMBINATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="size_on_range",
        expression={"$size": {"$range": ["$start", "$end"]}},
        doc={"start": 0, "end": 10},
        expected=10,
        msg="Should return size of $range result",
    ),
    ExpressionTestCase(
        id="size_on_split",
        expression={"$size": {"$split": ["$str", ","]}},
        doc={"str": "a,b,c,d"},
        expected=4,
        msg="Should return size of $split result",
    ),
    ExpressionTestCase(
        id="size_on_slice",
        expression={"$size": {"$slice": ["$arr", 3]}},
        doc={"arr": [1, 2, 3, 4, 5]},
        expected=3,
        msg="Should return size of $slice result",
    ),
    ExpressionTestCase(
        id="size_on_objectToArray",
        expression={"$size": {"$objectToArray": "$obj"}},
        doc={"obj": {"a": 1, "b": 2}},
        expected=2,
        msg="Should return size of $objectToArray result",
    ),
    ExpressionTestCase(
        id="size_on_reverseArray",
        expression={"$size": {"$reverseArray": "$arr"}},
        doc={"arr": [1, 2, 3]},
        expected=3,
        msg="Should return size of $reverseArray result",
    ),
    ExpressionTestCase(
        id="size_subtract",
        expression={"$subtract": [{"$size": "$a"}, {"$size": "$b"}]},
        doc={"a": [1, 2, 3, 4, 5], "b": [1, 2]},
        expected=3,
        msg="Should subtract two $size results",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SIZE_COMBINATION_TESTS))
def test_size_combination(collection, test):
    """Test $size composed with other operators."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
