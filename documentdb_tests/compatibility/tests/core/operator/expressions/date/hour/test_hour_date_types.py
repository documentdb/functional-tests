"""Tests for $hour with Timestamp, ObjectId, and extended-range date inputs."""

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
    DATE_MS_BEFORE_EPOCH,
    DATE_MS_EPOCH,
    DATE_MS_MAX,
    DATE_MS_MIN,
    DATE_MS_YEAR_10000,
    OID_MAX_SIGNED32,
    OID_MAX_UNSIGNED32,
    OID_MIN_SIGNED32,
    TS_MAX_SIGNED32,
    TS_MAX_UNSIGNED32,
)

# Property [Timestamp Input]: a BSON Timestamp is accepted as a date and yields its hour.
HOUR_TIMESTAMP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "timestamp_midnight",
        doc={"date": ts_from_args(2024, 6, 15, 0, 0, 0)},
        expression={"$hour": "$date"},
        expected=0,
        msg="$hour should return 0 for a Timestamp at midnight",
    ),
    ExpressionTestCase(
        "timestamp_noon",
        doc={"date": ts_from_args(2024, 6, 15, 12, 0, 0)},
        expression={"$hour": "$date"},
        expected=12,
        msg="$hour should return 12 for a Timestamp at noon",
    ),
    ExpressionTestCase(
        "timestamp_hour_23",
        doc={"date": ts_from_args(2024, 6, 15, 23, 0, 0)},
        expression={"$hour": "$date"},
        expected=23,
        msg="$hour should return 23 for a Timestamp in the last hour",
    ),
    ExpressionTestCase(
        "timestamp_zero_increment",
        doc={"date": ts_from_args(2024, 6, 15, 8, 0, 0, inc=0)},
        expression={"$hour": "$date"},
        expected=8,
        msg="$hour should return 8 for a Timestamp with a zero increment",
    ),
    ExpressionTestCase(
        "timestamp_epoch",
        doc={"date": ts_from_args(1970, 1, 1, 0, 0, 0)},
        expression={"$hour": "$date"},
        expected=0,
        msg="$hour should return 0 for a Timestamp at the epoch",
    ),
]

# Property [ObjectId Input]: an ObjectId is accepted as a date via its embedded timestamp.
HOUR_OBJECTID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "objectid_midnight",
        doc={"date": oid_from_args(2024, 6, 15, 0, 0, 0)},
        expression={"$hour": "$date"},
        expected=0,
        msg="$hour should return 0 for an ObjectId at midnight",
    ),
    ExpressionTestCase(
        "objectid_noon",
        doc={"date": oid_from_args(2024, 6, 15, 12, 0, 0)},
        expression={"$hour": "$date"},
        expected=12,
        msg="$hour should return 12 for an ObjectId at noon",
    ),
    ExpressionTestCase(
        "objectid_hour_23",
        doc={"date": oid_from_args(2024, 6, 15, 23, 0, 0)},
        expression={"$hour": "$date"},
        expected=23,
        msg="$hour should return 23 for an ObjectId in the last hour",
    ),
    ExpressionTestCase(
        "objectid_epoch",
        doc={"date": oid_from_args(1970, 1, 1, 0, 0, 0)},
        expression={"$hour": "$date"},
        expected=0,
        msg="$hour should return 0 for an ObjectId at the epoch",
    ),
]

# Property [Extended Range]: DatetimeMS, Timestamp, and ObjectId boundary instants
# beyond the native datetime range resolve to the correct hour.
HOUR_EXTENDED_RANGE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "date_ms_epoch",
        doc={"date": DATE_MS_EPOCH},
        expression={"$hour": "$date"},
        expected=0,
        msg="$hour should return 0 for the epoch as a DatetimeMS",
    ),
    ExpressionTestCase(
        "date_ms_before_epoch",
        doc={"date": DATE_MS_BEFORE_EPOCH},
        expression={"$hour": "$date"},
        expected=23,
        msg="$hour should return 23 for a DatetimeMS one millisecond before the epoch",
    ),
    ExpressionTestCase(
        "date_ms_year_10000",
        doc={"date": DATE_MS_YEAR_10000},
        expression={"$hour": "$date"},
        expected=0,
        msg="$hour should return 0 for a DatetimeMS at the year-10000 boundary",
    ),
    ExpressionTestCase(
        "date_ms_max",
        doc={"date": DATE_MS_MAX},
        expression={"$hour": "$date"},
        expected=7,
        msg="$hour should return 7 for the maximum 64-bit DatetimeMS",
    ),
    ExpressionTestCase(
        "date_ms_min",
        doc={"date": DATE_MS_MIN},
        expression={"$hour": "$date"},
        expected=16,
        msg="$hour should return 16 for the minimum 64-bit DatetimeMS",
    ),
    ExpressionTestCase(
        "ts_boundary_max_s32",
        doc={"date": TS_MAX_SIGNED32},
        expression={"$hour": "$date"},
        expected=3,
        msg="$hour should return 3 for the max signed 32-bit Timestamp",
    ),
    ExpressionTestCase(
        "ts_boundary_max_u32",
        doc={"date": TS_MAX_UNSIGNED32},
        expression={"$hour": "$date"},
        expected=6,
        msg="$hour should return 6 for the max unsigned 32-bit Timestamp",
    ),
    ExpressionTestCase(
        "oid_boundary_max_s32",
        doc={"date": OID_MAX_SIGNED32},
        expression={"$hour": "$date"},
        expected=3,
        msg="$hour should return 3 for the max signed 32-bit ObjectId",
    ),
    ExpressionTestCase(
        "oid_boundary_min_s32",
        doc={"date": OID_MIN_SIGNED32},
        expression={"$hour": "$date"},
        expected=20,
        msg="$hour should return 20 for the min signed 32-bit ObjectId",
    ),
    ExpressionTestCase(
        "oid_boundary_max_u32",
        doc={"date": OID_MAX_UNSIGNED32},
        expression={"$hour": "$date"},
        expected=23,
        msg="$hour should return 23 for the max unsigned 32-bit ObjectId",
    ),
]

HOUR_DATE_TYPES_TESTS: list[ExpressionTestCase] = (
    HOUR_TIMESTAMP_TESTS + HOUR_OBJECTID_TESTS + HOUR_EXTENDED_RANGE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(HOUR_DATE_TYPES_TESTS))
def test_hour_date_types(collection, test_case: ExpressionTestCase):
    """Test $hour with Timestamp, ObjectId, and extended-range date inputs."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
