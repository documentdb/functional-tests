"""Tests for $hour named-timezone application, including DST and abbreviations."""

from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Named Zones]: a named zone or abbreviation shifts the instant before the hour is
# taken, which may wrap past midnight forward or backward depending on the offset and DST.
HOUR_OLSON_DATETIME_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_olson_dt_utc",
        expression={
            "$hour": {
                "date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "UTC",
            }
        },
        expected=12,
        msg="$hour should return 12 for UTC with no wrap",
    ),
    ExpressionTestCase(
        "tz_olson_dt_ny_no_wrap",
        expression={
            "$hour": {
                "date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "America/New_York",
            }
        },
        expected=8,
        msg="$hour should return 8 for America/New_York with no wrap",
    ),
    ExpressionTestCase(
        "tz_olson_dt_tokyo_no_wrap",
        expression={
            "$hour": {
                "date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "Asia/Tokyo",
            }
        },
        expected=21,
        msg="$hour should return 21 for Asia/Tokyo with no wrap",
    ),
    ExpressionTestCase(
        "tz_olson_dt_tokyo_wrap_fwd",
        expression={
            "$hour": {
                "date": datetime(2024, 6, 30, 22, 0, 0, tzinfo=timezone.utc),
                "timezone": "Asia/Tokyo",
            }
        },
        expected=7,
        msg="$hour should wrap forward to 7 for Asia/Tokyo (+09:00)",
    ),
    ExpressionTestCase(
        "tz_olson_dt_la_wrap_bwd",
        expression={
            "$hour": {
                "date": datetime(2024, 7, 1, 3, 0, 0, tzinfo=timezone.utc),
                "timezone": "America/Los_Angeles",
            }
        },
        expected=20,
        msg="$hour should wrap backward to 20 for America/Los_Angeles (PDT)",
    ),
    ExpressionTestCase(
        "tz_olson_dt_denver_wrap_bwd",
        expression={
            "$hour": {
                "date": datetime(2024, 11, 1, 5, 0, 0, tzinfo=timezone.utc),
                "timezone": "America/Denver",
            }
        },
        expected=23,
        msg="$hour should wrap backward to 23 for America/Denver (MDT)",
    ),
    ExpressionTestCase(
        "tz_olson_dt_kolkata_half",
        expression={
            "$hour": {
                "date": datetime(2024, 3, 31, 20, 0, 0, tzinfo=timezone.utc),
                "timezone": "Asia/Kolkata",
            }
        },
        expected=1,
        msg="$hour should return 1 for Asia/Kolkata (+05:30) half-hour offset",
    ),
    ExpressionTestCase(
        "tz_olson_dt_kathmandu_quarter",
        expression={
            "$hour": {
                "date": datetime(2024, 8, 31, 23, 0, 0, tzinfo=timezone.utc),
                "timezone": "Asia/Kathmandu",
            }
        },
        expected=4,
        msg="$hour should return 4 for Asia/Kathmandu (+05:45) quarter-hour offset",
    ),
    ExpressionTestCase(
        "tz_olson_dt_kolkata_sep",
        expression={
            "$hour": {
                "date": datetime(2024, 9, 30, 22, 30, 0, tzinfo=timezone.utc),
                "timezone": "Asia/Kolkata",
            }
        },
        expected=4,
        msg="$hour should return 4 for Asia/Kolkata (+05:30) crossing into the next day",
    ),
    ExpressionTestCase(
        "tz_olson_dt_ny_year_bwd",
        expression={
            "$hour": {
                "date": datetime(2024, 1, 1, 3, 0, 0, tzinfo=timezone.utc),
                "timezone": "America/New_York",
            }
        },
        expected=22,
        msg="$hour should wrap backward across the year boundary to 22 for America/New_York",
    ),
    ExpressionTestCase(
        "tz_olson_dt_ny_year_stays",
        expression={
            "$hour": {
                "date": datetime(2024, 1, 1, 6, 0, 0, tzinfo=timezone.utc),
                "timezone": "America/New_York",
            }
        },
        expected=1,
        msg="$hour should return 1 for America/New_York after the year boundary",
    ),
    ExpressionTestCase(
        "tz_olson_dt_helsinki_year_fwd",
        expression={
            "$hour": {
                "date": datetime(2024, 12, 31, 23, 0, 0, tzinfo=timezone.utc),
                "timezone": "Europe/Helsinki",
            }
        },
        expected=1,
        msg="$hour should wrap forward across the year boundary to 1 for Europe/Helsinki",
    ),
    ExpressionTestCase(
        "tz_olson_dt_moscow_leap_fwd",
        expression={
            "$hour": {
                "date": datetime(2024, 2, 29, 23, 30, 0, tzinfo=timezone.utc),
                "timezone": "Europe/Moscow",
            }
        },
        expected=2,
        msg="$hour should wrap forward across the leap-day boundary to 2 for Europe/Moscow",
    ),
    ExpressionTestCase(
        "tz_olson_dt_ny_leap_bwd",
        expression={
            "$hour": {
                "date": datetime(2024, 3, 1, 2, 0, 0, tzinfo=timezone.utc),
                "timezone": "America/New_York",
            }
        },
        expected=21,
        msg="$hour should wrap backward across the leap-day boundary to 21 for America/New_York",
    ),
    ExpressionTestCase(
        "tz_olson_dt_ny_dst_spring",
        expression={
            "$hour": {
                "date": datetime(2024, 3, 10, 7, 0, 0, tzinfo=timezone.utc),
                "timezone": "America/New_York",
            }
        },
        expected=3,
        msg="$hour should return 3 across the spring DST transition in America/New_York",
    ),
    ExpressionTestCase(
        "tz_olson_dt_ny_dst_fall",
        expression={
            "$hour": {
                "date": datetime(2024, 11, 3, 6, 0, 0, tzinfo=timezone.utc),
                "timezone": "America/New_York",
            }
        },
        expected=1,
        msg="$hour should return 1 across the fall DST transition in America/New_York",
    ),
    ExpressionTestCase(
        "tz_olson_dt_london_bst_start",
        expression={
            "$hour": {
                "date": datetime(2024, 3, 31, 0, 30, 0, tzinfo=timezone.utc),
                "timezone": "Europe/London",
            }
        },
        expected=0,
        msg="$hour should return 0 at the Europe/London BST start",
    ),
    ExpressionTestCase(
        "tz_olson_dt_london_bst",
        expression={
            "$hour": {
                "date": datetime(2024, 7, 15, 23, 30, 0, tzinfo=timezone.utc),
                "timezone": "Europe/London",
            }
        },
        expected=0,
        msg="$hour should wrap forward to 0 for Europe/London in summer (BST +1)",
    ),
    ExpressionTestCase(
        "tz_olson_dt_pacific_apia",
        expression={
            "$hour": {
                "date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "Pacific/Apia",
            }
        },
        expected=1,
        msg="$hour should return 1 for Pacific/Apia (+13:00)",
    ),
    ExpressionTestCase(
        "tz_est_abbreviation",
        expression={
            "$hour": {
                "date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "EST",
            }
        },
        expected=7,
        msg="$hour should accept the EST three-letter abbreviation",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(HOUR_OLSON_DATETIME_TESTS))
def test_hour_timezone_names(collection, test_case: ExpressionTestCase):
    """Test $hour named-timezone application across zones, DST, and abbreviations."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
