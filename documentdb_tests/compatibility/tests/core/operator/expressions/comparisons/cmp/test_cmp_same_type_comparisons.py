"""
Tests for $cmp same-type comparisons.

Covers date, timestamp, ObjectId, BinData, regex, string, object,
and MinKey/MaxKey comparisons.
"""

from datetime import datetime

import pytest
from bson import SON, Binary, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

DATE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "same_date",
        expression={"$cmp": [datetime(2024, 1, 1), datetime(2024, 1, 1)]},
        expected=0,
        msg="Same dates equal",
    ),
    ExpressionTestCase(
        "diff_date",
        expression={"$cmp": [datetime(2024, 1, 1), datetime(2024, 1, 2)]},
        expected=-1,
        msg="Earlier date < later date",
    ),
    ExpressionTestCase(
        "ms_precision",
        expression={
            "$cmp": [datetime(2024, 1, 1, 0, 0, 0, 0), datetime(2024, 1, 1, 0, 0, 0, 1000)]
        },
        expected=-1,
        msg="Millisecond precision matters",
    ),
]


TIMESTAMP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "same_timestamp",
        expression={"$cmp": [Timestamp(1, 1), Timestamp(1, 1)]},
        expected=0,
        msg="Same timestamps equal",
    ),
    ExpressionTestCase(
        "diff_ordinal",
        expression={"$cmp": [Timestamp(1, 1), Timestamp(1, 2)]},
        expected=-1,
        msg="Different ordinal",
    ),
    ExpressionTestCase(
        "diff_seconds",
        expression={"$cmp": [Timestamp(1, 1), Timestamp(2, 1)]},
        expected=-1,
        msg="Different seconds",
    ),
]


OBJECTID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "same_objectid",
        expression={
            "$cmp": [ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa"), ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa")]
        },
        expected=0,
        msg="Same ObjectIds equal",
    ),
    ExpressionTestCase(
        "different",
        expression={
            "$cmp": [ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa"), ObjectId("bbbbbbbbbbbbbbbbbbbbbbbb")]
        },
        expected=-1,
        msg="Lower ObjectId < higher ObjectId",
    ),
]


BINDATA_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "same_bindata",
        expression={"$cmp": [Binary(b"\x00\x00\x00", 0), Binary(b"\x00\x00\x00", 0)]},
        expected=0,
        msg="Same BinData equal",
    ),
    ExpressionTestCase(
        "diff_data",
        expression={"$cmp": [Binary(b"\x00\x00\x00", 0), Binary(b"\x00\x00\x01", 0)]},
        expected=-1,
        msg="Different BinData data",
    ),
    ExpressionTestCase(
        "diff_subtype",
        expression={"$cmp": [Binary(b"\x00\x00\x00", 0), Binary(b"\x00\x00\x00", 1)]},
        expected=-1,
        msg="Different BinData subtype",
    ),
]


REGEX_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "same_regex",
        expression={"$cmp": [Regex("abc"), Regex("abc")]},
        expected=0,
        msg="Same regex equal",
    ),
    ExpressionTestCase(
        "diff_pattern",
        expression={"$cmp": [Regex("abc"), Regex("def")]},
        expected=-1,
        msg="Different regex patterns",
    ),
    ExpressionTestCase(
        "diff_flags",
        expression={"$cmp": [Regex("abc", "i"), Regex("abc")]},
        expected=1,
        msg="Regex with flags > without flags",
    ),
]


STRING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "same_string",
        expression={"$cmp": ["abc", "abc"]},
        expected=0,
        msg="Same strings equal",
    ),
    ExpressionTestCase(
        "diff_string",
        expression={"$cmp": ["abc", "def"]},
        expected=-1,
        msg="Lexicographically smaller string < larger",
    ),
    ExpressionTestCase(
        "empty_vs_nonempty",
        expression={"$cmp": ["", "a"]},
        expected=-1,
        msg="Empty string < non-empty string",
    ),
]


OBJECT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "same_object",
        expression={"$cmp": [SON([("x", 1)]), SON([("x", 1)])]},
        expected=0,
        msg="Same objects equal",
    ),
    ExpressionTestCase(
        "diff_object_value",
        expression={"$cmp": [SON([("x", 1)]), SON([("x", 2)])]},
        expected=-1,
        msg="Object with smaller field value < larger",
    ),
    ExpressionTestCase(
        "empty_vs_nonempty_object",
        expression={"$cmp": [SON(), SON([("x", 1)])]},
        expected=-1,
        msg="Empty object < non-empty object",
    ),
]


MINKEY_MAXKEY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "minkey_vs_minkey",
        expression={"$cmp": [MinKey(), MinKey()]},
        expected=0,
        msg="MinKey equals MinKey",
    ),
    ExpressionTestCase(
        "maxkey_vs_maxkey",
        expression={"$cmp": [MaxKey(), MaxKey()]},
        expected=0,
        msg="MaxKey equals MaxKey",
    ),
    ExpressionTestCase(
        "minkey_vs_maxkey",
        expression={"$cmp": [MinKey(), MaxKey()]},
        expected=-1,
        msg="MinKey < MaxKey",
    ),
]


ALL_TESTS = (
    DATE_TESTS
    + TIMESTAMP_TESTS
    + OBJECTID_TESTS
    + BINDATA_TESTS
    + REGEX_TESTS
    + STRING_TESTS
    + OBJECT_TESTS
    + MINKEY_MAXKEY_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_cmp_same_type_comparisons(collection, test):
    """Test $cmp same-type comparisons."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
