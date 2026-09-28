"""Tests for $dayOfMonth UTC-offset timezone application, including edge and unusual offsets."""

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

# Property [UTC Offsets, datetime]: an explicit +HH:MM/-HH:MM offset shifts the instant,
# including half/quarter-hour, extreme, and out-of-range offsets the server still accepts.
DAYOFMONTH_OFFSET_DATETIME_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_offset_dt_plus0_no_cross",
        expression={
            "$dayOfMonth": {
                "date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "+00:00",
            }
        },
        expected=15,
        msg="$dayOfMonth should return 15 for a +00:00 offset with no crossing",
    ),
    ExpressionTestCase(
        "tz_offset_dt_minus5_no_cross",
        expression={
            "$dayOfMonth": {
                "date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "-05:00",
            }
        },
        expected=15,
        msg="$dayOfMonth should return 15 for a -05:00 offset with no crossing",
    ),
    ExpressionTestCase(
        "tz_offset_dt_plus9_fwd",
        expression={
            "$dayOfMonth": {
                "date": datetime(2024, 6, 30, 22, 0, 0, tzinfo=timezone.utc),
                "timezone": "+09:00",
            }
        },
        expected=1,
        msg="$dayOfMonth should cross forward to day 1 for a +09:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_dt_minus8_bwd",
        expression={
            "$dayOfMonth": {
                "date": datetime(2024, 7, 1, 3, 0, 0, tzinfo=timezone.utc),
                "timezone": "-08:00",
            }
        },
        expected=30,
        msg="$dayOfMonth should cross backward to day 30 for a -08:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_dt_plus530_fwd",
        expression={
            "$dayOfMonth": {
                "date": datetime(2024, 3, 31, 20, 0, 0, tzinfo=timezone.utc),
                "timezone": "+05:30",
            }
        },
        expected=1,
        msg="$dayOfMonth should cross forward to day 1 for a +05:30 half-hour offset",
    ),
    ExpressionTestCase(
        "tz_offset_dt_plus545_fwd",
        expression={
            "$dayOfMonth": {
                "date": datetime(2024, 8, 31, 23, 0, 0, tzinfo=timezone.utc),
                "timezone": "+05:45",
            }
        },
        expected=1,
        msg="$dayOfMonth should cross forward to day 1 for a +05:45 quarter-hour offset",
    ),
    ExpressionTestCase(
        "tz_offset_dt_minus5_year_bwd",
        expression={
            "$dayOfMonth": {
                "date": datetime(2024, 1, 1, 3, 0, 0, tzinfo=timezone.utc),
                "timezone": "-05:00",
            }
        },
        expected=31,
        msg="$dayOfMonth should cross the year boundary backward to day 31 for a -05:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_dt_plus2_year_fwd",
        expression={
            "$dayOfMonth": {
                "date": datetime(2024, 12, 31, 23, 0, 0, tzinfo=timezone.utc),
                "timezone": "+02:00",
            }
        },
        expected=1,
        msg="$dayOfMonth should cross the year boundary forward to day 1 for a +02:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_dt_plus3_leap_fwd",
        expression={
            "$dayOfMonth": {
                "date": datetime(2024, 2, 29, 23, 30, 0, tzinfo=timezone.utc),
                "timezone": "+03:00",
            }
        },
        expected=1,
        msg="$dayOfMonth should cross the leap-day boundary forward to day 1 for a +03:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_dt_minus5_leap_bwd",
        expression={
            "$dayOfMonth": {
                "date": datetime(2024, 3, 1, 2, 0, 0, tzinfo=timezone.utc),
                "timezone": "-05:00",
            }
        },
        expected=29,
        msg="$dayOfMonth should cross backward to leap day 29 for a -05:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_dt_plus14_fwd",
        expression={
            "$dayOfMonth": {
                "date": datetime(2024, 6, 30, 11, 0, 0, tzinfo=timezone.utc),
                "timezone": "+14:00",
            }
        },
        expected=1,
        msg="$dayOfMonth should cross forward to day 1 for the extreme +14:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_dt_minus12_bwd",
        expression={
            "$dayOfMonth": {
                "date": datetime(2024, 7, 1, 11, 0, 0, tzinfo=timezone.utc),
                "timezone": "-12:00",
            }
        },
        expected=30,
        msg="$dayOfMonth should cross backward to day 30 for the extreme -12:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_no_colon",
        expression={
            "$dayOfMonth": {
                "date": datetime(2024, 7, 1, 3, 0, 0, tzinfo=timezone.utc),
                "timezone": "-0500",
            }
        },
        expected=30,
        msg="$dayOfMonth should accept a compact -0500 offset without a colon",
    ),
    ExpressionTestCase(
        "tz_offset_hour_only",
        expression={
            "$dayOfMonth": {
                "date": datetime(2024, 7, 1, 3, 0, 0, tzinfo=timezone.utc),
                "timezone": "-08",
            }
        },
        expected=30,
        msg="$dayOfMonth should accept an hour-only -08 offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus13",
        expression={
            "$dayOfMonth": {
                "date": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "-13:00",
            }
        },
        expected=31,
        msg="$dayOfMonth should accept a -13:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_plus15",
        expression={
            "$dayOfMonth": {
                "date": datetime(2024, 6, 30, 10, 0, 0, tzinfo=timezone.utc),
                "timezone": "+15:00",
            }
        },
        expected=1,
        msg="$dayOfMonth should accept a +15:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus0330",
        expression={
            "$dayOfMonth": {
                "date": datetime(2024, 7, 1, 2, 0, 0, tzinfo=timezone.utc),
                "timezone": "-03:30",
            }
        },
        expected=30,
        msg="$dayOfMonth should accept a -03:30 half-hour west offset",
    ),
    ExpressionTestCase(
        "tz_offset_plus0570",
        expression={
            "$dayOfMonth": {
                "date": datetime(2024, 6, 30, 17, 0, 0, tzinfo=timezone.utc),
                "timezone": "+05:70",
            }
        },
        expected=30,
        msg="$dayOfMonth should accept a +05:70 (70-minute) offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus0570",
        expression={
            "$dayOfMonth": {
                "date": datetime(2024, 7, 1, 5, 0, 0, tzinfo=timezone.utc),
                "timezone": "-05:70",
            }
        },
        expected=30,
        msg="$dayOfMonth should accept a -05:70 (70-minute) offset",
    ),
    ExpressionTestCase(
        "tz_offset_plus2500",
        expression={
            "$dayOfMonth": {
                "date": datetime(2024, 6, 29, 0, 0, 0, tzinfo=timezone.utc),
                "timezone": "+25:00",
            }
        },
        expected=30,
        msg="$dayOfMonth should accept a +25:00 (25-hour) offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus2500",
        expression={
            "$dayOfMonth": {
                "date": datetime(2024, 7, 2, 0, 0, 0, tzinfo=timezone.utc),
                "timezone": "-25:00",
            }
        },
        expected=30,
        msg="$dayOfMonth should accept a -25:00 (25-hour) offset",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(DAYOFMONTH_OFFSET_DATETIME_TESTS))
def test_dayOfMonth_timezone_offsets(collection, test_case: ExpressionTestCase):
    """Test $dayOfMonth UTC-offset timezone application, including edge and unusual offsets."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
