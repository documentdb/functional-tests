"""Tests for $millisecond UTC-offset timezone application, including unusual offsets."""

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

# Property [UTC Offsets, datetime]: an explicit +HH:MM/-HH:MM offset shifts the instant for
# parsing, but the millisecond is unchanged because every offset is a whole number of minutes.
MILLISECOND_OFFSET_DATETIME_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_offset_dt_plus0",
        expression={
            "$millisecond": {
                "date": datetime(2024, 7, 15, 12, 25, 37, 456000, tzinfo=timezone.utc),
                "timezone": "+00:00",
            }
        },
        expected=456,
        msg="$millisecond should return 456 for a +00:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_dt_plus9",
        expression={
            "$millisecond": {
                "date": datetime(2024, 7, 15, 12, 25, 37, 456000, tzinfo=timezone.utc),
                "timezone": "+09:00",
            }
        },
        expected=456,
        msg="$millisecond should leave the millisecond at 456 for a +09:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_dt_minus8",
        expression={
            "$millisecond": {
                "date": datetime(2024, 7, 15, 12, 25, 37, 456000, tzinfo=timezone.utc),
                "timezone": "-08:00",
            }
        },
        expected=456,
        msg="$millisecond should leave the millisecond at 456 for a -08:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_dt_plus530",
        expression={
            "$millisecond": {
                "date": datetime(2024, 3, 31, 20, 0, 37, 456000, tzinfo=timezone.utc),
                "timezone": "+05:30",
            }
        },
        expected=456,
        msg="$millisecond should leave the millisecond at 456 for a +05:30 offset",
    ),
    ExpressionTestCase(
        "tz_offset_dt_plus545",
        expression={
            "$millisecond": {
                "date": datetime(2024, 8, 31, 23, 0, 37, 456000, tzinfo=timezone.utc),
                "timezone": "+05:45",
            }
        },
        expected=456,
        msg="$millisecond should leave the millisecond at 456 for a +05:45 offset",
    ),
    ExpressionTestCase(
        "tz_offset_dt_minus930",
        expression={
            "$millisecond": {
                "date": datetime(2024, 6, 15, 12, 0, 37, 456000, tzinfo=timezone.utc),
                "timezone": "-09:30",
            }
        },
        expected=456,
        msg="$millisecond should leave the millisecond at 456 for a -09:30 offset",
    ),
    ExpressionTestCase(
        "tz_offset_dt_plus14",
        expression={
            "$millisecond": {
                "date": datetime(2024, 6, 30, 11, 33, 37, 456000, tzinfo=timezone.utc),
                "timezone": "+14:00",
            }
        },
        expected=456,
        msg="$millisecond should leave the millisecond at 456 for the extreme +14:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_dt_minus12",
        expression={
            "$millisecond": {
                "date": datetime(2024, 7, 1, 11, 33, 37, 456000, tzinfo=timezone.utc),
                "timezone": "-12:00",
            }
        },
        expected=456,
        msg="$millisecond should leave the millisecond at 456 for the extreme -12:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_no_colon",
        expression={
            "$millisecond": {
                "date": datetime(2024, 6, 15, 12, 0, 0, 500000, tzinfo=timezone.utc),
                "timezone": "-0500",
            }
        },
        expected=500,
        msg="$millisecond should accept a compact -0500 offset without a colon",
    ),
    ExpressionTestCase(
        "tz_offset_hour_only",
        expression={
            "$millisecond": {
                "date": datetime(2024, 6, 15, 12, 0, 0, 500000, tzinfo=timezone.utc),
                "timezone": "-08",
            }
        },
        expected=500,
        msg="$millisecond should accept an hour-only -08 offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus13",
        expression={
            "$millisecond": {
                "date": datetime(2024, 7, 15, 12, 0, 0, 456000, tzinfo=timezone.utc),
                "timezone": "-13:00",
            }
        },
        expected=456,
        msg="$millisecond should accept a -13:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_plus15",
        expression={
            "$millisecond": {
                "date": datetime(2024, 7, 15, 12, 0, 0, 456000, tzinfo=timezone.utc),
                "timezone": "+15:00",
            }
        },
        expected=456,
        msg="$millisecond should accept a +15:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus0330",
        expression={
            "$millisecond": {
                "date": datetime(2024, 7, 15, 12, 0, 0, 456000, tzinfo=timezone.utc),
                "timezone": "-03:30",
            }
        },
        expected=456,
        msg="$millisecond should accept a -03:30 half-hour west offset",
    ),
    ExpressionTestCase(
        "tz_offset_plus0570",
        expression={
            "$millisecond": {
                "date": datetime(2024, 7, 15, 12, 0, 0, 456000, tzinfo=timezone.utc),
                "timezone": "+05:70",
            }
        },
        expected=456,
        msg="$millisecond should accept a +05:70 (70-minute) offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus0570",
        expression={
            "$millisecond": {
                "date": datetime(2024, 7, 15, 12, 0, 0, 456000, tzinfo=timezone.utc),
                "timezone": "-05:70",
            }
        },
        expected=456,
        msg="$millisecond should accept a -05:70 (70-minute) offset",
    ),
    ExpressionTestCase(
        "tz_offset_plus2500",
        expression={
            "$millisecond": {
                "date": datetime(2024, 7, 15, 12, 0, 0, 456000, tzinfo=timezone.utc),
                "timezone": "+25:00",
            }
        },
        expected=456,
        msg="$millisecond should accept a +25:00 (25-hour) offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus2500",
        expression={
            "$millisecond": {
                "date": datetime(2024, 7, 15, 12, 0, 0, 456000, tzinfo=timezone.utc),
                "timezone": "-25:00",
            }
        },
        expected=456,
        msg="$millisecond should accept a -25:00 (25-hour) offset",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(MILLISECOND_OFFSET_DATETIME_TESTS))
def test_millisecond_timezone_offsets(collection, test_case: ExpressionTestCase):
    """Test $millisecond UTC-offset timezone application, including edge and unusual offsets."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
