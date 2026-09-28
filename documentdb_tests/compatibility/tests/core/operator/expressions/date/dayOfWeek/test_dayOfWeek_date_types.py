"""Tests for $dayOfWeek with Timestamp, ObjectId, and extended-range date inputs."""

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

# Property [Timestamp Input]: a BSON Timestamp is accepted as a date and yields its day of week.
DAYOFWEEK_TIMESTAMP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "timestamp_sunday",
        doc={"date": ts_from_args(2024, 6, 30, 12, 0, 0)},
        expression={"$dayOfWeek": "$date"},
        expected=1,
        msg="$dayOfWeek should return 1 for a Timestamp on a Sunday",
    ),
    ExpressionTestCase(
        "timestamp_monday",
        doc={"date": ts_from_args(2024, 7, 1, 12, 0, 0)},
        expression={"$dayOfWeek": "$date"},
        expected=2,
        msg="$dayOfWeek should return 2 for a Timestamp on a Monday",
    ),
    ExpressionTestCase(
        "timestamp_saturday",
        doc={"date": ts_from_args(2024, 7, 6, 12, 0, 0)},
        expression={"$dayOfWeek": "$date"},
        expected=7,
        msg="$dayOfWeek should return 7 for a Timestamp on a Saturday",
    ),
    ExpressionTestCase(
        "timestamp_zero_increment",
        doc={"date": ts_from_args(2024, 6, 30, 12, 0, 0, inc=0)},
        expression={"$dayOfWeek": "$date"},
        expected=1,
        msg="$dayOfWeek should return 1 for a Timestamp with a zero increment",
    ),
    ExpressionTestCase(
        "timestamp_epoch",
        doc={"date": ts_from_args(1970, 1, 1, 0, 0, 0)},
        expression={"$dayOfWeek": "$date"},
        expected=5,
        msg="$dayOfWeek should return 5 for a Timestamp at the epoch",
    ),
]

# Property [ObjectId Input]: an ObjectId is accepted as a date via its embedded timestamp.
DAYOFWEEK_OBJECTID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "objectid_sunday",
        doc={"date": oid_from_args(2024, 6, 30, 12, 0, 0)},
        expression={"$dayOfWeek": "$date"},
        expected=1,
        msg="$dayOfWeek should return 1 for an ObjectId on a Sunday",
    ),
    ExpressionTestCase(
        "objectid_monday",
        doc={"date": oid_from_args(2024, 7, 1, 12, 0, 0)},
        expression={"$dayOfWeek": "$date"},
        expected=2,
        msg="$dayOfWeek should return 2 for an ObjectId on a Monday",
    ),
    ExpressionTestCase(
        "objectid_saturday",
        doc={"date": oid_from_args(2024, 7, 6, 12, 0, 0)},
        expression={"$dayOfWeek": "$date"},
        expected=7,
        msg="$dayOfWeek should return 7 for an ObjectId on a Saturday",
    ),
    ExpressionTestCase(
        "objectid_epoch",
        doc={"date": oid_from_args(1970, 1, 1, 0, 0, 0)},
        expression={"$dayOfWeek": "$date"},
        expected=5,
        msg="$dayOfWeek should return 5 for an ObjectId at the epoch",
    ),
]

# Property [Extended Range]: DatetimeMS, Timestamp, and ObjectId boundary instants
# beyond the native datetime range resolve to the correct day of the week.
DAYOFWEEK_EXTENDED_RANGE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "date_ms_epoch",
        doc={"date": DATE_MS_EPOCH},
        expression={"$dayOfWeek": "$date"},
        expected=5,
        msg="$dayOfWeek should return 5 for the epoch as a DatetimeMS",
    ),
    ExpressionTestCase(
        "date_ms_before_epoch",
        doc={"date": DATE_MS_BEFORE_EPOCH},
        expression={"$dayOfWeek": "$date"},
        expected=4,
        msg="$dayOfWeek should return 4 for a DatetimeMS one millisecond before the epoch",
    ),
    ExpressionTestCase(
        "date_ms_year_10000",
        doc={"date": DATE_MS_YEAR_10000},
        expression={"$dayOfWeek": "$date"},
        expected=7,
        msg="$dayOfWeek should return 7 for a DatetimeMS at the year-10000 boundary",
    ),
    ExpressionTestCase(
        "date_ms_max",
        doc={"date": DATE_MS_MAX},
        expression={"$dayOfWeek": "$date"},
        expected=1,
        msg="$dayOfWeek should return 1 for the maximum 64-bit DatetimeMS",
    ),
    ExpressionTestCase(
        "date_ms_min",
        doc={"date": DATE_MS_MIN},
        expression={"$dayOfWeek": "$date"},
        expected=1,
        msg="$dayOfWeek should return 1 for the minimum 64-bit DatetimeMS",
    ),
    ExpressionTestCase(
        "ts_boundary_max_s32",
        doc={"date": TS_MAX_SIGNED32},
        expression={"$dayOfWeek": "$date"},
        expected=3,
        msg="$dayOfWeek should return 3 for the max signed 32-bit Timestamp",
    ),
    ExpressionTestCase(
        "ts_boundary_max_u32",
        doc={"date": TS_MAX_UNSIGNED32},
        expression={"$dayOfWeek": "$date"},
        expected=1,
        msg="$dayOfWeek should return 1 for the max unsigned 32-bit Timestamp",
    ),
    ExpressionTestCase(
        "oid_boundary_max_s32",
        doc={"date": OID_MAX_SIGNED32},
        expression={"$dayOfWeek": "$date"},
        expected=3,
        msg="$dayOfWeek should return 3 for the max signed 32-bit ObjectId",
    ),
    ExpressionTestCase(
        "oid_boundary_min_s32",
        doc={"date": OID_MIN_SIGNED32},
        expression={"$dayOfWeek": "$date"},
        expected=6,
        msg="$dayOfWeek should return 6 for the min signed 32-bit ObjectId",
    ),
    ExpressionTestCase(
        "oid_boundary_max_u32",
        doc={"date": OID_MAX_UNSIGNED32},
        expression={"$dayOfWeek": "$date"},
        expected=4,
        msg="$dayOfWeek should return 4 for the max unsigned 32-bit ObjectId",
    ),
]

DAYOFWEEK_DATE_TYPES_TESTS: list[ExpressionTestCase] = (
    DAYOFWEEK_TIMESTAMP_TESTS + DAYOFWEEK_OBJECTID_TESTS + DAYOFWEEK_EXTENDED_RANGE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DAYOFWEEK_DATE_TYPES_TESTS))
def test_dayOfWeek_date_types(collection, test_case: ExpressionTestCase):
    """Test $dayOfWeek with Timestamp, ObjectId, and extended-range date inputs."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
