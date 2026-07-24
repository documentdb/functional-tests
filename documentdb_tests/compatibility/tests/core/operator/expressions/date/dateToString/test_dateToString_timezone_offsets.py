"""Tests for $dateToString with numeric UTC offset timezones, including boundary offsets."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import ExpressionTestCase
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Numeric Offset Timezones]: UTC offsets in various syntaxes apply the correct shift,
# including out-of-range offsets the server accepts.
DATETOSTRING_OFFSET_TZ_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_offset",
        doc={"timezone": "+05:30"},
        expression={
            "$dateToString": {
                "date": datetime(2024, 6, 15, 10, 30, 45, 123000, tzinfo=timezone.utc),
                "format": "%Y-%m-%d",
                "timezone": "$timezone",
            }
        },
        expected="2024-06-15",
        msg="$dateToString should accept a colon-separated offset",
    ),
    ExpressionTestCase(
        "tz_zero",
        doc={"timezone": "+00:00"},
        expression={
            "$dateToString": {
                "date": datetime(2024, 6, 15, 10, 30, 45, 123000, tzinfo=timezone.utc),
                "format": "%Y-%m-%d",
                "timezone": "$timezone",
            }
        },
        expected="2024-06-15",
        msg="$dateToString should accept a zero offset",
    ),
    ExpressionTestCase(
        "tz_no_colon",
        doc={"timezone": "-0500"},
        expression={
            "$dateToString": {
                "date": datetime(2024, 6, 15, 10, 30, 45, 123000, tzinfo=timezone.utc),
                "format": "%H:%M",
                "timezone": "$timezone",
            }
        },
        expected="05:30",
        msg="$dateToString should accept a colonless offset",
    ),
    ExpressionTestCase(
        "tz_hour_only",
        doc={"timezone": "+03"},
        expression={
            "$dateToString": {
                "date": datetime(2024, 6, 15, 10, 30, 45, 123000, tzinfo=timezone.utc),
                "format": "%H:%M",
                "timezone": "$timezone",
            }
        },
        expected="13:30",
        msg="$dateToString should accept an hour-only offset",
    ),
    ExpressionTestCase(
        "tz_45min",
        doc={"timezone": "+05:45"},
        expression={
            "$dateToString": {
                "date": datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "format": "%H:%M",
                "timezone": "$timezone",
            }
        },
        expected="17:45",
        msg="$dateToString should accept a 45-minute offset",
    ),
    ExpressionTestCase(
        "tz_half_hour_west",
        doc={"timezone": "-03:30"},
        expression={
            "$dateToString": {
                "date": datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "format": "%H:%M",
                "timezone": "$timezone",
            }
        },
        expected="08:30",
        msg="$dateToString should accept a half-hour west offset",
    ),
    ExpressionTestCase(
        "tz_plus14",
        doc={"timezone": "+14:00"},
        expression={
            "$dateToString": {
                "date": datetime(2024, 6, 15, 11, 0, 0, tzinfo=timezone.utc),
                "format": "%Y-%m-%d",
                "timezone": "$timezone",
            }
        },
        expected="2024-06-16",
        msg="$dateToString should accept a +14:00 offset that rolls the date forward",
    ),
    ExpressionTestCase(
        "tz_minus11",
        doc={"timezone": "-11:00"},
        expression={
            "$dateToString": {
                "date": datetime(2024, 6, 15, 10, 0, 0, tzinfo=timezone.utc),
                "format": "%Y-%m-%d",
                "timezone": "$timezone",
            }
        },
        expected="2024-06-14",
        msg="$dateToString should accept a -11:00 offset that rolls the date backward",
    ),
    ExpressionTestCase(
        "tz_offset_minus13",
        doc={"timezone": "-13:00"},
        expression={
            "$dateToString": {
                "date": datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "format": "%Y-%m-%d %H:%M",
                "timezone": "$timezone",
            }
        },
        expected="2019-12-31 23:00",
        msg="$dateToString should accept a -13:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_plus15",
        doc={"timezone": "+15:00"},
        expression={
            "$dateToString": {
                "date": datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "format": "%Y-%m-%d %H:%M",
                "timezone": "$timezone",
            }
        },
        expected="2020-01-02 03:00",
        msg="$dateToString should accept a +15:00 offset",
    ),
    ExpressionTestCase(
        "tz_over60_minutes_positive",
        doc={"timezone": "+05:70"},
        expression={
            "$dateToString": {
                "date": datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "format": "%H:%M",
                "timezone": "$timezone",
            }
        },
        expected="18:10",
        msg="$dateToString should accept a positive offset with over 60 minutes",
    ),
    ExpressionTestCase(
        "tz_over60_minutes_negative",
        doc={"timezone": "-05:70"},
        expression={
            "$dateToString": {
                "date": datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "format": "%H:%M",
                "timezone": "$timezone",
            }
        },
        expected="05:50",
        msg="$dateToString should accept a negative offset with over 60 minutes",
    ),
    ExpressionTestCase(
        "tz_over24_hours_positive",
        doc={"timezone": "+25:00"},
        expression={
            "$dateToString": {
                "date": datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "format": "%Y-%m-%d %H:%M",
                "timezone": "$timezone",
            }
        },
        expected="2020-01-02 13:00",
        msg="$dateToString should accept a positive offset over 24 hours",
    ),
    ExpressionTestCase(
        "tz_over24_hours_negative",
        doc={"timezone": "-25:00"},
        expression={
            "$dateToString": {
                "date": datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "format": "%Y-%m-%d %H:%M",
                "timezone": "$timezone",
            }
        },
        expected="2019-12-31 11:00",
        msg="$dateToString should accept a negative offset over 24 hours",
    ),
    ExpressionTestCase(
        "tz_max_valid_positive",
        doc={"timezone": "+99:99"},
        expression={
            "$dateToString": {
                "date": datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "format": "%Y-%m-%d %H:%M",
                "timezone": "$timezone",
            }
        },
        expected="2020-01-05 16:39",
        msg="$dateToString should accept the maximum two-digit positive offset",
    ),
    ExpressionTestCase(
        "tz_max_valid_negative",
        doc={"timezone": "-99:99"},
        expression={
            "$dateToString": {
                "date": datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "format": "%Y-%m-%d %H:%M",
                "timezone": "$timezone",
            }
        },
        expected="2019-12-28 07:21",
        msg="$dateToString should accept the maximum two-digit negative offset",
    ),
    ExpressionTestCase(
        "tz_Z_430",
        doc={"timezone": "+04:30"},
        expression={
            "$dateToString": {
                "date": datetime(2014, 1, 1, 8, 15, 39, 736000, tzinfo=timezone.utc),
                "format": "%Z",
                "timezone": "$timezone",
            }
        },
        expected="270",
        msg="$dateToString should format %Z as offset minutes for a numeric offset",
    ),
    ExpressionTestCase(
        "tz_430_time",
        doc={"timezone": "+04:30"},
        expression={
            "$dateToString": {
                "date": datetime(2014, 1, 1, 8, 15, 39, 736000, tzinfo=timezone.utc),
                "format": "%H:%M:%S:%L%z",
                "timezone": "$timezone",
            }
        },
        expected="12:45:39:736+0430",
        msg="$dateToString should apply a +04:30 offset to a full time format",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(DATETOSTRING_OFFSET_TZ_TESTS))
def test_dateToString_timezone_offsets(collection, test_case: ExpressionTestCase):
    """Test $dateToString with numeric offset timezones."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
