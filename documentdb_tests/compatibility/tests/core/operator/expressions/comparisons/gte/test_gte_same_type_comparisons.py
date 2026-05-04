"""
Tests for $gte same-type comparisons and within-type ordering.

Covers string, object, array, date, and boolean comparisons,
and $gte vs $gt equality edge cases.
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
    ExpressionTestCase("greater", expression={"$gte": [300, 250]}, expected=True, msg="300 >= 250"),
    ExpressionTestCase(
        "less", expression={"$gte": [200, 250]}, expected=False, msg="200 not >= 250"
    ),
    ExpressionTestCase(
        "equal",
        expression={"$gte": [250, 250]},
        expected=True,
        msg="250 >= 250 (KEY: equal returns true)",
    ),
]

STRING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "banana_gte_apple",
        expression={"$gte": ["banana", "apple"]},
        expected=True,
        msg="banana >= apple",
    ),
    ExpressionTestCase(
        "apple_gte_banana",
        expression={"$gte": ["apple", "banana"]},
        expected=False,
        msg="apple not >= banana",
    ),
    ExpressionTestCase(
        "apple_self", expression={"$gte": ["apple", "apple"]}, expected=True, msg="apple >= apple"
    ),
    ExpressionTestCase(
        "upper_A_gte_lower_a",
        expression={"$gte": ["Apple", "apple"]},
        expected=False,
        msg="uppercase < lowercase",
    ),
    ExpressionTestCase(
        "lower_a_gte_upper_A",
        expression={"$gte": ["apple", "Apple"]},
        expected=True,
        msg="lowercase >= uppercase",
    ),
    ExpressionTestCase("a_gte_A", expression={"$gte": ["a", "A"]}, expected=True, msg="a >= A"),
    ExpressionTestCase(
        "empty_gte_a", expression={"$gte": ["", "a"]}, expected=False, msg="empty not >= a"
    ),
    ExpressionTestCase(
        "a_gte_empty", expression={"$gte": ["a", ""]}, expected=True, msg="a >= empty"
    ),
    ExpressionTestCase(
        "empty_self", expression={"$gte": ["", ""]}, expected=True, msg="empty >= empty"
    ),
    ExpressionTestCase(
        "abc_gte_ab", expression={"$gte": ["abc", "ab"]}, expected=True, msg="longer prefix wins"
    ),
    ExpressionTestCase(
        "ab_gte_abc", expression={"$gte": ["ab", "abc"]}, expected=False, msg="ab not >= abc"
    ),
    ExpressionTestCase(
        "abd_gte_abc",
        expression={"$gte": ["abd", "abc"]},
        expected=True,
        msg="last char comparison",
    ),
    ExpressionTestCase(
        "abc_gte_abd", expression={"$gte": ["abc", "abd"]}, expected=False, msg="abc not >= abd"
    ),
    ExpressionTestCase("z_gte_Z", expression={"$gte": ["z", "Z"]}, expected=True, msg="z >= Z"),
    ExpressionTestCase(
        "digit_0_gte_9", expression={"$gte": ["0", "9"]}, expected=False, msg="0 not >= 9"
    ),
    ExpressionTestCase(
        "digit_9_gte_0", expression={"$gte": ["9", "0"]}, expected=True, msg="9 >= 0"
    ),
    ExpressionTestCase(
        "space_gte_empty", expression={"$gte": [" ", ""]}, expected=True, msg="space >= empty"
    ),
]

OBJECT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "obj_a2_gte_a1",
        expression={"$gte": [{"a": 2}, {"a": 1}]},
        expected=True,
        msg="{a:2} >= {a:1}",
    ),
    ExpressionTestCase(
        "obj_a1_self",
        expression={"$gte": [{"a": 1}, {"a": 1}]},
        expected=True,
        msg="{a:1} >= {a:1}",
    ),
    ExpressionTestCase(
        "obj_ab_gte_a",
        expression={"$gte": [{"a": 1, "b": 1}, {"a": 1}]},
        expected=True,
        msg="more fields >= fewer",
    ),
    ExpressionTestCase(
        "obj_a_gte_ab",
        expression={"$gte": [{"a": 1}, {"a": 1, "b": 1}]},
        expected=False,
        msg="fewer not >= more",
    ),
    ExpressionTestCase(
        "obj_b_gte_a",
        expression={"$gte": [{"b": 1}, {"a": 1}]},
        expected=True,
        msg="field b >= field a",
    ),
    ExpressionTestCase(
        "obj_a_gte_b",
        expression={"$gte": [{"a": 1}, {"b": 1}]},
        expected=False,
        msg="field a not >= field b",
    ),
    ExpressionTestCase(
        "empty_obj_self", expression={"$gte": [{}, {}]}, expected=True, msg="{} >= {}"
    ),
    ExpressionTestCase(
        "obj_gte_empty", expression={"$gte": [{"a": 1}, {}]}, expected=True, msg="{a:1} >= {}"
    ),
    ExpressionTestCase(
        "empty_gte_obj", expression={"$gte": [{}, {"a": 1}]}, expected=False, msg="{} not >= {a:1}"
    ),
    ExpressionTestCase(
        "obj_a1_gte_a2",
        expression={"$gte": [{"a": 1}, {"a": 2}]},
        expected=False,
        msg="{a:1} not >= {a:2}",
    ),
]

ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "arr_2_gte_1", expression={"$gte": [[2], [1]]}, expected=True, msg="[2] >= [1]"
    ),
    ExpressionTestCase(
        "arr_1_gte_2", expression={"$gte": [[1], [2]]}, expected=False, msg="[1] not >= [2]"
    ),
    ExpressionTestCase(
        "arr_1_self", expression={"$gte": [[1], [1]]}, expected=True, msg="[1] >= [1]"
    ),
    ExpressionTestCase(
        "arr_12_gte_1", expression={"$gte": [[1, 2], [1]]}, expected=True, msg="[1,2] >= [1]"
    ),
    ExpressionTestCase(
        "arr_1_gte_12", expression={"$gte": [[1], [1, 2]]}, expected=False, msg="[1] not >= [1,2]"
    ),
    ExpressionTestCase(
        "arr_12_self", expression={"$gte": [[1, 2], [1, 2]]}, expected=True, msg="[1,2] >= [1,2]"
    ),
    ExpressionTestCase(
        "empty_arr_self", expression={"$gte": [[], []]}, expected=True, msg="[] >= []"
    ),
    ExpressionTestCase(
        "arr_1_gte_empty", expression={"$gte": [[1], []]}, expected=True, msg="[1] >= []"
    ),
    ExpressionTestCase(
        "empty_gte_arr_1", expression={"$gte": [[], [1]]}, expected=False, msg="[] not >= [1]"
    ),
    ExpressionTestCase(
        "arr_2_gte_1_999",
        expression={"$gte": [[2], [1, 999]]},
        expected=True,
        msg="first element wins",
    ),
    ExpressionTestCase(
        "arr_null_gte_empty", expression={"$gte": [[None], []]}, expected=True, msg="[null] >= []"
    ),
]

NESTED_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_1_gte_0", expression={"$gte": [[[1]], [[0]]]}, expected=True, msg="[[1]] >= [[0]]"
    ),
    ExpressionTestCase(
        "null_1_gte_null_0",
        expression={"$gte": [[None, 1], [None, 0]]},
        expected=True,
        msg="second element comparison",
    ),
    ExpressionTestCase(
        "arr_1_null_gte_1",
        expression={"$gte": [[1, None], [1]]},
        expected=True,
        msg="longer with same prefix",
    ),
]

DATE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "later_date",
        expression={
            "$gte": [
                datetime(2025, 6, 1, tzinfo=timezone.utc),
                datetime(2025, 1, 1, tzinfo=timezone.utc),
            ]
        },
        expected=True,
        msg="later date >= earlier",
    ),
    ExpressionTestCase(
        "earlier_date",
        expression={
            "$gte": [
                datetime(2025, 1, 1, tzinfo=timezone.utc),
                datetime(2025, 6, 1, tzinfo=timezone.utc),
            ]
        },
        expected=False,
        msg="earlier not >= later",
    ),
    ExpressionTestCase(
        "same_date",
        expression={
            "$gte": [
                datetime(2025, 1, 1, tzinfo=timezone.utc),
                datetime(2025, 1, 1, tzinfo=timezone.utc),
            ]
        },
        expected=True,
        msg="same date >= same date",
    ),
    ExpressionTestCase(
        "millisecond_precision",
        expression={
            "$gte": [
                datetime(2025, 1, 1, 0, 0, 0, 1000, tzinfo=timezone.utc),
                datetime(2025, 1, 1, tzinfo=timezone.utc),
            ]
        },
        expected=True,
        msg="1ms later >= earlier",
    ),
]

BOOLEAN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "true_gte_false", expression={"$gte": [True, False]}, expected=True, msg="true >= false"
    ),
    ExpressionTestCase(
        "false_gte_true",
        expression={"$gte": [False, True]},
        expected=False,
        msg="false not >= true",
    ),
    ExpressionTestCase(
        "true_self", expression={"$gte": [True, True]}, expected=True, msg="true >= true"
    ),
    ExpressionTestCase(
        "false_self", expression={"$gte": [False, False]}, expected=True, msg="false >= false"
    ),
]

EQUALITY_EDGE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase("zero_self", expression={"$gte": [0, 0]}, expected=True, msg="0 >= 0"),
]

OBJECTID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "objectid_gt",
        expression={
            "$gte": [ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa"), ObjectId("000000000000000000000000")]
        },
        expected=True,
        msg="higher ObjectId >= lower ObjectId",
    ),
    ExpressionTestCase(
        "objectid_equal",
        expression={
            "$gte": [ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa"), ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa")]
        },
        expected=True,
        msg="same ObjectId >= same ObjectId",
    ),
]

BINDATA_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "bindata_longer_gte_shorter",
        expression={"$gte": [Binary(b"\x01\x02\x03", 0), Binary(b"\x01\x02", 0)]},
        expected=True,
        msg="longer BinData >= shorter BinData",
    ),
    ExpressionTestCase(
        "bindata_higher_bytes",
        expression={"$gte": [Binary(b"\x02", 0), Binary(b"\x01", 0)]},
        expected=True,
        msg="same length, higher bytes >= lower bytes",
    ),
    ExpressionTestCase(
        "bindata_equal",
        expression={"$gte": [Binary(b"\x01", 0), Binary(b"\x01", 0)]},
        expected=True,
        msg="equal BinData >= equal BinData",
    ),
    ExpressionTestCase(
        "bindata_diff_subtype",
        expression={"$gte": [Binary(b"\x01", 5), Binary(b"\x01", 0)]},
        expected=True,
        msg="higher subtype >= lower subtype (same data)",
    ),
]

TIMESTAMP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "ts_lower_seconds",
        expression={"$gte": [Timestamp(50, 1), Timestamp(100, 1)]},
        expected=False,
        msg="lower seconds not >= higher seconds",
    ),
    ExpressionTestCase(
        "ts_equal",
        expression={"$gte": [Timestamp(100, 1), Timestamp(100, 1)]},
        expected=True,
        msg="equal timestamp >= equal timestamp",
    ),
    ExpressionTestCase(
        "ts_same_seconds_higher_ordinal",
        expression={"$gte": [Timestamp(100, 2), Timestamp(100, 1)]},
        expected=True,
        msg="same seconds, higher ordinal >= lower ordinal",
    ),
]

REGEX_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "regex_higher_pattern",
        expression={"$gte": [Regex("def"), Regex("abc")]},
        expected=True,
        msg="higher pattern >= lower pattern",
    ),
    ExpressionTestCase(
        "regex_equal",
        expression={"$gte": [Regex("abc"), Regex("abc")]},
        expected=True,
        msg="same regex >= same regex",
    ),
    ExpressionTestCase(
        "regex_flags_gte_no_flags",
        expression={"$gte": [Regex("abc", "i"), Regex("abc")]},
        expected=True,
        msg="regex with flags >= without flags",
    ),
    ExpressionTestCase(
        "regex_lower_pattern",
        expression={"$gte": [Regex("abc"), Regex("def")]},
        expected=False,
        msg="lower pattern not >= higher pattern",
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
    + EQUALITY_EDGE_TESTS
    + OBJECTID_TESTS
    + BINDATA_TESTS
    + TIMESTAMP_TESTS
    + REGEX_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_gte_same_type_comparisons(collection, test):
    """Test $gte same-type comparisons and within-type ordering."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
