"""Tests for $hour extraction across the 24-hour clock, calendar boundaries, and year range."""

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

# Property [Hour Extraction]: $hour returns the hour component (0-23) of a UTC date.
HOUR_EXTRACTION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "midnight",
        doc={"date": datetime(2024, 6, 15, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$hour": "$date"},
        expected=0,
        msg="$hour should return 0 for midnight",
    ),
    ExpressionTestCase(
        "hour_1",
        doc={"date": datetime(2024, 6, 15, 1, 0, 0, tzinfo=timezone.utc)},
        expression={"$hour": "$date"},
        expected=1,
        msg="$hour should return 1 for the 1 AM hour",
    ),
    ExpressionTestCase(
        "hour_6",
        doc={"date": datetime(2024, 6, 15, 6, 30, 0, tzinfo=timezone.utc)},
        expression={"$hour": "$date"},
        expected=6,
        msg="$hour should return 6 for a time in the 6 AM hour",
    ),
    ExpressionTestCase(
        "noon",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$hour": "$date"},
        expected=12,
        msg="$hour should return 12 for noon",
    ),
    ExpressionTestCase(
        "hour_13",
        doc={"date": datetime(2024, 6, 15, 13, 0, 0, tzinfo=timezone.utc)},
        expression={"$hour": "$date"},
        expected=13,
        msg="$hour should return 13 for the 1 PM hour",
    ),
    ExpressionTestCase(
        "hour_18",
        doc={"date": datetime(2024, 6, 15, 18, 45, 30, tzinfo=timezone.utc)},
        expression={"$hour": "$date"},
        expected=18,
        msg="$hour should return 18 for a time in the 6 PM hour",
    ),
    ExpressionTestCase(
        "hour_23",
        doc={"date": datetime(2024, 6, 15, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$hour": "$date"},
        expected=23,
        msg="$hour should return 23 for the last hour of the day",
    ),
]

# Property [Calendar Boundaries]: year edges, leap-year Feb 29, century rules, and
# sub-second precision resolve to the correct hour.
HOUR_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "first_moment_of_year",
        doc={"date": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$hour": "$date"},
        expected=0,
        msg="$hour should return 0 for the first moment of the year",
    ),
    ExpressionTestCase(
        "last_moment_of_year",
        doc={"date": datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$hour": "$date"},
        expected=23,
        msg="$hour should return 23 for the last moment of the year",
    ),
    ExpressionTestCase(
        "leap_year_feb_29",
        doc={"date": datetime(2024, 2, 29, 15, 0, 0, tzinfo=timezone.utc)},
        expression={"$hour": "$date"},
        expected=15,
        msg="$hour should return 15 for Feb 29 in a leap year",
    ),
    ExpressionTestCase(
        "non_leap_year_feb_28",
        doc={"date": datetime(2023, 2, 28, 15, 0, 0, tzinfo=timezone.utc)},
        expression={"$hour": "$date"},
        expected=15,
        msg="$hour should return 15 for Feb 28 in a non-leap year",
    ),
    ExpressionTestCase(
        "leap_year_feb_29_2020",
        doc={"date": datetime(2020, 2, 29, 15, 0, 0, tzinfo=timezone.utc)},
        expression={"$hour": "$date"},
        expected=15,
        msg="$hour should return 15 for Feb 29 in the leap year 2020",
    ),
    ExpressionTestCase(
        "leap_year_feb_29_2000",
        doc={"date": datetime(2000, 2, 29, 15, 0, 0, tzinfo=timezone.utc)},
        expression={"$hour": "$date"},
        expected=15,
        msg="$hour should return 15 for Feb 29 in the century leap year 2000",
    ),
    ExpressionTestCase(
        "non_leap_century_1900_feb_28",
        doc={"date": datetime(1900, 2, 28, 15, 0, 0, tzinfo=timezone.utc)},
        expression={"$hour": "$date"},
        expected=15,
        msg="$hour should return 15 for Feb 28 in the non-leap century year 1900",
    ),
    ExpressionTestCase(
        "millisecond_before_next_hour",
        doc={"date": datetime(2024, 6, 15, 11, 59, 59, 999000, tzinfo=timezone.utc)},
        expression={"$hour": "$date"},
        expected=11,
        msg="$hour should return 11 one millisecond before the next hour",
    ),
    ExpressionTestCase(
        "millisecond_after_hour_start",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, 1000, tzinfo=timezone.utc)},
        expression={"$hour": "$date"},
        expected=12,
        msg="$hour should return 12 one millisecond after the hour starts",
    ),
    ExpressionTestCase(
        "millisecond_mid_hour",
        doc={"date": datetime(2024, 6, 15, 12, 30, 30, 500000, tzinfo=timezone.utc)},
        expression={"$hour": "$date"},
        expected=12,
        msg="$hour should return 12 for a mid-hour instant with milliseconds",
    ),
    ExpressionTestCase(
        "millisecond_before_midnight",
        doc={"date": datetime(2024, 6, 15, 23, 59, 59, 999000, tzinfo=timezone.utc)},
        expression={"$hour": "$date"},
        expected=23,
        msg="$hour should return 23 one millisecond before midnight",
    ),
    ExpressionTestCase(
        "millisecond_after_midnight",
        doc={"date": datetime(2024, 6, 15, 0, 0, 0, 1000, tzinfo=timezone.utc)},
        expression={"$hour": "$date"},
        expected=0,
        msg="$hour should return 0 one millisecond after midnight",
    ),
]

# Property [Year Range]: the hour component is correct across a wide span of years.
HOUR_YEAR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "year_2000",
        doc={"date": datetime(2000, 1, 1, 8, 0, 0, tzinfo=timezone.utc)},
        expression={"$hour": "$date"},
        expected=8,
        msg="$hour should return 8 for a date in the year 2000",
    ),
    ExpressionTestCase(
        "year_1970_epoch",
        doc={"date": DATE_EPOCH},
        expression={"$hour": "$date"},
        expected=0,
        msg="$hour should return 0 for the Unix epoch",
    ),
    ExpressionTestCase(
        "year_1999",
        doc={"date": datetime(1999, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$hour": "$date"},
        expected=23,
        msg="$hour should return 23 for the last moment of 1999",
    ),
    ExpressionTestCase(
        "year_2099",
        doc={"date": datetime(2099, 7, 15, 14, 0, 0, tzinfo=timezone.utc)},
        expression={"$hour": "$date"},
        expected=14,
        msg="$hour should return 14 for a date in the year 2099",
    ),
    ExpressionTestCase(
        "year_9999",
        doc={"date": datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$hour": "$date"},
        expected=23,
        msg="$hour should return 23 for the last representable year 9999",
    ),
]

# Property [Pre-Epoch]: negative-millisecond dates before 1970 resolve to the correct hour.
HOUR_PRE_EPOCH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "pre_epoch_1960",
        doc={"date": datetime(1960, 3, 15, 14, 0, 0, tzinfo=timezone.utc)},
        expression={"$hour": "$date"},
        expected=14,
        msg="$hour should return 14 for a pre-epoch date in 1960",
    ),
    ExpressionTestCase(
        "pre_epoch_1900",
        doc={"date": datetime(1900, 7, 4, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$hour": "$date"},
        expected=0,
        msg="$hour should return 0 for a pre-epoch date in 1900",
    ),
    ExpressionTestCase(
        "pre_epoch_1969_dec",
        doc={"date": datetime(1969, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$hour": "$date"},
        expected=23,
        msg="$hour should return 23 for the last moment before the epoch",
    ),
    ExpressionTestCase(
        "pre_epoch_1969_jan",
        doc={"date": datetime(1969, 1, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$hour": "$date"},
        expected=0,
        msg="$hour should return 0 for the first moment of 1969",
    ),
    ExpressionTestCase(
        "pre_epoch_1952_leap",
        doc={"date": datetime(1952, 2, 29, 7, 0, 0, tzinfo=timezone.utc)},
        expression={"$hour": "$date"},
        expected=7,
        msg="$hour should return 7 for Feb 29 in the pre-epoch leap year 1952",
    ),
]

HOUR_CLOCK_TESTS: list[ExpressionTestCase] = (
    HOUR_EXTRACTION_TESTS + HOUR_BOUNDARY_TESTS + HOUR_YEAR_TESTS + HOUR_PRE_EPOCH_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(HOUR_CLOCK_TESTS))
def test_hour_clock(collection, test_case: ExpressionTestCase):
    """Test $hour extraction across the clock, calendar boundaries, and year range."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
