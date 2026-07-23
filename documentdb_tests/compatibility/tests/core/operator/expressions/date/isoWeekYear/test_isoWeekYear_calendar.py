"""Tests for $isoWeekYear ISO week-numbering year extraction across the calendar and year range."""

from datetime import datetime, timezone

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DATE_EPOCH, DATE_LEAP_FEB29

# Property [ISO Week-Year Extraction]: $isoWeekYear returns the ISO 8601 week-numbering year,
# which differs from the calendar year for dates in a week that belongs to the adjacent year.
ISOWEEKYEAR_EXTRACTION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "jan1_2018_monday",
        doc={"date": datetime(2018, 1, 1, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": "$date"},
        expected=Int64(2018),
        msg="$isoWeekYear should return 2018 for a Jan 1 that falls on a Monday",
    ),
    ExpressionTestCase(
        "jan1_2019_tuesday",
        doc={"date": datetime(2019, 1, 1, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": "$date"},
        expected=Int64(2019),
        msg="$isoWeekYear should return 2019 for a Jan 1 that falls on a Tuesday",
    ),
    ExpressionTestCase(
        "jan1_2020_wednesday",
        doc={"date": datetime(2020, 1, 1, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": "$date"},
        expected=Int64(2020),
        msg="$isoWeekYear should return 2020 for a Jan 1 that falls on a Wednesday",
    ),
    ExpressionTestCase(
        "jan1_2015_thursday",
        doc={"date": datetime(2015, 1, 1, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": "$date"},
        expected=Int64(2015),
        msg="$isoWeekYear should return 2015 for a Jan 1 that falls on a Thursday",
    ),
    ExpressionTestCase(
        "jan1_2010_friday",
        doc={"date": datetime(2010, 1, 1, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": "$date"},
        expected=Int64(2009),
        msg="$isoWeekYear should return the prior ISO year for a Jan 1 Friday",
    ),
    ExpressionTestCase(
        "jan1_2011_saturday",
        doc={"date": datetime(2011, 1, 1, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": "$date"},
        expected=Int64(2010),
        msg="$isoWeekYear should return the prior ISO year for a Jan 1 Saturday",
    ),
    ExpressionTestCase(
        "jan1_2012_sunday",
        doc={"date": datetime(2012, 1, 1, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": "$date"},
        expected=Int64(2011),
        msg="$isoWeekYear should return the prior ISO year for a Jan 1 Sunday",
    ),
    ExpressionTestCase(
        "jan1_2016_prior_year",
        doc={"date": datetime(2016, 1, 1, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": "$date"},
        expected=Int64(2015),
        msg="$isoWeekYear should return 2015 for a Jan 1 that belongs to the prior ISO year",
    ),
    ExpressionTestCase(
        "jan4_2016_current_year",
        doc={"date": datetime(2016, 1, 4, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": "$date"},
        expected=Int64(2016),
        msg="$isoWeekYear should return 2016 for Jan 4, which is always in the current ISO year",
    ),
    ExpressionTestCase(
        "dec31_2018_next_year",
        doc={"date": datetime(2018, 12, 31, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": "$date"},
        expected=Int64(2019),
        msg="$isoWeekYear should return 2019 for a Dec 31 that belongs to the next ISO year",
    ),
    ExpressionTestCase(
        "dec29_2014_next_year",
        doc={"date": datetime(2014, 12, 29, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": "$date"},
        expected=Int64(2015),
        msg="$isoWeekYear should return 2015 for a Dec 29 that belongs to the next ISO year",
    ),
    ExpressionTestCase(
        "dec31_2015_same_year",
        doc={"date": datetime(2015, 12, 31, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": "$date"},
        expected=Int64(2015),
        msg="$isoWeekYear should return 2015 for a Dec 31 that stays in the same ISO year",
    ),
    ExpressionTestCase(
        "dec31_2020_same_year",
        doc={"date": datetime(2020, 12, 31, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": "$date"},
        expected=Int64(2020),
        msg="$isoWeekYear should return 2020 for a Dec 31 that stays in the same ISO year",
    ),
    ExpressionTestCase(
        "dec31_2000_same_year",
        doc={"date": datetime(2000, 12, 31, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": "$date"},
        expected=Int64(2000),
        msg="$isoWeekYear should return 2000 for a Dec 31 that stays in the same ISO year",
    ),
    ExpressionTestCase(
        "mid_year_2024",
        doc={"date": datetime(2024, 6, 15, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": "$date"},
        expected=Int64(2024),
        msg="$isoWeekYear should return 2024 for a mid-year date",
    ),
]

# Property [Year Range]: the ISO week-numbering year is correct at the epoch and at distant
# past and future dates, including the day immediately before the epoch.
ISOWEEKYEAR_YEAR_RANGE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "epoch",
        doc={"date": DATE_EPOCH},
        expression={"$isoWeekYear": "$date"},
        expected=Int64(1970),
        msg="$isoWeekYear should return 1970 for the epoch",
    ),
    ExpressionTestCase(
        "pre_epoch",
        doc={"date": datetime(1969, 12, 31, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": "$date"},
        expected=Int64(1970),
        msg="$isoWeekYear should return 1970 for the day before the epoch",
    ),
    ExpressionTestCase(
        "distant_past",
        doc={"date": datetime(1900, 6, 15, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": "$date"},
        expected=Int64(1900),
        msg="$isoWeekYear should return 1900 for a distant past date in June 1900",
    ),
    ExpressionTestCase(
        "distant_future",
        doc={"date": datetime(2100, 6, 15, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": "$date"},
        expected=Int64(2100),
        msg="$isoWeekYear should return 2100 for a distant future date in June 2100",
    ),
]

# Property [Leap Years]: the ISO week-numbering year is correct on and around leap day,
# including century and non-century leap-rule boundaries.
ISOWEEKYEAR_LEAP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "leap_day_2000",
        doc={"date": DATE_LEAP_FEB29},
        expression={"$isoWeekYear": "$date"},
        expected=Int64(2000),
        msg="$isoWeekYear should return 2000 for leap day of the year-2000 century leap",
    ),
    ExpressionTestCase(
        "leap_day_2020",
        doc={"date": datetime(2020, 2, 29, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": "$date"},
        expected=Int64(2020),
        msg="$isoWeekYear should return 2020 for leap day 2020",
    ),
    ExpressionTestCase(
        "non_leap_century_1900",
        doc={"date": datetime(1900, 2, 28, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": "$date"},
        expected=Int64(1900),
        msg="$isoWeekYear should return 1900 for Feb 28 of the non-leap century 1900",
    ),
]

ISOWEEKYEAR_CALENDAR_TESTS: list[ExpressionTestCase] = (
    ISOWEEKYEAR_EXTRACTION_TESTS + ISOWEEKYEAR_YEAR_RANGE_TESTS + ISOWEEKYEAR_LEAP_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(ISOWEEKYEAR_CALENDAR_TESTS))
def test_isoWeekYear_calendar(collection, test_case: ExpressionTestCase):
    """Test $isoWeekYear extraction across the calendar, year range, and leap years."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
