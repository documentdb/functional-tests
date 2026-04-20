"""
Tests for $lte same-type comparisons.

Covers numeric, string, boolean, date, object, array, and sign handling.
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
    ExpressionTestCase(
        "greater",
        expression={"$lte": [300, 250]},
        expected=False,
        msg="300 <= 250",
    ),
    ExpressionTestCase("less", expression={"$lte": [200, 250]}, expected=True, msg="200 <= 250"),
    ExpressionTestCase(
        "int_lt", expression={"$lte": [1, 2]}, expected=True, msg="int(1) <= int(2)"
    ),
    ExpressionTestCase(
        "int_gt", expression={"$lte": [2, 1]}, expected=False, msg="int(2) not <= int(1)"
    ),
    ExpressionTestCase(
        "int_eq", expression={"$lte": [1, 1]}, expected=True, msg="int(1) <= int(1)"
    ),
    ExpressionTestCase(
        "long_lt",
        expression={"$lte": [Int64(1), Int64(2)]},
        expected=True,
        msg="long(1) <= long(2)",
    ),
    ExpressionTestCase(
        "double_lt",
        expression={"$lte": [1.5, 2.5]},
        expected=True,
        msg="double(1.5) <= double(2.5)",
    ),
    ExpressionTestCase(
        "decimal_lt",
        expression={"$lte": [Decimal128("1"), Decimal128("2")]},
        expected=True,
        msg="decimal(1) <= decimal(2)",
    ),
    ExpressionTestCase("zero_self", expression={"$lte": [0, 0]}, expected=True, msg="0 <= 0"),
]

STRING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase("a_lte_b", expression={"$lte": ["a", "b"]}, expected=True, msg="'a' <= 'b'"),
    ExpressionTestCase(
        "b_lte_a", expression={"$lte": ["b", "a"]}, expected=False, msg="'b' not <= 'a'"
    ),
    ExpressionTestCase("a_lte_a", expression={"$lte": ["a", "a"]}, expected=True, msg="'a' <= 'a'"),
    ExpressionTestCase(
        "abc_lte_abd", expression={"$lte": ["abc", "abd"]}, expected=True, msg="'abc' <= 'abd'"
    ),
    ExpressionTestCase(
        "empty_lte_a", expression={"$lte": ["", "a"]}, expected=True, msg="'' <= 'a'"
    ),
    ExpressionTestCase(
        "a_lte_empty", expression={"$lte": ["a", ""]}, expected=False, msg="'a' not <= ''"
    ),
    ExpressionTestCase(
        "str_empty_lte_empty", expression={"$lte": ["", ""]}, expected=True, msg="'' <= ''"
    ),
    ExpressionTestCase(
        "apple_self", expression={"$lte": ["apple", "apple"]}, expected=True, msg="apple <= apple"
    ),
    ExpressionTestCase(
        "a_lte_A", expression={"$lte": ["a", "A"]}, expected=False, msg="lowercase > uppercase"
    ),
    ExpressionTestCase(
        "abc_lte_ab", expression={"$lte": ["abc", "ab"]}, expected=False, msg="abc not <= ab"
    ),
    ExpressionTestCase(
        "ab_lte_abc", expression={"$lte": ["ab", "abc"]}, expected=True, msg="ab <= abc"
    ),
    ExpressionTestCase(
        "z_lte_Z", expression={"$lte": ["z", "Z"]}, expected=False, msg="z not <= Z"
    ),
    ExpressionTestCase(
        "digit_0_lte_9", expression={"$lte": ["0", "9"]}, expected=True, msg="0 <= 9"
    ),
    ExpressionTestCase(
        "digit_9_lte_0", expression={"$lte": ["9", "0"]}, expected=False, msg="9 not <= 0"
    ),
    ExpressionTestCase(
        "space_lte_empty", expression={"$lte": [" ", ""]}, expected=False, msg="space not <= empty"
    ),
]

BOOLEAN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "false_lte_true", expression={"$lte": [False, True]}, expected=True, msg="false <= true"
    ),
    ExpressionTestCase(
        "true_lte_false",
        expression={"$lte": [True, False]},
        expected=False,
        msg="true not <= false",
    ),
    ExpressionTestCase(
        "false_lte_false", expression={"$lte": [False, False]}, expected=True, msg="false <= false"
    ),
    ExpressionTestCase(
        "true_lte_true", expression={"$lte": [True, True]}, expected=True, msg="true <= true"
    ),
]

DATE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "date_lt",
        expression={"$lte": [datetime(2024, 1, 1), datetime(2024, 12, 31)]},
        expected=True,
        msg="earlier date <= later date",
    ),
    ExpressionTestCase(
        "date_gt",
        expression={"$lte": [datetime(2024, 12, 31), datetime(2024, 1, 1)]},
        expected=False,
        msg="later date not <= earlier date",
    ),
    ExpressionTestCase(
        "date_eq",
        expression={"$lte": [datetime(2024, 1, 1), datetime(2024, 1, 1)]},
        expected=True,
        msg="same date <= same date",
    ),
]

OBJECT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "obj_lt", expression={"$lte": [{"a": 1}, {"a": 2}]}, expected=True, msg="{a:1} <= {a:2}"
    ),
    ExpressionTestCase(
        "obj_gt",
        expression={"$lte": [{"a": 2}, {"a": 1}]},
        expected=False,
        msg="{a:2} not <= {a:1}",
    ),
    ExpressionTestCase(
        "obj_eq", expression={"$lte": [{"a": 1}, {"a": 1}]}, expected=True, msg="{a:1} <= {a:1}"
    ),
    ExpressionTestCase(
        "empty_lte_obj", expression={"$lte": [{}, {"a": 1}]}, expected=True, msg="{} <= {a:1}"
    ),
    ExpressionTestCase(
        "obj_lte_empty", expression={"$lte": [{"a": 1}, {}]}, expected=False, msg="{a:1} not <= {}"
    ),
    ExpressionTestCase(
        "obj_empty_lte_empty", expression={"$lte": [{}, {}]}, expected=True, msg="{} <= {}"
    ),
]

ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase("arr_lt", expression={"$lte": [[1], [2]]}, expected=True, msg="[1] <= [2]"),
    ExpressionTestCase(
        "arr_gt", expression={"$lte": [[2], [1]]}, expected=False, msg="[2] not <= [1]"
    ),
    ExpressionTestCase("arr_eq", expression={"$lte": [[1], [1]]}, expected=True, msg="[1] <= [1]"),
    ExpressionTestCase(
        "empty_lte_arr", expression={"$lte": [[], [1]]}, expected=True, msg="[] <= [1]"
    ),
    ExpressionTestCase(
        "arr_1_lte_empty", expression={"$lte": [[1], []]}, expected=False, msg="[1] not <= []"
    ),
    ExpressionTestCase(
        "prefix_lte_longer",
        expression={"$lte": [[1, 2], [1, 2, 3]]},
        expected=True,
        msg="shorter prefix <= longer",
    ),
    ExpressionTestCase(
        "element_wise",
        expression={"$lte": [[1, 3], [1, 2, 999]]},
        expected=False,
        msg="[1,3] not <= [1,2,999] element-wise",
    ),
    ExpressionTestCase(
        "empty_arr_self", expression={"$lte": [[], []]}, expected=True, msg="[] <= []"
    ),
    ExpressionTestCase(
        "arr_12_lte_1", expression={"$lte": [[1, 2], [1]]}, expected=False, msg="[1,2] not <= [1]"
    ),
    ExpressionTestCase(
        "arr_1_lte_12", expression={"$lte": [[1], [1, 2]]}, expected=True, msg="[1] <= [1,2]"
    ),
    ExpressionTestCase(
        "arr_12_self", expression={"$lte": [[1, 2], [1, 2]]}, expected=True, msg="[1,2] <= [1,2]"
    ),
    ExpressionTestCase(
        "arr_null_lte_empty",
        expression={"$lte": [[None], []]},
        expected=False,
        msg="[null] not <= []",
    ),
]

SIGN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase("neg_lte_pos", expression={"$lte": [-1, 1]}, expected=True, msg="-1 <= 1"),
    ExpressionTestCase(
        "pos_lte_neg", expression={"$lte": [1, -1]}, expected=False, msg="1 not <= -1"
    ),
    ExpressionTestCase("neg_lte_neg", expression={"$lte": [-1, -1]}, expected=True, msg="-1 <= -1"),
    ExpressionTestCase("zero_lte_zero", expression={"$lte": [0, 0]}, expected=True, msg="0 <= 0"),
    ExpressionTestCase("neg_lte_zero", expression={"$lte": [-1, 0]}, expected=True, msg="-1 <= 0"),
    ExpressionTestCase(
        "zero_lte_neg", expression={"$lte": [0, -1]}, expected=False, msg="0 not <= -1"
    ),
]

NESTED_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_1_lte_0",
        expression={"$lte": [[[1]], [[0]]]},
        expected=False,
        msg="[[1]] not <= [[0]]",
    ),
]

ALL_TESTS: list[ExpressionTestCase] = (
    NUMERIC_TESTS
    + STRING_TESTS
    + BOOLEAN_TESTS
    + DATE_TESTS
    + OBJECT_TESTS
    + ARRAY_TESTS
    + SIGN_TESTS
    + NESTED_ARRAY_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_lte_same_type_comparisons(collection, test):
    """Test $lte same-type comparisons."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
