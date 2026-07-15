"""Tests for $week Sunday-based week numbering across the calendar, leap years, and years."""

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

# Property [Week Numbering]: $week numbers weeks from 0, weeks start on Sunday, and days before
# the first Sunday of the year are week 0, so the number increments only as each Sunday is crossed.
WEEK_NUMBERING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "week_0_jan1",
        doc={"date": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": "$date"},
        expected=0,
        msg="$week should return 0 for Jan 1 2024, before the first Sunday",
    ),
    ExpressionTestCase(
        "week_0_jan6",
        doc={"date": datetime(2024, 1, 6, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$week": "$date"},
        expected=0,
        msg="$week should return 0 for the last instant before the first Sunday of 2024",
    ),
    ExpressionTestCase(
        "week_1_jan7",
        doc={"date": datetime(2024, 1, 7, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": "$date"},
        expected=1,
        msg="$week should return 1 for the first Sunday of 2024",
    ),
    ExpressionTestCase(
        "week_1_jan13",
        doc={"date": datetime(2024, 1, 13, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$week": "$date"},
        expected=1,
        msg="$week should return 1 for the last instant of the first full week",
    ),
    ExpressionTestCase(
        "week_2_jan14",
        doc={"date": datetime(2024, 1, 14, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": "$date"},
        expected=2,
        msg="$week should return 2 for the second Sunday of 2024",
    ),
    ExpressionTestCase(
        "week_23_jun15",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": "$date"},
        expected=23,
        msg="$week should return 23 for a mid-June 2024 date",
    ),
    ExpressionTestCase(
        "week_26_jun30",
        doc={"date": datetime(2024, 6, 30, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": "$date"},
        expected=26,
        msg="$week should return 26 for the last day of June 2024",
    ),
    ExpressionTestCase(
        "week_26_jul1",
        doc={"date": datetime(2024, 7, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": "$date"},
        expected=26,
        msg="$week should return 26 for the first day of July 2024, still in the same week",
    ),
    ExpressionTestCase(
        "week_52_dec31",
        doc={"date": datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$week": "$date"},
        expected=52,
        msg="$week should return 52 for the last instant of 2024",
    ),
    ExpressionTestCase(
        "week_1_2023_jan1",
        doc={"date": datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": "$date"},
        expected=1,
        msg="$week should return 1 for Jan 1 2023, which is itself a Sunday",
    ),
    ExpressionTestCase(
        "week_53_2023_dec31",
        doc={"date": datetime(2023, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$week": "$date"},
        expected=53,
        msg="$week should return 53 for the last instant of 2023, which has a week 53",
    ),
]

# Property [Leap Years]: leap and non-leap February dates map to the correct Sunday-based week,
# including the century leap-year rules, which shift the day-of-year and produce different week
# numbers (week 8 versus week 9).
WEEK_LEAP_YEAR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "leap_year_feb_29_2024",
        doc={"date": datetime(2024, 2, 29, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": "$date"},
        expected=8,
        msg="$week should return 8 for Feb 29 in the 2024 leap year",
    ),
    ExpressionTestCase(
        "non_leap_year_feb_28_2023",
        doc={"date": datetime(2023, 2, 28, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": "$date"},
        expected=9,
        msg="$week should return 9 for Feb 28 in the non-leap 2023 year",
    ),
    ExpressionTestCase(
        "leap_year_feb_29_2020",
        doc={"date": datetime(2020, 2, 29, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": "$date"},
        expected=8,
        msg="$week should return 8 for Feb 29 in the 2020 leap year",
    ),
    ExpressionTestCase(
        "leap_year_feb_29_2000",
        doc={"date": datetime(2000, 2, 29, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": "$date"},
        expected=9,
        msg="$week should return 9 for Feb 29 in the 2000 century leap year",
    ),
    ExpressionTestCase(
        "non_leap_century_1900_feb_28",
        doc={"date": datetime(1900, 2, 28, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": "$date"},
        expected=8,
        msg="$week should return 8 for Feb 28 1900, a non-leap century year",
    ),
]

# Property [Sub-Second Precision]: the week number is determined by the instant, so a millisecond
# on either side of a Sunday or a year boundary lands in the expected week.
WEEK_MILLISECOND_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "millisecond_before_sunday",
        doc={"date": datetime(2024, 1, 6, 23, 59, 59, 999000, tzinfo=timezone.utc)},
        expression={"$week": "$date"},
        expected=0,
        msg="$week should return 0 one millisecond before the first Sunday of 2024",
    ),
    ExpressionTestCase(
        "millisecond_after_sunday_start",
        doc={"date": datetime(2024, 1, 7, 0, 0, 0, 1000, tzinfo=timezone.utc)},
        expression={"$week": "$date"},
        expected=1,
        msg="$week should return 1 one millisecond after the first Sunday begins",
    ),
    ExpressionTestCase(
        "millisecond_mid_week",
        doc={"date": datetime(2024, 6, 15, 12, 30, 30, 500000, tzinfo=timezone.utc)},
        expression={"$week": "$date"},
        expected=23,
        msg="$week should return 23 for a mid-week instant with sub-second precision",
    ),
    ExpressionTestCase(
        "millisecond_year_boundary",
        doc={"date": datetime(2024, 12, 31, 23, 59, 59, 999000, tzinfo=timezone.utc)},
        expression={"$week": "$date"},
        expected=52,
        msg="$week should return 52 one millisecond before the end of 2024",
    ),
]

# Property [Year Range]: $week returns the correct Sunday-based week across the representable
# calendar year range, including the epoch and the maximum year.
WEEK_YEAR_RANGE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "year_2000",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": "$date"},
        expected=0,
        msg="$week should return 0 for Jan 1 2000, before the first Sunday",
    ),
    ExpressionTestCase(
        "year_1970_epoch",
        doc={"date": DATE_EPOCH},
        expression={"$week": "$date"},
        expected=0,
        msg="$week should return 0 for the Unix epoch",
    ),
    ExpressionTestCase(
        "year_1999",
        doc={"date": datetime(1999, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$week": "$date"},
        expected=52,
        msg="$week should return 52 for the last instant of 1999",
    ),
    ExpressionTestCase(
        "year_2099",
        doc={"date": datetime(2099, 7, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": "$date"},
        expected=28,
        msg="$week should return 28 for a mid-2099 date",
    ),
    ExpressionTestCase(
        "year_9999",
        doc={"date": datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$week": "$date"},
        expected=52,
        msg="$week should return 52 for the last instant of the maximum year",
    ),
]

# Property [Pre-Epoch]: dates before the Unix epoch resolve to the correct Sunday-based week.
WEEK_PRE_EPOCH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "pre_epoch_1960",
        doc={"date": datetime(1960, 3, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": "$date"},
        expected=11,
        msg="$week should return 11 for a mid-March 1960 date",
    ),
    ExpressionTestCase(
        "pre_epoch_1900",
        doc={"date": datetime(1900, 7, 4, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": "$date"},
        expected=26,
        msg="$week should return 26 for Jul 4 1900",
    ),
    ExpressionTestCase(
        "pre_epoch_1969_dec",
        doc={"date": datetime(1969, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$week": "$date"},
        expected=52,
        msg="$week should return 52 for the last instant before the epoch year",
    ),
    ExpressionTestCase(
        "pre_epoch_1969_jan",
        doc={"date": datetime(1969, 1, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": "$date"},
        expected=0,
        msg="$week should return 0 for Jan 1 1969, before the first Sunday",
    ),
    ExpressionTestCase(
        "pre_epoch_1952_leap",
        doc={"date": datetime(1952, 2, 29, 6, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": "$date"},
        expected=8,
        msg="$week should return 8 for Feb 29 1952, a pre-epoch leap year",
    ),
]

WEEK_CALENDAR_TESTS: list[ExpressionTestCase] = (
    WEEK_NUMBERING_TESTS
    + WEEK_LEAP_YEAR_TESTS
    + WEEK_MILLISECOND_TESTS
    + WEEK_YEAR_RANGE_TESTS
    + WEEK_PRE_EPOCH_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(WEEK_CALENDAR_TESTS))
def test_week_calendar(collection, test_case: ExpressionTestCase):
    """Test $week Sunday-based week numbering across the calendar, leap years, and years."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
