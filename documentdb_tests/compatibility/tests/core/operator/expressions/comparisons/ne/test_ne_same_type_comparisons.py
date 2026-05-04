"""
Tests for $ne same-type comparisons.

Covers date, timestamp, ObjectId, BinData, regex, UUID, and large input comparisons.
String comparison semantics are tested in /core/bson_types/test_bson_types_ordering.py.
"""

from datetime import datetime, timezone
from uuid import UUID

import pytest
from bson import Binary, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

DATE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "same_date",
        expression={
            "$ne": [
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                datetime(2024, 1, 1, tzinfo=timezone.utc),
            ]
        },
        expected=False,
        msg="Same dates equal",
    ),
    ExpressionTestCase(
        "diff_date",
        expression={
            "$ne": [
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                datetime(2024, 1, 2, tzinfo=timezone.utc),
            ]
        },
        expected=True,
        msg="Different dates not equal",
    ),
    ExpressionTestCase(
        "ms_precision",
        expression={
            "$ne": [
                datetime(2024, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc),
                datetime(2024, 1, 1, 0, 0, 0, 1000, tzinfo=timezone.utc),
            ]
        },
        expected=True,
        msg="Millisecond precision matters",
    ),
]


TIMESTAMP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "same",
        expression={"$ne": [Timestamp(1, 1), Timestamp(1, 1)]},
        expected=False,
        msg="Same timestamps equal",
    ),
    ExpressionTestCase(
        "diff_ordinal",
        expression={"$ne": [Timestamp(1, 1), Timestamp(1, 2)]},
        expected=True,
        msg="Different ordinal not equal",
    ),
    ExpressionTestCase(
        "diff_seconds",
        expression={"$ne": [Timestamp(1, 1), Timestamp(2, 1)]},
        expected=True,
        msg="Different seconds not equal",
    ),
]


OBJECTID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "same",
        expression={
            "$ne": [ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa"), ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa")]
        },
        expected=False,
        msg="Same ObjectIds equal",
    ),
    ExpressionTestCase(
        "different",
        expression={
            "$ne": [ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa"), ObjectId("bbbbbbbbbbbbbbbbbbbbbbbb")]
        },
        expected=True,
        msg="Different ObjectIds not equal",
    ),
]


BINDATA_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "same",
        expression={"$ne": [Binary(b"\x00\x00\x00", 0), Binary(b"\x00\x00\x00", 0)]},
        expected=False,
        msg="Same BinData equal",
    ),
    ExpressionTestCase(
        "diff_data",
        expression={"$ne": [Binary(b"\x00\x00\x00", 0), Binary(b"\x00\x00\x01", 0)]},
        expected=True,
        msg="Different BinData data not equal",
    ),
    ExpressionTestCase(
        "diff_subtype",
        expression={"$ne": [Binary(b"\x00\x00\x00", 0), Binary(b"\x00\x00\x00", 1)]},
        expected=True,
        msg="Different BinData subtype not equal",
    ),
]


REGEX_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "same",
        expression={"$ne": [Regex("abc"), Regex("abc")]},
        expected=False,
        msg="Same regex equal",
    ),
    ExpressionTestCase(
        "diff_pattern",
        expression={"$ne": [Regex("abc"), Regex("def")]},
        expected=True,
        msg="Different regex patterns not equal",
    ),
    ExpressionTestCase(
        "diff_flags",
        expression={"$ne": [Regex("abc", "i"), Regex("abc")]},
        expected=True,
        msg="Different regex flags not equal",
    ),
]


BOOLEAN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "true_true",
        expression={"$ne": [True, True]},
        expected=False,
        msg="True equals True",
    ),
    ExpressionTestCase(
        "false_false",
        expression={"$ne": [False, False]},
        expected=False,
        msg="False equals False",
    ),
    ExpressionTestCase(
        "true_false",
        expression={"$ne": [True, False]},
        expected=True,
        msg="True not equal to False",
    ),
]

UUID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "same",
        expression={
            "$ne": [
                Binary(UUID("01234567-89ab-cdef-fedc-ba9876543210").bytes, 4),
                Binary(UUID("01234567-89ab-cdef-fedc-ba9876543210").bytes, 4),
            ]
        },
        expected=False,
        msg="Same UUIDs equal",
    ),
    ExpressionTestCase(
        "different",
        expression={
            "$ne": [
                Binary(UUID("01234567-89ab-cdef-fedc-ba9876543210").bytes, 4),
                Binary(UUID("11111111-1111-1111-1111-111111111111").bytes, 4),
            ]
        },
        expected=True,
        msg="Different UUIDs not equal",
    ),
]

LARGE_INPUT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "large_string_equal",
        expression={"$ne": ["a" * 10000, "a" * 10000]},
        expected=False,
        msg="Large identical strings are equal",
    ),
    ExpressionTestCase(
        "large_string_diff_last_char",
        expression={"$ne": ["a" * 9999 + "b", "a" * 9999 + "c"]},
        expected=True,
        msg="Large strings differing at last char are not equal",
    ),
    ExpressionTestCase(
        "large_array_equal",
        expression={"$ne": [list(range(1000)), list(range(1000))]},
        expected=False,
        msg="Large identical arrays are equal",
    ),
    ExpressionTestCase(
        "large_array_diff_last_elem",
        expression={"$ne": [list(range(1000)), list(range(999)) + [9999]]},
        expected=True,
        msg="Large arrays differing at last element are not equal",
    ),
]

ALL_TESTS = (
    DATE_TESTS
    + TIMESTAMP_TESTS
    + OBJECTID_TESTS
    + BINDATA_TESTS
    + REGEX_TESTS
    + BOOLEAN_TESTS
    + UUID_TESTS
    + LARGE_INPUT_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_ne_same_type(collection, test):
    """Test $ne same-type comparisons."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
