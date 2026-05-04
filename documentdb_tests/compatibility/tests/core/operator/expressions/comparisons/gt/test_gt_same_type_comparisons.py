"""
Tests for $gt same-type comparisons and within-type ordering.

Covers string, object, array, date, and boolean comparisons.
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

CORE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase("greater", expression={"$gt": [300, 250]}, expected=True, msg="300 > 250"),
    ExpressionTestCase("less", expression={"$gt": [200, 250]}, expected=False, msg="200 not > 250"),
    ExpressionTestCase(
        "equal", expression={"$gt": [250, 250]}, expected=False, msg="250 not > 250"
    ),
]

STRING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "banana_gt_apple",
        expression={"$gt": ["banana", "apple"]},
        expected=True,
        msg="banana > apple",
    ),
    ExpressionTestCase(
        "apple_gt_banana",
        expression={"$gt": ["apple", "banana"]},
        expected=False,
        msg="apple not > banana",
    ),
    ExpressionTestCase(
        "upper_A_gt_lower_a",
        expression={"$gt": ["Apple", "apple"]},
        expected=False,
        msg="uppercase < lowercase",
    ),
    ExpressionTestCase(
        "lower_a_gt_upper_A",
        expression={"$gt": ["apple", "Apple"]},
        expected=True,
        msg="lowercase > uppercase",
    ),
    ExpressionTestCase("a_gt_A", expression={"$gt": ["a", "A"]}, expected=True, msg="a > A"),
    ExpressionTestCase(
        "empty_gt_a", expression={"$gt": ["", "a"]}, expected=False, msg="empty not > a"
    ),
    ExpressionTestCase("a_gt_empty", expression={"$gt": ["a", ""]}, expected=True, msg="a > empty"),
    ExpressionTestCase(
        "empty_gt_empty", expression={"$gt": ["", ""]}, expected=False, msg="empty not > empty"
    ),
    ExpressionTestCase(
        "abc_gt_ab", expression={"$gt": ["abc", "ab"]}, expected=True, msg="longer prefix wins"
    ),
    ExpressionTestCase(
        "abd_gt_abc", expression={"$gt": ["abd", "abc"]}, expected=True, msg="last char comparison"
    ),
    ExpressionTestCase(
        "abc_gt_abd", expression={"$gt": ["abc", "abd"]}, expected=False, msg="abc not > abd"
    ),
    ExpressionTestCase("z_gt_Z", expression={"$gt": ["z", "Z"]}, expected=True, msg="z > Z"),
    ExpressionTestCase(
        "digit_0_gt_9", expression={"$gt": ["0", "9"]}, expected=False, msg="0 not > 9"
    ),
    ExpressionTestCase("digit_9_gt_0", expression={"$gt": ["9", "0"]}, expected=True, msg="9 > 0"),
    ExpressionTestCase(
        "space_gt_empty", expression={"$gt": [" ", ""]}, expected=True, msg="space > empty"
    ),
]

OBJECT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "obj_a2_gt_a1", expression={"$gt": [{"a": 2}, {"a": 1}]}, expected=True, msg="{a:2} > {a:1}"
    ),
    ExpressionTestCase(
        "obj_a1_gt_a2",
        expression={"$gt": [{"a": 1}, {"a": 2}]},
        expected=False,
        msg="{a:1} not > {a:2}",
    ),
    ExpressionTestCase(
        "obj_ab_gt_a",
        expression={"$gt": [{"a": 1, "b": 1}, {"a": 1}]},
        expected=True,
        msg="more fields > fewer",
    ),
    ExpressionTestCase(
        "obj_a_gt_ab",
        expression={"$gt": [{"a": 1}, {"a": 1, "b": 1}]},
        expected=False,
        msg="fewer not > more",
    ),
    ExpressionTestCase(
        "obj_b_gt_a",
        expression={"$gt": [{"b": 1}, {"a": 1}]},
        expected=True,
        msg="field b > field a",
    ),
    ExpressionTestCase(
        "obj_a_gt_b",
        expression={"$gt": [{"a": 1}, {"b": 1}]},
        expected=False,
        msg="field a not > field b",
    ),
    ExpressionTestCase(
        "empty_obj_self", expression={"$gt": [{}, {}]}, expected=False, msg="{} not > {}"
    ),
    ExpressionTestCase(
        "obj_gt_empty", expression={"$gt": [{"a": 1}, {}]}, expected=True, msg="{a:1} > {}"
    ),
    ExpressionTestCase(
        "empty_gt_obj", expression={"$gt": [{}, {"a": 1}]}, expected=False, msg="{} not > {a:1}"
    ),
]

ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "arr_2_gt_1", expression={"$gt": [[2], [1]]}, expected=True, msg="[2] > [1]"
    ),
    ExpressionTestCase(
        "arr_1_gt_2", expression={"$gt": [[1], [2]]}, expected=False, msg="[1] not > [2]"
    ),
    ExpressionTestCase(
        "arr_12_gt_1", expression={"$gt": [[1, 2], [1]]}, expected=True, msg="[1,2] > [1]"
    ),
    ExpressionTestCase(
        "arr_1_gt_12", expression={"$gt": [[1], [1, 2]]}, expected=False, msg="[1] not > [1,2]"
    ),
    ExpressionTestCase(
        "arr_12_self", expression={"$gt": [[1, 2], [1, 2]]}, expected=False, msg="[1,2] not > [1,2]"
    ),
    ExpressionTestCase(
        "arr_2_gt_1_999",
        expression={"$gt": [[2], [1, 999]]},
        expected=True,
        msg="first element wins",
    ),
    ExpressionTestCase(
        "empty_arr_self", expression={"$gt": [[], []]}, expected=False, msg="[] not > []"
    ),
    ExpressionTestCase(
        "arr_1_gt_empty", expression={"$gt": [[1], []]}, expected=True, msg="[1] > []"
    ),
    ExpressionTestCase(
        "empty_gt_arr_1", expression={"$gt": [[], [1]]}, expected=False, msg="[] not > [1]"
    ),
    ExpressionTestCase(
        "arr_null_gt_empty", expression={"$gt": [[None], []]}, expected=True, msg="[null] > []"
    ),
]

NESTED_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_1_gt_0", expression={"$gt": [[[1]], [[0]]]}, expected=True, msg="[[1]] > [[0]]"
    ),
    ExpressionTestCase(
        "null_1_gt_null_0",
        expression={"$gt": [[None, 1], [None, 0]]},
        expected=True,
        msg="second element comparison",
    ),
    ExpressionTestCase(
        "arr_1_null_gt_1",
        expression={"$gt": [[1, None], [1]]},
        expected=True,
        msg="longer with same prefix",
    ),
]

DATE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "later_date",
        expression={
            "$gt": [
                datetime(2025, 6, 1, tzinfo=timezone.utc),
                datetime(2025, 1, 1, tzinfo=timezone.utc),
            ]
        },
        expected=True,
        msg="later date > earlier",
    ),
    ExpressionTestCase(
        "earlier_date",
        expression={
            "$gt": [
                datetime(2025, 1, 1, tzinfo=timezone.utc),
                datetime(2025, 6, 1, tzinfo=timezone.utc),
            ]
        },
        expected=False,
        msg="earlier not > later",
    ),
    ExpressionTestCase(
        "same_date",
        expression={
            "$gt": [
                datetime(2025, 1, 1, tzinfo=timezone.utc),
                datetime(2025, 1, 1, tzinfo=timezone.utc),
            ]
        },
        expected=False,
        msg="same date not > same date",
    ),
    ExpressionTestCase(
        "millisecond_precision",
        expression={
            "$gt": [
                datetime(2025, 1, 1, 0, 0, 0, 1000, tzinfo=timezone.utc),
                datetime(2025, 1, 1, tzinfo=timezone.utc),
            ]
        },
        expected=True,
        msg="1ms later > earlier",
    ),
]

BOOLEAN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "true_gt_false", expression={"$gt": [True, False]}, expected=True, msg="true > false"
    ),
    ExpressionTestCase(
        "false_gt_true", expression={"$gt": [False, True]}, expected=False, msg="false not > true"
    ),
    ExpressionTestCase(
        "true_self", expression={"$gt": [True, True]}, expected=False, msg="true not > true"
    ),
    ExpressionTestCase(
        "false_self", expression={"$gt": [False, False]}, expected=False, msg="false not > false"
    ),
]

OBJECTID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "objectid_gt",
        expression={
            "$gt": [ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa"), ObjectId("000000000000000000000000")]
        },
        expected=True,
        msg="higher ObjectId > lower ObjectId",
    ),
]

BINDATA_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "bindata_longer_gt_shorter",
        expression={"$gt": [Binary(b"\x01\x02\x03", 0), Binary(b"\x01\x02", 0)]},
        expected=True,
        msg="longer BinData > shorter BinData",
    ),
    ExpressionTestCase(
        "bindata_higher_bytes",
        expression={"$gt": [Binary(b"\x02", 0), Binary(b"\x01", 0)]},
        expected=True,
        msg="same length, higher bytes > lower bytes",
    ),
    ExpressionTestCase(
        "bindata_equal",
        expression={"$gt": [Binary(b"\x01", 0), Binary(b"\x01", 0)]},
        expected=False,
        msg="equal BinData not > equal BinData",
    ),
    ExpressionTestCase(
        "bindata_diff_subtype",
        expression={"$gt": [Binary(b"\x01", 5), Binary(b"\x01", 0)]},
        expected=True,
        msg="higher subtype > lower subtype (same data)",
    ),
]

TIMESTAMP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "ts_lower_seconds",
        expression={"$gt": [Timestamp(50, 1), Timestamp(100, 1)]},
        expected=False,
        msg="lower seconds not > higher seconds",
    ),
    ExpressionTestCase(
        "ts_equal",
        expression={"$gt": [Timestamp(100, 1), Timestamp(100, 1)]},
        expected=False,
        msg="equal timestamp not > equal timestamp",
    ),
    ExpressionTestCase(
        "ts_same_seconds_higher_ordinal",
        expression={"$gt": [Timestamp(100, 2), Timestamp(100, 1)]},
        expected=True,
        msg="same seconds, higher ordinal > lower ordinal",
    ),
]

REGEX_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "regex_higher_pattern",
        expression={"$gt": [Regex("def"), Regex("abc")]},
        expected=True,
        msg="higher pattern > lower pattern",
    ),
    ExpressionTestCase(
        "regex_equal",
        expression={"$gt": [Regex("abc"), Regex("abc")]},
        expected=False,
        msg="same regex not > same regex",
    ),
    ExpressionTestCase(
        "regex_flags_gt_no_flags",
        expression={"$gt": [Regex("abc", "i"), Regex("abc")]},
        expected=True,
        msg="regex with flags > without flags",
    ),
]

ALL_TESTS = (
    CORE_TESTS
    + STRING_TESTS
    + OBJECT_TESTS
    + ARRAY_TESTS
    + NESTED_ARRAY_TESTS
    + DATE_TESTS
    + BOOLEAN_TESTS
    + OBJECTID_TESTS
    + BINDATA_TESTS
    + TIMESTAMP_TESTS
    + REGEX_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_gt_same_type_comparisons(collection, test):
    """Test $gt same-type comparisons and within-type ordering."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
