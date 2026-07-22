"""Tests for $month UTC-offset timezone application, including edge and unusual offsets."""

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
MONTH_OFFSET_DATETIME_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_offset_dt_plus0_no_cross",
        expression={
            "$month": {
                "date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "+00:00",
            }
        },
        expected=7,
        msg="$month should return 7 for a +00:00 offset with no crossing",
    ),
    ExpressionTestCase(
        "tz_offset_dt_minus5_no_cross",
        expression={
            "$month": {
                "date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "-05:00",
            }
        },
        expected=7,
        msg="$month should return 7 for a -05:00 offset with no crossing",
    ),
    ExpressionTestCase(
        "tz_offset_dt_plus9_fwd",
        expression={
            "$month": {
                "date": datetime(2024, 6, 30, 22, 0, 0, tzinfo=timezone.utc),
                "timezone": "+09:00",
            }
        },
        expected=7,
        msg="$month should cross forward to July for a +09:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_dt_minus8_bwd",
        expression={
            "$month": {
                "date": datetime(2024, 7, 1, 3, 0, 0, tzinfo=timezone.utc),
                "timezone": "-08:00",
            }
        },
        expected=6,
        msg="$month should cross backward to June for a -08:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_dt_plus530_fwd",
        expression={
            "$month": {
                "date": datetime(2024, 3, 31, 20, 0, 0, tzinfo=timezone.utc),
                "timezone": "+05:30",
            }
        },
        expected=4,
        msg="$month should cross forward to April for a +05:30 half-hour offset",
    ),
    ExpressionTestCase(
        "tz_offset_dt_plus545_fwd",
        expression={
            "$month": {
                "date": datetime(2024, 8, 31, 23, 0, 0, tzinfo=timezone.utc),
                "timezone": "+05:45",
            }
        },
        expected=9,
        msg="$month should cross forward to September for a +05:45 quarter-hour offset",
    ),
    ExpressionTestCase(
        "tz_offset_dt_minus5_year_bwd",
        expression={
            "$month": {
                "date": datetime(2024, 1, 1, 3, 0, 0, tzinfo=timezone.utc),
                "timezone": "-05:00",
            }
        },
        expected=12,
        msg="$month should cross the year boundary backward to December for a -05:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_dt_plus2_year_fwd",
        expression={
            "$month": {
                "date": datetime(2024, 12, 31, 23, 0, 0, tzinfo=timezone.utc),
                "timezone": "+02:00",
            }
        },
        expected=1,
        msg="$month should cross the year boundary forward to January for a +02:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_dt_plus3_leap_fwd",
        expression={
            "$month": {
                "date": datetime(2024, 2, 29, 23, 30, 0, tzinfo=timezone.utc),
                "timezone": "+03:00",
            }
        },
        expected=3,
        msg="$month should cross the leap-day boundary forward to March for a +03:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_dt_minus5_leap_bwd",
        expression={
            "$month": {
                "date": datetime(2024, 3, 1, 2, 0, 0, tzinfo=timezone.utc),
                "timezone": "-05:00",
            }
        },
        expected=2,
        msg="$month should cross backward into February for a -05:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_dt_plus14_fwd",
        expression={
            "$month": {
                "date": datetime(2024, 6, 30, 11, 0, 0, tzinfo=timezone.utc),
                "timezone": "+14:00",
            }
        },
        expected=7,
        msg="$month should cross forward to July for the extreme +14:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_dt_minus12_bwd",
        expression={
            "$month": {
                "date": datetime(2024, 7, 1, 11, 0, 0, tzinfo=timezone.utc),
                "timezone": "-12:00",
            }
        },
        expected=6,
        msg="$month should cross backward to June for the extreme -12:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_no_colon",
        expression={
            "$month": {
                "date": datetime(2024, 7, 1, 3, 0, 0, tzinfo=timezone.utc),
                "timezone": "-0530",
            }
        },
        expected=6,
        msg="$month should accept a compact -0530 offset without a colon",
    ),
    ExpressionTestCase(
        "tz_offset_hour_only",
        expression={
            "$month": {
                "date": datetime(2024, 7, 1, 3, 0, 0, tzinfo=timezone.utc),
                "timezone": "-08",
            }
        },
        expected=6,
        msg="$month should accept an hour-only -08 offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus13",
        expression={
            "$month": {
                "date": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "-13:00",
            }
        },
        expected=12,
        msg="$month should accept a -13:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_plus15",
        expression={
            "$month": {
                "date": datetime(2024, 6, 30, 10, 0, 0, tzinfo=timezone.utc),
                "timezone": "+15:00",
            }
        },
        expected=7,
        msg="$month should accept a +15:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus0330",
        expression={
            "$month": {
                "date": datetime(2024, 7, 1, 2, 0, 0, tzinfo=timezone.utc),
                "timezone": "-03:30",
            }
        },
        expected=6,
        msg="$month should accept a -03:30 half-hour west offset",
    ),
    ExpressionTestCase(
        "tz_offset_plus0570",
        expression={
            "$month": {
                "date": datetime(2024, 6, 30, 17, 0, 0, tzinfo=timezone.utc),
                "timezone": "+05:70",
            }
        },
        expected=6,
        msg="$month should accept a +05:70 (70-minute) offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus0570",
        expression={
            "$month": {
                "date": datetime(2024, 7, 1, 5, 0, 0, tzinfo=timezone.utc),
                "timezone": "-05:70",
            }
        },
        expected=6,
        msg="$month should accept a -05:70 (70-minute) offset",
    ),
    ExpressionTestCase(
        "tz_offset_plus2500",
        expression={
            "$month": {
                "date": datetime(2024, 6, 29, 0, 0, 0, tzinfo=timezone.utc),
                "timezone": "+25:00",
            }
        },
        expected=6,
        msg="$month should accept a +25:00 (25-hour) offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus2500",
        expression={
            "$month": {
                "date": datetime(2024, 7, 2, 0, 0, 0, tzinfo=timezone.utc),
                "timezone": "-25:00",
            }
        },
        expected=6,
        msg="$month should accept a -25:00 (25-hour) offset",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(MONTH_OFFSET_DATETIME_TESTS))
def test_month_timezone_offsets(collection, test_case: ExpressionTestCase):
    """Test $month UTC-offset timezone application, including edge and unusual offsets."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
