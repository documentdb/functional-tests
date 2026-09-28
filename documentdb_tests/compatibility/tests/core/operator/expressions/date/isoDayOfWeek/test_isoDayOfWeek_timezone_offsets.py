"""Tests for $isoDayOfWeek UTC-offset timezone application, including edge and unusual offsets."""

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

# Property [UTC Offsets]: an explicit +HH:MM/-HH:MM offset shifts the instant before the ISO
# day is taken, including compact, half-hour, extreme, and out-of-range offsets the server
# still accepts.
ISODAYOFWEEK_OFFSET_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_offset_plus530_no_cross",
        expression={
            "$isoDayOfWeek": {
                "date": datetime(2024, 6, 15, 0, 0, 0, tzinfo=timezone.utc),
                "timezone": "+05:30",
            }
        },
        expected=6,
        msg="$isoDayOfWeek should return 6 for a +05:30 offset with no day crossing",
    ),
    ExpressionTestCase(
        "tz_offset_minus5_bwd",
        expression={
            "$isoDayOfWeek": {
                "date": datetime(2024, 6, 15, 0, 0, 0, tzinfo=timezone.utc),
                "timezone": "-05:00",
            }
        },
        expected=5,
        msg="$isoDayOfWeek should cross backward to Friday for a -05:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_zero_no_cross",
        expression={
            "$isoDayOfWeek": {
                "date": datetime(2024, 6, 15, 0, 0, 0, tzinfo=timezone.utc),
                "timezone": "+00:00",
            }
        },
        expected=6,
        msg="$isoDayOfWeek should return 6 for a +00:00 offset with no day crossing",
    ),
    ExpressionTestCase(
        "tz_offset_minus4_to_friday",
        expression={
            "$isoDayOfWeek": {
                "date": datetime(1998, 11, 7, 0, 0, 0, tzinfo=timezone.utc),
                "timezone": "-0400",
            }
        },
        expected=5,
        msg="$isoDayOfWeek should cross backward from Saturday to Friday for a -0400 offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus5_monday_to_sunday",
        expression={
            "$isoDayOfWeek": {
                "date": datetime(2024, 1, 15, 0, 0, 0, tzinfo=timezone.utc),
                "timezone": "-05:00",
            }
        },
        expected=7,
        msg="$isoDayOfWeek should cross backward from Monday to Sunday for a -05:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_plus2_sunday_to_monday",
        expression={
            "$isoDayOfWeek": {
                "date": datetime(2024, 1, 21, 23, 0, 0, tzinfo=timezone.utc),
                "timezone": "+02:00",
            }
        },
        expected=1,
        msg="$isoDayOfWeek should cross forward from Sunday to Monday for a +02:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_no_colon",
        expression={
            "$isoDayOfWeek": {
                "date": datetime(2024, 1, 15, 0, 0, 0, tzinfo=timezone.utc),
                "timezone": "-0500",
            }
        },
        expected=7,
        msg="$isoDayOfWeek should accept a compact -0500 offset without a colon",
    ),
    ExpressionTestCase(
        "tz_offset_hour_only",
        expression={
            "$isoDayOfWeek": {
                "date": datetime(2024, 1, 15, 0, 0, 0, tzinfo=timezone.utc),
                "timezone": "-08",
            }
        },
        expected=7,
        msg="$isoDayOfWeek should accept an hour-only -08 offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus13",
        expression={
            "$isoDayOfWeek": {
                "date": datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "-13:00",
            }
        },
        expected=7,
        msg="$isoDayOfWeek should accept a -13:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_plus15",
        expression={
            "$isoDayOfWeek": {
                "date": datetime(2024, 1, 14, 10, 0, 0, tzinfo=timezone.utc),
                "timezone": "+15:00",
            }
        },
        expected=1,
        msg="$isoDayOfWeek should accept a +15:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus0330",
        expression={
            "$isoDayOfWeek": {
                "date": datetime(2024, 1, 15, 2, 0, 0, tzinfo=timezone.utc),
                "timezone": "-03:30",
            }
        },
        expected=7,
        msg="$isoDayOfWeek should accept a -03:30 half-hour west offset",
    ),
    ExpressionTestCase(
        "tz_offset_plus0570",
        expression={
            "$isoDayOfWeek": {
                "date": datetime(2024, 1, 14, 17, 0, 0, tzinfo=timezone.utc),
                "timezone": "+05:70",
            }
        },
        expected=7,
        msg="$isoDayOfWeek should accept a +05:70 (70-minute) offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus0570",
        expression={
            "$isoDayOfWeek": {
                "date": datetime(2024, 1, 15, 5, 0, 0, tzinfo=timezone.utc),
                "timezone": "-05:70",
            }
        },
        expected=7,
        msg="$isoDayOfWeek should accept a -05:70 (70-minute) offset",
    ),
    ExpressionTestCase(
        "tz_offset_plus2500",
        expression={
            "$isoDayOfWeek": {
                "date": datetime(2024, 1, 13, 0, 0, 0, tzinfo=timezone.utc),
                "timezone": "+25:00",
            }
        },
        expected=7,
        msg="$isoDayOfWeek should accept a +25:00 (25-hour) offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus2500",
        expression={
            "$isoDayOfWeek": {
                "date": datetime(2024, 1, 16, 0, 0, 0, tzinfo=timezone.utc),
                "timezone": "-25:00",
            }
        },
        expected=7,
        msg="$isoDayOfWeek should accept a -25:00 (25-hour) offset",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(ISODAYOFWEEK_OFFSET_TESTS))
def test_isoDayOfWeek_timezone_offsets(collection, test_case: ExpressionTestCase):
    """Test $isoDayOfWeek UTC-offset timezone application, including edge and unusual offsets."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
