"""Tests for $minute timezone application when the date is a Timestamp or ObjectId."""

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

# Property [Timestamp Input with Zones]: a Timestamp input honours the zone offset,
# leaving whole-hour offsets unchanged and shifting fractional ones.
MINUTE_TIMESTAMP_ZONE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_olson_ts_utc",
        expression={"$minute": {"date": ts_from_args(2024, 7, 15, 12, 25, 0), "timezone": "UTC"}},
        expected=25,
        msg="$minute should return 25 for a Timestamp in UTC",
    ),
    ExpressionTestCase(
        "tz_olson_ts_tokyo",
        expression={
            "$minute": {"date": ts_from_args(2024, 7, 15, 12, 25, 0), "timezone": "Asia/Tokyo"}
        },
        expected=25,
        msg="$minute should leave the minute at 25 for a Timestamp in whole-hour Asia/Tokyo",
    ),
    ExpressionTestCase(
        "tz_olson_ts_kolkata_on_hour",
        expression={
            "$minute": {"date": ts_from_args(2024, 3, 31, 20, 0, 0), "timezone": "Asia/Kolkata"}
        },
        expected=30,
        msg="$minute should return 30 for a Timestamp in Asia/Kolkata (+05:30)",
    ),
    ExpressionTestCase(
        "tz_olson_ts_kolkata_45",
        expression={
            "$minute": {"date": ts_from_args(2024, 6, 15, 20, 45, 0), "timezone": "Asia/Kolkata"}
        },
        expected=15,
        msg="$minute should return 15 for a Timestamp in Asia/Kolkata (+05:30) wrapping the hour",
    ),
    ExpressionTestCase(
        "tz_olson_ts_kathmandu_on_hour",
        expression={
            "$minute": {"date": ts_from_args(2024, 8, 31, 23, 0, 0), "timezone": "Asia/Kathmandu"}
        },
        expected=45,
        msg="$minute should return 45 for a Timestamp in Asia/Kathmandu (+05:45)",
    ),
    ExpressionTestCase(
        "tz_olson_ts_kathmandu_20",
        expression={
            "$minute": {"date": ts_from_args(2024, 6, 15, 23, 20, 0), "timezone": "Asia/Kathmandu"}
        },
        expected=5,
        msg="$minute should return 5 for a Timestamp in Asia/Kathmandu (+05:45) wrapping the hour",
    ),
    ExpressionTestCase(
        "tz_offset_ts_plus9",
        expression={
            "$minute": {"date": ts_from_args(2024, 7, 15, 12, 25, 0), "timezone": "+09:00"}
        },
        expected=25,
        msg="$minute should leave the minute at 25 for a Timestamp at a whole-hour +09:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_ts_plus530_on_hour",
        expression={"$minute": {"date": ts_from_args(2024, 3, 31, 20, 0, 0), "timezone": "+05:30"}},
        expected=30,
        msg="$minute should return 30 for a Timestamp at a +05:30 offset on the hour",
    ),
    ExpressionTestCase(
        "tz_offset_ts_plus530_wrap",
        expression={
            "$minute": {"date": ts_from_args(2024, 6, 15, 20, 45, 0), "timezone": "+05:30"}
        },
        expected=15,
        msg="$minute should return 15 for a Timestamp at a +05:30 offset wrapping the hour",
    ),
    ExpressionTestCase(
        "tz_offset_ts_plus545_on_hour",
        expression={"$minute": {"date": ts_from_args(2024, 8, 31, 23, 0, 0), "timezone": "+05:45"}},
        expected=45,
        msg="$minute should return 45 for a Timestamp at a +05:45 offset on the hour",
    ),
    ExpressionTestCase(
        "tz_offset_ts_minus930_on_hour",
        expression={"$minute": {"date": ts_from_args(2024, 6, 15, 12, 0, 0), "timezone": "-09:30"}},
        expected=30,
        msg="$minute should return 30 for a Timestamp at a -09:30 offset on the hour",
    ),
]

# Property [ObjectId Input with Zones]: an ObjectId input honours the zone offset,
# leaving whole-hour offsets unchanged and shifting fractional ones.
MINUTE_OBJECTID_ZONE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_olson_oid_utc",
        expression={"$minute": {"date": oid_from_args(2024, 7, 15, 12, 25, 0), "timezone": "UTC"}},
        expected=25,
        msg="$minute should return 25 for an ObjectId in UTC",
    ),
    ExpressionTestCase(
        "tz_olson_oid_tokyo",
        expression={
            "$minute": {"date": oid_from_args(2024, 7, 15, 12, 25, 0), "timezone": "Asia/Tokyo"}
        },
        expected=25,
        msg="$minute should leave the minute at 25 for an ObjectId in whole-hour Asia/Tokyo",
    ),
    ExpressionTestCase(
        "tz_olson_oid_kolkata_on_hour",
        expression={
            "$minute": {"date": oid_from_args(2024, 3, 31, 20, 0, 0), "timezone": "Asia/Kolkata"}
        },
        expected=30,
        msg="$minute should return 30 for an ObjectId in Asia/Kolkata (+05:30)",
    ),
    ExpressionTestCase(
        "tz_olson_oid_kolkata_45",
        expression={
            "$minute": {"date": oid_from_args(2024, 6, 15, 20, 45, 0), "timezone": "Asia/Kolkata"}
        },
        expected=15,
        msg="$minute should return 15 for an ObjectId in Asia/Kolkata (+05:30) wrapping the hour",
    ),
    ExpressionTestCase(
        "tz_olson_oid_kathmandu_on_hour",
        expression={
            "$minute": {"date": oid_from_args(2024, 8, 31, 23, 0, 0), "timezone": "Asia/Kathmandu"}
        },
        expected=45,
        msg="$minute should return 45 for an ObjectId in Asia/Kathmandu (+05:45)",
    ),
    ExpressionTestCase(
        "tz_offset_oid_plus9",
        expression={
            "$minute": {"date": oid_from_args(2024, 7, 15, 12, 25, 0), "timezone": "+09:00"}
        },
        expected=25,
        msg="$minute should leave the minute at 25 for an ObjectId at a whole-hour +09:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_oid_plus530_on_hour",
        expression={
            "$minute": {"date": oid_from_args(2024, 3, 31, 20, 0, 0), "timezone": "+05:30"}
        },
        expected=30,
        msg="$minute should return 30 for an ObjectId at a +05:30 offset on the hour",
    ),
    ExpressionTestCase(
        "tz_offset_oid_plus545_on_hour",
        expression={
            "$minute": {"date": oid_from_args(2024, 8, 31, 23, 0, 0), "timezone": "+05:45"}
        },
        expected=45,
        msg="$minute should return 45 for an ObjectId at a +05:45 offset on the hour",
    ),
    ExpressionTestCase(
        "tz_offset_oid_minus930_on_hour",
        expression={
            "$minute": {"date": oid_from_args(2024, 6, 15, 12, 0, 0), "timezone": "-09:30"}
        },
        expected=30,
        msg="$minute should return 30 for an ObjectId at a -09:30 offset on the hour",
    ),
]

MINUTE_TIMEZONE_INPUT_TYPES_TESTS: list[ExpressionTestCase] = (
    MINUTE_TIMESTAMP_ZONE_TESTS + MINUTE_OBJECTID_ZONE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(MINUTE_TIMEZONE_INPUT_TYPES_TESTS))
def test_minute_timezone_input_types(collection, test_case: ExpressionTestCase):
    """Test $minute timezone application for Timestamp and ObjectId date inputs."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
