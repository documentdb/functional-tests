"""Tests for $isoWeek with Timestamp, ObjectId, and extended-range date inputs."""

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

# Property [Timestamp Input]: a BSON Timestamp is accepted as a date and yields its ISO week.
ISOWEEK_TIMESTAMP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "timestamp_jan1",
        doc={"date": ts_from_args(2024, 1, 1, 0, 0, 0)},
        expression={"$isoWeek": "$date"},
        expected=1,
        msg="$isoWeek should return 1 for a Timestamp on Jan 1",
    ),
    ExpressionTestCase(
        "timestamp_jan15",
        doc={"date": ts_from_args(2024, 1, 15, 0, 0, 0)},
        expression={"$isoWeek": "$date"},
        expected=3,
        msg="$isoWeek should return 3 for a Timestamp in mid-January",
    ),
    ExpressionTestCase(
        "timestamp_jun15",
        doc={"date": ts_from_args(2024, 6, 15, 12, 0, 0)},
        expression={"$isoWeek": "$date"},
        expected=24,
        msg="$isoWeek should return 24 for a Timestamp in mid-June",
    ),
    ExpressionTestCase(
        "timestamp_dec31",
        doc={"date": ts_from_args(2024, 12, 31, 0, 0, 0)},
        expression={"$isoWeek": "$date"},
        expected=1,
        msg="$isoWeek should return 1 for a Timestamp on a Dec 31 in next year's week 1",
    ),
    ExpressionTestCase(
        "timestamp_epoch",
        doc={"date": ts_from_args(1970, 1, 1, 0, 0, 0)},
        expression={"$isoWeek": "$date"},
        expected=1,
        msg="$isoWeek should return 1 for a Timestamp at the epoch",
    ),
    ExpressionTestCase(
        "timestamp_distant_future",
        doc={"date": ts_from_args(2100, 6, 15, 0, 0, 0)},
        expression={"$isoWeek": "$date"},
        expected=24,
        msg="$isoWeek should return 24 for a Timestamp at a distant future date",
    ),
]

# Property [ObjectId Input]: an ObjectId is accepted as a date via its embedded timestamp.
ISOWEEK_OBJECTID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "objectid_jan1",
        doc={"date": oid_from_args(2024, 1, 1, 0, 0, 0)},
        expression={"$isoWeek": "$date"},
        expected=1,
        msg="$isoWeek should return 1 for an ObjectId on Jan 1",
    ),
    ExpressionTestCase(
        "objectid_jan15",
        doc={"date": oid_from_args(2024, 1, 15, 0, 0, 0)},
        expression={"$isoWeek": "$date"},
        expected=3,
        msg="$isoWeek should return 3 for an ObjectId in mid-January",
    ),
    ExpressionTestCase(
        "objectid_jun15",
        doc={"date": oid_from_args(2024, 6, 15, 12, 0, 0)},
        expression={"$isoWeek": "$date"},
        expected=24,
        msg="$isoWeek should return 24 for an ObjectId in mid-June",
    ),
    ExpressionTestCase(
        "objectid_dec31",
        doc={"date": oid_from_args(2024, 12, 31, 0, 0, 0)},
        expression={"$isoWeek": "$date"},
        expected=1,
        msg="$isoWeek should return 1 for an ObjectId on a Dec 31 in next year's week 1",
    ),
    ExpressionTestCase(
        "objectid_epoch",
        doc={"date": oid_from_args(1970, 1, 1, 0, 0, 0)},
        expression={"$isoWeek": "$date"},
        expected=1,
        msg="$isoWeek should return 1 for an ObjectId at the epoch",
    ),
    ExpressionTestCase(
        "objectid_1980",
        doc={"date": oid_from_args(1980, 6, 15, 0, 0, 0)},
        expression={"$isoWeek": "$date"},
        expected=24,
        msg="$isoWeek should return 24 for an ObjectId in mid-June 1980",
    ),
]

# Property [Extended Range]: DatetimeMS, Timestamp, and ObjectId boundary instants
# beyond the native datetime range resolve to the correct ISO week.
ISOWEEK_EXTENDED_RANGE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "date_ms_epoch",
        doc={"date": DATE_MS_EPOCH},
        expression={"$isoWeek": "$date"},
        expected=1,
        msg="$isoWeek should return 1 for the epoch as a DatetimeMS",
    ),
    ExpressionTestCase(
        "date_ms_before_epoch",
        doc={"date": DATE_MS_BEFORE_EPOCH},
        expression={"$isoWeek": "$date"},
        expected=1,
        msg="$isoWeek should return 1 for a DatetimeMS one millisecond before the epoch",
    ),
    ExpressionTestCase(
        "date_ms_year_10000",
        doc={"date": DATE_MS_YEAR_10000},
        expression={"$isoWeek": "$date"},
        expected=52,
        msg="$isoWeek should return 52 for a DatetimeMS at the year-10000 boundary",
    ),
    ExpressionTestCase(
        "date_ms_max",
        doc={"date": DATE_MS_MAX},
        expression={"$isoWeek": "$date"},
        expected=33,
        msg="$isoWeek should return 33 for the maximum 64-bit DatetimeMS",
    ),
    ExpressionTestCase(
        "date_ms_min",
        doc={"date": DATE_MS_MIN},
        expression={"$isoWeek": "$date"},
        expected=19,
        msg="$isoWeek should return 19 for the minimum 64-bit DatetimeMS",
    ),
    ExpressionTestCase(
        "ts_boundary_max_s32",
        doc={"date": TS_MAX_SIGNED32},
        expression={"$isoWeek": "$date"},
        expected=3,
        msg="$isoWeek should return 3 for the max signed 32-bit Timestamp",
    ),
    ExpressionTestCase(
        "ts_boundary_max_u32",
        doc={"date": TS_MAX_UNSIGNED32},
        expression={"$isoWeek": "$date"},
        expected=5,
        msg="$isoWeek should return 5 for the max unsigned 32-bit Timestamp",
    ),
    ExpressionTestCase(
        "oid_boundary_max_s32",
        doc={"date": OID_MAX_SIGNED32},
        expression={"$isoWeek": "$date"},
        expected=3,
        msg="$isoWeek should return 3 for the max signed 32-bit ObjectId",
    ),
    ExpressionTestCase(
        "oid_boundary_min_s32",
        doc={"date": OID_MIN_SIGNED32},
        expression={"$isoWeek": "$date"},
        expected=50,
        msg="$isoWeek should return 50 for the min signed 32-bit ObjectId",
    ),
    ExpressionTestCase(
        "oid_boundary_max_u32",
        doc={"date": OID_MAX_UNSIGNED32},
        expression={"$isoWeek": "$date"},
        expected=1,
        msg="$isoWeek should return 1 for the max unsigned 32-bit ObjectId",
    ),
]

ISOWEEK_DATE_TYPES_TESTS: list[ExpressionTestCase] = (
    ISOWEEK_TIMESTAMP_TESTS + ISOWEEK_OBJECTID_TESTS + ISOWEEK_EXTENDED_RANGE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(ISOWEEK_DATE_TYPES_TESTS))
def test_isoWeek_date_types(collection, test_case: ExpressionTestCase):
    """Test $isoWeek with Timestamp, ObjectId, and extended-range date inputs."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
