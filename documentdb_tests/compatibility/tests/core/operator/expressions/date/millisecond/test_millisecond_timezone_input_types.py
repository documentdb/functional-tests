"""Tests for $millisecond timezone application when the date is a Timestamp or ObjectId."""

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

# Property [Timestamp Input with Zones]: a Timestamp has only second-level precision, so the
# millisecond is always 0 regardless of the requested zone.
MILLISECOND_TIMESTAMP_ZONE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_olson_ts_utc",
        expression={
            "$millisecond": {"date": ts_from_args(2024, 7, 15, 12, 25, 37), "timezone": "UTC"}
        },
        expected=0,
        msg="$millisecond should return 0 for a Timestamp in UTC",
    ),
    ExpressionTestCase(
        "tz_olson_ts_tokyo",
        expression={
            "$millisecond": {
                "date": ts_from_args(2024, 7, 15, 12, 25, 37),
                "timezone": "Asia/Tokyo",
            }
        },
        expected=0,
        msg="$millisecond should return 0 for a Timestamp in Asia/Tokyo",
    ),
    ExpressionTestCase(
        "tz_olson_ts_kolkata",
        expression={
            "$millisecond": {
                "date": ts_from_args(2024, 3, 31, 20, 0, 37),
                "timezone": "Asia/Kolkata",
            }
        },
        expected=0,
        msg="$millisecond should return 0 for a Timestamp in Asia/Kolkata (+05:30)",
    ),
    ExpressionTestCase(
        "tz_offset_ts_plus9",
        expression={
            "$millisecond": {"date": ts_from_args(2024, 7, 15, 12, 25, 37), "timezone": "+09:00"}
        },
        expected=0,
        msg="$millisecond should return 0 for a Timestamp at a +09:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_ts_plus530",
        expression={
            "$millisecond": {"date": ts_from_args(2024, 3, 31, 20, 0, 37), "timezone": "+05:30"}
        },
        expected=0,
        msg="$millisecond should return 0 for a Timestamp at a +05:30 offset",
    ),
]

# Property [ObjectId Input with Zones]: an ObjectId embeds only a second-resolution timestamp,
# so the millisecond is always 0 regardless of the requested zone.
MILLISECOND_OBJECTID_ZONE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_olson_oid_utc",
        expression={
            "$millisecond": {"date": oid_from_args(2024, 7, 15, 12, 25, 37), "timezone": "UTC"}
        },
        expected=0,
        msg="$millisecond should return 0 for an ObjectId in UTC",
    ),
    ExpressionTestCase(
        "tz_olson_oid_tokyo",
        expression={
            "$millisecond": {
                "date": oid_from_args(2024, 7, 15, 12, 25, 37),
                "timezone": "Asia/Tokyo",
            }
        },
        expected=0,
        msg="$millisecond should return 0 for an ObjectId in Asia/Tokyo",
    ),
    ExpressionTestCase(
        "tz_olson_oid_kolkata",
        expression={
            "$millisecond": {
                "date": oid_from_args(2024, 3, 31, 20, 0, 37),
                "timezone": "Asia/Kolkata",
            }
        },
        expected=0,
        msg="$millisecond should return 0 for an ObjectId in Asia/Kolkata (+05:30)",
    ),
    ExpressionTestCase(
        "tz_offset_oid_plus9",
        expression={
            "$millisecond": {"date": oid_from_args(2024, 7, 15, 12, 25, 37), "timezone": "+09:00"}
        },
        expected=0,
        msg="$millisecond should return 0 for an ObjectId at a +09:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_oid_plus530",
        expression={
            "$millisecond": {"date": oid_from_args(2024, 3, 31, 20, 0, 37), "timezone": "+05:30"}
        },
        expected=0,
        msg="$millisecond should return 0 for an ObjectId at a +05:30 offset",
    ),
]

MILLISECOND_TIMEZONE_INPUT_TYPES_TESTS: list[ExpressionTestCase] = (
    MILLISECOND_TIMESTAMP_ZONE_TESTS + MILLISECOND_OBJECTID_ZONE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(MILLISECOND_TIMEZONE_INPUT_TYPES_TESTS))
def test_millisecond_timezone_input_types(collection, test_case: ExpressionTestCase):
    """Test $millisecond timezone application for Timestamp and ObjectId date inputs."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
