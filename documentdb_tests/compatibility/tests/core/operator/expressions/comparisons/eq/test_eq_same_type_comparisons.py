"""
Tests for $eq same-type comparisons.

Covers date, timestamp, ObjectId, BinData, regex, UUID, and large input comparisons.
String comparison semantics are tested in /core/bson_types/test_bson_types_ordering.py.
"""

from datetime import datetime
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
        expression={"$eq": [datetime(2024, 1, 1), datetime(2024, 1, 1)]},
        expected=True,
        msg="Same dates equal",
    ),
    ExpressionTestCase(
        "diff_date",
        expression={"$eq": [datetime(2024, 1, 1), datetime(2024, 1, 2)]},
        expected=False,
        msg="Different dates not equal",
    ),
    ExpressionTestCase(
        "ms_precision",
        expression={"$eq": [datetime(2024, 1, 1, 0, 0, 0, 0), datetime(2024, 1, 1, 0, 0, 0, 1000)]},
        expected=False,
        msg="Millisecond precision matters",
    ),
]


TIMESTAMP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "same",
        expression={"$eq": [Timestamp(1, 1), Timestamp(1, 1)]},
        expected=True,
        msg="Same timestamps equal",
    ),
    ExpressionTestCase(
        "diff_ordinal",
        expression={"$eq": [Timestamp(1, 1), Timestamp(1, 2)]},
        expected=False,
        msg="Different ordinal not equal",
    ),
    ExpressionTestCase(
        "diff_seconds",
        expression={"$eq": [Timestamp(1, 1), Timestamp(2, 1)]},
        expected=False,
        msg="Different seconds not equal",
    ),
    ExpressionTestCase(
        "date_ne_timestamp",
        expression={"$eq": [datetime(2024, 1, 1), Timestamp(1704067200, 0)]},
        expected=False,
        msg="Date and Timestamp are different BSON types, never equal",
    ),
]


OBJECTID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "same",
        expression={
            "$eq": [ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa"), ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa")]
        },
        expected=True,
        msg="Same ObjectIds equal",
    ),
    ExpressionTestCase(
        "different",
        expression={
            "$eq": [ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa"), ObjectId("bbbbbbbbbbbbbbbbbbbbbbbb")]
        },
        expected=False,
        msg="Different ObjectIds not equal",
    ),
]


BINDATA_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "same",
        expression={"$eq": [Binary(b"\x00\x00\x00", 0), Binary(b"\x00\x00\x00", 0)]},
        expected=True,
        msg="Same BinData equal",
    ),
    ExpressionTestCase(
        "diff_data",
        expression={"$eq": [Binary(b"\x00\x00\x00", 0), Binary(b"\x00\x00\x01", 0)]},
        expected=False,
        msg="Different BinData data not equal",
    ),
    ExpressionTestCase(
        "diff_subtype",
        expression={"$eq": [Binary(b"\x00\x00\x00", 0), Binary(b"\x00\x00\x00", 1)]},
        expected=False,
        msg="Different BinData subtype not equal",
    ),
]


REGEX_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "same",
        expression={"$eq": [Regex("abc"), Regex("abc")]},
        expected=True,
        msg="Same regex equal",
    ),
    ExpressionTestCase(
        "diff_pattern",
        expression={"$eq": [Regex("abc"), Regex("def")]},
        expected=False,
        msg="Different regex patterns not equal",
    ),
    ExpressionTestCase(
        "diff_flags",
        expression={"$eq": [Regex("abc", "i"), Regex("abc")]},
        expected=False,
        msg="Different regex flags not equal",
    ),
]


BOOLEAN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "true_true",
        expression={"$eq": [True, True]},
        expected=True,
        msg="True equals True",
    ),
    ExpressionTestCase(
        "false_false",
        expression={"$eq": [False, False]},
        expected=True,
        msg="False equals False",
    ),
    ExpressionTestCase(
        "true_false",
        expression={"$eq": [True, False]},
        expected=False,
        msg="True not equal to False",
    ),
]

UUID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "same",
        expression={
            "$eq": [
                Binary(UUID("01234567-89ab-cdef-fedc-ba9876543210").bytes, 4),
                Binary(UUID("01234567-89ab-cdef-fedc-ba9876543210").bytes, 4),
            ]
        },
        expected=True,
        msg="Same UUIDs equal",
    ),
    ExpressionTestCase(
        "different",
        expression={
            "$eq": [
                Binary(UUID("01234567-89ab-cdef-fedc-ba9876543210").bytes, 4),
                Binary(UUID("11111111-1111-1111-1111-111111111111").bytes, 4),
            ]
        },
        expected=False,
        msg="Different UUIDs not equal",
    ),
]

LARGE_INPUT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "large_string_equal",
        expression={"$eq": ["a" * 10000, "a" * 10000]},
        expected=True,
        msg="Large identical strings are equal",
    ),
    ExpressionTestCase(
        "large_string_diff_last_char",
        expression={"$eq": ["a" * 9999 + "b", "a" * 9999 + "c"]},
        expected=False,
        msg="Large strings differing at last char are not equal",
    ),
    ExpressionTestCase(
        "large_array_equal",
        expression={"$eq": [list(range(1000)), list(range(1000))]},
        expected=True,
        msg="Large identical arrays are equal",
    ),
    ExpressionTestCase(
        "large_array_diff_last_elem",
        expression={"$eq": [list(range(1000)), list(range(999)) + [9999]]},
        expected=False,
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
def test_eq_same_type_comparisons(collection, test):
    """Test $eq same-type comparisons"""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
