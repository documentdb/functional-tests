"""Tests for $isoWeek ISO week-of-year extraction across the calendar and year range."""

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
from documentdb_tests.framework.test_constants import DATE_EPOCH, DATE_LEAP_FEB29

# Property [ISO Week Extraction]: $isoWeek returns the ISO 8601 week number (1 to 53) of a
# UTC date, where week 1 is the week containing the first Thursday of the year.
ISOWEEK_EXTRACTION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "jan1_2018_monday",
        doc={"date": datetime(2018, 1, 1, tzinfo=timezone.utc)},
        expression={"$isoWeek": "$date"},
        expected=1,
        msg="$isoWeek should return 1 for a Jan 1 that falls on a Monday",
    ),
    ExpressionTestCase(
        "jan1_2019_tuesday",
        doc={"date": datetime(2019, 1, 1, tzinfo=timezone.utc)},
        expression={"$isoWeek": "$date"},
        expected=1,
        msg="$isoWeek should return 1 for a Jan 1 that falls on a Tuesday",
    ),
    ExpressionTestCase(
        "jan1_2020_wednesday",
        doc={"date": datetime(2020, 1, 1, tzinfo=timezone.utc)},
        expression={"$isoWeek": "$date"},
        expected=1,
        msg="$isoWeek should return 1 for a Jan 1 that falls on a Wednesday",
    ),
    ExpressionTestCase(
        "jan1_2015_thursday",
        doc={"date": datetime(2015, 1, 1, tzinfo=timezone.utc)},
        expression={"$isoWeek": "$date"},
        expected=1,
        msg="$isoWeek should return 1 for a Jan 1 that falls on a Thursday",
    ),
    ExpressionTestCase(
        "jan1_2010_friday",
        doc={"date": datetime(2010, 1, 1, tzinfo=timezone.utc)},
        expression={"$isoWeek": "$date"},
        expected=53,
        msg="$isoWeek should return 53 for a Jan 1 Friday that belongs to the prior ISO year",
    ),
    ExpressionTestCase(
        "jan1_2011_saturday",
        doc={"date": datetime(2011, 1, 1, tzinfo=timezone.utc)},
        expression={"$isoWeek": "$date"},
        expected=52,
        msg="$isoWeek should return 52 for a Jan 1 Saturday that belongs to the prior ISO year",
    ),
    ExpressionTestCase(
        "jan1_2012_sunday",
        doc={"date": datetime(2012, 1, 1, tzinfo=timezone.utc)},
        expression={"$isoWeek": "$date"},
        expected=52,
        msg="$isoWeek should return 52 for a Jan 1 Sunday that belongs to the prior ISO year",
    ),
    ExpressionTestCase(
        "jan4_always_week1",
        doc={"date": datetime(2016, 1, 4, tzinfo=timezone.utc)},
        expression={"$isoWeek": "$date"},
        expected=1,
        msg="$isoWeek should return 1 for Jan 4, which is always in ISO week 1",
    ),
    ExpressionTestCase(
        "dec31_2004_week53",
        doc={"date": datetime(2004, 12, 31, tzinfo=timezone.utc)},
        expression={"$isoWeek": "$date"},
        expected=53,
        msg="$isoWeek should return 53 for a Dec 31 in a 53-week year",
    ),
    ExpressionTestCase(
        "dec31_2009_week53",
        doc={"date": datetime(2009, 12, 31, tzinfo=timezone.utc)},
        expression={"$isoWeek": "$date"},
        expected=53,
        msg="$isoWeek should return 53 for a Dec 31 in a 53-week year",
    ),
    ExpressionTestCase(
        "dec31_2015_week53",
        doc={"date": datetime(2015, 12, 31, tzinfo=timezone.utc)},
        expression={"$isoWeek": "$date"},
        expected=53,
        msg="$isoWeek should return 53 for a Dec 31 in a 53-week year",
    ),
    ExpressionTestCase(
        "dec31_2020_week53",
        doc={"date": datetime(2020, 12, 31, tzinfo=timezone.utc)},
        expression={"$isoWeek": "$date"},
        expected=53,
        msg="$isoWeek should return 53 for a Dec 31 in a 53-week year",
    ),
    ExpressionTestCase(
        "dec31_2018_week1",
        doc={"date": datetime(2018, 12, 31, tzinfo=timezone.utc)},
        expression={"$isoWeek": "$date"},
        expected=1,
        msg="$isoWeek should return 1 for a Dec 31 that belongs to the next ISO year's week 1",
    ),
    ExpressionTestCase(
        "dec29_2014_week1",
        doc={"date": datetime(2014, 12, 29, tzinfo=timezone.utc)},
        expression={"$isoWeek": "$date"},
        expected=1,
        msg="$isoWeek should return 1 for a Dec 29 that belongs to the next ISO year's week 1",
    ),
    ExpressionTestCase(
        "monday_week2_2024",
        doc={"date": datetime(2024, 1, 8, tzinfo=timezone.utc)},
        expression={"$isoWeek": "$date"},
        expected=2,
        msg="$isoWeek should return 2 for the Monday that starts the second ISO week of 2024",
    ),
    ExpressionTestCase(
        "sunday_late_week1_2024",
        doc={"date": datetime(2024, 1, 7, 23, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeek": "$date"},
        expected=1,
        msg="$isoWeek should return 1 for the last hour of the Sunday closing ISO week 1 of 2024",
    ),
    ExpressionTestCase(
        "nov2_1998_week45",
        doc={"date": datetime(1998, 11, 2, tzinfo=timezone.utc)},
        expression={"$isoWeek": "$date"},
        expected=45,
        msg="$isoWeek should return 45 for a Monday in November 1998",
    ),
]

# Property [Year Range]: the ISO week is correct at the epoch and at distant past and future
# dates, including the day immediately before the epoch.
ISOWEEK_YEAR_RANGE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "epoch",
        doc={"date": DATE_EPOCH},
        expression={"$isoWeek": "$date"},
        expected=1,
        msg="$isoWeek should return 1 for the epoch",
    ),
    ExpressionTestCase(
        "pre_epoch",
        doc={"date": datetime(1969, 12, 31, tzinfo=timezone.utc)},
        expression={"$isoWeek": "$date"},
        expected=1,
        msg="$isoWeek should return 1 for the day before the epoch",
    ),
    ExpressionTestCase(
        "distant_past",
        doc={"date": datetime(1900, 6, 15, tzinfo=timezone.utc)},
        expression={"$isoWeek": "$date"},
        expected=24,
        msg="$isoWeek should return 24 for a distant past date in June 1900",
    ),
    ExpressionTestCase(
        "distant_future",
        doc={"date": datetime(2100, 6, 15, tzinfo=timezone.utc)},
        expression={"$isoWeek": "$date"},
        expected=24,
        msg="$isoWeek should return 24 for a distant future date in June 2100",
    ),
]

# Property [Leap Years]: the ISO week is correct on and around leap day, including century
# and non-century leap-rule boundaries.
ISOWEEK_LEAP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "leap_day_2000",
        doc={"date": DATE_LEAP_FEB29},
        expression={"$isoWeek": "$date"},
        expected=9,
        msg="$isoWeek should return 9 for leap day of the year-2000 century leap",
    ),
    ExpressionTestCase(
        "leap_day_2020",
        doc={"date": datetime(2020, 2, 29, tzinfo=timezone.utc)},
        expression={"$isoWeek": "$date"},
        expected=9,
        msg="$isoWeek should return 9 for leap day 2020",
    ),
    ExpressionTestCase(
        "non_leap_century_1900",
        doc={"date": datetime(1900, 2, 28, tzinfo=timezone.utc)},
        expression={"$isoWeek": "$date"},
        expected=9,
        msg="$isoWeek should return 9 for Feb 28 of the non-leap century 1900",
    ),
]

ISOWEEK_CALENDAR_TESTS: list[ExpressionTestCase] = (
    ISOWEEK_EXTRACTION_TESTS + ISOWEEK_YEAR_RANGE_TESTS + ISOWEEK_LEAP_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(ISOWEEK_CALENDAR_TESTS))
def test_isoWeek_calendar(collection, test_case: ExpressionTestCase):
    """Test $isoWeek ISO week extraction across the calendar, year range, and leap years."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
