"""Tests for $year with Timestamp, ObjectId, and extended-range date inputs."""

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

# Property [Timestamp Input]: a BSON Timestamp is accepted as a date and yields its calendar
# year.
YEAR_TIMESTAMP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "timestamp_2024",
        doc={"date": ts_from_args(2024, 6, 15, 0, 0, 0)},
        expression={"$year": "$date"},
        expected=2024,
        msg="$year should return 2024 for a Timestamp in mid-2024",
    ),
    ExpressionTestCase(
        "timestamp_2000",
        doc={"date": ts_from_args(2000, 1, 1, 0, 0, 0)},
        expression={"$year": "$date"},
        expected=2000,
        msg="$year should return 2000 for a Timestamp on Jan 1 2000",
    ),
    ExpressionTestCase(
        "timestamp_zero_increment",
        doc={"date": ts_from_args(2024, 6, 15, 0, 0, 0, inc=0)},
        expression={"$year": "$date"},
        expected=2024,
        msg="$year should return 2024 for a Timestamp with a zero increment",
    ),
    ExpressionTestCase(
        "timestamp_epoch",
        doc={"date": ts_from_args(1970, 1, 1, 0, 0, 0)},
        expression={"$year": "$date"},
        expected=1970,
        msg="$year should return 1970 for a Timestamp at the epoch",
    ),
]

# Property [ObjectId Input]: an ObjectId is accepted as a date via its embedded timestamp.
YEAR_OBJECTID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "objectid_2024",
        doc={"date": oid_from_args(2024, 6, 15, 0, 0, 0)},
        expression={"$year": "$date"},
        expected=2024,
        msg="$year should return 2024 for an ObjectId in mid-2024",
    ),
    ExpressionTestCase(
        "objectid_2000",
        doc={"date": oid_from_args(2000, 1, 1, 0, 0, 0)},
        expression={"$year": "$date"},
        expected=2000,
        msg="$year should return 2000 for an ObjectId on Jan 1 2000",
    ),
    ExpressionTestCase(
        "objectid_epoch",
        doc={"date": oid_from_args(1970, 1, 1, 0, 0, 0)},
        expression={"$year": "$date"},
        expected=1970,
        msg="$year should return 1970 for an ObjectId at the epoch",
    ),
]

# Property [Extended Range]: DatetimeMS, Timestamp, and ObjectId boundary instants beyond the
# native datetime range resolve to the correct calendar year.
YEAR_EXTENDED_RANGE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "date_ms_epoch",
        doc={"date": DATE_MS_EPOCH},
        expression={"$year": "$date"},
        expected=1970,
        msg="$year should return 1970 for the epoch as a DatetimeMS",
    ),
    ExpressionTestCase(
        "date_ms_before_epoch",
        doc={"date": DATE_MS_BEFORE_EPOCH},
        expression={"$year": "$date"},
        expected=1969,
        msg="$year should return 1969 for a DatetimeMS one millisecond before the epoch",
    ),
    ExpressionTestCase(
        "date_ms_year_10000",
        doc={"date": DATE_MS_YEAR_10000},
        expression={"$year": "$date"},
        expected=10000,
        msg="$year should return 10000 for a DatetimeMS at the year-10000 boundary",
    ),
    ExpressionTestCase(
        "date_ms_max",
        doc={"date": DATE_MS_MAX},
        expression={"$year": "$date"},
        expected=292_278_994,
        msg="$year should return the far-future year for the maximum 64-bit DatetimeMS",
    ),
    ExpressionTestCase(
        "date_ms_min",
        doc={"date": DATE_MS_MIN},
        expression={"$year": "$date"},
        expected=-292_275_055,
        msg="$year should return the far-past year for the minimum 64-bit DatetimeMS",
    ),
    ExpressionTestCase(
        "ts_boundary_max_s32",
        doc={"date": TS_MAX_SIGNED32},
        expression={"$year": "$date"},
        expected=2038,
        msg="$year should return 2038 for the max signed 32-bit Timestamp",
    ),
    ExpressionTestCase(
        "ts_boundary_max_u32",
        doc={"date": TS_MAX_UNSIGNED32},
        expression={"$year": "$date"},
        expected=2106,
        msg="$year should return 2106 for the max unsigned 32-bit Timestamp",
    ),
    ExpressionTestCase(
        "oid_boundary_max_s32",
        doc={"date": OID_MAX_SIGNED32},
        expression={"$year": "$date"},
        expected=2038,
        msg="$year should return 2038 for the max signed 32-bit ObjectId",
    ),
    ExpressionTestCase(
        "oid_boundary_min_s32",
        doc={"date": OID_MIN_SIGNED32},
        expression={"$year": "$date"},
        expected=1901,
        msg="$year should return 1901 for the min signed 32-bit ObjectId",
    ),
    ExpressionTestCase(
        "oid_boundary_max_u32",
        doc={"date": OID_MAX_UNSIGNED32},
        expression={"$year": "$date"},
        expected=1969,
        msg="$year should return 1969 for the max unsigned 32-bit ObjectId read as signed",
    ),
]

YEAR_DATE_TYPES_TESTS: list[ExpressionTestCase] = (
    YEAR_TIMESTAMP_TESTS + YEAR_OBJECTID_TESTS + YEAR_EXTENDED_RANGE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(YEAR_DATE_TYPES_TESTS))
def test_year_date_types(collection, test_case: ExpressionTestCase):
    """Test $year with Timestamp, ObjectId, and extended-range date inputs."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
