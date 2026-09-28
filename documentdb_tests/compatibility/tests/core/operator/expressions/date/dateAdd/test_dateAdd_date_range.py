"""$dateAdd across the representable date range: historical, future, epoch, and limit dates."""

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
    DATE_EPOCH,
    DATE_YEAR_1900,
    DATE_YEAR_9999,
)

# Property [Historical And Future]: distant past and future start dates are handled.
DATEADD_HISTORICAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "historical_date",
        doc={"date": datetime(1900, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "year", "amount": 10}},
        expected=datetime(1910, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should handle a 1900 historical date",
    ),
    ExpressionTestCase(
        "pre_epoch_1960",
        doc={"date": datetime(1960, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 100}},
        expected=datetime(1960, 4, 10, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should handle a pre-epoch 1960 date",
    ),
    ExpressionTestCase(
        "far_future",
        doc={"date": datetime(2100, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "year", "amount": 100}},
        expected=datetime(2200, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should handle a far-future 2100 date",
    ),
    ExpressionTestCase(
        "large_year_amount",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "year", "amount": 1000}},
        expected=datetime(3000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should handle adding 1000 years",
    ),
    ExpressionTestCase(
        "distant_past",
        doc={"date": DATE_YEAR_1900},
        expression={"$dateAdd": {"startDate": "$date", "unit": "year", "amount": 1}},
        expected=datetime(1901, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should handle 1900 plus 1 year",
    ),
    ExpressionTestCase(
        "distant_future_month",
        doc={"date": datetime(2100, 1, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "month", "amount": 6}},
        expected=datetime(2100, 7, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should handle 2100 plus 6 months",
    ),
]

# Property [Epoch Crossing]: adding forward and backward across the Unix epoch is correct.
DATEADD_EPOCH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "epoch_add_day",
        doc={"date": DATE_EPOCH},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(1970, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should add a day to the epoch",
    ),
    ExpressionTestCase(
        "pre_epoch_add_day",
        doc={"date": datetime(1969, 12, 31, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=DATE_EPOCH,
        msg="$dateAdd should cross the epoch forward from 1969",
    ),
    ExpressionTestCase(
        "cross_epoch_back",
        doc={"date": DATE_EPOCH},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": -1}},
        expected=datetime(1969, 12, 31, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should cross the epoch backward to 1969",
    ),
]

# Property [Date Limits]: adding near the maximum representable date is handled.
DATEADD_DATE_LIMIT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "near_max_date",
        doc={"date": datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "millisecond", "amount": 1}},
        expected=datetime(9999, 12, 31, 23, 59, 59, 1000, tzinfo=timezone.utc),
        msg="$dateAdd should add 1 millisecond near the maximum date",
    ),
    ExpressionTestCase(
        "epoch_plus_large_ms",
        doc={"date": DATE_EPOCH},
        expression={
            "$dateAdd": {"startDate": "$date", "unit": "millisecond", "amount": 253_402_300_799_999}
        },
        expected=DATE_YEAR_9999,
        msg="$dateAdd should reach the near-maximum date from the epoch with a large ms amount",
    ),
    ExpressionTestCase(
        "at_python_max_year",
        doc={"date": datetime(9999, 12, 31, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "hour", "amount": 23}},
        expected=datetime(9999, 12, 31, 23, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should add 23 hours at year 9999",
    ),
]

DATEADD_DATE_RANGE_TESTS: list[ExpressionTestCase] = (
    DATEADD_HISTORICAL_TESTS + DATEADD_EPOCH_TESTS + DATEADD_DATE_LIMIT_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATEADD_DATE_RANGE_TESTS))
def test_dateAdd_date_range(collection, test_case: ExpressionTestCase):
    """Test $dateAdd remains correct across distant, epoch-crossing, and boundary dates."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
