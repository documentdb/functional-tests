"""Tests for $millisecond with Timestamp, ObjectId, and extended-range date inputs."""

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
    DATE_MS_BEFORE_EPOCH,
    DATE_MS_EPOCH,
    DATE_MS_MAX,
    DATE_MS_MIN,
    DATE_MS_YEAR_10000,
    INT32_MAX,
    OID_MAX_SIGNED32,
    OID_MAX_UNSIGNED32,
    OID_MIN_SIGNED32,
    TS_MAX_SIGNED32,
    TS_MAX_UNSIGNED32,
)

# Property [Timestamp Input]: a BSON Timestamp has only second-level precision, so its
# millisecond is always 0 regardless of the increment field.
MILLISECOND_TIMESTAMP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "timestamp_inc_0",
        doc={"date": ts_from_args(2024, 6, 15, 12, 30, 0, inc=0)},
        expression={"$millisecond": "$date"},
        expected=0,
        msg="$millisecond should return 0 for a Timestamp with a zero increment",
    ),
    ExpressionTestCase(
        "timestamp_inc_1",
        doc={"date": ts_from_args(2024, 6, 15, 12, 30, 0, inc=1)},
        expression={"$millisecond": "$date"},
        expected=0,
        msg="$millisecond should ignore an increment of 1 and return 0",
    ),
    ExpressionTestCase(
        "timestamp_inc_500",
        doc={"date": ts_from_args(2024, 6, 15, 12, 30, 0, inc=500)},
        expression={"$millisecond": "$date"},
        expected=0,
        msg="$millisecond should ignore a mid-range increment and return 0",
    ),
    ExpressionTestCase(
        "timestamp_inc_999",
        doc={"date": ts_from_args(2024, 6, 15, 12, 30, 0, inc=999)},
        expression={"$millisecond": "$date"},
        expected=0,
        msg="$millisecond should not treat a 999 increment as milliseconds",
    ),
    ExpressionTestCase(
        "timestamp_inc_1000",
        doc={"date": ts_from_args(2024, 6, 15, 12, 30, 0, inc=1000)},
        expression={"$millisecond": "$date"},
        expected=0,
        msg="$millisecond should ignore an increment above 999 and return 0",
    ),
    ExpressionTestCase(
        "timestamp_inc_large",
        doc={"date": ts_from_args(2024, 6, 15, 12, 30, 0, inc=999999)},
        expression={"$millisecond": "$date"},
        expected=0,
        msg="$millisecond should ignore a large increment and return 0",
    ),
    ExpressionTestCase(
        "timestamp_inc_max32",
        doc={"date": Timestamp(1718451000, INT32_MAX)},
        expression={"$millisecond": "$date"},
        expected=0,
        msg="$millisecond should ignore the maximum signed 32-bit increment and return 0",
    ),
    ExpressionTestCase(
        "timestamp_with_seconds",
        doc={"date": ts_from_args(2024, 6, 15, 12, 30, 59)},
        expression={"$millisecond": "$date"},
        expected=0,
        msg="$millisecond should return 0 for a Timestamp at a non-zero second",
    ),
    ExpressionTestCase(
        "timestamp_epoch",
        doc={"date": ts_from_args(1970, 1, 1, 0, 0, 0)},
        expression={"$millisecond": "$date"},
        expected=0,
        msg="$millisecond should return 0 for a Timestamp at the epoch",
    ),
]

# Property [ObjectId Input]: an ObjectId embeds only a second-resolution timestamp, so its
# millisecond is always 0 regardless of the machine/process/counter tail.
MILLISECOND_OBJECTID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "objectid_zero_tail",
        doc={"date": oid_from_args(2024, 6, 15, 12, 30, 0)},
        expression={"$millisecond": "$date"},
        expected=0,
        msg="$millisecond should return 0 for an ObjectId with a zero tail",
    ),
    ExpressionTestCase(
        "objectid_with_seconds",
        doc={"date": oid_from_args(2024, 6, 15, 12, 30, 59)},
        expression={"$millisecond": "$date"},
        expected=0,
        msg="$millisecond should return 0 for an ObjectId at a non-zero second",
    ),
    ExpressionTestCase(
        "objectid_nonzero_tail",
        doc={"date": ObjectId("666cd980ffffff0000000000")},
        expression={"$millisecond": "$date"},
        expected=0,
        msg="$millisecond should ignore a non-zero ObjectId tail and return 0",
    ),
    ExpressionTestCase(
        "objectid_all_f_tail",
        doc={"date": ObjectId("666cd980ffffffffffffffff")},
        expression={"$millisecond": "$date"},
        expected=0,
        msg="$millisecond should ignore an all-ones ObjectId tail and return 0",
    ),
    ExpressionTestCase(
        "objectid_epoch",
        doc={"date": oid_from_args(1970, 1, 1, 0, 0, 0)},
        expression={"$millisecond": "$date"},
        expected=0,
        msg="$millisecond should return 0 for an ObjectId at the epoch",
    ),
]

# Property [Extended Range]: DatetimeMS, Timestamp, and ObjectId boundary instants beyond the
# native datetime range resolve to the correct millisecond.
MILLISECOND_EXTENDED_RANGE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "date_ms_epoch",
        doc={"date": DATE_MS_EPOCH},
        expression={"$millisecond": "$date"},
        expected=0,
        msg="$millisecond should return 0 for the epoch as a DatetimeMS",
    ),
    ExpressionTestCase(
        "date_ms_before_epoch",
        doc={"date": DATE_MS_BEFORE_EPOCH},
        expression={"$millisecond": "$date"},
        expected=999,
        msg="$millisecond should return 999 for a DatetimeMS one millisecond before the epoch",
    ),
    ExpressionTestCase(
        "date_ms_year_10000",
        doc={"date": DATE_MS_YEAR_10000},
        expression={"$millisecond": "$date"},
        expected=0,
        msg="$millisecond should return 0 for a DatetimeMS at the year-10000 boundary",
    ),
    ExpressionTestCase(
        "date_ms_max",
        doc={"date": DATE_MS_MAX},
        expression={"$millisecond": "$date"},
        expected=807,
        msg="$millisecond should return 807 for the maximum 64-bit DatetimeMS",
    ),
    ExpressionTestCase(
        "date_ms_min",
        doc={"date": DATE_MS_MIN},
        expression={"$millisecond": "$date"},
        expected=192,
        msg="$millisecond should return 192 for the minimum 64-bit DatetimeMS",
    ),
    ExpressionTestCase(
        "ts_boundary_max_s32",
        doc={"date": TS_MAX_SIGNED32},
        expression={"$millisecond": "$date"},
        expected=0,
        msg="$millisecond should return 0 for the max signed 32-bit Timestamp",
    ),
    ExpressionTestCase(
        "ts_boundary_max_u32",
        doc={"date": TS_MAX_UNSIGNED32},
        expression={"$millisecond": "$date"},
        expected=0,
        msg="$millisecond should return 0 for the max unsigned 32-bit Timestamp",
    ),
    ExpressionTestCase(
        "oid_boundary_max_s32",
        doc={"date": OID_MAX_SIGNED32},
        expression={"$millisecond": "$date"},
        expected=0,
        msg="$millisecond should return 0 for the max signed 32-bit ObjectId",
    ),
    ExpressionTestCase(
        "oid_boundary_min_s32",
        doc={"date": OID_MIN_SIGNED32},
        expression={"$millisecond": "$date"},
        expected=0,
        msg="$millisecond should return 0 for the min signed 32-bit ObjectId",
    ),
    ExpressionTestCase(
        "oid_boundary_max_u32",
        doc={"date": OID_MAX_UNSIGNED32},
        expression={"$millisecond": "$date"},
        expected=0,
        msg="$millisecond should return 0 for the max unsigned 32-bit ObjectId",
    ),
]

MILLISECOND_DATE_TYPES_TESTS: list[ExpressionTestCase] = (
    MILLISECOND_TIMESTAMP_TESTS + MILLISECOND_OBJECTID_TESTS + MILLISECOND_EXTENDED_RANGE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(MILLISECOND_DATE_TYPES_TESTS))
def test_millisecond_date_types(collection, test_case: ExpressionTestCase):
    """Test $millisecond with Timestamp, ObjectId, and extended-range date inputs."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
