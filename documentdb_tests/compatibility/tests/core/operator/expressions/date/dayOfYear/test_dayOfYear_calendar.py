"""Tests for $dayOfYear day-of-year extraction from datetimes across the calendar and year range."""

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

# Property [Day Extraction]: $dayOfYear returns the ordinal day (1-366) of a UTC date.
DAYOFYEAR_EXTRACTION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "day_1",
        doc={"date": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfYear": "$date"},
        expected=1,
        msg="$dayOfYear should return 1 for the first day of the year",
    ),
    ExpressionTestCase(
        "day_15",
        doc={"date": datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfYear": "$date"},
        expected=15,
        msg="$dayOfYear should return 15 for the fifteenth day of the year",
    ),
    ExpressionTestCase(
        "day_60_leap_feb29",
        doc={"date": datetime(2024, 2, 29, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfYear": "$date"},
        expected=60,
        msg="$dayOfYear should return 60 for Feb 29 in a leap year",
    ),
    ExpressionTestCase(
        "day_167_jun15",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfYear": "$date"},
        expected=167,
        msg="$dayOfYear should return the ordinal day for Jun 15 in a leap year",
    ),
    ExpressionTestCase(
        "day_366_dec31_leap",
        doc={"date": datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$dayOfYear": "$date"},
        expected=366,
        msg="$dayOfYear should return 366, the maximum ordinal day, for Dec 31 in a leap year",
    ),
]

# Property [Calendar Boundaries]: year edges, leap-year Feb 29, century rules, and
# sub-second precision resolve to the correct ordinal day.
DAYOFYEAR_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "first_moment_of_year",
        doc={"date": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfYear": "$date"},
        expected=1,
        msg="$dayOfYear should return 1 for the first moment of the year",
    ),
    ExpressionTestCase(
        "non_leap_year_feb_28",
        doc={"date": datetime(2023, 2, 28, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfYear": "$date"},
        expected=59,
        msg="$dayOfYear should return 59 for Feb 28 in a non-leap year",
    ),
    ExpressionTestCase(
        "leap_year_feb_29_2000",
        doc={"date": datetime(2000, 2, 29, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfYear": "$date"},
        expected=60,
        msg="$dayOfYear should return 60 for Feb 29 in the century leap year 2000",
    ),
    ExpressionTestCase(
        "non_leap_century_1900_feb_28",
        doc={"date": datetime(1900, 2, 28, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfYear": "$date"},
        expected=59,
        msg="$dayOfYear should return 59 for Feb 28 in the non-leap century year 1900",
    ),
    ExpressionTestCase(
        "non_leap_year_dec_31",
        doc={"date": datetime(2023, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$dayOfYear": "$date"},
        expected=365,
        msg="$dayOfYear should return 365 for Dec 31 in a non-leap year",
    ),
    ExpressionTestCase(
        "millisecond_before_next_day",
        doc={"date": datetime(2024, 6, 15, 23, 59, 59, 999000, tzinfo=timezone.utc)},
        expression={"$dayOfYear": "$date"},
        expected=167,
        msg="$dayOfYear should not advance to the next day one millisecond before it",
    ),
    ExpressionTestCase(
        "millisecond_after_day_start",
        doc={"date": datetime(2024, 6, 16, 0, 0, 0, 1000, tzinfo=timezone.utc)},
        expression={"$dayOfYear": "$date"},
        expected=168,
        msg="$dayOfYear should advance to the new day one millisecond after it starts",
    ),
    ExpressionTestCase(
        "millisecond_mid_day",
        doc={"date": datetime(2024, 6, 15, 12, 30, 30, 500000, tzinfo=timezone.utc)},
        expression={"$dayOfYear": "$date"},
        expected=167,
        msg="$dayOfYear should return the day for a mid-day instant with milliseconds",
    ),
    ExpressionTestCase(
        "millisecond_year_boundary",
        doc={"date": datetime(2024, 12, 31, 23, 59, 59, 999000, tzinfo=timezone.utc)},
        expression={"$dayOfYear": "$date"},
        expected=366,
        msg="$dayOfYear should return 366 one millisecond before the year boundary",
    ),
    ExpressionTestCase(
        "millisecond_leap_feb_end",
        doc={"date": datetime(2024, 2, 29, 23, 59, 59, 999000, tzinfo=timezone.utc)},
        expression={"$dayOfYear": "$date"},
        expected=60,
        msg="$dayOfYear should return 60 one millisecond before the end of leap-year February",
    ),
]

# Property [Year Range]: the ordinal day is correct across a wide span of years.
DAYOFYEAR_YEAR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "year_2000",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfYear": "$date"},
        expected=1,
        msg="$dayOfYear should return 1 for a date in the year 2000",
    ),
    ExpressionTestCase(
        "year_1970_epoch",
        doc={"date": DATE_EPOCH},
        expression={"$dayOfYear": "$date"},
        expected=1,
        msg="$dayOfYear should return 1 for the Unix epoch",
    ),
    ExpressionTestCase(
        "year_1999",
        doc={"date": datetime(1999, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$dayOfYear": "$date"},
        expected=365,
        msg="$dayOfYear should return 365 for the last day of 1999",
    ),
    ExpressionTestCase(
        "year_2099",
        doc={"date": datetime(2099, 7, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfYear": "$date"},
        expected=196,
        msg="$dayOfYear should return 196 for Jul 15 2099",
    ),
    ExpressionTestCase(
        "year_9999",
        doc={"date": datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$dayOfYear": "$date"},
        expected=365,
        msg="$dayOfYear should return 365 for the last day of the last representable year 9999",
    ),
]

# Property [Pre-Epoch]: negative-millisecond dates before 1970 resolve to the correct day.
DAYOFYEAR_PRE_EPOCH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "pre_epoch_1960",
        doc={"date": datetime(1960, 3, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfYear": "$date"},
        expected=75,
        msg="$dayOfYear should return 75 for a pre-epoch date in 1960",
    ),
    ExpressionTestCase(
        "pre_epoch_1900",
        doc={"date": datetime(1900, 7, 4, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfYear": "$date"},
        expected=185,
        msg="$dayOfYear should return 185 for a pre-epoch date in 1900",
    ),
    ExpressionTestCase(
        "pre_epoch_1969_dec",
        doc={"date": datetime(1969, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$dayOfYear": "$date"},
        expected=365,
        msg="$dayOfYear should return 365 for the last day before the epoch",
    ),
    ExpressionTestCase(
        "pre_epoch_1969_jan",
        doc={"date": datetime(1969, 1, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfYear": "$date"},
        expected=1,
        msg="$dayOfYear should return 1 for the first day of 1969",
    ),
    ExpressionTestCase(
        "pre_epoch_1950_leap",
        doc={"date": datetime(1952, 2, 29, 6, 0, 0, tzinfo=timezone.utc)},
        expression={"$dayOfYear": "$date"},
        expected=60,
        msg="$dayOfYear should return 60 for Feb 29 in the pre-epoch leap year 1952",
    ),
]

DAYOFYEAR_CALENDAR_TESTS: list[ExpressionTestCase] = (
    DAYOFYEAR_EXTRACTION_TESTS
    + DAYOFYEAR_BOUNDARY_TESTS
    + DAYOFYEAR_YEAR_TESTS
    + DAYOFYEAR_PRE_EPOCH_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DAYOFYEAR_CALENDAR_TESTS))
def test_dayOfYear_calendar(collection, test_case: ExpressionTestCase):
    """Test $dayOfYear day-of-year extraction across the calendar and year range."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
