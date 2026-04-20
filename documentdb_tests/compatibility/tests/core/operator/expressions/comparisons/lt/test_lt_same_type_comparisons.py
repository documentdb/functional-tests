"""
Tests for $lt same-type comparisons and within-type ordering.

Covers string, object, array, date, and boolean comparisons.
"""

from datetime import datetime

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

NUMERIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase("int_lt", expression={"$lt": [1, 2]}, expected=True, msg="int 1 < 2"),
    ExpressionTestCase("int_eq", expression={"$lt": [1, 1]}, expected=False, msg="int 1 not < 1"),
    ExpressionTestCase("int_gt", expression={"$lt": [2, 1]}, expected=False, msg="int 2 not < 1"),
    ExpressionTestCase(
        "long_lt", expression={"$lt": [Int64(1), Int64(2)]}, expected=True, msg="long 1 < 2"
    ),
    ExpressionTestCase(
        "long_eq", expression={"$lt": [Int64(1), Int64(1)]}, expected=False, msg="long 1 not < 1"
    ),
    ExpressionTestCase(
        "double_lt", expression={"$lt": [1.0, 1.5]}, expected=True, msg="double 1.0 < 1.5"
    ),
    ExpressionTestCase(
        "double_eq", expression={"$lt": [1.0, 1.0]}, expected=False, msg="double 1.0 not < 1.0"
    ),
    ExpressionTestCase(
        "dec_lt",
        expression={"$lt": [Decimal128("1"), Decimal128("2")]},
        expected=True,
        msg="dec 1 < 2",
    ),
    ExpressionTestCase(
        "dec_eq",
        expression={"$lt": [Decimal128("1"), Decimal128("1")]},
        expected=False,
        msg="dec 1 not < 1",
    ),
    ExpressionTestCase("neg_lt_pos", expression={"$lt": [-1, 1]}, expected=True, msg="-1 < 1"),
    ExpressionTestCase("pos_lt_neg", expression={"$lt": [1, -1]}, expected=False, msg="1 not < -1"),
    ExpressionTestCase("neg_lt_zero", expression={"$lt": [-1, 0]}, expected=True, msg="-1 < 0"),
    ExpressionTestCase(
        "zero_lt_neg", expression={"$lt": [0, -1]}, expected=False, msg="0 not < -1"
    ),
    ExpressionTestCase(
        "neg_lt_neg", expression={"$lt": [-1, -1]}, expected=False, msg="-1 not < -1"
    ),
]


STRING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "apple_lt_banana",
        expression={"$lt": ["apple", "banana"]},
        expected=True,
        msg="apple < banana",
    ),
    ExpressionTestCase(
        "banana_lt_apple",
        expression={"$lt": ["banana", "apple"]},
        expected=False,
        msg="banana not < apple",
    ),
    ExpressionTestCase(
        "apple_self",
        expression={"$lt": ["apple", "apple"]},
        expected=False,
        msg="apple not < apple",
    ),
    ExpressionTestCase(
        "Apple_lt_apple",
        expression={"$lt": ["Apple", "apple"]},
        expected=True,
        msg="uppercase < lowercase",
    ),
    ExpressionTestCase(
        "apple_lt_Apple",
        expression={"$lt": ["apple", "Apple"]},
        expected=False,
        msg="lowercase not < uppercase",
    ),
    ExpressionTestCase("empty_lt_a", expression={"$lt": ["", "a"]}, expected=True, msg="empty < a"),
    ExpressionTestCase(
        "a_lt_empty", expression={"$lt": ["a", ""]}, expected=False, msg="a not < empty"
    ),
    ExpressionTestCase(
        "empty_self", expression={"$lt": ["", ""]}, expected=False, msg="empty not < empty"
    ),
    ExpressionTestCase(
        "ab_lt_abc", expression={"$lt": ["ab", "abc"]}, expected=True, msg="shorter prefix < longer"
    ),
    ExpressionTestCase(
        "abc_lt_ab",
        expression={"$lt": ["abc", "ab"]},
        expected=False,
        msg="longer not < shorter prefix",
    ),
]

OBJECT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "obj_a1_lt_a2", expression={"$lt": [{"a": 1}, {"a": 2}]}, expected=True, msg="{a:1} < {a:2}"
    ),
    ExpressionTestCase(
        "obj_a1_self",
        expression={"$lt": [{"a": 1}, {"a": 1}]},
        expected=False,
        msg="{a:1} not < {a:1}",
    ),
    ExpressionTestCase(
        "obj_a_lt_ab",
        expression={"$lt": [{"a": 1}, {"a": 1, "b": 1}]},
        expected=True,
        msg="fewer fields < more",
    ),
    ExpressionTestCase(
        "empty_obj_self", expression={"$lt": [{}, {}]}, expected=False, msg="{} not < {}"
    ),
    ExpressionTestCase(
        "empty_lt_obj", expression={"$lt": [{}, {"a": 1}]}, expected=True, msg="{} < {a:1}"
    ),
]


ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "arr_1_lt_2", expression={"$lt": [[1], [2]]}, expected=True, msg="[1] < [2]"
    ),
    ExpressionTestCase(
        "arr_1_self", expression={"$lt": [[1], [1]]}, expected=False, msg="[1] not < [1]"
    ),
    ExpressionTestCase(
        "arr_1_lt_12", expression={"$lt": [[1], [1, 2]]}, expected=True, msg="[1] < [1,2]"
    ),
    ExpressionTestCase(
        "arr_12_self", expression={"$lt": [[1, 2], [1, 2]]}, expected=False, msg="[1,2] not < [1,2]"
    ),
    ExpressionTestCase(
        "empty_arr_self", expression={"$lt": [[], []]}, expected=False, msg="[] not < []"
    ),
    ExpressionTestCase(
        "empty_lt_arr_1", expression={"$lt": [[], [1]]}, expected=True, msg="[] < [1]"
    ),
    ExpressionTestCase(
        "arr_5_100_200_lt_4_15",
        expression={"$lt": [[5, 100, 200], [4, 15, 300, 400, 500]]},
        expected=False,
        msg="first elem 5 > 4",
    ),
    ExpressionTestCase(
        "arr_5_14_lt_5_15",
        expression={"$lt": [[5, 14], [5, 15]]},
        expected=True,
        msg="second elem 14 < 15",
    ),
    ExpressionTestCase(
        "arr_5_14_100_lt_5_15_0",
        expression={"$lt": [[5, 14, 100], [5, 15, 0]]},
        expected=True,
        msg="second elem 14 < 15",
    ),
]


NESTED_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_0_lt_1", expression={"$lt": [[[0]], [[1]]]}, expected=True, msg="[[0]] < [[1]]"
    ),
    ExpressionTestCase(
        "null_0_lt_null_1",
        expression={"$lt": [[None, 0], [None, 1]]},
        expected=True,
        msg="second element comparison",
    ),
    ExpressionTestCase(
        "arr_1_lt_1_null",
        expression={"$lt": [[1], [1, None]]},
        expected=True,
        msg="shorter < longer with same prefix",
    ),
]


DATE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "date_earlier_lt_later",
        expression={"$lt": [datetime(2025, 1, 1), datetime(2025, 6, 1)]},
        expected=True,
        msg="earlier < later",
    ),
    ExpressionTestCase(
        "date_later_lt_earlier",
        expression={"$lt": [datetime(2025, 6, 1), datetime(2025, 1, 1)]},
        expected=False,
        msg="later not < earlier",
    ),
    ExpressionTestCase(
        "date_self",
        expression={"$lt": [datetime(2025, 1, 1), datetime(2025, 1, 1)]},
        expected=False,
        msg="same date not < itself",
    ),
]


BOOLEAN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "false_lt_true", expression={"$lt": [False, True]}, expected=True, msg="false < true"
    ),
    ExpressionTestCase(
        "true_lt_false", expression={"$lt": [True, False]}, expected=False, msg="true not < false"
    ),
    ExpressionTestCase(
        "true_self", expression={"$lt": [True, True]}, expected=False, msg="true not < true"
    ),
    ExpressionTestCase(
        "false_self", expression={"$lt": [False, False]}, expected=False, msg="false not < false"
    ),
]


ALL_TESTS = (
    NUMERIC_TESTS
    + STRING_TESTS
    + OBJECT_TESTS
    + ARRAY_TESTS
    + NESTED_ARRAY_TESTS
    + DATE_TESTS
    + BOOLEAN_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_lt_same_type_comparisons(collection, test):
    """Test $lt same-type comparisons and within-type ordering."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
