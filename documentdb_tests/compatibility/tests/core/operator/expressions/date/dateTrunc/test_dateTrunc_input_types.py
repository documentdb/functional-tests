"""$dateTrunc date-like input types: ObjectId, Timestamp, numeric boundaries, and return type."""

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
    DATE_MS_BEFORE_EPOCH,
    DATE_MS_EPOCH,
    OID_MAX_SIGNED32,
    OID_MIN_SIGNED32,
    TS_MAX_SIGNED32,
    TS_MAX_UNSIGNED32,
)

# Property [ObjectId And Timestamp Input]: ObjectId and Timestamp inputs are truncated by their
# embedded time.
DATETRUNC_OID_TS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "oid_trunc_day",
        doc={"date": oid_from_args(2021, 3, 20, 11, 30, 5)},
        expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
        expected=datetime(2021, 3, 20, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate an ObjectId to the day",
    ),
    ExpressionTestCase(
        "oid_trunc_hour",
        doc={"date": oid_from_args(2021, 3, 20, 11, 30, 5)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour"}},
        expected=datetime(2021, 3, 20, 11, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate an ObjectId to the hour",
    ),
    ExpressionTestCase(
        "oid_trunc_month",
        doc={"date": oid_from_args(2021, 3, 20, 11, 30, 5)},
        expression={"$dateTrunc": {"date": "$date", "unit": "month"}},
        expected=datetime(2021, 3, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate an ObjectId to the month",
    ),
    ExpressionTestCase(
        "oid_trunc_year",
        doc={"date": oid_from_args(2021, 3, 20, 11, 30, 5)},
        expression={"$dateTrunc": {"date": "$date", "unit": "year"}},
        expected=datetime(2021, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate an ObjectId to the year",
    ),
    ExpressionTestCase(
        "oid_with_tz",
        doc={"date": oid_from_args(2021, 3, 20, 11, 30, 5)},
        expression={"$dateTrunc": {"date": "$date", "unit": "day", "timezone": "UTC"}},
        expected=datetime(2021, 3, 20, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate an ObjectId with a timezone",
    ),
    ExpressionTestCase(
        "ts_trunc_day",
        doc={"date": ts_from_args(2021, 3, 20, 11, 30, 5)},
        expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
        expected=datetime(2021, 3, 20, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a Timestamp to the day",
    ),
    ExpressionTestCase(
        "ts_trunc_hour",
        doc={"date": ts_from_args(2021, 3, 20, 11, 30, 5)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour"}},
        expected=datetime(2021, 3, 20, 11, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a Timestamp to the hour",
    ),
    ExpressionTestCase(
        "ts_trunc_month",
        doc={"date": ts_from_args(2021, 3, 20, 11, 30, 5)},
        expression={"$dateTrunc": {"date": "$date", "unit": "month"}},
        expected=datetime(2021, 3, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a Timestamp to the month",
    ),
    ExpressionTestCase(
        "ts_trunc_year",
        doc={"date": ts_from_args(2021, 3, 20, 11, 30, 5)},
        expression={"$dateTrunc": {"date": "$date", "unit": "year"}},
        expected=datetime(2021, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a Timestamp to the year",
    ),
    ExpressionTestCase(
        "ts_with_tz",
        doc={"date": ts_from_args(2021, 3, 20, 11, 30, 5)},
        expression={"$dateTrunc": {"date": "$date", "unit": "day", "timezone": "UTC"}},
        expected=datetime(2021, 3, 20, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a Timestamp with a timezone",
    ),
]

# Property [DatetimeMS And Numeric Boundaries]: DatetimeMS, max Timestamp, and signed-boundary
# ObjectId inputs truncate correctly.
DATETRUNC_NUMERIC_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "date_ms_epoch_trunc_day",
        doc={"date": DATE_MS_EPOCH},
        expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
        expected=DATE_EPOCH,
        msg="$dateTrunc should truncate an epoch DatetimeMS to the day",
    ),
    ExpressionTestCase(
        "date_ms_before_epoch_trunc_day",
        doc={"date": DATE_MS_BEFORE_EPOCH},
        expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
        expected=datetime(1969, 12, 31, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a pre-epoch DatetimeMS to the day",
    ),
    ExpressionTestCase(
        "ts_max_s32_trunc_day",
        doc={"date": TS_MAX_SIGNED32},
        expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
        expected=datetime(2038, 1, 19, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a max signed 32-bit Timestamp to the day",
    ),
    ExpressionTestCase(
        "ts_max_u32_trunc_month",
        doc={"date": TS_MAX_UNSIGNED32},
        expression={"$dateTrunc": {"date": "$date", "unit": "month"}},
        expected=datetime(2106, 2, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a max unsigned 32-bit Timestamp to the month",
    ),
    ExpressionTestCase(
        "oid_max_signed32_trunc_day",
        doc={"date": OID_MAX_SIGNED32},
        expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
        expected=datetime(2038, 1, 19, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a max signed 32-bit ObjectId to the day",
    ),
    ExpressionTestCase(
        "oid_high_bit_trunc_year",
        doc={"date": OID_MIN_SIGNED32},
        expression={"$dateTrunc": {"date": "$date", "unit": "year"}},
        expected=datetime(1901, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a high-bit ObjectId to the year",
    ),
]

# Property [Return Type]: $dateTrunc returns the date type regardless of the input date type.
DATETRUNC_RETURN_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "return_type_date",
        expression={
            "$type": {
                "$dateTrunc": {
                    "date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc),
                    "unit": "day",
                }
            }
        },
        expected="date",
        msg="$dateTrunc should return the date type for a Date input",
    ),
    ExpressionTestCase(
        "return_type_from_timestamp",
        doc={"ts": ts_from_args(2021, 3, 20, 11, 30, 5)},
        expression={"$type": {"$dateTrunc": {"date": "$ts", "unit": "day"}}},
        expected="date",
        msg="$dateTrunc should return the date type for a Timestamp input",
    ),
    ExpressionTestCase(
        "return_type_from_objectid",
        doc={"oid": oid_from_args(2021, 3, 20, 11, 30, 5)},
        expression={"$type": {"$dateTrunc": {"date": "$oid", "unit": "day"}}},
        expected="date",
        msg="$dateTrunc should return the date type for an ObjectId input",
    ),
]

DATETRUNC_INPUT_TYPE_TESTS: list[ExpressionTestCase] = (
    DATETRUNC_OID_TS_TESTS + DATETRUNC_NUMERIC_BOUNDARY_TESTS + DATETRUNC_RETURN_TYPE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATETRUNC_INPUT_TYPE_TESTS))
def test_dateTrunc_input_types(collection, test_case: ExpressionTestCase):
    """Test $dateTrunc accepts date-like inputs and returns the date type."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
