"""Tests for $dateToParts numeric UTC offset timezones."""

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

# Property [Numeric Offsets]: a numeric UTC offset shifts the extracted parts by that offset.
DATETOPARTS_TZ_NUMERIC_OFFSET_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_gmt",
        doc={"timezone": "GMT"},
        expression={
            "$dateToParts": {
                "date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "$timezone",
            }
        },
        expected={
            "year": 2024,
            "month": 6,
            "day": 15,
            "hour": 12,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should accept the GMT timezone",
    ),
    ExpressionTestCase(
        "tz_utc",
        doc={"timezone": "UTC"},
        expression={
            "$dateToParts": {
                "date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "$timezone",
            }
        },
        expected={
            "year": 2024,
            "month": 6,
            "day": 15,
            "hour": 12,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should accept the UTC timezone",
    ),
    ExpressionTestCase(
        "tz_offset",
        doc={"timezone": "+05:30"},
        expression={
            "$dateToParts": {
                "date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "$timezone",
            }
        },
        expected={
            "year": 2024,
            "month": 6,
            "day": 15,
            "hour": 17,
            "minute": 30,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should apply a positive half-hour offset",
    ),
    ExpressionTestCase(
        "tz_zero",
        doc={"timezone": "+00:00"},
        expression={
            "$dateToParts": {
                "date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "$timezone",
            }
        },
        expected={
            "year": 2024,
            "month": 6,
            "day": 15,
            "hour": 12,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should apply a zero offset",
    ),
    ExpressionTestCase(
        "tz_no_colon",
        doc={"timezone": "-0500"},
        expression={
            "$dateToParts": {
                "date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "$timezone",
            }
        },
        expected={
            "year": 2024,
            "month": 6,
            "day": 15,
            "hour": 7,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should accept an offset without a colon",
    ),
    ExpressionTestCase(
        "tz_hour_only",
        doc={"timezone": "+03"},
        expression={
            "$dateToParts": {
                "date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "$timezone",
            }
        },
        expected={
            "year": 2024,
            "month": 6,
            "day": 15,
            "hour": 15,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should accept an hour-only offset",
    ),
    ExpressionTestCase(
        "tz_45min",
        doc={"timezone": "+05:45"},
        expression={
            "$dateToParts": {
                "date": datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "$timezone",
            }
        },
        expected={
            "year": 2020,
            "month": 1,
            "day": 1,
            "hour": 17,
            "minute": 45,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should apply a 45-minute offset",
    ),
    ExpressionTestCase(
        "tz_half_hour_west",
        doc={"timezone": "-03:30"},
        expression={
            "$dateToParts": {
                "date": datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "$timezone",
            }
        },
        expected={
            "year": 2020,
            "month": 1,
            "day": 1,
            "hour": 8,
            "minute": 30,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should apply a half-hour west offset",
    ),
    ExpressionTestCase(
        "tz_plus14",
        doc={"timezone": "+14:00"},
        expression={
            "$dateToParts": {
                "date": datetime(2024, 6, 15, 11, 0, 0, tzinfo=timezone.utc),
                "timezone": "$timezone",
            }
        },
        expected={
            "year": 2024,
            "month": 6,
            "day": 16,
            "hour": 1,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should apply a +14:00 offset",
    ),
    ExpressionTestCase(
        "tz_minus11",
        doc={"timezone": "-11:00"},
        expression={
            "$dateToParts": {
                "date": datetime(2024, 6, 15, 10, 0, 0, tzinfo=timezone.utc),
                "timezone": "$timezone",
            }
        },
        expected={
            "year": 2024,
            "month": 6,
            "day": 14,
            "hour": 23,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should apply a -11:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus13",
        doc={"timezone": "-13:00"},
        expression={
            "$dateToParts": {
                "date": datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "$timezone",
            }
        },
        expected={
            "year": 2019,
            "month": 12,
            "day": 31,
            "hour": 23,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should accept a -13:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_plus15",
        doc={"timezone": "+15:00"},
        expression={
            "$dateToParts": {
                "date": datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "$timezone",
            }
        },
        expected={
            "year": 2020,
            "month": 1,
            "day": 2,
            "hour": 3,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should accept a +15:00 offset",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(DATETOPARTS_TZ_NUMERIC_OFFSET_TESTS))
def test_dateToParts_timezone_numeric(collection, test_case: ExpressionTestCase):
    """Test $dateToParts numeric offset timezones."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
