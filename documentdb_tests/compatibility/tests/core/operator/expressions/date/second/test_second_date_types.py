"""Tests for $second with Timestamp, ObjectId, and extended-range date inputs."""

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

# Property [Timestamp Input]: a BSON Timestamp is accepted as a date and yields its second.
SECOND_TIMESTAMP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "timestamp_second_0",
        doc={"date": ts_from_args(2024, 6, 15, 12, 30, 0)},
        expression={"$second": "$date"},
        expected=0,
        msg="$second should return 0 for a Timestamp at the top of the minute",
    ),
    ExpressionTestCase(
        "timestamp_second_30",
        doc={"date": ts_from_args(2024, 6, 15, 12, 30, 30)},
        expression={"$second": "$date"},
        expected=30,
        msg="$second should return 30 for a Timestamp at half past the minute",
    ),
    ExpressionTestCase(
        "timestamp_second_59",
        doc={"date": ts_from_args(2024, 6, 15, 12, 30, 59)},
        expression={"$second": "$date"},
        expected=59,
        msg="$second should return 59 for a Timestamp in the last second",
    ),
    ExpressionTestCase(
        "timestamp_zero_increment",
        doc={"date": ts_from_args(2024, 6, 15, 8, 15, 42, inc=0)},
        expression={"$second": "$date"},
        expected=42,
        msg="$second should return 42 for a Timestamp with a zero increment",
    ),
    ExpressionTestCase(
        "timestamp_epoch",
        doc={"date": ts_from_args(1970, 1, 1, 0, 0, 0)},
        expression={"$second": "$date"},
        expected=0,
        msg="$second should return 0 for a Timestamp at the epoch",
    ),
]

# Property [ObjectId Input]: an ObjectId is accepted as a date via its embedded timestamp.
SECOND_OBJECTID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "objectid_second_0",
        doc={"date": oid_from_args(2024, 6, 15, 12, 30, 0)},
        expression={"$second": "$date"},
        expected=0,
        msg="$second should return 0 for an ObjectId at the top of the minute",
    ),
    ExpressionTestCase(
        "objectid_second_30",
        doc={"date": oid_from_args(2024, 6, 15, 12, 30, 30)},
        expression={"$second": "$date"},
        expected=30,
        msg="$second should return 30 for an ObjectId at half past the minute",
    ),
    ExpressionTestCase(
        "objectid_second_59",
        doc={"date": oid_from_args(2024, 6, 15, 12, 30, 59)},
        expression={"$second": "$date"},
        expected=59,
        msg="$second should return 59 for an ObjectId in the last second",
    ),
    ExpressionTestCase(
        "objectid_epoch",
        doc={"date": oid_from_args(1970, 1, 1, 0, 0, 0)},
        expression={"$second": "$date"},
        expected=0,
        msg="$second should return 0 for an ObjectId at the epoch",
    ),
]

# Property [Extended Range]: DatetimeMS, Timestamp, and ObjectId boundary instants
# beyond the native datetime range resolve to the correct second.
SECOND_EXTENDED_RANGE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "date_ms_epoch",
        doc={"date": DATE_MS_EPOCH},
        expression={"$second": "$date"},
        expected=0,
        msg="$second should return 0 for the epoch as a DatetimeMS",
    ),
    ExpressionTestCase(
        "date_ms_before_epoch",
        doc={"date": DATE_MS_BEFORE_EPOCH},
        expression={"$second": "$date"},
        expected=59,
        msg="$second should return 59 for a DatetimeMS one millisecond before the epoch",
    ),
    ExpressionTestCase(
        "date_ms_year_10000",
        doc={"date": DATE_MS_YEAR_10000},
        expression={"$second": "$date"},
        expected=0,
        msg="$second should return 0 for a DatetimeMS at the year-10000 boundary",
    ),
    ExpressionTestCase(
        "date_ms_max",
        doc={"date": DATE_MS_MAX},
        expression={"$second": "$date"},
        expected=55,
        msg="$second should return 55 for the maximum 64-bit DatetimeMS",
    ),
    ExpressionTestCase(
        "date_ms_min",
        doc={"date": DATE_MS_MIN},
        expression={"$second": "$date"},
        expected=4,
        msg="$second should return 4 for the minimum 64-bit DatetimeMS",
    ),
    ExpressionTestCase(
        "ts_boundary_max_s32",
        doc={"date": TS_MAX_SIGNED32},
        expression={"$second": "$date"},
        expected=7,
        msg="$second should return 7 for the max signed 32-bit Timestamp",
    ),
    ExpressionTestCase(
        "ts_boundary_max_u32",
        doc={"date": TS_MAX_UNSIGNED32},
        expression={"$second": "$date"},
        expected=15,
        msg="$second should return 15 for the max unsigned 32-bit Timestamp",
    ),
    ExpressionTestCase(
        "oid_boundary_max_s32",
        doc={"date": OID_MAX_SIGNED32},
        expression={"$second": "$date"},
        expected=7,
        msg="$second should return 7 for the max signed 32-bit ObjectId",
    ),
    ExpressionTestCase(
        "oid_boundary_min_s32",
        doc={"date": OID_MIN_SIGNED32},
        expression={"$second": "$date"},
        expected=52,
        msg="$second should return 52 for the min signed 32-bit ObjectId",
    ),
    ExpressionTestCase(
        "oid_boundary_max_u32",
        doc={"date": OID_MAX_UNSIGNED32},
        expression={"$second": "$date"},
        expected=59,
        msg="$second should return 59 for the max unsigned 32-bit ObjectId",
    ),
]

SECOND_DATE_TYPES_TESTS: list[ExpressionTestCase] = (
    SECOND_TIMESTAMP_TESTS + SECOND_OBJECTID_TESTS + SECOND_EXTENDED_RANGE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SECOND_DATE_TYPES_TESTS))
def test_second_date_types(collection, test_case: ExpressionTestCase):
    """Test $second with Timestamp, ObjectId, and extended-range date inputs."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
