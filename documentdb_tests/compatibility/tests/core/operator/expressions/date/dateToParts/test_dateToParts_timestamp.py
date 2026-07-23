"""Tests for $dateToParts extraction from Timestamp inputs."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.date_utils import (
    ts_from_args,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Timestamp Inputs]: the embedded time of a Timestamp is used for extraction.
DATETOPARTS_TIMESTAMP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "ts_jun15",
        doc={"date": ts_from_args(2024, 6, 15, 12, 0, 0)},
        expression={"$dateToParts": {"date": "$date"}},
        expected={
            "year": 2024,
            "month": 6,
            "day": 15,
            "hour": 12,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should extract parts from a Timestamp",
    ),
    ExpressionTestCase(
        "ts_jan1",
        doc={"date": ts_from_args(2024, 1, 1, 0, 0, 0)},
        expression={"$dateToParts": {"date": "$date"}},
        expected={
            "year": 2024,
            "month": 1,
            "day": 1,
            "hour": 0,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should extract parts from a Timestamp at the start of the year",
    ),
    ExpressionTestCase(
        "ts_dec31",
        doc={"date": ts_from_args(2024, 12, 31, 23, 59, 59)},
        expression={"$dateToParts": {"date": "$date"}},
        expected={
            "year": 2024,
            "month": 12,
            "day": 31,
            "hour": 23,
            "minute": 59,
            "second": 59,
            "millisecond": 0,
        },
        msg="$dateToParts should extract parts from a Timestamp at the end of the year",
    ),
    ExpressionTestCase(
        "ts_iso",
        doc={"date": ts_from_args(2024, 6, 15, 12, 0, 0)},
        expression={"$dateToParts": {"date": "$date", "iso8601": True}},
        expected={
            "isoWeekYear": 2024,
            "isoWeek": 24,
            "isoDayOfWeek": 6,
            "hour": 12,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should return ISO parts from a Timestamp",
    ),
    ExpressionTestCase(
        "ts_with_tz",
        doc={"date": ts_from_args(2024, 6, 15, 12, 0, 0)},
        expression={"$dateToParts": {"date": "$date", "timezone": "UTC"}},
        expected={
            "year": 2024,
            "month": 6,
            "day": 15,
            "hour": 12,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should apply a timezone to a Timestamp",
    ),
    ExpressionTestCase(
        "ts_epoch",
        doc={"date": ts_from_args(1970, 1, 1, 0, 0, 0)},
        expression={"$dateToParts": {"date": "$date"}},
        expected={
            "year": 1970,
            "month": 1,
            "day": 1,
            "hour": 0,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should extract parts from a Timestamp at the epoch",
    ),
    ExpressionTestCase(
        "ts_future",
        doc={"date": ts_from_args(2100, 3, 1, 0, 0, 0)},
        expression={"$dateToParts": {"date": "$date"}},
        expected={
            "year": 2100,
            "month": 3,
            "day": 1,
            "hour": 0,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should extract parts from a future Timestamp",
    ),
    ExpressionTestCase(
        "ts_ms_zero",
        doc={"date": ts_from_args(2024, 6, 15, 12, 30, 45)},
        expression={"$dateToParts": {"date": "$date"}},
        expected={
            "year": 2024,
            "month": 6,
            "day": 15,
            "hour": 12,
            "minute": 30,
            "second": 45,
            "millisecond": 0,
        },
        msg="$dateToParts should report zero milliseconds for a Timestamp",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(DATETOPARTS_TIMESTAMP_TESTS))
def test_dateToParts_timestamp(collection, test_case: ExpressionTestCase):
    """Test $dateToParts extraction from Timestamp inputs."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
