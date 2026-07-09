"""$dateTrunc truncation results by unit, binSize multiples, bin alignment, and week start."""

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
from documentdb_tests.framework.test_constants import DATE_Y2K

# Property [Unit Truncation]: truncating to a unit returns the start of the period containing
# the date.
DATETRUNC_UNIT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "unit_year",
        doc={"date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "year"}},
        expected=datetime(2021, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate to the start of the year",
    ),
    ExpressionTestCase(
        "unit_quarter_q1",
        doc={"date": datetime(2021, 2, 15, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "quarter"}},
        expected=datetime(2021, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a Q1 date to the Q1 start",
    ),
    ExpressionTestCase(
        "unit_quarter_q2",
        doc={"date": datetime(2021, 5, 15, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "quarter"}},
        expected=datetime(2021, 4, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a Q2 date to the Q2 start",
    ),
    ExpressionTestCase(
        "unit_quarter_q3",
        doc={"date": datetime(2021, 8, 15, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "quarter"}},
        expected=datetime(2021, 7, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a Q3 date to the Q3 start",
    ),
    ExpressionTestCase(
        "unit_quarter_q4",
        doc={"date": datetime(2021, 11, 15, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "quarter"}},
        expected=datetime(2021, 10, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a Q4 date to the Q4 start",
    ),
    ExpressionTestCase(
        "unit_month",
        doc={"date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "month"}},
        expected=datetime(2021, 3, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate to the start of the month",
    ),
    ExpressionTestCase(
        "unit_day",
        doc={"date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
        expected=datetime(2021, 3, 20, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate to the start of the day",
    ),
    ExpressionTestCase(
        "unit_hour",
        doc={"date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour"}},
        expected=datetime(2021, 3, 20, 11, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate to the start of the hour",
    ),
    ExpressionTestCase(
        "unit_minute",
        doc={"date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "minute"}},
        expected=datetime(2021, 3, 20, 11, 30, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate to the start of the minute",
    ),
    ExpressionTestCase(
        "unit_second",
        doc={"date": datetime(2021, 3, 20, 11, 30, 5, 500000, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "second"}},
        expected=datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate to the start of the second",
    ),
    ExpressionTestCase(
        "unit_millisecond",
        doc={"date": datetime(2021, 1, 1, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "millisecond"}},
        expected=datetime(2021, 1, 1, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate to the millisecond",
    ),
]

# Property [BinSize Multiple]: a binSize greater than one truncates to multiples of the unit.
DATETRUNC_BINSIZE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "bin_2hour",
        doc={"date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour", "binSize": 2}},
        expected=datetime(2021, 3, 20, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate to a 2-hour bin",
    ),
    ExpressionTestCase(
        "bin_10year",
        doc={"date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "year", "binSize": 10}},
        expected=datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate to a 10-year bin",
    ),
    ExpressionTestCase(
        "bin_6month",
        doc={"date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "month", "binSize": 6}},
        expected=datetime(2021, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate to a 6-month bin",
    ),
    ExpressionTestCase(
        "bin_15min",
        doc={"date": datetime(2021, 3, 20, 11, 37, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "minute", "binSize": 15}},
        expected=datetime(2021, 3, 20, 11, 30, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate to a 15-minute bin",
    ),
]

# Property [Bin Alignment]: bins are aligned relative to the 2000-01-01 reference date, extending
# backward before it.
DATETRUNC_BIN_ALIGNMENT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "bin_5year_at_ref",
        doc={"date": DATE_Y2K},
        expression={"$dateTrunc": {"date": "$date", "unit": "year", "binSize": 5}},
        expected=DATE_Y2K,
        msg="$dateTrunc should align a 5-year bin to the reference date",
    ),
    ExpressionTestCase(
        "bin_5year_before_ref",
        doc={"date": datetime(1999, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "year", "binSize": 5}},
        expected=datetime(1995, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should extend 5-year bins backward before the reference date",
    ),
    ExpressionTestCase(
        "bin_5year_next_bin",
        doc={"date": datetime(2005, 1, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "year", "binSize": 5}},
        expected=datetime(2005, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should align to the next 5-year bin",
    ),
    ExpressionTestCase(
        "bin_3month_align",
        doc={"date": datetime(2000, 2, 15, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "month", "binSize": 3}},
        expected=DATE_Y2K,
        msg="$dateTrunc should align a 3-month bin from the reference date",
    ),
    ExpressionTestCase(
        "bin_3month_next",
        doc={"date": datetime(2000, 4, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "month", "binSize": 3}},
        expected=datetime(2000, 4, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should align to the next 3-month bin",
    ),
]

# Property [Week Truncation]: the week unit truncates to the configured start of week, defaulting
# to Sunday.
DATETRUNC_WEEK_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "week_default_sun",
        doc={"date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week"}},
        expected=datetime(2021, 3, 14, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should default the week start to Sunday",
    ),
    ExpressionTestCase(
        "week_monday",
        doc={"date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "monday"}},
        expected=datetime(2021, 3, 15, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate the week to Monday",
    ),
    ExpressionTestCase(
        "week_friday",
        doc={"date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "friday"}},
        expected=datetime(2021, 3, 19, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate the week to Friday",
    ),
    ExpressionTestCase(
        "week_sunday",
        doc={"date": datetime(2021, 6, 16, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "sunday"}},
        expected=datetime(2021, 6, 13, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate the week to Sunday",
    ),
    ExpressionTestCase(
        "week_tuesday",
        doc={"date": datetime(2021, 6, 16, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "tuesday"}},
        expected=datetime(2021, 6, 15, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate the week to Tuesday",
    ),
    ExpressionTestCase(
        "week_wednesday",
        doc={"date": datetime(2021, 6, 16, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "wednesday"}},
        expected=datetime(2021, 6, 16, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate the week to Wednesday",
    ),
    ExpressionTestCase(
        "week_thursday",
        doc={"date": datetime(2021, 6, 16, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "thursday"}},
        expected=datetime(2021, 6, 10, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate the week to Thursday",
    ),
    ExpressionTestCase(
        "week_saturday",
        doc={"date": datetime(2021, 6, 16, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "saturday"}},
        expected=datetime(2021, 6, 12, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate the week to Saturday",
    ),
    ExpressionTestCase(
        "week_mon_abbrev",
        doc={"date": datetime(2021, 6, 16, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "mon"}},
        expected=datetime(2021, 6, 14, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept the mon abbreviation for startOfWeek",
    ),
    ExpressionTestCase(
        "week_monday_mixed_case",
        doc={"date": datetime(2021, 6, 16, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "Monday"}},
        expected=datetime(2021, 6, 14, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept a mixed-case Monday for startOfWeek",
    ),
]

# Property [StartOfWeek Ignored]: startOfWeek has no effect for a non-week unit.
DATETRUNC_SOW_IGNORED_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "sow_ignored_month",
        doc={"date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "month", "startOfWeek": "friday"}},
        expected=datetime(2021, 3, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should ignore startOfWeek for the month unit",
    ),
]

DATETRUNC_DATE_TESTS: list[ExpressionTestCase] = (
    DATETRUNC_UNIT_TESTS
    + DATETRUNC_BINSIZE_TESTS
    + DATETRUNC_BIN_ALIGNMENT_TESTS
    + DATETRUNC_WEEK_TESTS
    + DATETRUNC_SOW_IGNORED_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATETRUNC_DATE_TESTS))
def test_dateTrunc_dates(collection, test_case: ExpressionTestCase):
    """Test $dateTrunc truncation results."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
