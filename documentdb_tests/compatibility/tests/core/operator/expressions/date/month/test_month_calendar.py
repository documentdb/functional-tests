"""Tests for $month month extraction from datetimes across the calendar and year range."""

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

# Property [Month Extraction]: $month returns the month component (1-12) of a UTC date.
MONTH_EXTRACTION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "january",
        doc={"date": datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)},
        expression={"$month": "$date"},
        expected=1,
        msg="$month should return 1 for a date in January",
    ),
    ExpressionTestCase(
        "february",
        doc={"date": datetime(2024, 2, 28, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$month": "$date"},
        expected=2,
        msg="$month should return 2 for a date in February",
    ),
    ExpressionTestCase(
        "march",
        doc={"date": datetime(2024, 3, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$month": "$date"},
        expected=3,
        msg="$month should return 3 for a date in March",
    ),
    ExpressionTestCase(
        "april",
        doc={"date": datetime(2024, 4, 30, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$month": "$date"},
        expected=4,
        msg="$month should return 4 for a date in April",
    ),
    ExpressionTestCase(
        "may",
        doc={"date": datetime(2024, 5, 15, 6, 0, 0, tzinfo=timezone.utc)},
        expression={"$month": "$date"},
        expected=5,
        msg="$month should return 5 for a date in May",
    ),
    ExpressionTestCase(
        "june",
        doc={"date": datetime(2024, 6, 21, 18, 0, 0, tzinfo=timezone.utc)},
        expression={"$month": "$date"},
        expected=6,
        msg="$month should return 6 for a date in June",
    ),
    ExpressionTestCase(
        "july",
        doc={"date": datetime(2024, 7, 4, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$month": "$date"},
        expected=7,
        msg="$month should return 7 for a date in July",
    ),
    ExpressionTestCase(
        "august",
        doc={"date": datetime(2024, 8, 31, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$month": "$date"},
        expected=8,
        msg="$month should return 8 for a date in August",
    ),
    ExpressionTestCase(
        "september",
        doc={"date": datetime(2024, 9, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$month": "$date"},
        expected=9,
        msg="$month should return 9 for a date in September",
    ),
    ExpressionTestCase(
        "october",
        doc={"date": datetime(2024, 10, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$month": "$date"},
        expected=10,
        msg="$month should return 10 for a date in October",
    ),
    ExpressionTestCase(
        "november",
        doc={"date": datetime(2024, 11, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$month": "$date"},
        expected=11,
        msg="$month should return 11 for a date in November",
    ),
    ExpressionTestCase(
        "december",
        doc={"date": datetime(2024, 12, 25, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$month": "$date"},
        expected=12,
        msg="$month should return 12 for a date in December",
    ),
]

# Property [Calendar Boundaries]: year edges, the three leap-year branches (ordinary in 2024,
# century leap in 2000, century non-leap in 1900), and sub-second precision resolve to the
# correct month.
MONTH_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "first_day_of_year",
        doc={"date": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$month": "$date"},
        expected=1,
        msg="$month should return 1 for the first day of the year",
    ),
    ExpressionTestCase(
        "last_day_of_year",
        doc={"date": datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$month": "$date"},
        expected=12,
        msg="$month should return 12 for the last day of the year",
    ),
    ExpressionTestCase(
        "leap_year_feb_29",
        doc={"date": datetime(2024, 2, 29, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$month": "$date"},
        expected=2,
        msg="$month should return 2 for Feb 29 in a leap year",
    ),
    ExpressionTestCase(
        "non_leap_year_feb_28",
        doc={"date": datetime(2023, 2, 28, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$month": "$date"},
        expected=2,
        msg="$month should return 2 for Feb 28 in a non-leap year",
    ),
    ExpressionTestCase(
        "leap_year_feb_29_2000",
        doc={"date": datetime(2000, 2, 29, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$month": "$date"},
        expected=2,
        msg="$month should return 2 for Feb 29 in the century leap year 2000",
    ),
    ExpressionTestCase(
        "non_leap_century_1900_mar_1",
        doc={"date": datetime(1900, 3, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$month": "$date"},
        expected=3,
        msg="$month should return 3 for Mar 1 1900, a non-leap century year with no Feb 29",
    ),
    ExpressionTestCase(
        "midnight",
        doc={"date": datetime(2024, 6, 15, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$month": "$date"},
        expected=6,
        msg="$month should return 6 at the start of a day",
    ),
    ExpressionTestCase(
        "end_of_day",
        doc={"date": datetime(2024, 6, 15, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$month": "$date"},
        expected=6,
        msg="$month should return 6 at the end of a day",
    ),
    ExpressionTestCase(
        "millisecond_before_month_end",
        doc={"date": datetime(2024, 6, 30, 23, 59, 59, 999000, tzinfo=timezone.utc)},
        expression={"$month": "$date"},
        expected=6,
        msg="$month should return 6 one millisecond before the month ends",
    ),
    ExpressionTestCase(
        "millisecond_after_month_start",
        doc={"date": datetime(2024, 7, 1, 0, 0, 0, 1000, tzinfo=timezone.utc)},
        expression={"$month": "$date"},
        expected=7,
        msg="$month should return 7 one millisecond after the month starts",
    ),
    ExpressionTestCase(
        "millisecond_mid_month",
        doc={"date": datetime(2024, 6, 15, 12, 30, 30, 500000, tzinfo=timezone.utc)},
        expression={"$month": "$date"},
        expected=6,
        msg="$month should return 6 for a mid-month instant with milliseconds",
    ),
    ExpressionTestCase(
        "millisecond_year_boundary",
        doc={"date": datetime(2024, 12, 31, 23, 59, 59, 999000, tzinfo=timezone.utc)},
        expression={"$month": "$date"},
        expected=12,
        msg="$month should return 12 one millisecond before the year ends",
    ),
    ExpressionTestCase(
        "millisecond_leap_feb_end",
        doc={"date": datetime(2024, 2, 29, 23, 59, 59, 999000, tzinfo=timezone.utc)},
        expression={"$month": "$date"},
        expected=2,
        msg="$month should return 2 one millisecond before the end of leap-year February",
    ),
]

# Property [Year Range]: the month component is correct across a wide span of years.
MONTH_YEAR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "year_2000",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$month": "$date"},
        expected=1,
        msg="$month should return 1 for a date in the year 2000",
    ),
    ExpressionTestCase(
        "year_1970_epoch",
        doc={"date": DATE_EPOCH},
        expression={"$month": "$date"},
        expected=1,
        msg="$month should return 1 for the Unix epoch",
    ),
    ExpressionTestCase(
        "year_1999",
        doc={"date": datetime(1999, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$month": "$date"},
        expected=12,
        msg="$month should return 12 for the last day of 1999",
    ),
    ExpressionTestCase(
        "year_2099",
        doc={"date": datetime(2099, 7, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$month": "$date"},
        expected=7,
        msg="$month should return 7 for a date in the year 2099",
    ),
    ExpressionTestCase(
        "year_9999",
        doc={"date": datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$month": "$date"},
        expected=12,
        msg="$month should return 12 for the last representable year 9999",
    ),
]

# Property [Pre-Epoch]: negative-millisecond dates before 1970 resolve to the correct month.
MONTH_PRE_EPOCH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "pre_epoch_1960",
        doc={"date": datetime(1960, 3, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$month": "$date"},
        expected=3,
        msg="$month should return 3 for a pre-epoch date in 1960",
    ),
    ExpressionTestCase(
        "pre_epoch_1900",
        doc={"date": datetime(1900, 7, 4, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$month": "$date"},
        expected=7,
        msg="$month should return 7 for a pre-epoch date in 1900",
    ),
    ExpressionTestCase(
        "pre_epoch_1969_dec",
        doc={"date": datetime(1969, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$month": "$date"},
        expected=12,
        msg="$month should return 12 for the last month before the epoch",
    ),
    ExpressionTestCase(
        "pre_epoch_1969_jan",
        doc={"date": datetime(1969, 1, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$month": "$date"},
        expected=1,
        msg="$month should return 1 for the first month of 1969",
    ),
    ExpressionTestCase(
        "pre_epoch_1950_leap",
        doc={"date": datetime(1952, 2, 29, 6, 0, 0, tzinfo=timezone.utc)},
        expression={"$month": "$date"},
        expected=2,
        msg="$month should return 2 for Feb 29 in the pre-epoch leap year 1952",
    ),
]

MONTH_CALENDAR_TESTS: list[ExpressionTestCase] = (
    MONTH_EXTRACTION_TESTS + MONTH_BOUNDARY_TESTS + MONTH_YEAR_TESTS + MONTH_PRE_EPOCH_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(MONTH_CALENDAR_TESTS))
def test_month_calendar(collection, test_case: ExpressionTestCase):
    """Test $month month extraction across the calendar and year range."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
