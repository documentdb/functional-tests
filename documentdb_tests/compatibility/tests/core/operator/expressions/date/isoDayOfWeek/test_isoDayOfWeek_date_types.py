"""Tests for $isoDayOfWeek with Timestamp, ObjectId, and extended-range date inputs."""

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

# Property [Timestamp Input]: a BSON Timestamp is accepted as a date and yields its ISO day.
ISODAYOFWEEK_TIMESTAMP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "timestamp_monday",
        doc={"date": ts_from_args(2024, 1, 15, 0, 0, 0)},
        expression={"$isoDayOfWeek": "$date"},
        expected=1,
        msg="$isoDayOfWeek should return 1 for a Timestamp on a Monday",
    ),
    ExpressionTestCase(
        "timestamp_saturday",
        doc={"date": ts_from_args(2024, 1, 20, 0, 0, 0)},
        expression={"$isoDayOfWeek": "$date"},
        expected=6,
        msg="$isoDayOfWeek should return 6 for a Timestamp on a Saturday",
    ),
    ExpressionTestCase(
        "timestamp_sunday",
        doc={"date": ts_from_args(2024, 1, 21, 0, 0, 0)},
        expression={"$isoDayOfWeek": "$date"},
        expected=7,
        msg="$isoDayOfWeek should return 7 for a Timestamp on a Sunday",
    ),
    ExpressionTestCase(
        "timestamp_summer",
        doc={"date": ts_from_args(2024, 6, 15, 12, 0, 0)},
        expression={"$isoDayOfWeek": "$date"},
        expected=6,
        msg="$isoDayOfWeek should return 6 for a Timestamp on a summer Saturday",
    ),
    ExpressionTestCase(
        "timestamp_epoch",
        doc={"date": ts_from_args(1970, 1, 1, 0, 0, 0)},
        expression={"$isoDayOfWeek": "$date"},
        expected=4,
        msg="$isoDayOfWeek should return 4 for a Timestamp at the epoch",
    ),
    ExpressionTestCase(
        "timestamp_distant_future",
        doc={"date": ts_from_args(2100, 1, 1, 0, 0, 0)},
        expression={"$isoDayOfWeek": "$date"},
        expected=5,
        msg="$isoDayOfWeek should return 5 for a Timestamp at a distant future date",
    ),
]

# Property [ObjectId Input]: an ObjectId is accepted as a date via its embedded timestamp.
ISODAYOFWEEK_OBJECTID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "objectid_monday",
        doc={"date": oid_from_args(2024, 1, 15, 0, 0, 0)},
        expression={"$isoDayOfWeek": "$date"},
        expected=1,
        msg="$isoDayOfWeek should return 1 for an ObjectId on a Monday",
    ),
    ExpressionTestCase(
        "objectid_saturday",
        doc={"date": oid_from_args(2024, 1, 20, 0, 0, 0)},
        expression={"$isoDayOfWeek": "$date"},
        expected=6,
        msg="$isoDayOfWeek should return 6 for an ObjectId on a Saturday",
    ),
    ExpressionTestCase(
        "objectid_sunday",
        doc={"date": oid_from_args(2024, 1, 21, 0, 0, 0)},
        expression={"$isoDayOfWeek": "$date"},
        expected=7,
        msg="$isoDayOfWeek should return 7 for an ObjectId on a Sunday",
    ),
    ExpressionTestCase(
        "objectid_summer",
        doc={"date": oid_from_args(2024, 6, 15, 12, 0, 0)},
        expression={"$isoDayOfWeek": "$date"},
        expected=6,
        msg="$isoDayOfWeek should return 6 for an ObjectId on a summer Saturday",
    ),
    ExpressionTestCase(
        "objectid_epoch",
        doc={"date": oid_from_args(1970, 1, 1, 0, 0, 0)},
        expression={"$isoDayOfWeek": "$date"},
        expected=4,
        msg="$isoDayOfWeek should return 4 for an ObjectId at the epoch",
    ),
    ExpressionTestCase(
        "objectid_1980",
        doc={"date": oid_from_args(1980, 1, 1, 0, 0, 0)},
        expression={"$isoDayOfWeek": "$date"},
        expected=2,
        msg="$isoDayOfWeek should return 2 for an ObjectId in 1980, a Tuesday",
    ),
]

# Property [Extended Range]: DatetimeMS, Timestamp, and ObjectId boundary instants
# beyond the native datetime range resolve to the correct ISO day of the week.
ISODAYOFWEEK_EXTENDED_RANGE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "date_ms_epoch",
        doc={"date": DATE_MS_EPOCH},
        expression={"$isoDayOfWeek": "$date"},
        expected=4,
        msg="$isoDayOfWeek should return 4 for the epoch as a DatetimeMS",
    ),
    ExpressionTestCase(
        "date_ms_before_epoch",
        doc={"date": DATE_MS_BEFORE_EPOCH},
        expression={"$isoDayOfWeek": "$date"},
        expected=3,
        msg="$isoDayOfWeek should return 3 for a DatetimeMS one millisecond before the epoch",
    ),
    ExpressionTestCase(
        "date_ms_year_10000",
        doc={"date": DATE_MS_YEAR_10000},
        expression={"$isoDayOfWeek": "$date"},
        expected=6,
        msg="$isoDayOfWeek should return 6 for a DatetimeMS at the year-10000 boundary",
    ),
    ExpressionTestCase(
        "date_ms_max",
        doc={"date": DATE_MS_MAX},
        expression={"$isoDayOfWeek": "$date"},
        expected=7,
        msg="$isoDayOfWeek should return 7 for the maximum 64-bit DatetimeMS",
    ),
    ExpressionTestCase(
        "date_ms_min",
        doc={"date": DATE_MS_MIN},
        expression={"$isoDayOfWeek": "$date"},
        expected=7,
        msg="$isoDayOfWeek should return 7 for the minimum 64-bit DatetimeMS",
    ),
    ExpressionTestCase(
        "ts_boundary_max_s32",
        doc={"date": TS_MAX_SIGNED32},
        expression={"$isoDayOfWeek": "$date"},
        expected=2,
        msg="$isoDayOfWeek should return 2 for the max signed 32-bit Timestamp",
    ),
    ExpressionTestCase(
        "ts_boundary_max_u32",
        doc={"date": TS_MAX_UNSIGNED32},
        expression={"$isoDayOfWeek": "$date"},
        expected=7,
        msg="$isoDayOfWeek should return 7 for the max unsigned 32-bit Timestamp",
    ),
    ExpressionTestCase(
        "oid_boundary_max_s32",
        doc={"date": OID_MAX_SIGNED32},
        expression={"$isoDayOfWeek": "$date"},
        expected=2,
        msg="$isoDayOfWeek should return 2 for the max signed 32-bit ObjectId",
    ),
    ExpressionTestCase(
        "oid_boundary_min_s32",
        doc={"date": OID_MIN_SIGNED32},
        expression={"$isoDayOfWeek": "$date"},
        expected=5,
        msg="$isoDayOfWeek should return 5 for the min signed 32-bit ObjectId",
    ),
    ExpressionTestCase(
        "oid_boundary_max_u32",
        doc={"date": OID_MAX_UNSIGNED32},
        expression={"$isoDayOfWeek": "$date"},
        expected=3,
        msg="$isoDayOfWeek should return 3 for the max unsigned 32-bit ObjectId",
    ),
]

ISODAYOFWEEK_DATE_TYPES_TESTS: list[ExpressionTestCase] = (
    ISODAYOFWEEK_TIMESTAMP_TESTS + ISODAYOFWEEK_OBJECTID_TESTS + ISODAYOFWEEK_EXTENDED_RANGE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(ISODAYOFWEEK_DATE_TYPES_TESTS))
def test_isoDayOfWeek_date_types(collection, test_case: ExpressionTestCase):
    """Test $isoDayOfWeek with Timestamp, ObjectId, and extended-range date inputs."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
