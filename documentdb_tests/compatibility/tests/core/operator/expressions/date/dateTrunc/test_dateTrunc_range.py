"""$dateTrunc across the date range: epoch, distant, leap-year, and far-future dates."""

from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.date_utils import (
    oid_from_args,
    ts_from_args,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DATE_EPOCH,
    DATE_YEAR_1900,
)

# Property [Epoch And Distant Dates]: epoch, pre-epoch, distant past, and distant future dates
# truncate correctly, including from ObjectId and Timestamp inputs.
DATETRUNC_EPOCH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "epoch",
        doc={"date": datetime(1970, 1, 1, 12, 30, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
        expected=DATE_EPOCH,
        msg="$dateTrunc should truncate an epoch-day date",
    ),
    ExpressionTestCase(
        "pre_epoch",
        doc={"date": datetime(1969, 6, 15, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "month"}},
        expected=datetime(1969, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a pre-epoch date",
    ),
    ExpressionTestCase(
        "distant_past",
        doc={"date": datetime(1900, 3, 15, 8, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "year"}},
        expected=DATE_YEAR_1900,
        msg="$dateTrunc should truncate a distant past date",
    ),
    ExpressionTestCase(
        "distant_future",
        doc={"date": datetime(2100, 7, 20, 15, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "quarter"}},
        expected=datetime(2100, 7, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a distant future date",
    ),
    ExpressionTestCase(
        "oid_epoch",
        doc={"date": oid_from_args(1970, 1, 1, 12, 30, 0)},
        expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
        expected=DATE_EPOCH,
        msg="$dateTrunc should truncate an epoch ObjectId",
    ),
    ExpressionTestCase(
        "ts_epoch",
        doc={"date": ts_from_args(1970, 1, 1, 12, 30, 0)},
        expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
        expected=DATE_EPOCH,
        msg="$dateTrunc should truncate an epoch Timestamp",
    ),
    ExpressionTestCase(
        "oid_future",
        doc={"date": oid_from_args(2035, 7, 20, 15, 0, 0)},
        expression={"$dateTrunc": {"date": "$date", "unit": "year"}},
        expected=datetime(2035, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a future ObjectId",
    ),
    ExpressionTestCase(
        "ts_future",
        doc={"date": ts_from_args(2100, 7, 20, 15, 0, 0)},
        expression={"$dateTrunc": {"date": "$date", "unit": "year"}},
        expected=datetime(2100, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a future Timestamp",
    ),
]

# Property [Leap Year]: leap-day dates truncate correctly, including century leap-year rules.
DATETRUNC_LEAP_YEAR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "leap_day_trunc_day",
        doc={"date": datetime(2020, 2, 29, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
        expected=datetime(2020, 2, 29, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a leap day to the day start",
    ),
    ExpressionTestCase(
        "leap_day_trunc_month",
        doc={"date": datetime(2020, 2, 29, 23, 59, 59, 999000, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "month"}},
        expected=datetime(2020, 2, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a leap day to the month start",
    ),
    ExpressionTestCase(
        "century_non_leap_1900_trunc_month",
        doc={"date": datetime(1900, 2, 28, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "month"}},
        expected=datetime(1900, 2, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a 1900 February date to the month start",
    ),
    ExpressionTestCase(
        "century_leap_2000_trunc_month",
        doc={"date": datetime(2000, 2, 29, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "month"}},
        expected=datetime(2000, 2, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a 2000 leap day to the month start",
    ),
]

# Property [Far Future]: dates in year 9999 truncate correctly.
DATETRUNC_FAR_FUTURE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "far_future_year",
        doc={"date": datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "year"}},
        expected=datetime(9999, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a year 9999 date to the year start",
    ),
    ExpressionTestCase(
        "far_future_quarter",
        doc={"date": datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "quarter"}},
        expected=datetime(9999, 10, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a year 9999 date to the Q4 start",
    ),
]

DATETRUNC_RANGE_TESTS: list[ExpressionTestCase] = (
    DATETRUNC_EPOCH_TESTS + DATETRUNC_LEAP_YEAR_TESTS + DATETRUNC_FAR_FUTURE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATETRUNC_RANGE_TESTS))
def test_dateTrunc_range(collection, test_case: ExpressionTestCase):
    """Test $dateTrunc truncates correctly across epoch, leap-year, and far-future dates."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
