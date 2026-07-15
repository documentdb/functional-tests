"""$dateSubtract calendar rules: leap years, century rule, month clamping, and boundary carry."""

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

# Property [Leap Year]: subtracting across February resolves leap-year day counts correctly.
DATESUBTRACT_LEAP_YEAR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "leap_year_feb28_sub_year",
        doc={"date": datetime(2001, 2, 28, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "year", "amount": 1}},
        expected=datetime(2000, 2, 28, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should land on Feb 28 when subtracting a year into a leap year",
    ),
    ExpressionTestCase(
        "leap_year_feb29_sub_year",
        doc={"date": datetime(2020, 2, 29, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "year", "amount": 1}},
        expected=datetime(2019, 2, 28, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should clamp Feb 29 to Feb 28 subtracting a year into a non-leap year",
    ),
    ExpressionTestCase(
        "leap_year_sub_day_to_feb29",
        doc={"date": datetime(2000, 3, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(2000, 2, 29, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should land on Feb 29 in a leap year",
    ),
    ExpressionTestCase(
        "non_leap_year_mar1_sub_day",
        doc={"date": datetime(1999, 3, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(1999, 2, 28, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should land on Feb 28 in a non-leap year",
    ),
    ExpressionTestCase(
        "leap_year_mar29_sub_month",
        doc={"date": datetime(2020, 3, 29, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "month", "amount": 1}},
        expected=datetime(2020, 2, 29, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should subtract a month from Mar 29 to Feb 29 in a leap year",
    ),
    ExpressionTestCase(
        "leap_year_365_days",
        doc={"date": datetime(2020, 12, 31, 15, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": 365}},
        expected=datetime(2020, 1, 1, 15, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should not wrap the year when subtracting 365 days in a leap year",
    ),
    ExpressionTestCase(
        "non_leap_year_365_days",
        doc={"date": datetime(2020, 1, 1, 15, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": 365}},
        expected=datetime(2019, 1, 1, 15, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should wrap to the prior year subtracting 365 days into a non-leap year",
    ),
]

# Property [Century Leap Year]: the divisible-by-100/400 leap rule is honored.
DATESUBTRACT_CENTURY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "century_non_leap_1900_mar1_sub_day",
        doc={"date": datetime(1900, 3, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(1900, 2, 28, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should land on Feb 28 in 1900, a non-leap century year",
    ),
    ExpressionTestCase(
        "century_leap_2000_mar1_sub_day",
        doc={"date": datetime(2000, 3, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(2000, 2, 29, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should land on Feb 29 in 2000, a leap century year",
    ),
]

# Property [Month Clamping]: subtracting months or quarters clamps to the last valid day of the
# target month.
DATESUBTRACT_MONTH_CLAMP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "mar31_sub_month_leap",
        doc={"date": datetime(2000, 3, 31, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "month", "amount": 1}},
        expected=datetime(2000, 2, 29, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should clamp Mar 31 minus 1 month to Feb 29 in a leap year",
    ),
    ExpressionTestCase(
        "mar31_sub_month_non_leap",
        doc={"date": datetime(2021, 3, 31, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "month", "amount": 1}},
        expected=datetime(2021, 2, 28, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should clamp Mar 31 minus 1 month to Feb 28 in a non-leap year",
    ),
    ExpressionTestCase(
        "may31_sub_month",
        doc={"date": datetime(2000, 5, 31, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "month", "amount": 1}},
        expected=datetime(2000, 4, 30, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should clamp May 31 minus 1 month to Apr 30",
    ),
    ExpressionTestCase(
        "jul31_sub_month",
        doc={"date": datetime(2000, 7, 31, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "month", "amount": 1}},
        expected=datetime(2000, 6, 30, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should clamp Jul 31 minus 1 month to Jun 30",
    ),
    ExpressionTestCase(
        "jan31_sub_month_no_adjustment",
        doc={"date": datetime(2021, 1, 31, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "month", "amount": 1}},
        expected=datetime(2020, 12, 31, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should not adjust Jan 31 minus 1 month, landing on Dec 31",
    ),
    ExpressionTestCase(
        "dec31_sub_year_no_adjustment",
        doc={"date": datetime(2021, 12, 31, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "year", "amount": 1}},
        expected=datetime(2020, 12, 31, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should not adjust Dec 31 when subtracting a year",
    ),
    ExpressionTestCase(
        "apr30_sub_quarter",
        doc={"date": datetime(2021, 4, 30, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "quarter", "amount": 1}},
        expected=datetime(2021, 1, 30, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should subtract 1 quarter from Apr 30 to Jan 30",
    ),
    ExpressionTestCase(
        "large_positive_month",
        doc={"date": datetime(2020, 12, 31, 12, 10, 5, 10000, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "month", "amount": 49}},
        expected=datetime(2016, 11, 30, 12, 10, 5, 10000, tzinfo=timezone.utc),
        msg="$dateSubtract should clamp a large positive month amount to end-of-month",
    ),
    ExpressionTestCase(
        "large_negative_month",
        doc={"date": datetime(2020, 12, 31, 12, 10, 5, 10000, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "month", "amount": -50}},
        expected=datetime(2025, 2, 28, 12, 10, 5, 10000, tzinfo=timezone.utc),
        msg="$dateSubtract should clamp a large negative month amount to end-of-month",
    ),
]

# Property [Boundary Crossing]: subtracting across day, month, and year boundaries carries
# correctly.
DATESUBTRACT_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "dec31_sub_day",
        doc={"date": datetime(2001, 1, 1, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(2000, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
        msg="$dateSubtract should cross the year boundary from Jan 1 minus 1 day",
    ),
    ExpressionTestCase(
        "jan1_add_day",
        doc={"date": DATE_Y2K},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": -1}},
        expected=datetime(2000, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should cross the day boundary from Jan 1 with a negative amount",
    ),
    ExpressionTestCase(
        "dec31_sub_hour",
        doc={"date": datetime(2001, 1, 1, 1, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "hour", "amount": 2}},
        expected=datetime(2000, 12, 31, 23, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should cross the year boundary from Jan 1 minus 2 hours",
    ),
]

DATESUBTRACT_CALENDAR_TESTS: list[ExpressionTestCase] = (
    DATESUBTRACT_LEAP_YEAR_TESTS
    + DATESUBTRACT_CENTURY_TESTS
    + DATESUBTRACT_MONTH_CLAMP_TESTS
    + DATESUBTRACT_BOUNDARY_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATESUBTRACT_CALENDAR_TESTS))
def test_dateSubtract_calendar(collection, test_case: ExpressionTestCase):
    """Test $dateSubtract honors calendar rules across months, years, and boundaries."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
