"""$dateAdd date-like input types: Timestamp and ObjectId start dates always return a Date."""

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
DATEADD_TIMESTAMP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "timestamp_startDate_day",
        doc={"date": ts_from_args(2020, 12, 31, 12, 10, 5)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(2021, 1, 1, 12, 10, 5, tzinfo=timezone.utc),
        msg="$dateAdd should accept a Timestamp start date and return a Date",
    ),
    ExpressionTestCase(
        "timestamp_startDate_second",
        doc={"date": ts_from_args(2000, 1, 1, 12, 0, 0)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "second", "amount": 1}},
        expected=datetime(2000, 1, 1, 12, 0, 1, tzinfo=timezone.utc),
        msg="$dateAdd should add a second to a Timestamp start date",
    ),
    ExpressionTestCase(
        "timestamp_epoch",
        doc={"date": TS_EPOCH},
        expression={"$dateAdd": {"startDate": "$date", "unit": "second", "amount": 1}},
        expected=datetime(1970, 1, 1, 0, 0, 1, tzinfo=timezone.utc),
        msg="$dateAdd should accept an epoch Timestamp start date",
    ),
    ExpressionTestCase(
        "date_ms_epoch_add_day",
        doc={"date": DATE_MS_EPOCH},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(1970, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should add a day to an epoch DatetimeMS start date",
    ),
    ExpressionTestCase(
        "ts_max_s32_add_second",
        doc={"date": TS_MAX_SIGNED32},
        expression={"$dateAdd": {"startDate": "$date", "unit": "second", "amount": 1}},
        expected=datetime(2038, 1, 19, 3, 14, 8, tzinfo=timezone.utc),
        msg="$dateAdd should add a second to a max signed 32-bit Timestamp",
    ),
    ExpressionTestCase(
        "ts_max_u32_add_second",
        doc={"date": TS_MAX_UNSIGNED32},
        expression={"$dateAdd": {"startDate": "$date", "unit": "second", "amount": 1}},
        expected=datetime(2106, 2, 7, 6, 28, 16, tzinfo=timezone.utc),
        msg="$dateAdd should add a second to a max unsigned 32-bit Timestamp",
    ),
]

# Property [ObjectId Start Date]: an ObjectId start date uses its embedded timestamp and
# returns a Date.
DATEADD_OBJECTID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "objectid_startDate_day",
        doc={"date": oid_from_args(2022, 7, 15, 22, 32, 25)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "year", "amount": 1}},
        expected=datetime(2023, 7, 15, 22, 32, 25, tzinfo=timezone.utc),
        msg="$dateAdd should accept an ObjectId start date and return a Date",
    ),
    ExpressionTestCase(
        "objectid_startDate_second",
        doc={"date": oid_from_args(2022, 7, 15, 22, 32, 25)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "second", "amount": 1}},
        expected=datetime(2022, 7, 15, 22, 32, 26, tzinfo=timezone.utc),
        msg="$dateAdd should add a second to an ObjectId start date",
    ),
    ExpressionTestCase(
        "objectid_startDate_millisecond",
        doc={"date": oid_from_args(2022, 7, 15, 22, 32, 25)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "millisecond", "amount": 500}},
        expected=datetime(2022, 7, 15, 22, 32, 25, 500000, tzinfo=timezone.utc),
        msg="$dateAdd should add sub-second precision to an ObjectId start date",
    ),
    ExpressionTestCase(
        "objectid_epoch",
        doc={"date": OID_EPOCH},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(1970, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should accept an epoch ObjectId start date",
    ),
    ExpressionTestCase(
        "objectid_max_signed32",
        doc={"date": OID_MAX_SIGNED32},
        expression={"$dateAdd": {"startDate": "$date", "unit": "second", "amount": 1}},
        expected=datetime(2038, 1, 19, 3, 14, 8, tzinfo=timezone.utc),
        msg="$dateAdd should add a second to a max signed 32-bit ObjectId",
    ),
    ExpressionTestCase(
        "objectid_high_bit_pre_epoch",
        doc={"date": OID_MIN_SIGNED32},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(1901, 12, 14, 20, 45, 52, tzinfo=timezone.utc),
        msg="$dateAdd should handle an ObjectId with the high timestamp bit set",
    ),
]

# Property [Return Type]: $dateAdd returns a Date regardless of the start date's date-like type.
DATEADD_RETURN_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "return_type_from_date",
        doc={"date": datetime(2021, 1, 1, tzinfo=timezone.utc)},
        expression={"$type": {"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 1}}},
        expected="date",
        msg="$dateAdd should return a Date from a Date start date",
    ),
    ExpressionTestCase(
        "return_type_from_timestamp",
        doc={"date": Timestamp(1609459200, 1)},
        expression={"$type": {"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 1}}},
        expected="date",
        msg="$dateAdd should return a Date from a Timestamp start date",
    ),
    ExpressionTestCase(
        "return_type_from_objectid",
        doc={"date": ObjectId("600000000000000000000000")},
        expression={"$type": {"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 1}}},
        expected="date",
        msg="$dateAdd should return a Date from an ObjectId start date",
    ),
]

DATEADD_INPUT_TYPE_TESTS: list[ExpressionTestCase] = (
    DATEADD_TIMESTAMP_TESTS + DATEADD_OBJECTID_TESTS + DATEADD_RETURN_TYPE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATEADD_INPUT_TYPE_TESTS))
def test_dateAdd_input_types(collection, test_case: ExpressionTestCase):
    """Test $dateAdd accepts date-like input types and always returns a Date."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
