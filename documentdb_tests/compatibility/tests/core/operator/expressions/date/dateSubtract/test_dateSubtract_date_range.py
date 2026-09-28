"""$dateSubtract across the representable date range: historical, future, epoch, and limit dates."""

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
    DATE_YEAR_1,
    DATE_YEAR_1900,
    DATE_YEAR_9999,
)

# Property [Historical And Future]: distant past and future start dates are handled.
DATESUBTRACT_HISTORICAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "historical_date",
        doc={"date": datetime(1910, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "year", "amount": 10}},
        expected=datetime(1900, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should handle a 1910 historical date",
    ),
    ExpressionTestCase(
        "pre_epoch_1960",
        doc={"date": datetime(1960, 4, 10, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": 100}},
        expected=datetime(1960, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should handle a pre-epoch 1960 date",
    ),
    ExpressionTestCase(
        "far_future",
        doc={"date": datetime(2200, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "year", "amount": 100}},
        expected=datetime(2100, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should handle a far-future 2200 date",
    ),
    ExpressionTestCase(
        "large_year_amount",
        doc={"date": datetime(3000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "year", "amount": 1000}},
        expected=datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should handle subtracting 1000 years",
    ),
    ExpressionTestCase(
        "distant_past",
        doc={"date": datetime(1901, 1, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "year", "amount": 1}},
        expected=DATE_YEAR_1900,
        msg="$dateSubtract should handle 1901 minus 1 year",
    ),
    ExpressionTestCase(
        "distant_future_month",
        doc={"date": datetime(2100, 7, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "month", "amount": 6}},
        expected=datetime(2100, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should handle 2100 minus 6 months",
    ),
]

# Property [Epoch Crossing]: subtracting forward and backward across the Unix epoch is correct.
DATESUBTRACT_EPOCH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "epoch_sub_day",
        doc={"date": datetime(1970, 1, 2, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=DATE_EPOCH,
        msg="$dateSubtract should subtract a day to reach the epoch",
    ),
    ExpressionTestCase(
        "cross_epoch_back",
        doc={"date": DATE_EPOCH},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(1969, 12, 31, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should cross the epoch backward to 1969",
    ),
    ExpressionTestCase(
        "pre_epoch_to_epoch",
        doc={"date": datetime(1969, 12, 31, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": -1}},
        expected=DATE_EPOCH,
        msg="$dateSubtract should cross the epoch forward from 1969 with a negative amount",
    ),
]

# Property [Date Limits]: subtracting near the minimum representable date is handled.
DATESUBTRACT_DATE_LIMIT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "near_min_date",
        doc={"date": datetime(1, 1, 1, 0, 0, 1, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "millisecond", "amount": 1}},
        expected=datetime(1, 1, 1, 0, 0, 0, 999000, tzinfo=timezone.utc),
        msg="$dateSubtract should subtract 1 millisecond near the minimum date",
    ),
    ExpressionTestCase(
        "year_9999_sub_large_ms",
        doc={"date": DATE_YEAR_9999},
        expression={
            "$dateSubtract": {
                "startDate": "$date",
                "unit": "millisecond",
                "amount": 253_402_300_799_999,
            }
        },
        expected=DATE_EPOCH,
        msg="$dateSubtract should reach the epoch from the max date with a large ms amount",
    ),
    ExpressionTestCase(
        "at_python_min_year",
        doc={"date": datetime(1, 1, 1, 23, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "hour", "amount": 23}},
        expected=DATE_YEAR_1,
        msg="$dateSubtract should subtract 23 hours at year 1",
    ),
]

DATESUBTRACT_DATE_RANGE_TESTS: list[ExpressionTestCase] = (
    DATESUBTRACT_HISTORICAL_TESTS + DATESUBTRACT_EPOCH_TESTS + DATESUBTRACT_DATE_LIMIT_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATESUBTRACT_DATE_RANGE_TESTS))
def test_dateSubtract_date_range(collection, test_case: ExpressionTestCase):
    """Test $dateSubtract remains correct across distant, epoch-crossing, and boundary dates."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
