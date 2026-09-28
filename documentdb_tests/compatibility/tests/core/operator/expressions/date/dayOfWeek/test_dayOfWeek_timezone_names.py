"""Tests for $dayOfWeek named-timezone application, including DST and abbreviations."""

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

# Property [Named Zones]: a named zone or abbreviation shifts the instant before the day of
# week is taken, which may cross a day, month, year, or leap boundary depending on offset and DST.
DAYOFWEEK_OLSON_DATETIME_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_olson_dt_utc_no_cross",
        expression={
            "$dayOfWeek": {
                "date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "UTC",
            }
        },
        expected=2,
        msg="$dayOfWeek should return 2 for UTC with no day crossing",
    ),
    ExpressionTestCase(
        "tz_olson_dt_ny_no_cross",
        expression={
            "$dayOfWeek": {
                "date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "America/New_York",
            }
        },
        expected=2,
        msg="$dayOfWeek should return 2 for America/New_York with no day crossing",
    ),
    ExpressionTestCase(
        "tz_olson_dt_tokyo_no_cross",
        expression={
            "$dayOfWeek": {
                "date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "Asia/Tokyo",
            }
        },
        expected=2,
        msg="$dayOfWeek should return 2 for Asia/Tokyo with no day crossing",
    ),
    ExpressionTestCase(
        "tz_olson_dt_tokyo_fwd",
        expression={
            "$dayOfWeek": {
                "date": datetime(2024, 6, 30, 22, 0, 0, tzinfo=timezone.utc),
                "timezone": "Asia/Tokyo",
            }
        },
        expected=2,
        msg="$dayOfWeek should cross forward from Sunday to Monday for Asia/Tokyo (+09:00)",
    ),
    ExpressionTestCase(
        "tz_olson_dt_la_bwd",
        expression={
            "$dayOfWeek": {
                "date": datetime(2024, 7, 1, 3, 0, 0, tzinfo=timezone.utc),
                "timezone": "America/Los_Angeles",
            }
        },
        expected=1,
        msg="$dayOfWeek should cross backward from Monday to Sunday for America/Los_Angeles (PDT)",
    ),
    ExpressionTestCase(
        "tz_olson_dt_denver_bwd",
        expression={
            "$dayOfWeek": {
                "date": datetime(2024, 11, 1, 5, 0, 0, tzinfo=timezone.utc),
                "timezone": "America/Denver",
            }
        },
        expected=5,
        msg="$dayOfWeek should cross backward from Friday to Thursday for America/Denver (MDT)",
    ),
    ExpressionTestCase(
        "tz_olson_dt_kolkata_fwd",
        expression={
            "$dayOfWeek": {
                "date": datetime(2024, 3, 31, 20, 0, 0, tzinfo=timezone.utc),
                "timezone": "Asia/Kolkata",
            }
        },
        expected=2,
        msg="$dayOfWeek should cross forward from Sunday to Monday for Asia/Kolkata (+05:30)",
    ),
    ExpressionTestCase(
        "tz_olson_dt_kathmandu_fwd",
        expression={
            "$dayOfWeek": {
                "date": datetime(2024, 8, 31, 23, 0, 0, tzinfo=timezone.utc),
                "timezone": "Asia/Kathmandu",
            }
        },
        expected=1,
        msg="$dayOfWeek should cross forward from Saturday to Sunday for Asia/Kathmandu (+05:45)",
    ),
    ExpressionTestCase(
        "tz_olson_dt_ny_year_bwd",
        expression={
            "$dayOfWeek": {
                "date": datetime(2024, 1, 1, 3, 0, 0, tzinfo=timezone.utc),
                "timezone": "America/New_York",
            }
        },
        expected=1,
        msg="$dayOfWeek should cross the year boundary backward to Sunday for America/New_York",
    ),
    ExpressionTestCase(
        "tz_olson_dt_ny_year_stays",
        expression={
            "$dayOfWeek": {
                "date": datetime(2024, 1, 1, 6, 0, 0, tzinfo=timezone.utc),
                "timezone": "America/New_York",
            }
        },
        expected=2,
        msg="$dayOfWeek should stay on Monday for America/New_York after the year boundary",
    ),
    ExpressionTestCase(
        "tz_olson_dt_helsinki_year_fwd",
        expression={
            "$dayOfWeek": {
                "date": datetime(2024, 12, 31, 23, 0, 0, tzinfo=timezone.utc),
                "timezone": "Europe/Helsinki",
            }
        },
        expected=4,
        msg="$dayOfWeek should cross the year boundary forward to Wednesday for Europe/Helsinki",
    ),
    ExpressionTestCase(
        "tz_olson_dt_moscow_leap_fwd",
        expression={
            "$dayOfWeek": {
                "date": datetime(2024, 2, 29, 23, 30, 0, tzinfo=timezone.utc),
                "timezone": "Europe/Moscow",
            }
        },
        expected=6,
        msg="$dayOfWeek should cross the leap-day boundary forward to Friday for Europe/Moscow",
    ),
    ExpressionTestCase(
        "tz_olson_dt_ny_leap_bwd",
        expression={
            "$dayOfWeek": {
                "date": datetime(2024, 3, 1, 2, 0, 0, tzinfo=timezone.utc),
                "timezone": "America/New_York",
            }
        },
        expected=5,
        msg="$dayOfWeek should cross backward to leap-day Thursday for America/New_York",
    ),
    ExpressionTestCase(
        "tz_olson_dt_ny_dst_spring",
        expression={
            "$dayOfWeek": {
                "date": datetime(2024, 3, 10, 7, 0, 0, tzinfo=timezone.utc),
                "timezone": "America/New_York",
            }
        },
        expected=1,
        msg="$dayOfWeek should return 1 across the spring DST transition in America/New_York",
    ),
    ExpressionTestCase(
        "tz_olson_dt_ny_dst_fall",
        expression={
            "$dayOfWeek": {
                "date": datetime(2024, 11, 3, 6, 0, 0, tzinfo=timezone.utc),
                "timezone": "America/New_York",
            }
        },
        expected=1,
        msg="$dayOfWeek should return 1 across the fall DST transition in America/New_York",
    ),
    ExpressionTestCase(
        "tz_olson_dt_london_bst_start",
        expression={
            "$dayOfWeek": {
                "date": datetime(2024, 3, 31, 0, 30, 0, tzinfo=timezone.utc),
                "timezone": "Europe/London",
            }
        },
        expected=1,
        msg="$dayOfWeek should return 1 at the Europe/London BST start",
    ),
    ExpressionTestCase(
        "tz_olson_dt_london_bst",
        expression={
            "$dayOfWeek": {
                "date": datetime(2020, 6, 30, 23, 30, 0, tzinfo=timezone.utc),
                "timezone": "Europe/London",
            }
        },
        expected=4,
        msg="$dayOfWeek should cross forward to Wednesday for Europe/London in summer (BST)",
    ),
    ExpressionTestCase(
        "tz_olson_dt_pacific_apia",
        expression={
            "$dayOfWeek": {
                "date": datetime(2024, 6, 30, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "Pacific/Apia",
            }
        },
        expected=2,
        msg="$dayOfWeek should cross forward to Monday for Pacific/Apia (+13:00)",
    ),
    ExpressionTestCase(
        "tz_est_abbreviation",
        expression={
            "$dayOfWeek": {
                "date": datetime(2024, 7, 1, 3, 0, 0, tzinfo=timezone.utc),
                "timezone": "EST",
            }
        },
        expected=1,
        msg="$dayOfWeek should accept the EST three-letter abbreviation",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(DAYOFWEEK_OLSON_DATETIME_TESTS))
def test_dayOfWeek_timezone_names(collection, test_case: ExpressionTestCase):
    """Test $dayOfWeek named-timezone application across zones, DST, and abbreviations."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
