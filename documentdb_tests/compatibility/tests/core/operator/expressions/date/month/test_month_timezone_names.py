"""Tests for $month named-timezone application, including DST and abbreviations."""

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

# Property [Named Zones]: a named zone or abbreviation shifts the instant before the month is
# taken, which may cross a month, year, or leap boundary depending on the offset and DST.
MONTH_OLSON_DATETIME_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_olson_dt_utc_no_cross",
        expression={
            "$month": {
                "date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "UTC",
            }
        },
        expected=7,
        msg="$month should return 7 for UTC with no month crossing",
    ),
    ExpressionTestCase(
        "tz_olson_dt_ny_no_cross",
        expression={
            "$month": {
                "date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "America/New_York",
            }
        },
        expected=7,
        msg="$month should return 7 for America/New_York with no month crossing",
    ),
    ExpressionTestCase(
        "tz_olson_dt_tokyo_no_cross",
        expression={
            "$month": {
                "date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "Asia/Tokyo",
            }
        },
        expected=7,
        msg="$month should return 7 for Asia/Tokyo with no month crossing",
    ),
    ExpressionTestCase(
        "tz_olson_dt_tokyo_fwd",
        expression={
            "$month": {
                "date": datetime(2024, 6, 30, 22, 0, 0, tzinfo=timezone.utc),
                "timezone": "Asia/Tokyo",
            }
        },
        expected=7,
        msg="$month should cross forward to July for Asia/Tokyo (+09:00)",
    ),
    ExpressionTestCase(
        "tz_olson_dt_la_bwd",
        expression={
            "$month": {
                "date": datetime(2024, 7, 1, 3, 0, 0, tzinfo=timezone.utc),
                "timezone": "America/Los_Angeles",
            }
        },
        expected=6,
        msg="$month should cross backward to June for America/Los_Angeles (PDT)",
    ),
    ExpressionTestCase(
        "tz_olson_dt_denver_bwd",
        expression={
            "$month": {
                "date": datetime(2024, 11, 1, 5, 0, 0, tzinfo=timezone.utc),
                "timezone": "America/Denver",
            }
        },
        expected=10,
        msg="$month should cross backward to October for America/Denver (MDT)",
    ),
    ExpressionTestCase(
        "tz_olson_dt_kolkata_fwd",
        expression={
            "$month": {
                "date": datetime(2024, 3, 31, 20, 0, 0, tzinfo=timezone.utc),
                "timezone": "Asia/Kolkata",
            }
        },
        expected=4,
        msg="$month should cross forward to April for Asia/Kolkata (+05:30)",
    ),
    ExpressionTestCase(
        "tz_olson_dt_kathmandu_fwd",
        expression={
            "$month": {
                "date": datetime(2024, 8, 31, 23, 0, 0, tzinfo=timezone.utc),
                "timezone": "Asia/Kathmandu",
            }
        },
        expected=9,
        msg="$month should cross forward to September for Asia/Kathmandu (+05:45)",
    ),
    ExpressionTestCase(
        "tz_olson_dt_kolkata_sep_fwd",
        expression={
            "$month": {
                "date": datetime(2024, 9, 30, 22, 30, 0, tzinfo=timezone.utc),
                "timezone": "Asia/Kolkata",
            }
        },
        expected=10,
        msg="$month should cross forward to October for Asia/Kolkata at a September boundary",
    ),
    ExpressionTestCase(
        "tz_olson_dt_ny_year_bwd",
        expression={
            "$month": {
                "date": datetime(2024, 1, 1, 3, 0, 0, tzinfo=timezone.utc),
                "timezone": "America/New_York",
            }
        },
        expected=12,
        msg="$month should cross the year boundary backward to December for America/New_York",
    ),
    ExpressionTestCase(
        "tz_olson_dt_ny_year_stays",
        expression={
            "$month": {
                "date": datetime(2024, 1, 1, 6, 0, 0, tzinfo=timezone.utc),
                "timezone": "America/New_York",
            }
        },
        expected=1,
        msg="$month should stay in January for America/New_York after the year boundary",
    ),
    ExpressionTestCase(
        "tz_olson_dt_helsinki_year_fwd",
        expression={
            "$month": {
                "date": datetime(2024, 12, 31, 23, 0, 0, tzinfo=timezone.utc),
                "timezone": "Europe/Helsinki",
            }
        },
        expected=1,
        msg="$month should cross the year boundary forward to January for Europe/Helsinki",
    ),
    ExpressionTestCase(
        "tz_olson_dt_moscow_leap_fwd",
        expression={
            "$month": {
                "date": datetime(2024, 2, 29, 23, 30, 0, tzinfo=timezone.utc),
                "timezone": "Europe/Moscow",
            }
        },
        expected=3,
        msg="$month should cross the leap-day boundary forward to March for Europe/Moscow",
    ),
    ExpressionTestCase(
        "tz_olson_dt_ny_leap_bwd",
        expression={
            "$month": {
                "date": datetime(2024, 3, 1, 2, 0, 0, tzinfo=timezone.utc),
                "timezone": "America/New_York",
            }
        },
        expected=2,
        msg="$month should cross backward into February for America/New_York",
    ),
    ExpressionTestCase(
        "tz_olson_dt_ny_dst_spring",
        expression={
            "$month": {
                "date": datetime(2024, 3, 10, 7, 0, 0, tzinfo=timezone.utc),
                "timezone": "America/New_York",
            }
        },
        expected=3,
        msg="$month should return 3 across the spring DST transition in America/New_York",
    ),
    ExpressionTestCase(
        "tz_olson_dt_ny_dst_fall",
        expression={
            "$month": {
                "date": datetime(2024, 11, 3, 6, 0, 0, tzinfo=timezone.utc),
                "timezone": "America/New_York",
            }
        },
        expected=11,
        msg="$month should return 11 across the fall DST transition in America/New_York",
    ),
    ExpressionTestCase(
        "tz_olson_dt_london_bst_start",
        expression={
            "$month": {
                "date": datetime(2024, 3, 31, 0, 30, 0, tzinfo=timezone.utc),
                "timezone": "Europe/London",
            }
        },
        expected=3,
        msg="$month should return 3 at the Europe/London BST start",
    ),
    ExpressionTestCase(
        "tz_olson_dt_london_bst",
        expression={
            "$month": {
                "date": datetime(2020, 6, 30, 23, 30, 0, tzinfo=timezone.utc),
                "timezone": "Europe/London",
            }
        },
        expected=7,
        msg="$month should cross forward to July for Europe/London in summer (BST)",
    ),
    ExpressionTestCase(
        "tz_olson_dt_pacific_apia",
        expression={
            "$month": {
                "date": datetime(2024, 6, 30, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "Pacific/Apia",
            }
        },
        expected=7,
        msg="$month should cross forward to July for Pacific/Apia (+13:00)",
    ),
    ExpressionTestCase(
        "tz_est_abbreviation",
        expression={
            "$month": {
                "date": datetime(2024, 7, 1, 3, 0, 0, tzinfo=timezone.utc),
                "timezone": "EST",
            }
        },
        expected=6,
        msg="$month should accept the EST three-letter abbreviation",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(MONTH_OLSON_DATETIME_TESTS))
def test_month_timezone_names(collection, test_case: ExpressionTestCase):
    """Test $month named-timezone application across zones, DST, and abbreviations."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
