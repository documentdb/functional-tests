"""Tests for $dayOfWeek day-of-week extraction across the calendar and year range."""

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
from documentdb_tests.framework.test_constants import DATE_EPOCH

# Property [Day Extraction]: $dayOfWeek returns the day of the week (1=Sunday to 7=Saturday)
# of a UTC date.
DAYOFWEEK_EXTRACTION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "sunday",
        doc={"date": datetime(2024, 6, 30, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfWeek": "$date"},
        expected=1,
        msg="$dayOfWeek should return 1 for a Sunday",
    ),
    ExpressionTestCase(
        "monday",
        doc={"date": datetime(2024, 7, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfWeek": "$date"},
        expected=2,
        msg="$dayOfWeek should return 2 for a Monday",
    ),
    ExpressionTestCase(
        "tuesday",
        doc={"date": datetime(2024, 7, 2, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfWeek": "$date"},
        expected=3,
        msg="$dayOfWeek should return 3 for a Tuesday",
    ),
    ExpressionTestCase(
        "wednesday",
        doc={"date": datetime(2024, 7, 3, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfWeek": "$date"},
        expected=4,
        msg="$dayOfWeek should return 4 for a Wednesday",
    ),
    ExpressionTestCase(
        "thursday",
        doc={"date": datetime(2024, 7, 4, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfWeek": "$date"},
        expected=5,
        msg="$dayOfWeek should return 5 for a Thursday",
    ),
    ExpressionTestCase(
        "friday",
        doc={"date": datetime(2024, 7, 5, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfWeek": "$date"},
        expected=6,
        msg="$dayOfWeek should return 6 for a Friday",
    ),
    ExpressionTestCase(
        "saturday",
        doc={"date": datetime(2024, 7, 6, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfWeek": "$date"},
        expected=7,
        msg="$dayOfWeek should return 7 for a Saturday",
    ),
]

# Property [Calendar Boundaries]: year edges, leap-year Feb 29, century rules, and
# sub-second precision resolve to the correct day of the week.
DAYOFWEEK_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "first_day_of_year",
        doc={"date": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfWeek": "$date"},
        expected=2,
        msg="$dayOfWeek should return 2 for the first day of the year",
    ),
    ExpressionTestCase(
        "last_day_of_year",
        doc={"date": datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$dayOfWeek": "$date"},
        expected=3,
        msg="$dayOfWeek should return 3 for the last day of the year",
    ),
    ExpressionTestCase(
        "leap_year_feb_29",
        doc={"date": datetime(2024, 2, 29, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfWeek": "$date"},
        expected=5,
        msg="$dayOfWeek should return 5 for Feb 29 in a leap year",
    ),
    ExpressionTestCase(
        "non_leap_year_feb_28",
        doc={"date": datetime(2023, 2, 28, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfWeek": "$date"},
        expected=3,
        msg="$dayOfWeek should return 3 for Feb 28 in a non-leap year",
    ),
    ExpressionTestCase(
        "leap_year_feb_29_2020",
        doc={"date": datetime(2020, 2, 29, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfWeek": "$date"},
        expected=7,
        msg="$dayOfWeek should return 7 for Feb 29 2020",
    ),
    ExpressionTestCase(
        "leap_year_feb_29_2000",
        doc={"date": datetime(2000, 2, 29, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfWeek": "$date"},
        expected=3,
        msg="$dayOfWeek should return 3 for Feb 29 in the century leap year 2000",
    ),
    ExpressionTestCase(
        "non_leap_century_1900_feb_28",
        doc={"date": datetime(1900, 2, 28, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfWeek": "$date"},
        expected=4,
        msg="$dayOfWeek should return 4 for Feb 28 in the non-leap century year 1900",
    ),
    ExpressionTestCase(
        "millisecond_after_day_start",
        doc={"date": datetime(2024, 7, 1, 0, 0, 0, 1000, tzinfo=timezone.utc)},
        expression={"$dayOfWeek": "$date"},
        expected=2,
        msg="$dayOfWeek should return 2 one millisecond after the day starts",
    ),
    ExpressionTestCase(
        "millisecond_mid_day",
        doc={"date": datetime(2024, 6, 15, 12, 30, 30, 500000, tzinfo=timezone.utc)},
        expression={"$dayOfWeek": "$date"},
        expected=7,
        msg="$dayOfWeek should return 7 for a mid-day instant with milliseconds",
    ),
    ExpressionTestCase(
        "millisecond_month_boundary",
        doc={"date": datetime(2024, 6, 30, 23, 59, 59, 999000, tzinfo=timezone.utc)},
        expression={"$dayOfWeek": "$date"},
        expected=1,
        msg="$dayOfWeek should return 1 one millisecond before the month boundary",
    ),
    ExpressionTestCase(
        "millisecond_year_boundary",
        doc={"date": datetime(2024, 12, 31, 23, 59, 59, 999000, tzinfo=timezone.utc)},
        expression={"$dayOfWeek": "$date"},
        expected=3,
        msg="$dayOfWeek should return 3 one millisecond before the year boundary",
    ),
]

# Property [Year Range]: the day of the week is correct across a wide span of years.
DAYOFWEEK_YEAR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "year_2000",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfWeek": "$date"},
        expected=7,
        msg="$dayOfWeek should return 7 for a date in the year 2000",
    ),
    ExpressionTestCase(
        "year_1970_epoch",
        doc={"date": DATE_EPOCH},
        expression={"$dayOfWeek": "$date"},
        expected=5,
        msg="$dayOfWeek should return 5 for the Unix epoch",
    ),
    ExpressionTestCase(
        "year_1999",
        doc={"date": datetime(1999, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$dayOfWeek": "$date"},
        expected=6,
        msg="$dayOfWeek should return 6 for the last day of 1999",
    ),
    ExpressionTestCase(
        "year_2099",
        doc={"date": datetime(2099, 7, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfWeek": "$date"},
        expected=4,
        msg="$dayOfWeek should return 4 for a date in the year 2099",
    ),
    ExpressionTestCase(
        "year_9999",
        doc={"date": datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$dayOfWeek": "$date"},
        expected=6,
        msg="$dayOfWeek should return 6 for the last representable year 9999",
    ),
]

# Property [Pre-Epoch]: negative-millisecond dates before 1970 resolve to the correct day.
DAYOFWEEK_PRE_EPOCH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "pre_epoch_1960",
        doc={"date": datetime(1960, 3, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfWeek": "$date"},
        expected=3,
        msg="$dayOfWeek should return 3 for a pre-epoch date in 1960",
    ),
    ExpressionTestCase(
        "pre_epoch_1900",
        doc={"date": datetime(1900, 7, 4, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfWeek": "$date"},
        expected=4,
        msg="$dayOfWeek should return 4 for a pre-epoch date in 1900",
    ),
    ExpressionTestCase(
        "pre_epoch_1969_dec",
        doc={"date": datetime(1969, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$dayOfWeek": "$date"},
        expected=4,
        msg="$dayOfWeek should return 4 for the last day before the epoch",
    ),
    ExpressionTestCase(
        "pre_epoch_1969_jan",
        doc={"date": datetime(1969, 1, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfWeek": "$date"},
        expected=4,
        msg="$dayOfWeek should return 4 for the first day of 1969",
    ),
    ExpressionTestCase(
        "pre_epoch_1950_leap",
        doc={"date": datetime(1952, 2, 29, 6, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfWeek": "$date"},
        expected=6,
        msg="$dayOfWeek should return 6 for Feb 29 in the pre-epoch leap year 1952",
    ),
]

DAYOFWEEK_CALENDAR_TESTS: list[ExpressionTestCase] = (
    DAYOFWEEK_EXTRACTION_TESTS
    + DAYOFWEEK_BOUNDARY_TESTS
    + DAYOFWEEK_YEAR_TESTS
    + DAYOFWEEK_PRE_EPOCH_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DAYOFWEEK_CALENDAR_TESTS))
def test_dayOfWeek_calendar(collection, test_case: ExpressionTestCase):
    """Test $dayOfWeek day-of-week extraction across the calendar and year range."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
