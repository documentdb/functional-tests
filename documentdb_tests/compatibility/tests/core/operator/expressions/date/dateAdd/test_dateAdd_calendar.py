"""$dateAdd calendar rules: leap years, century leap rule, month clamping, and boundary carry."""

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
from documentdb_tests.framework.test_constants import (
    DATE_Y2K,
)

# Property [Leap Year]: adding across February resolves leap-year day counts correctly.
DATEADD_LEAP_YEAR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "leap_year_feb29_add_year",
        doc={"date": datetime(2000, 2, 29, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "year", "amount": 1}},
        expected=datetime(2001, 2, 28, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should clamp Feb 29 to Feb 28 when adding a year into a non-leap year",
    ),
    ExpressionTestCase(
        "leap_year_add_day_to_feb28",
        doc={"date": datetime(2000, 2, 28, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(2000, 2, 29, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should land on Feb 29 in a leap year",
    ),
    ExpressionTestCase(
        "non_leap_year_feb28_add_day",
        doc={"date": datetime(1999, 2, 28, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(1999, 3, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should roll to Mar 1 in a non-leap year",
    ),
    ExpressionTestCase(
        "leap_year_feb29_add_month",
        doc={"date": datetime(2020, 2, 29, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "month", "amount": 1}},
        expected=datetime(2020, 3, 29, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should add a month from Feb 29 to Mar 29",
    ),
    ExpressionTestCase(
        "leap_year_feb27_add_2days",
        doc={"date": datetime(2020, 2, 27, 14, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 2}},
        expected=datetime(2020, 2, 29, 14, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should land on Feb 29 in a leap year",
    ),
    ExpressionTestCase(
        "non_leap_year_feb27_add_2days",
        doc={"date": datetime(2021, 2, 27, 14, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 2}},
        expected=datetime(2021, 3, 1, 14, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should roll to Mar 1 in a non-leap year",
    ),
    ExpressionTestCase(
        "leap_year_365_days",
        doc={"date": datetime(2020, 1, 1, 15, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 365}},
        expected=datetime(2020, 12, 31, 15, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should not wrap the year when adding 365 days in a leap year",
    ),
    ExpressionTestCase(
        "non_leap_year_365_days",
        doc={"date": datetime(2019, 1, 1, 15, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 365}},
        expected=datetime(2020, 1, 1, 15, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should wrap to the next year when adding 365 days in a non-leap year",
    ),
]

# Property [Century Leap Year]: the divisible-by-100/400 leap rule is honored.
DATEADD_CENTURY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "century_non_leap_1900_feb28_add_day",
        doc={"date": datetime(1900, 2, 28, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(1900, 3, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should roll to Mar 1 in 1900, a non-leap century year",
    ),
    ExpressionTestCase(
        "century_leap_2000_feb28_add_day",
        doc={"date": datetime(2000, 2, 28, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(2000, 2, 29, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should land on Feb 29 in 2000, a leap century year",
    ),
]

# Property [Month Clamping]: adding months or quarters clamps to the last valid day of the
# target month.
DATEADD_MONTH_CLAMP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "jan31_add_month_leap",
        doc={"date": datetime(2020, 1, 31, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "month", "amount": 1}},
        expected=datetime(2020, 2, 29, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should clamp Jan 31 plus 1 month to Feb 29 in a leap year",
    ),
    ExpressionTestCase(
        "jan31_add_month_non_leap",
        doc={"date": datetime(2021, 1, 31, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "month", "amount": 1}},
        expected=datetime(2021, 2, 28, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should clamp Jan 31 plus 1 month to Feb 28 in a non-leap year",
    ),
    ExpressionTestCase(
        "jan29_add_month_non_leap",
        doc={"date": datetime(2021, 1, 29, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "month", "amount": 1}},
        expected=datetime(2021, 2, 28, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should clamp Jan 29 plus 1 month to Feb 28 in a non-leap year",
    ),
    ExpressionTestCase(
        "oct31_add_month",
        doc={"date": datetime(2020, 10, 31, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "month", "amount": 1}},
        expected=datetime(2020, 11, 30, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should clamp Oct 31 plus 1 month to Nov 30",
    ),
    ExpressionTestCase(
        "mar31_add_month",
        doc={"date": datetime(2000, 3, 31, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "month", "amount": 1}},
        expected=datetime(2000, 4, 30, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should clamp Mar 31 plus 1 month to Apr 30",
    ),
    ExpressionTestCase(
        "may31_add_month",
        doc={"date": datetime(2000, 5, 31, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "month", "amount": 1}},
        expected=datetime(2000, 6, 30, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should clamp May 31 plus 1 month to Jun 30",
    ),
    ExpressionTestCase(
        "aug31_add_month",
        doc={"date": datetime(2020, 8, 31, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "month", "amount": 1}},
        expected=datetime(2020, 9, 30, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should clamp Aug 31 plus 1 month to Sep 30",
    ),
    ExpressionTestCase(
        "dec31_add_year_no_adjustment",
        doc={"date": datetime(2020, 12, 31, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "year", "amount": 1}},
        expected=datetime(2021, 12, 31, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should not adjust Dec 31 when adding a year",
    ),
    ExpressionTestCase(
        "mar31_subtract_month_leap",
        doc={"date": datetime(2020, 3, 31, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "month", "amount": -1}},
        expected=datetime(2020, 2, 29, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should clamp Mar 31 minus 1 month to Feb 29 in a leap year",
    ),
    ExpressionTestCase(
        "mar31_subtract_month_non_leap",
        doc={"date": datetime(2021, 3, 31, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "month", "amount": -1}},
        expected=datetime(2021, 2, 28, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should clamp Mar 31 minus 1 month to Feb 28 in a non-leap year",
    ),
    ExpressionTestCase(
        "jan31_subtract_month_no_adjustment",
        doc={"date": datetime(2021, 1, 31, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "month", "amount": -1}},
        expected=datetime(2020, 12, 31, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should not adjust Jan 31 minus 1 month, landing on Dec 31",
    ),
    ExpressionTestCase(
        "jan31_add_quarter",
        doc={"date": datetime(2021, 1, 31, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "quarter", "amount": 1}},
        expected=datetime(2021, 4, 30, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should clamp Jan 31 plus 1 quarter to Apr 30",
    ),
    ExpressionTestCase(
        "quarter_subtract",
        doc={"date": datetime(2021, 4, 30, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "quarter", "amount": -1}},
        expected=datetime(2021, 1, 30, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should subtract 1 quarter",
    ),
    ExpressionTestCase(
        "large_positive_month",
        doc={"date": datetime(2020, 12, 31, 12, 10, 5, 10000, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "month", "amount": 49}},
        expected=datetime(2025, 1, 31, 12, 10, 5, 10000, tzinfo=timezone.utc),
        msg="$dateAdd should clamp a large positive month amount to end-of-month",
    ),
    ExpressionTestCase(
        "large_negative_month",
        doc={"date": datetime(2020, 12, 31, 12, 10, 5, 10000, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "month", "amount": -49}},
        expected=datetime(2016, 11, 30, 12, 10, 5, 10000, tzinfo=timezone.utc),
        msg="$dateAdd should clamp a large negative month amount to end-of-month",
    ),
]

# Property [Boundary Crossing]: adding across day, month, and year boundaries carries correctly.
DATEADD_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "dec31_add_day",
        doc={"date": datetime(2000, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(2001, 1, 1, 23, 59, 59, tzinfo=timezone.utc),
        msg="$dateAdd should cross the year boundary from Dec 31 plus 1 day",
    ),
    ExpressionTestCase(
        "jan1_subtract_day",
        doc={"date": DATE_Y2K},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": -1}},
        expected=datetime(1999, 12, 31, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should cross the year boundary from Jan 1 minus 1 day",
    ),
    ExpressionTestCase(
        "dec31_add_hour",
        doc={"date": datetime(2000, 12, 31, 23, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "hour", "amount": 2}},
        expected=datetime(2001, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should cross the year boundary from Dec 31 plus 2 hours",
    ),
]

DATEADD_CALENDAR_TESTS: list[ExpressionTestCase] = (
    DATEADD_LEAP_YEAR_TESTS
    + DATEADD_CENTURY_TESTS
    + DATEADD_MONTH_CLAMP_TESTS
    + DATEADD_BOUNDARY_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATEADD_CALENDAR_TESTS))
def test_dateAdd_calendar(collection, test_case: ExpressionTestCase):
    """Test $dateAdd honors calendar rules when adding months, years, and across boundaries."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
