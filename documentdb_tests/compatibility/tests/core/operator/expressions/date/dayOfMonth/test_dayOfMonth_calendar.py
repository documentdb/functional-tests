"""Tests for $dayOfMonth day extraction from datetimes across the calendar and year range."""

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

# Property [Day Extraction]: $dayOfMonth returns the day component (1-31) of a UTC date.
DAYOFMONTH_EXTRACTION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "day_1",
        doc={"date": datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfMonth": "$date"},
        expected=1,
        msg="$dayOfMonth should return 1 for the first day of the month",
    ),
    ExpressionTestCase(
        "day_15",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfMonth": "$date"},
        expected=15,
        msg="$dayOfMonth should return 15 for the fifteenth day of the month",
    ),
    ExpressionTestCase(
        "day_28",
        doc={"date": datetime(2024, 6, 28, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfMonth": "$date"},
        expected=28,
        msg="$dayOfMonth should return 28 for the twenty-eighth day of the month",
    ),
    ExpressionTestCase(
        "day_30",
        doc={"date": datetime(2024, 6, 30, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfMonth": "$date"},
        expected=30,
        msg="$dayOfMonth should return 30 for the thirtieth day of the month",
    ),
    ExpressionTestCase(
        "day_31",
        doc={"date": datetime(2024, 7, 31, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfMonth": "$date"},
        expected=31,
        msg="$dayOfMonth should return 31 for the thirty-first day of the month",
    ),
]

# Property [Calendar Boundaries]: year edges, leap-year Feb 29, century rules, and
# sub-second precision resolve to the correct day.
DAYOFMONTH_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "first_day_of_year",
        doc={"date": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfMonth": "$date"},
        expected=1,
        msg="$dayOfMonth should return 1 for the first day of the year",
    ),
    ExpressionTestCase(
        "last_day_of_year",
        doc={"date": datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$dayOfMonth": "$date"},
        expected=31,
        msg="$dayOfMonth should return 31 for the last day of the year",
    ),
    ExpressionTestCase(
        "leap_year_feb_29",
        doc={"date": datetime(2024, 2, 29, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfMonth": "$date"},
        expected=29,
        msg="$dayOfMonth should return 29 for Feb 29 in a leap year",
    ),
    ExpressionTestCase(
        "non_leap_year_feb_28",
        doc={"date": datetime(2023, 2, 28, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfMonth": "$date"},
        expected=28,
        msg="$dayOfMonth should return 28 for Feb 28 in a non-leap year",
    ),
    ExpressionTestCase(
        "leap_year_feb_29_2000",
        doc={"date": datetime(2000, 2, 29, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfMonth": "$date"},
        expected=29,
        msg="$dayOfMonth should return 29 for Feb 29 in the century leap year 2000",
    ),
    ExpressionTestCase(
        "non_leap_century_1900_feb_28",
        doc={"date": datetime(1900, 2, 28, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfMonth": "$date"},
        expected=28,
        msg="$dayOfMonth should return 28 for Feb 28 in the non-leap century year 1900",
    ),
    ExpressionTestCase(
        "millisecond_before_next_day",
        doc={"date": datetime(2024, 6, 15, 23, 59, 59, 999000, tzinfo=timezone.utc)},
        expression={"$dayOfMonth": "$date"},
        expected=15,
        msg="$dayOfMonth should return 15 one millisecond before the next day",
    ),
    ExpressionTestCase(
        "millisecond_after_day_start",
        doc={"date": datetime(2024, 6, 16, 0, 0, 0, 1000, tzinfo=timezone.utc)},
        expression={"$dayOfMonth": "$date"},
        expected=16,
        msg="$dayOfMonth should return 16 one millisecond after the day starts",
    ),
    ExpressionTestCase(
        "millisecond_mid_day",
        doc={"date": datetime(2024, 6, 15, 12, 30, 30, 500000, tzinfo=timezone.utc)},
        expression={"$dayOfMonth": "$date"},
        expected=15,
        msg="$dayOfMonth should return 15 for a mid-day instant with milliseconds",
    ),
    ExpressionTestCase(
        "millisecond_month_boundary",
        doc={"date": datetime(2024, 6, 30, 23, 59, 59, 999000, tzinfo=timezone.utc)},
        expression={"$dayOfMonth": "$date"},
        expected=30,
        msg="$dayOfMonth should return 30 one millisecond before the month boundary",
    ),
    ExpressionTestCase(
        "millisecond_leap_feb_end",
        doc={"date": datetime(2024, 2, 29, 23, 59, 59, 999000, tzinfo=timezone.utc)},
        expression={"$dayOfMonth": "$date"},
        expected=29,
        msg="$dayOfMonth should return 29 one millisecond before the end of leap-year February",
    ),
]

# Property [Year Range]: the day component is correct across a wide span of years.
DAYOFMONTH_YEAR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "year_2000",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfMonth": "$date"},
        expected=1,
        msg="$dayOfMonth should return 1 for a date in the year 2000",
    ),
    ExpressionTestCase(
        "year_1970_epoch",
        doc={"date": DATE_EPOCH},
        expression={"$dayOfMonth": "$date"},
        expected=1,
        msg="$dayOfMonth should return 1 for the Unix epoch",
    ),
    ExpressionTestCase(
        "year_1999",
        doc={"date": datetime(1999, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$dayOfMonth": "$date"},
        expected=31,
        msg="$dayOfMonth should return 31 for the last day of 1999",
    ),
    ExpressionTestCase(
        "year_2099",
        doc={"date": datetime(2099, 7, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfMonth": "$date"},
        expected=15,
        msg="$dayOfMonth should return 15 for a date in the year 2099",
    ),
    ExpressionTestCase(
        "year_9999",
        doc={"date": datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$dayOfMonth": "$date"},
        expected=31,
        msg="$dayOfMonth should return 31 for the last representable year 9999",
    ),
]

# Property [Pre-Epoch]: negative-millisecond dates before 1970 resolve to the correct day.
DAYOFMONTH_PRE_EPOCH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "pre_epoch_1960",
        doc={"date": datetime(1960, 3, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfMonth": "$date"},
        expected=15,
        msg="$dayOfMonth should return 15 for a pre-epoch date in 1960",
    ),
    ExpressionTestCase(
        "pre_epoch_1900",
        doc={"date": datetime(1900, 7, 4, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfMonth": "$date"},
        expected=4,
        msg="$dayOfMonth should return 4 for a pre-epoch date in 1900",
    ),
    ExpressionTestCase(
        "pre_epoch_1969_dec",
        doc={"date": datetime(1969, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$dayOfMonth": "$date"},
        expected=31,
        msg="$dayOfMonth should return 31 for the last day before the epoch",
    ),
    ExpressionTestCase(
        "pre_epoch_1969_jan",
        doc={"date": datetime(1969, 1, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfMonth": "$date"},
        expected=1,
        msg="$dayOfMonth should return 1 for the first day of 1969",
    ),
    ExpressionTestCase(
        "pre_epoch_1950_leap",
        doc={"date": datetime(1952, 2, 29, 6, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfMonth": "$date"},
        expected=29,
        msg="$dayOfMonth should return 29 for Feb 29 in the pre-epoch leap year 1952",
    ),
]

DAYOFMONTH_CALENDAR_TESTS: list[ExpressionTestCase] = (
    DAYOFMONTH_EXTRACTION_TESTS
    + DAYOFMONTH_BOUNDARY_TESTS
    + DAYOFMONTH_YEAR_TESTS
    + DAYOFMONTH_PRE_EPOCH_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DAYOFMONTH_CALENDAR_TESTS))
def test_dayOfMonth_calendar(collection, test_case: ExpressionTestCase):
    """Test $dayOfMonth day extraction across the calendar and year range."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
