"""Tests for $dateToParts standard, ISO, and millisecond part extraction."""

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

# Property [Standard Parts]: calendar parts are extracted correctly across the calendar.
DATETOPARTS_STANDARD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "midnight",
        doc={"date": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateToParts": {"date": "$date"}},
        expected={
            "year": 2024,
            "month": 1,
            "day": 1,
            "hour": 0,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should extract parts at midnight",
    ),
    ExpressionTestCase(
        "end_of_year",
        doc={"date": datetime(2024, 12, 31, 23, 59, 59, 999000, tzinfo=timezone.utc)},
        expression={"$dateToParts": {"date": "$date"}},
        expected={
            "year": 2024,
            "month": 12,
            "day": 31,
            "hour": 23,
            "minute": 59,
            "second": 59,
            "millisecond": 999,
        },
        msg="$dateToParts should extract parts at the end of the year",
    ),
    ExpressionTestCase(
        "leap_day",
        doc={"date": datetime(2000, 2, 29, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateToParts": {"date": "$date"}},
        expected={
            "year": 2000,
            "month": 2,
            "day": 29,
            "hour": 12,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should extract parts on a leap day in a 400-divisible year",
    ),
    ExpressionTestCase(
        "leap_day_2024",
        doc={"date": datetime(2024, 2, 29, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateToParts": {"date": "$date"}},
        expected={
            "year": 2024,
            "month": 2,
            "day": 29,
            "hour": 0,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should extract parts on a leap day",
    ),
    ExpressionTestCase(
        "non_leap_century_1900",
        doc={"date": datetime(1900, 2, 28, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateToParts": {"date": "$date"}},
        expected={
            "year": 1900,
            "month": 2,
            "day": 28,
            "hour": 0,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should treat 1900 as a non-leap century year",
    ),
]

# Property [ISO Parts]: iso8601 selects between ISO week-date parts and calendar parts.
DATETOPARTS_ISO_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "iso_mid_year",
        doc={"date": datetime(2024, 6, 15, 10, 30, 0, tzinfo=timezone.utc)},
        expression={
            "$dateToParts": {
                "date": "$date",
                "iso8601": True,
            }
        },
        expected={
            "isoWeekYear": 2024,
            "isoWeek": 24,
            "isoDayOfWeek": 6,
            "hour": 10,
            "minute": 30,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should return ISO parts for a mid-year date",
    ),
    ExpressionTestCase(
        "iso_year_differs",
        doc={"date": datetime(2016, 1, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateToParts": {
                "date": "$date",
                "iso8601": True,
            }
        },
        expected={
            "isoWeekYear": 2015,
            "isoWeek": 53,
            "isoDayOfWeek": 5,
            "hour": 0,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should return an ISO week-year that differs from the calendar year",
    ),
    ExpressionTestCase(
        "iso_false_same",
        doc={"date": datetime(2024, 6, 15, 10, 30, 45, 500000, tzinfo=timezone.utc)},
        expression={
            "$dateToParts": {
                "date": "$date",
                "iso8601": False,
            }
        },
        expected={
            "year": 2024,
            "month": 6,
            "day": 15,
            "hour": 10,
            "minute": 30,
            "second": 45,
            "millisecond": 500,
        },
        msg="$dateToParts should return calendar parts when iso8601 is false",
    ),
    ExpressionTestCase(
        "iso_2021_jan1",
        doc={"date": datetime(2021, 1, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateToParts": {
                "date": "$date",
                "iso8601": True,
            }
        },
        expected={
            "isoWeekYear": 2020,
            "isoWeek": 53,
            "isoDayOfWeek": 5,
            "hour": 0,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should assign Jan 1 2021 to ISO week 53 of 2020",
    ),
    ExpressionTestCase(
        "iso_2020_dec31",
        doc={"date": datetime(2020, 12, 31, 0, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateToParts": {
                "date": "$date",
                "iso8601": True,
            }
        },
        expected={
            "isoWeekYear": 2020,
            "isoWeek": 53,
            "isoDayOfWeek": 4,
            "hour": 0,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should assign Dec 31 2020 to ISO week 53 of 2020",
    ),
    ExpressionTestCase(
        "iso_2015_jan1",
        doc={"date": datetime(2015, 1, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateToParts": {
                "date": "$date",
                "iso8601": True,
            }
        },
        expected={
            "isoWeekYear": 2015,
            "isoWeek": 1,
            "isoDayOfWeek": 4,
            "hour": 0,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should assign Jan 1 2015 to ISO week 1 of 2015",
    ),
]

# Property [Millisecond Precision]: sub-second milliseconds are preserved.
DATETOPARTS_MS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "ms_zero",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateToParts": {"date": "$date"}},
        expected={
            "year": 2024,
            "month": 6,
            "day": 15,
            "hour": 12,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should report zero milliseconds",
    ),
    ExpressionTestCase(
        "ms_999",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, 999000, tzinfo=timezone.utc)},
        expression={"$dateToParts": {"date": "$date"}},
        expected={
            "year": 2024,
            "month": 6,
            "day": 15,
            "hour": 12,
            "minute": 0,
            "second": 0,
            "millisecond": 999,
        },
        msg="$dateToParts should report 999 milliseconds",
    ),
    ExpressionTestCase(
        "ms_500",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, 500000, tzinfo=timezone.utc)},
        expression={"$dateToParts": {"date": "$date"}},
        expected={
            "year": 2024,
            "month": 6,
            "day": 15,
            "hour": 12,
            "minute": 0,
            "second": 0,
            "millisecond": 500,
        },
        msg="$dateToParts should report 500 milliseconds",
    ),
]

DATETOPARTS_PARTS_TESTS: list[ExpressionTestCase] = (
    DATETOPARTS_STANDARD_TESTS + DATETOPARTS_ISO_TESTS + DATETOPARTS_MS_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATETOPARTS_PARTS_TESTS))
def test_dateToParts_parts(collection, test_case: ExpressionTestCase):
    """Test $dateToParts part extraction."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
