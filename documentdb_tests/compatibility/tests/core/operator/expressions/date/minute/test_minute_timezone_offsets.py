"""Tests for $minute UTC-offset timezone application, including fractional and unusual offsets."""

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

# Property [UTC Offsets, datetime]: an explicit +HH:MM/-HH:MM offset shifts the instant;
# whole-hour offsets leave the minute unchanged while fractional offsets change it.
MINUTE_OFFSET_DATETIME_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_offset_dt_plus0",
        expression={
            "$minute": {
                "date": datetime(2024, 7, 15, 12, 25, 0, tzinfo=timezone.utc),
                "timezone": "+00:00",
            }
        },
        expected=25,
        msg="$minute should return 25 for a +00:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_dt_plus9",
        expression={
            "$minute": {
                "date": datetime(2024, 7, 15, 12, 25, 0, tzinfo=timezone.utc),
                "timezone": "+09:00",
            }
        },
        expected=25,
        msg="$minute should leave the minute at 25 for a whole-hour +09:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_dt_minus8",
        expression={
            "$minute": {
                "date": datetime(2024, 7, 15, 12, 25, 0, tzinfo=timezone.utc),
                "timezone": "-08:00",
            }
        },
        expected=25,
        msg="$minute should leave the minute at 25 for a whole-hour -08:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_dt_plus14",
        expression={
            "$minute": {
                "date": datetime(2024, 6, 30, 11, 33, 0, tzinfo=timezone.utc),
                "timezone": "+14:00",
            }
        },
        expected=33,
        msg="$minute should leave the minute at 33 for the extreme +14:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_dt_minus12",
        expression={
            "$minute": {
                "date": datetime(2024, 7, 1, 11, 33, 0, tzinfo=timezone.utc),
                "timezone": "-12:00",
            }
        },
        expected=33,
        msg="$minute should leave the minute at 33 for the extreme -12:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_dt_plus530_on_hour",
        expression={
            "$minute": {
                "date": datetime(2024, 3, 31, 20, 0, 0, tzinfo=timezone.utc),
                "timezone": "+05:30",
            }
        },
        expected=30,
        msg="$minute should return 30 for a +05:30 offset applied on the hour",
    ),
    ExpressionTestCase(
        "tz_offset_dt_plus530_wrap",
        expression={
            "$minute": {
                "date": datetime(2024, 6, 15, 20, 45, 0, tzinfo=timezone.utc),
                "timezone": "+05:30",
            }
        },
        expected=15,
        msg="$minute should return 15 for a +05:30 offset wrapping past the hour",
    ),
    ExpressionTestCase(
        "tz_offset_dt_plus545_on_hour",
        expression={
            "$minute": {
                "date": datetime(2024, 8, 31, 23, 0, 0, tzinfo=timezone.utc),
                "timezone": "+05:45",
            }
        },
        expected=45,
        msg="$minute should return 45 for a +05:45 offset applied on the hour",
    ),
    ExpressionTestCase(
        "tz_offset_dt_plus545_wrap",
        expression={
            "$minute": {
                "date": datetime(2024, 6, 15, 23, 20, 0, tzinfo=timezone.utc),
                "timezone": "+05:45",
            }
        },
        expected=5,
        msg="$minute should return 5 for a +05:45 offset wrapping past the hour",
    ),
    ExpressionTestCase(
        "tz_offset_dt_minus930_on_hour",
        expression={
            "$minute": {
                "date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "-09:30",
            }
        },
        expected=30,
        msg="$minute should return 30 for a -09:30 offset applied on the hour",
    ),
    ExpressionTestCase(
        "tz_offset_dt_minus930_15",
        expression={
            "$minute": {
                "date": datetime(2024, 6, 15, 12, 15, 0, tzinfo=timezone.utc),
                "timezone": "-09:30",
            }
        },
        expected=45,
        msg="$minute should return 45 for a -09:30 offset at :15",
    ),
    ExpressionTestCase(
        "tz_offset_dt_minus930_20",
        expression={
            "$minute": {
                "date": datetime(2024, 6, 15, 12, 20, 0, tzinfo=timezone.utc),
                "timezone": "-09:30",
            }
        },
        expected=50,
        msg="$minute should return 50 for a -09:30 offset at :20",
    ),
    ExpressionTestCase(
        "tz_offset_eucla_on_hour",
        expression={
            "$minute": {
                "date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "+08:45",
            }
        },
        expected=45,
        msg="$minute should return 45 for the +08:45 (Eucla) offset applied on the hour",
    ),
    ExpressionTestCase(
        "tz_offset_eucla_30_wrap",
        expression={
            "$minute": {
                "date": datetime(2024, 7, 15, 12, 30, 0, tzinfo=timezone.utc),
                "timezone": "+08:45",
            }
        },
        expected=15,
        msg="$minute should return 15 for the +08:45 (Eucla) offset wrapping past the hour",
    ),
    ExpressionTestCase(
        "tz_offset_no_colon",
        expression={
            "$minute": {
                "date": datetime(2024, 6, 15, 12, 30, 0, tzinfo=timezone.utc),
                "timezone": "-0500",
            }
        },
        expected=30,
        msg="$minute should accept a compact -0500 offset without a colon",
    ),
    ExpressionTestCase(
        "tz_offset_hour_only",
        expression={
            "$minute": {
                "date": datetime(2024, 6, 15, 12, 30, 0, tzinfo=timezone.utc),
                "timezone": "-08",
            }
        },
        expected=30,
        msg="$minute should accept an hour-only -08 offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus13",
        expression={
            "$minute": {
                "date": datetime(2024, 7, 15, 12, 25, 0, tzinfo=timezone.utc),
                "timezone": "-13:00",
            }
        },
        expected=25,
        msg="$minute should accept a -13:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_plus15",
        expression={
            "$minute": {
                "date": datetime(2024, 7, 15, 12, 25, 0, tzinfo=timezone.utc),
                "timezone": "+15:00",
            }
        },
        expected=25,
        msg="$minute should accept a +15:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus0330",
        expression={
            "$minute": {
                "date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "-03:30",
            }
        },
        expected=30,
        msg="$minute should accept a -03:30 half-hour west offset",
    ),
    ExpressionTestCase(
        "tz_offset_plus0570",
        expression={
            "$minute": {
                "date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "+05:70",
            }
        },
        expected=10,
        msg="$minute should accept a +05:70 (70-minute) offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus0570",
        expression={
            "$minute": {
                "date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "-05:70",
            }
        },
        expected=50,
        msg="$minute should accept a -05:70 (70-minute) offset",
    ),
    ExpressionTestCase(
        "tz_offset_plus2500",
        expression={
            "$minute": {
                "date": datetime(2024, 7, 15, 12, 25, 0, tzinfo=timezone.utc),
                "timezone": "+25:00",
            }
        },
        expected=25,
        msg="$minute should accept a +25:00 (25-hour) offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus2500",
        expression={
            "$minute": {
                "date": datetime(2024, 7, 15, 12, 25, 0, tzinfo=timezone.utc),
                "timezone": "-25:00",
            }
        },
        expected=25,
        msg="$minute should accept a -25:00 (25-hour) offset",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(MINUTE_OFFSET_DATETIME_TESTS))
def test_minute_timezone_offsets(collection, test_case: ExpressionTestCase):
    """Test $minute UTC-offset timezone application, including edge and unusual offsets."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
