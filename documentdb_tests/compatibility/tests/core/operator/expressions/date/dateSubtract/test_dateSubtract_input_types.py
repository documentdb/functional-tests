"""$dateSubtract date-like input types: Timestamp and ObjectId start dates always return a Date."""

from datetime import datetime, timezone

import pytest
from bson import ObjectId, Timestamp

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
    DATE_MS_EPOCH,
    OID_EPOCH,
    OID_MAX_SIGNED32,
    OID_MIN_SIGNED32,
    TS_EPOCH,
    TS_MAX_SIGNED32,
    TS_MAX_UNSIGNED32,
)

# Property [Timestamp Start Date]: a Timestamp or DatetimeMS start date is accepted and returns
# a Date.
DATESUBTRACT_TIMESTAMP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "timestamp_startDate_day",
        doc={"date": ts_from_args(2021, 1, 1, 12, 10, 5)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(2020, 12, 31, 12, 10, 5, tzinfo=timezone.utc),
        msg="$dateSubtract should accept a Timestamp start date and return a Date",
    ),
    ExpressionTestCase(
        "timestamp_startDate_second",
        doc={"date": ts_from_args(2000, 1, 1, 12, 0, 1)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "second", "amount": 1}},
        expected=datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should subtract a second from a Timestamp start date",
    ),
    ExpressionTestCase(
        "timestamp_epoch",
        doc={"date": TS_EPOCH},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "second", "amount": -1}},
        expected=datetime(1970, 1, 1, 0, 0, 1, tzinfo=timezone.utc),
        msg="$dateSubtract should accept an epoch Timestamp start date",
    ),
    ExpressionTestCase(
        "date_ms_epoch_sub_day",
        doc={"date": DATE_MS_EPOCH},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(1969, 12, 31, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should subtract a day from an epoch DatetimeMS start date",
    ),
    ExpressionTestCase(
        "ts_max_s32_sub_second",
        doc={"date": TS_MAX_SIGNED32},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "second", "amount": 1}},
        expected=datetime(2038, 1, 19, 3, 14, 6, tzinfo=timezone.utc),
        msg="$dateSubtract should subtract a second from a max signed 32-bit Timestamp",
    ),
    ExpressionTestCase(
        "ts_max_u32_sub_second",
        doc={"date": TS_MAX_UNSIGNED32},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "second", "amount": 1}},
        expected=datetime(2106, 2, 7, 6, 28, 14, tzinfo=timezone.utc),
        msg="$dateSubtract should subtract a second from a max unsigned 32-bit Timestamp",
    ),
]

# Property [ObjectId Start Date]: an ObjectId start date uses its embedded timestamp and
# returns a Date.
DATESUBTRACT_OBJECTID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "objectid_startDate_year",
        doc={"date": oid_from_args(2023, 7, 15, 22, 32, 25)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "year", "amount": 1}},
        expected=datetime(2022, 7, 15, 22, 32, 25, tzinfo=timezone.utc),
        msg="$dateSubtract should accept an ObjectId start date and return a Date",
    ),
    ExpressionTestCase(
        "objectid_startDate_second",
        doc={"date": oid_from_args(2022, 7, 15, 22, 32, 26)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "second", "amount": 1}},
        expected=datetime(2022, 7, 15, 22, 32, 25, tzinfo=timezone.utc),
        msg="$dateSubtract should subtract a second from an ObjectId start date",
    ),
    ExpressionTestCase(
        "objectid_startDate_millisecond",
        doc={"date": oid_from_args(2022, 7, 15, 22, 32, 26)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "millisecond", "amount": 500}},
        expected=datetime(2022, 7, 15, 22, 32, 25, 500000, tzinfo=timezone.utc),
        msg="$dateSubtract should subtract sub-second precision from an ObjectId start date",
    ),
    ExpressionTestCase(
        "objectid_epoch",
        doc={"date": OID_EPOCH},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": -1}},
        expected=datetime(1970, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should accept an epoch ObjectId start date",
    ),
    ExpressionTestCase(
        "objectid_max_signed32",
        doc={"date": OID_MAX_SIGNED32},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "second", "amount": 1}},
        expected=datetime(2038, 1, 19, 3, 14, 6, tzinfo=timezone.utc),
        msg="$dateSubtract should subtract a second from a max signed 32-bit ObjectId",
    ),
    ExpressionTestCase(
        "objectid_high_bit_pre_epoch",
        doc={"date": OID_MIN_SIGNED32},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(1901, 12, 12, 20, 45, 52, tzinfo=timezone.utc),
        msg="$dateSubtract should handle an ObjectId with the high timestamp bit set",
    ),
]

# Property [Return Type]: $dateSubtract returns a Date regardless of the start date's date-like
# type.
DATESUBTRACT_RETURN_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "return_type_from_date",
        doc={"date": datetime(2021, 1, 1, tzinfo=timezone.utc)},
        expression={"$type": {"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": 1}}},
        expected="date",
        msg="$dateSubtract should return a Date from a Date start date",
    ),
    ExpressionTestCase(
        "return_type_from_timestamp",
        doc={"date": Timestamp(1609459200, 1)},
        expression={"$type": {"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": 1}}},
        expected="date",
        msg="$dateSubtract should return a Date from a Timestamp start date",
    ),
    ExpressionTestCase(
        "return_type_from_objectid",
        doc={"date": ObjectId("600000000000000000000000")},
        expression={"$type": {"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": 1}}},
        expected="date",
        msg="$dateSubtract should return a Date from an ObjectId start date",
    ),
]

DATESUBTRACT_INPUT_TYPE_TESTS: list[ExpressionTestCase] = (
    DATESUBTRACT_TIMESTAMP_TESTS + DATESUBTRACT_OBJECTID_TESTS + DATESUBTRACT_RETURN_TYPE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATESUBTRACT_INPUT_TYPE_TESTS))
def test_dateSubtract_input_types(collection, test_case: ExpressionTestCase):
    """Test $dateSubtract accepts date-like input types and always returns a Date."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
