"""Tests for $dayOfYear with Timestamp, ObjectId, and extended-range date inputs."""

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

# Property [Timestamp Input]: a BSON Timestamp is accepted as a date and yields its ordinal day.
DAYOFYEAR_TIMESTAMP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "timestamp_day_1",
        doc={"date": ts_from_args(2024, 1, 1, 0, 0, 0)},
        expression={"$dayOfYear": "$date"},
        expected=1,
        msg="$dayOfYear should return 1 for a Timestamp on day 1",
    ),
    ExpressionTestCase(
        "timestamp_day_167",
        doc={"date": ts_from_args(2024, 6, 15, 0, 0, 0)},
        expression={"$dayOfYear": "$date"},
        expected=167,
        msg="$dayOfYear should return the ordinal day for a Timestamp mid-year",
    ),
    ExpressionTestCase(
        "timestamp_day_366",
        doc={"date": ts_from_args(2024, 12, 31, 0, 0, 0)},
        expression={"$dayOfYear": "$date"},
        expected=366,
        msg="$dayOfYear should return 366 for a Timestamp on day 366",
    ),
    ExpressionTestCase(
        "timestamp_zero_increment",
        doc={"date": ts_from_args(2024, 6, 15, 0, 0, 0, inc=0)},
        expression={"$dayOfYear": "$date"},
        expected=167,
        msg="$dayOfYear should return the ordinal day for a Timestamp with a zero increment",
    ),
    ExpressionTestCase(
        "timestamp_epoch",
        doc={"date": ts_from_args(1970, 1, 1, 0, 0, 0)},
        expression={"$dayOfYear": "$date"},
        expected=1,
        msg="$dayOfYear should return 1 for a Timestamp at the epoch",
    ),
]

# Property [ObjectId Input]: an ObjectId is accepted as a date via its embedded timestamp.
DAYOFYEAR_OBJECTID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "objectid_day_1",
        doc={"date": oid_from_args(2024, 1, 1, 0, 0, 0)},
        expression={"$dayOfYear": "$date"},
        expected=1,
        msg="$dayOfYear should return 1 for an ObjectId on day 1",
    ),
    ExpressionTestCase(
        "objectid_day_167",
        doc={"date": oid_from_args(2024, 6, 15, 0, 0, 0)},
        expression={"$dayOfYear": "$date"},
        expected=167,
        msg="$dayOfYear should return the ordinal day for an ObjectId mid-year",
    ),
    ExpressionTestCase(
        "objectid_day_366",
        doc={"date": oid_from_args(2024, 12, 31, 0, 0, 0)},
        expression={"$dayOfYear": "$date"},
        expected=366,
        msg="$dayOfYear should return 366 for an ObjectId on day 366",
    ),
    ExpressionTestCase(
        "objectid_epoch",
        doc={"date": oid_from_args(1970, 1, 1, 0, 0, 0)},
        expression={"$dayOfYear": "$date"},
        expected=1,
        msg="$dayOfYear should return 1 for an ObjectId at the epoch",
    ),
]

# Property [Extended Range]: DatetimeMS, Timestamp, and ObjectId boundary instants
# beyond the native datetime range resolve to the correct ordinal day.
DAYOFYEAR_EXTENDED_RANGE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "date_ms_epoch",
        doc={"date": DATE_MS_EPOCH},
        expression={"$dayOfYear": "$date"},
        expected=1,
        msg="$dayOfYear should return 1 for the epoch as a DatetimeMS",
    ),
    ExpressionTestCase(
        "date_ms_before_epoch",
        doc={"date": DATE_MS_BEFORE_EPOCH},
        expression={"$dayOfYear": "$date"},
        expected=365,
        msg="$dayOfYear should return 365 for a DatetimeMS one millisecond before the epoch",
    ),
    ExpressionTestCase(
        "date_ms_year_10000",
        doc={"date": DATE_MS_YEAR_10000},
        expression={"$dayOfYear": "$date"},
        expected=1,
        msg="$dayOfYear should return the ordinal day for a DatetimeMS at the year-10000 boundary",
    ),
    ExpressionTestCase(
        "date_ms_max",
        doc={"date": DATE_MS_MAX},
        expression={"$dayOfYear": "$date"},
        expected=229,
        msg="$dayOfYear should return the ordinal day for the maximum 64-bit DatetimeMS",
    ),
    ExpressionTestCase(
        "date_ms_min",
        doc={"date": DATE_MS_MIN},
        expression={"$dayOfYear": "$date"},
        expected=136,
        msg="$dayOfYear should return the ordinal day for the minimum 64-bit DatetimeMS",
    ),
    ExpressionTestCase(
        "ts_boundary_max_s32",
        doc={"date": TS_MAX_SIGNED32},
        expression={"$dayOfYear": "$date"},
        expected=19,
        msg="$dayOfYear should return 19 for the max signed 32-bit Timestamp",
    ),
    ExpressionTestCase(
        "ts_boundary_max_u32",
        doc={"date": TS_MAX_UNSIGNED32},
        expression={"$dayOfYear": "$date"},
        expected=38,
        msg="$dayOfYear should return 38 for the max unsigned 32-bit Timestamp",
    ),
    ExpressionTestCase(
        "oid_boundary_max_s32",
        doc={"date": OID_MAX_SIGNED32},
        expression={"$dayOfYear": "$date"},
        expected=19,
        msg="$dayOfYear should return 19 for the max signed 32-bit ObjectId",
    ),
    ExpressionTestCase(
        "oid_boundary_min_s32",
        doc={"date": OID_MIN_SIGNED32},
        expression={"$dayOfYear": "$date"},
        expected=347,
        msg="$dayOfYear should return 347 for the min signed 32-bit ObjectId",
    ),
    ExpressionTestCase(
        "oid_boundary_max_u32",
        doc={"date": OID_MAX_UNSIGNED32},
        expression={"$dayOfYear": "$date"},
        expected=365,
        msg="$dayOfYear should return 365 for the max unsigned 32-bit ObjectId",
    ),
]

DAYOFYEAR_DATE_TYPES_TESTS: list[ExpressionTestCase] = (
    DAYOFYEAR_TIMESTAMP_TESTS + DAYOFYEAR_OBJECTID_TESTS + DAYOFYEAR_EXTENDED_RANGE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DAYOFYEAR_DATE_TYPES_TESTS))
def test_dayOfYear_date_types(collection, test_case: ExpressionTestCase):
    """Test $dayOfYear with Timestamp, ObjectId, and extended-range date inputs."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
