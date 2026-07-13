"""Tests for $isoDayOfWeek ISO day-of-week extraction across the calendar and year range."""

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
from documentdb_tests.framework.test_constants import DATE_EPOCH, DATE_YEAR_1900

# Property [ISO Day Extraction]: $isoDayOfWeek returns the ISO 8601 day of the week
# (1=Monday to 7=Sunday) of a UTC date.
ISODAYOFWEEK_EXTRACTION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "monday",
        doc={"date": datetime(2024, 1, 15, tzinfo=timezone.utc)},
        expression={"$isoDayOfWeek": "$date"},
        expected=1,
        msg="$isoDayOfWeek should return 1 for a Monday",
    ),
    ExpressionTestCase(
        "tuesday",
        doc={"date": datetime(2024, 1, 16, tzinfo=timezone.utc)},
        expression={"$isoDayOfWeek": "$date"},
        expected=2,
        msg="$isoDayOfWeek should return 2 for a Tuesday",
    ),
    ExpressionTestCase(
        "wednesday",
        doc={"date": datetime(2024, 1, 17, tzinfo=timezone.utc)},
        expression={"$isoDayOfWeek": "$date"},
        expected=3,
        msg="$isoDayOfWeek should return 3 for a Wednesday",
    ),
    ExpressionTestCase(
        "thursday",
        doc={"date": datetime(2024, 1, 18, tzinfo=timezone.utc)},
        expression={"$isoDayOfWeek": "$date"},
        expected=4,
        msg="$isoDayOfWeek should return 4 for a Thursday",
    ),
    ExpressionTestCase(
        "friday",
        doc={"date": datetime(2024, 1, 19, tzinfo=timezone.utc)},
        expression={"$isoDayOfWeek": "$date"},
        expected=5,
        msg="$isoDayOfWeek should return 5 for a Friday",
    ),
    ExpressionTestCase(
        "saturday",
        doc={"date": datetime(2024, 1, 20, tzinfo=timezone.utc)},
        expression={"$isoDayOfWeek": "$date"},
        expected=6,
        msg="$isoDayOfWeek should return 6 for a Saturday",
    ),
    ExpressionTestCase(
        "sunday",
        doc={"date": datetime(2024, 1, 21, tzinfo=timezone.utc)},
        expression={"$isoDayOfWeek": "$date"},
        expected=7,
        msg="$isoDayOfWeek should return 7 for a Sunday",
    ),
    ExpressionTestCase(
        "saturday_1998",
        doc={"date": datetime(1998, 11, 7, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoDayOfWeek": "$date"},
        expected=6,
        msg="$isoDayOfWeek should return 6 for a Saturday in 1998",
    ),
]

# Property [Year Range]: the ISO day is correct at the epoch and at distant past and future
# dates, including the day immediately before the epoch.
ISODAYOFWEEK_YEAR_RANGE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "epoch",
        doc={"date": DATE_EPOCH},
        expression={"$isoDayOfWeek": "$date"},
        expected=4,
        msg="$isoDayOfWeek should return 4 for the epoch, a Thursday",
    ),
    ExpressionTestCase(
        "pre_epoch",
        doc={"date": datetime(1969, 12, 31, tzinfo=timezone.utc)},
        expression={"$isoDayOfWeek": "$date"},
        expected=3,
        msg="$isoDayOfWeek should return 3 for the day before the epoch, a Wednesday",
    ),
    ExpressionTestCase(
        "distant_past",
        doc={"date": DATE_YEAR_1900},
        expression={"$isoDayOfWeek": "$date"},
        expected=1,
        msg="$isoDayOfWeek should return 1 for a distant past date, a Monday",
    ),
    ExpressionTestCase(
        "distant_future",
        doc={"date": datetime(2100, 1, 1, tzinfo=timezone.utc)},
        expression={"$isoDayOfWeek": "$date"},
        expected=5,
        msg="$isoDayOfWeek should return 5 for a distant future date, a Friday",
    ),
]

# Property [Leap Years]: the ISO day is correct on and around leap day, including century
# and non-century leap-rule boundaries.
ISODAYOFWEEK_LEAP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "leap_day_2020",
        doc={"date": datetime(2020, 2, 29, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoDayOfWeek": "$date"},
        expected=6,
        msg="$isoDayOfWeek should return 6 for leap day 2020, a Saturday",
    ),
    ExpressionTestCase(
        "leap_day_2000",
        doc={"date": datetime(2000, 2, 29, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoDayOfWeek": "$date"},
        expected=2,
        msg="$isoDayOfWeek should return 2 for leap day of the year-2000 century leap, a Tuesday",
    ),
    ExpressionTestCase(
        "non_leap_century_1900",
        doc={"date": datetime(1900, 2, 28, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoDayOfWeek": "$date"},
        expected=3,
        msg="$isoDayOfWeek should return 3 for Feb 28 of the non-leap century 1900, a Wednesday",
    ),
]

ISODAYOFWEEK_CALENDAR_TESTS: list[ExpressionTestCase] = (
    ISODAYOFWEEK_EXTRACTION_TESTS + ISODAYOFWEEK_YEAR_RANGE_TESTS + ISODAYOFWEEK_LEAP_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(ISODAYOFWEEK_CALENDAR_TESTS))
def test_isoDayOfWeek_calendar(collection, test_case: ExpressionTestCase):
    """Test $isoDayOfWeek ISO day extraction across the calendar, year range, and leap years."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
