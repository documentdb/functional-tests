"""$dateTrunc truncation semantics: unit periods, bin multiples, alignment, and idempotence."""

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

# Property [Boundary Idempotence]: a date already at a unit boundary is returned unchanged.
DATETRUNC_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "year_at_boundary",
        doc={"date": datetime(2021, 1, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "year"}},
        expected=datetime(2021, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should return the date unchanged at a year boundary",
    ),
    ExpressionTestCase(
        "month_at_boundary",
        doc={"date": datetime(2021, 6, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "month"}},
        expected=datetime(2021, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should return the date unchanged at a month boundary",
    ),
    ExpressionTestCase(
        "day_at_boundary",
        doc={"date": datetime(2021, 6, 15, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
        expected=datetime(2021, 6, 15, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should return the date unchanged at a day boundary",
    ),
    ExpressionTestCase(
        "hour_at_boundary",
        doc={"date": datetime(2021, 6, 15, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour"}},
        expected=datetime(2021, 6, 15, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should return the date unchanged at an hour boundary",
    ),
    ExpressionTestCase(
        "minute_at_boundary",
        doc={"date": datetime(2021, 6, 15, 10, 30, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "minute"}},
        expected=datetime(2021, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should return the date unchanged at a minute boundary",
    ),
    ExpressionTestCase(
        "second_at_boundary",
        doc={"date": datetime(2021, 6, 15, 10, 30, 45, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "second"}},
        expected=datetime(2021, 6, 15, 10, 30, 45, tzinfo=timezone.utc),
        msg="$dateTrunc should return the date unchanged at a second boundary",
    ),
]

# Property [End Of Period]: a date at the end of a period truncates to that period's start.
DATETRUNC_END_OF_PERIOD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "year_end",
        doc={"date": datetime(2021, 12, 31, 23, 59, 59, 999000, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "year"}},
        expected=datetime(2021, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate the last millisecond of a year to the year start",
    ),
    ExpressionTestCase(
        "quarter_end_q1",
        doc={"date": datetime(2021, 3, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "quarter"}},
        expected=datetime(2021, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate the end of Q1 to the Q1 start",
    ),
    ExpressionTestCase(
        "quarter_start_q2",
        doc={"date": datetime(2021, 4, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "quarter"}},
        expected=datetime(2021, 4, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should return the Q2 start at the exact boundary",
    ),
    ExpressionTestCase(
        "day_end",
        doc={"date": datetime(2021, 6, 15, 23, 59, 59, 999000, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
        expected=datetime(2021, 6, 15, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate the last millisecond of a day to the day start",
    ),
]

DATETRUNC_TRUNCATION_TESTS: list[ExpressionTestCase] = (
    DATETRUNC_UNIT_TESTS
    + DATETRUNC_BINSIZE_TESTS
    + DATETRUNC_BIN_ALIGNMENT_TESTS
    + DATETRUNC_BOUNDARY_TESTS
    + DATETRUNC_END_OF_PERIOD_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATETRUNC_TRUNCATION_TESTS))
def test_dateTrunc_truncation(collection, test_case: ExpressionTestCase):
    """Test $dateTrunc returns the start of the period, honoring binSize and alignment."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
