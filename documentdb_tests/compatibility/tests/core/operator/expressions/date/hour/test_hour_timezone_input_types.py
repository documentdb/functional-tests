"""Tests for $hour timezone application when the date is a Timestamp or ObjectId."""

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

# Property [Timestamp Input with Zones]: a Timestamp input honours the zone offset.
HOUR_TIMESTAMP_ZONE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_olson_ts_utc",
        expression={"$hour": {"date": ts_from_args(2024, 7, 15, 12, 0, 0), "timezone": "UTC"}},
        expected=12,
        msg="$hour should return 12 for a Timestamp in UTC with no wrap",
    ),
    ExpressionTestCase(
        "tz_olson_ts_tokyo_fwd",
        expression={
            "$hour": {"date": ts_from_args(2024, 6, 30, 22, 0, 0), "timezone": "Asia/Tokyo"}
        },
        expected=7,
        msg="$hour should wrap forward to 7 for a Timestamp in Asia/Tokyo",
    ),
    ExpressionTestCase(
        "tz_olson_ts_la_bwd",
        expression={
            "$hour": {
                "date": ts_from_args(2024, 7, 1, 3, 0, 0),
                "timezone": "America/Los_Angeles",
            }
        },
        expected=20,
        msg="$hour should wrap backward to 20 for a Timestamp in America/Los_Angeles",
    ),
    ExpressionTestCase(
        "tz_olson_ts_kolkata_half",
        expression={
            "$hour": {"date": ts_from_args(2024, 3, 31, 20, 0, 0), "timezone": "Asia/Kolkata"}
        },
        expected=1,
        msg="$hour should return 1 for a Timestamp in Asia/Kolkata (+05:30)",
    ),
    ExpressionTestCase(
        "tz_olson_ts_ny_year_bwd",
        expression={
            "$hour": {"date": ts_from_args(2024, 1, 1, 3, 0, 0), "timezone": "America/New_York"}
        },
        expected=22,
        msg="$hour should wrap backward across the year boundary for a Timestamp in New York",
    ),
    ExpressionTestCase(
        "tz_olson_ts_helsinki_year_fwd",
        expression={
            "$hour": {"date": ts_from_args(2024, 12, 31, 23, 0, 0), "timezone": "Europe/Helsinki"}
        },
        expected=1,
        msg="$hour should wrap forward across the year boundary for a Timestamp in Europe/Helsinki",
    ),
    ExpressionTestCase(
        "tz_offset_ts_plus9_fwd",
        expression={"$hour": {"date": ts_from_args(2024, 6, 30, 22, 0, 0), "timezone": "+09:00"}},
        expected=7,
        msg="$hour should wrap forward to 7 for a Timestamp at a +09:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_ts_minus8_bwd",
        expression={"$hour": {"date": ts_from_args(2024, 7, 1, 3, 0, 0), "timezone": "-08:00"}},
        expected=19,
        msg="$hour should wrap backward to 19 for a Timestamp at a -08:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_ts_plus530_fwd",
        expression={"$hour": {"date": ts_from_args(2024, 3, 31, 20, 0, 0), "timezone": "+05:30"}},
        expected=1,
        msg="$hour should return 1 for a Timestamp at a +05:30 offset",
    ),
    ExpressionTestCase(
        "tz_offset_ts_plus545_fwd",
        expression={"$hour": {"date": ts_from_args(2024, 8, 31, 23, 0, 0), "timezone": "+05:45"}},
        expected=4,
        msg="$hour should return 4 for a Timestamp at a +05:45 offset",
    ),
    ExpressionTestCase(
        "tz_offset_ts_plus3_leap_fwd",
        expression={"$hour": {"date": ts_from_args(2024, 2, 29, 23, 30, 0), "timezone": "+03:00"}},
        expected=2,
        msg="$hour should wrap forward across the leap-day boundary for a Timestamp at +03:00",
    ),
]

# Property [ObjectId Input with Zones]: an ObjectId input honours the zone offset.
HOUR_OBJECTID_ZONE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_olson_oid_utc",
        expression={"$hour": {"date": oid_from_args(2024, 7, 15, 12, 0, 0), "timezone": "UTC"}},
        expected=12,
        msg="$hour should return 12 for an ObjectId in UTC with no wrap",
    ),
    ExpressionTestCase(
        "tz_olson_oid_tokyo_fwd",
        expression={
            "$hour": {"date": oid_from_args(2024, 6, 30, 22, 0, 0), "timezone": "Asia/Tokyo"}
        },
        expected=7,
        msg="$hour should wrap forward to 7 for an ObjectId in Asia/Tokyo",
    ),
    ExpressionTestCase(
        "tz_olson_oid_la_bwd",
        expression={
            "$hour": {
                "date": oid_from_args(2024, 7, 1, 3, 0, 0),
                "timezone": "America/Los_Angeles",
            }
        },
        expected=20,
        msg="$hour should wrap backward to 20 for an ObjectId in America/Los_Angeles",
    ),
    ExpressionTestCase(
        "tz_olson_oid_kolkata_half",
        expression={
            "$hour": {"date": oid_from_args(2024, 3, 31, 20, 0, 0), "timezone": "Asia/Kolkata"}
        },
        expected=1,
        msg="$hour should return 1 for an ObjectId in Asia/Kolkata (+05:30)",
    ),
    ExpressionTestCase(
        "tz_olson_oid_ny_year_bwd",
        expression={
            "$hour": {"date": oid_from_args(2024, 1, 1, 3, 0, 0), "timezone": "America/New_York"}
        },
        expected=22,
        msg="$hour should wrap backward across the year boundary for an ObjectId in New York",
    ),
    ExpressionTestCase(
        "tz_olson_oid_helsinki_year_fwd",
        expression={
            "$hour": {"date": oid_from_args(2024, 12, 31, 23, 0, 0), "timezone": "Europe/Helsinki"}
        },
        expected=1,
        msg="$hour should wrap forward across the year boundary for an ObjectId in Europe/Helsinki",
    ),
    ExpressionTestCase(
        "tz_offset_oid_plus9_fwd",
        expression={"$hour": {"date": oid_from_args(2024, 6, 30, 22, 0, 0), "timezone": "+09:00"}},
        expected=7,
        msg="$hour should wrap forward to 7 for an ObjectId at a +09:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_oid_minus8_bwd",
        expression={"$hour": {"date": oid_from_args(2024, 7, 1, 3, 0, 0), "timezone": "-08:00"}},
        expected=19,
        msg="$hour should wrap backward to 19 for an ObjectId at a -08:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_oid_plus530_fwd",
        expression={"$hour": {"date": oid_from_args(2024, 3, 31, 20, 0, 0), "timezone": "+05:30"}},
        expected=1,
        msg="$hour should return 1 for an ObjectId at a +05:30 offset",
    ),
    ExpressionTestCase(
        "tz_offset_oid_plus3_leap_fwd",
        expression={"$hour": {"date": oid_from_args(2024, 2, 29, 23, 30, 0), "timezone": "+03:00"}},
        expected=2,
        msg="$hour should wrap forward across the leap-day boundary for an ObjectId at +03:00",
    ),
]

HOUR_TIMEZONE_INPUT_TYPES_TESTS: list[ExpressionTestCase] = (
    HOUR_TIMESTAMP_ZONE_TESTS + HOUR_OBJECTID_ZONE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(HOUR_TIMEZONE_INPUT_TYPES_TESTS))
def test_hour_timezone_input_types(collection, test_case: ExpressionTestCase):
    """Test $hour timezone application for Timestamp and ObjectId date inputs."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
