"""Tests for $minute named-timezone application, including DST and fractional-offset zones."""

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

# Property [Named Zones]: a named zone or abbreviation shifts the instant before the minute is
# taken; whole-hour zones leave the minute unchanged while fractional-offset zones change it.
MINUTE_OLSON_DATETIME_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_olson_dt_utc",
        expression={
            "$minute": {
                "date": datetime(2024, 7, 15, 12, 25, 0, tzinfo=timezone.utc),
                "timezone": "UTC",
            }
        },
        expected=25,
        msg="$minute should return 25 for UTC",
    ),
    ExpressionTestCase(
        "tz_olson_dt_ny",
        expression={
            "$minute": {
                "date": datetime(2024, 7, 15, 12, 25, 0, tzinfo=timezone.utc),
                "timezone": "America/New_York",
            }
        },
        expected=25,
        msg="$minute should leave the minute at 25 for the whole-hour America/New_York offset",
    ),
    ExpressionTestCase(
        "tz_olson_dt_tokyo",
        expression={
            "$minute": {
                "date": datetime(2024, 7, 15, 12, 25, 0, tzinfo=timezone.utc),
                "timezone": "Asia/Tokyo",
            }
        },
        expected=25,
        msg="$minute should leave the minute at 25 for the whole-hour Asia/Tokyo offset",
    ),
    ExpressionTestCase(
        "tz_olson_dt_kolkata_on_hour",
        expression={
            "$minute": {
                "date": datetime(2024, 3, 31, 20, 0, 0, tzinfo=timezone.utc),
                "timezone": "Asia/Kolkata",
            }
        },
        expected=30,
        msg="$minute should return 30 for Asia/Kolkata (+05:30) applied on the hour",
    ),
    ExpressionTestCase(
        "tz_olson_dt_kolkata_15",
        expression={
            "$minute": {
                "date": datetime(2024, 6, 15, 20, 15, 0, tzinfo=timezone.utc),
                "timezone": "Asia/Kolkata",
            }
        },
        expected=45,
        msg="$minute should return 45 for Asia/Kolkata (+05:30) at :15",
    ),
    ExpressionTestCase(
        "tz_olson_dt_kolkata_45",
        expression={
            "$minute": {
                "date": datetime(2024, 6, 15, 20, 45, 0, tzinfo=timezone.utc),
                "timezone": "Asia/Kolkata",
            }
        },
        expected=15,
        msg="$minute should return 15 for Asia/Kolkata (+05:30) wrapping past the hour",
    ),
    ExpressionTestCase(
        "tz_olson_dt_kathmandu_on_hour",
        expression={
            "$minute": {
                "date": datetime(2024, 8, 31, 23, 0, 0, tzinfo=timezone.utc),
                "timezone": "Asia/Kathmandu",
            }
        },
        expected=45,
        msg="$minute should return 45 for Asia/Kathmandu (+05:45) applied on the hour",
    ),
    ExpressionTestCase(
        "tz_olson_dt_kathmandu_10",
        expression={
            "$minute": {
                "date": datetime(2024, 6, 15, 23, 10, 0, tzinfo=timezone.utc),
                "timezone": "Asia/Kathmandu",
            }
        },
        expected=55,
        msg="$minute should return 55 for Asia/Kathmandu (+05:45) at :10",
    ),
    ExpressionTestCase(
        "tz_olson_dt_kathmandu_20",
        expression={
            "$minute": {
                "date": datetime(2024, 6, 15, 23, 20, 0, tzinfo=timezone.utc),
                "timezone": "Asia/Kathmandu",
            }
        },
        expected=5,
        msg="$minute should return 5 for Asia/Kathmandu (+05:45) wrapping past the hour",
    ),
    ExpressionTestCase(
        "tz_olson_dt_kolkata_30",
        expression={
            "$minute": {
                "date": datetime(2024, 9, 30, 22, 30, 0, tzinfo=timezone.utc),
                "timezone": "Asia/Kolkata",
            }
        },
        expected=0,
        msg="$minute should return 0 for Asia/Kolkata (+05:30) landing on the hour",
    ),
    ExpressionTestCase(
        "tz_olson_dt_ny_dst_spring",
        expression={
            "$minute": {
                "date": datetime(2024, 3, 10, 7, 17, 0, tzinfo=timezone.utc),
                "timezone": "America/New_York",
            }
        },
        expected=17,
        msg="$minute should leave the minute at 17 across the spring DST transition in New York",
    ),
    ExpressionTestCase(
        "tz_olson_dt_ny_dst_fall",
        expression={
            "$minute": {
                "date": datetime(2024, 11, 3, 6, 42, 0, tzinfo=timezone.utc),
                "timezone": "America/New_York",
            }
        },
        expected=42,
        msg="$minute should leave the minute at 42 across the fall DST transition in New York",
    ),
    ExpressionTestCase(
        "tz_olson_dt_london_bst",
        expression={
            "$minute": {
                "date": datetime(2024, 7, 15, 12, 25, 0, tzinfo=timezone.utc),
                "timezone": "Europe/London",
            }
        },
        expected=25,
        msg="$minute should leave the minute at 25 for Europe/London in summer (BST +1)",
    ),
    ExpressionTestCase(
        "tz_olson_dt_pacific_apia",
        expression={
            "$minute": {
                "date": datetime(2024, 7, 15, 12, 25, 0, tzinfo=timezone.utc),
                "timezone": "Pacific/Apia",
            }
        },
        expected=25,
        msg="$minute should leave the minute at 25 for the whole-hour Pacific/Apia offset",
    ),
    ExpressionTestCase(
        "tz_est_abbreviation",
        expression={
            "$minute": {
                "date": datetime(2024, 7, 15, 12, 25, 0, tzinfo=timezone.utc),
                "timezone": "EST",
            }
        },
        expected=25,
        msg="$minute should accept the EST three-letter abbreviation",
    ),
    ExpressionTestCase(
        "tz_olson_newfoundland_on_hour",
        expression={
            "$minute": {
                "date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "America/St_Johns",
            }
        },
        expected=30,
        msg="$minute should return 30 for America/St_Johns (-03:30) applied on the hour",
    ),
    ExpressionTestCase(
        "tz_olson_newfoundland_15",
        expression={
            "$minute": {
                "date": datetime(2024, 7, 15, 12, 15, 0, tzinfo=timezone.utc),
                "timezone": "America/St_Johns",
            }
        },
        expected=45,
        msg="$minute should return 45 for America/St_Johns (-03:30) at :15",
    ),
    ExpressionTestCase(
        "tz_olson_newfoundland_45_wrap",
        expression={
            "$minute": {
                "date": datetime(2024, 7, 15, 12, 45, 0, tzinfo=timezone.utc),
                "timezone": "America/St_Johns",
            }
        },
        expected=15,
        msg="$minute should return 15 for America/St_Johns (-03:30) wrapping past the hour",
    ),
    ExpressionTestCase(
        "tz_olson_chatham_on_hour",
        expression={
            "$minute": {
                "date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "Pacific/Chatham",
            }
        },
        expected=45,
        msg="$minute should return 45 for Pacific/Chatham (+12:45) applied on the hour",
    ),
    ExpressionTestCase(
        "tz_olson_chatham_20_wrap",
        expression={
            "$minute": {
                "date": datetime(2024, 7, 15, 12, 20, 0, tzinfo=timezone.utc),
                "timezone": "Pacific/Chatham",
            }
        },
        expected=5,
        msg="$minute should return 5 for Pacific/Chatham (+12:45) wrapping past the hour",
    ),
    ExpressionTestCase(
        "tz_olson_marquesas_on_hour",
        expression={
            "$minute": {
                "date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "Pacific/Marquesas",
            }
        },
        expected=30,
        msg="$minute should return 30 for Pacific/Marquesas (-09:30) applied on the hour",
    ),
    ExpressionTestCase(
        "tz_olson_marquesas_40_wrap",
        expression={
            "$minute": {
                "date": datetime(2024, 7, 15, 12, 40, 0, tzinfo=timezone.utc),
                "timezone": "Pacific/Marquesas",
            }
        },
        expected=10,
        msg="$minute should return 10 for Pacific/Marquesas (-09:30) wrapping past the hour",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(MINUTE_OLSON_DATETIME_TESTS))
def test_minute_timezone_names(collection, test_case: ExpressionTestCase):
    """Test $minute named-timezone application across zones, DST, and fractional offsets."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
