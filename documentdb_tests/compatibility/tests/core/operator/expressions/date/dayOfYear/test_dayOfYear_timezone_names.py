"""Tests for $dayOfYear named-timezone application, including DST and abbreviations."""

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

# Property [Named Zones]: a named zone or abbreviation shifts the instant before the ordinal
# day is taken, which may cross a day, year, or leap boundary depending on the offset and DST.
DAYOFYEAR_OLSON_DATETIME_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_olson_dt_utc_no_cross",
        expression={
            "$dayOfYear": {
                "date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "UTC",
            }
        },
        expected=197,
        msg="$dayOfYear should not change the ordinal day for UTC with no day crossing",
    ),
    ExpressionTestCase(
        "tz_olson_dt_ny_no_cross",
        expression={
            "$dayOfYear": {
                "date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "America/New_York",
            }
        },
        expected=197,
        msg="$dayOfYear should keep the ordinal day for America/New_York with no day crossing",
    ),
    ExpressionTestCase(
        "tz_olson_dt_tokyo_no_cross",
        expression={
            "$dayOfYear": {
                "date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "Asia/Tokyo",
            }
        },
        expected=197,
        msg="$dayOfYear should not change the ordinal day for Asia/Tokyo with no day crossing",
    ),
    ExpressionTestCase(
        "tz_olson_dt_tokyo_fwd",
        expression={
            "$dayOfYear": {
                "date": datetime(2024, 6, 30, 22, 0, 0, tzinfo=timezone.utc),
                "timezone": "Asia/Tokyo",
            }
        },
        expected=183,
        msg="$dayOfYear should cross forward to day 183 for Asia/Tokyo (+09:00)",
    ),
    ExpressionTestCase(
        "tz_olson_dt_la_bwd",
        expression={
            "$dayOfYear": {
                "date": datetime(2024, 7, 1, 3, 0, 0, tzinfo=timezone.utc),
                "timezone": "America/Los_Angeles",
            }
        },
        expected=182,
        msg="$dayOfYear should cross backward to day 182 for America/Los_Angeles (PDT)",
    ),
    ExpressionTestCase(
        "tz_olson_dt_denver_bwd",
        expression={
            "$dayOfYear": {
                "date": datetime(2024, 11, 1, 5, 0, 0, tzinfo=timezone.utc),
                "timezone": "America/Denver",
            }
        },
        expected=305,
        msg="$dayOfYear should cross backward to day 305 for America/Denver (MDT)",
    ),
    ExpressionTestCase(
        "tz_olson_dt_kolkata_fwd",
        expression={
            "$dayOfYear": {
                "date": datetime(2024, 3, 31, 20, 0, 0, tzinfo=timezone.utc),
                "timezone": "Asia/Kolkata",
            }
        },
        expected=92,
        msg="$dayOfYear should cross forward to day 92 for Asia/Kolkata (+05:30)",
    ),
    ExpressionTestCase(
        "tz_olson_dt_kathmandu_fwd",
        expression={
            "$dayOfYear": {
                "date": datetime(2024, 8, 31, 23, 0, 0, tzinfo=timezone.utc),
                "timezone": "Asia/Kathmandu",
            }
        },
        expected=245,
        msg="$dayOfYear should cross forward to day 245 for Asia/Kathmandu (+05:45)",
    ),
    ExpressionTestCase(
        "tz_olson_dt_ny_year_bwd",
        expression={
            "$dayOfYear": {
                "date": datetime(2024, 1, 1, 3, 0, 0, tzinfo=timezone.utc),
                "timezone": "America/New_York",
            }
        },
        expected=365,
        msg="$dayOfYear should cross the year boundary backward to day 365 for America/New_York",
    ),
    ExpressionTestCase(
        "tz_olson_dt_ny_year_stays",
        expression={
            "$dayOfYear": {
                "date": datetime(2024, 1, 1, 6, 0, 0, tzinfo=timezone.utc),
                "timezone": "America/New_York",
            }
        },
        expected=1,
        msg="$dayOfYear should stay on day 1 for America/New_York after the year boundary",
    ),
    ExpressionTestCase(
        "tz_olson_dt_helsinki_year_fwd",
        expression={
            "$dayOfYear": {
                "date": datetime(2024, 12, 31, 23, 0, 0, tzinfo=timezone.utc),
                "timezone": "Europe/Helsinki",
            }
        },
        expected=1,
        msg="$dayOfYear should cross the year boundary forward to day 1 for Europe/Helsinki",
    ),
    ExpressionTestCase(
        "tz_olson_dt_moscow_leap_fwd",
        expression={
            "$dayOfYear": {
                "date": datetime(2024, 2, 29, 23, 30, 0, tzinfo=timezone.utc),
                "timezone": "Europe/Moscow",
            }
        },
        expected=61,
        msg="$dayOfYear should cross the leap-day boundary forward to day 61 for Europe/Moscow",
    ),
    ExpressionTestCase(
        "tz_olson_dt_ny_leap_bwd",
        expression={
            "$dayOfYear": {
                "date": datetime(2024, 3, 1, 2, 0, 0, tzinfo=timezone.utc),
                "timezone": "America/New_York",
            }
        },
        expected=60,
        msg="$dayOfYear should cross backward to leap day 60 for America/New_York",
    ),
    ExpressionTestCase(
        "tz_olson_dt_ny_dst_spring",
        expression={
            "$dayOfYear": {
                "date": datetime(2024, 3, 10, 7, 0, 0, tzinfo=timezone.utc),
                "timezone": "America/New_York",
            }
        },
        expected=70,
        msg="$dayOfYear should return 70 across the spring DST transition in America/New_York",
    ),
    ExpressionTestCase(
        "tz_olson_dt_ny_dst_fall",
        expression={
            "$dayOfYear": {
                "date": datetime(2024, 11, 3, 6, 0, 0, tzinfo=timezone.utc),
                "timezone": "America/New_York",
            }
        },
        expected=308,
        msg="$dayOfYear should return 308 across the fall DST transition in America/New_York",
    ),
    ExpressionTestCase(
        "tz_olson_dt_london_bst_start",
        expression={
            "$dayOfYear": {
                "date": datetime(2024, 3, 31, 0, 30, 0, tzinfo=timezone.utc),
                "timezone": "Europe/London",
            }
        },
        expected=91,
        msg="$dayOfYear should return 91 at the Europe/London BST start",
    ),
    ExpressionTestCase(
        "tz_olson_dt_london_bst",
        expression={
            "$dayOfYear": {
                "date": datetime(2020, 6, 30, 23, 30, 0, tzinfo=timezone.utc),
                "timezone": "Europe/London",
            }
        },
        expected=183,
        msg="$dayOfYear should cross forward to day 183 for Europe/London in summer (BST)",
    ),
    ExpressionTestCase(
        "tz_olson_dt_pacific_apia",
        expression={
            "$dayOfYear": {
                "date": datetime(2024, 6, 30, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "Pacific/Apia",
            }
        },
        expected=183,
        msg="$dayOfYear should cross forward to day 183 for Pacific/Apia (+13:00)",
    ),
    ExpressionTestCase(
        "tz_est_abbreviation",
        expression={
            "$dayOfYear": {
                "date": datetime(2024, 7, 1, 3, 0, 0, tzinfo=timezone.utc),
                "timezone": "EST",
            }
        },
        expected=182,
        msg="$dayOfYear should accept the EST three-letter abbreviation",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(DAYOFYEAR_OLSON_DATETIME_TESTS))
def test_dayOfYear_timezone_names(collection, test_case: ExpressionTestCase):
    """Test $dayOfYear named-timezone application across zones, DST, and abbreviations."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
