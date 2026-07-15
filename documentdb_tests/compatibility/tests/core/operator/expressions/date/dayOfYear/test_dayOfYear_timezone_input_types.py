"""Tests for $dayOfYear timezone application when the date is a Timestamp or ObjectId."""

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
DAYOFYEAR_TIMESTAMP_ZONE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_olson_ts_utc_no_cross",
        expression={"$dayOfYear": {"date": ts_from_args(2024, 7, 15, 12, 0, 0), "timezone": "UTC"}},
        expected=197,
        msg="$dayOfYear should return the same ordinal day for a Timestamp in UTC with no crossing",
    ),
    ExpressionTestCase(
        "tz_olson_ts_tokyo_fwd",
        expression={
            "$dayOfYear": {"date": ts_from_args(2024, 6, 30, 22, 0, 0), "timezone": "Asia/Tokyo"}
        },
        expected=183,
        msg="$dayOfYear should cross forward to day 183 for a Timestamp in Asia/Tokyo",
    ),
    ExpressionTestCase(
        "tz_olson_ts_la_bwd",
        expression={
            "$dayOfYear": {
                "date": ts_from_args(2024, 7, 1, 3, 0, 0),
                "timezone": "America/Los_Angeles",
            }
        },
        expected=182,
        msg="$dayOfYear should cross backward to day 182 for a Timestamp in America/Los_Angeles",
    ),
    ExpressionTestCase(
        "tz_olson_ts_kolkata_fwd",
        expression={
            "$dayOfYear": {"date": ts_from_args(2024, 3, 31, 20, 0, 0), "timezone": "Asia/Kolkata"}
        },
        expected=92,
        msg="$dayOfYear should cross forward to day 92 for a Timestamp in Asia/Kolkata",
    ),
    ExpressionTestCase(
        "tz_olson_ts_ny_year_bwd",
        expression={
            "$dayOfYear": {
                "date": ts_from_args(2024, 1, 1, 3, 0, 0),
                "timezone": "America/New_York",
            }
        },
        expected=365,
        msg="$dayOfYear should cross the year boundary backward for a Timestamp in New York",
    ),
    ExpressionTestCase(
        "tz_olson_ts_helsinki_year_fwd",
        expression={
            "$dayOfYear": {
                "date": ts_from_args(2024, 12, 31, 23, 0, 0),
                "timezone": "Europe/Helsinki",
            }
        },
        expected=1,
        msg="$dayOfYear should cross the year boundary forward for a Timestamp in Europe/Helsinki",
    ),
    ExpressionTestCase(
        "tz_offset_ts_plus9_fwd",
        expression={
            "$dayOfYear": {"date": ts_from_args(2024, 6, 30, 22, 0, 0), "timezone": "+09:00"}
        },
        expected=183,
        msg="$dayOfYear should cross forward to day 183 for a Timestamp at a +09:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_ts_minus8_bwd",
        expression={
            "$dayOfYear": {"date": ts_from_args(2024, 7, 1, 3, 0, 0), "timezone": "-08:00"}
        },
        expected=182,
        msg="$dayOfYear should cross backward to day 182 for a Timestamp at a -08:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_ts_plus530_fwd",
        expression={
            "$dayOfYear": {"date": ts_from_args(2024, 3, 31, 20, 0, 0), "timezone": "+05:30"}
        },
        expected=92,
        msg="$dayOfYear should cross forward to day 92 for a Timestamp at a +05:30 offset",
    ),
    ExpressionTestCase(
        "tz_offset_ts_plus545_fwd",
        expression={
            "$dayOfYear": {"date": ts_from_args(2024, 8, 31, 23, 0, 0), "timezone": "+05:45"}
        },
        expected=245,
        msg="$dayOfYear should cross forward to day 245 for a Timestamp at a +05:45 offset",
    ),
    ExpressionTestCase(
        "tz_offset_ts_plus3_leap_fwd",
        expression={
            "$dayOfYear": {"date": ts_from_args(2024, 2, 29, 23, 30, 0), "timezone": "+03:00"}
        },
        expected=61,
        msg="$dayOfYear should cross the leap-day boundary forward for a Timestamp at +03:00",
    ),
]

# Property [ObjectId Input with Zones]: an ObjectId input honours the zone offset.
DAYOFYEAR_OBJECTID_ZONE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_olson_oid_utc_no_cross",
        expression={
            "$dayOfYear": {"date": oid_from_args(2024, 7, 15, 12, 0, 0), "timezone": "UTC"}
        },
        expected=197,
        msg="$dayOfYear should return the same ordinal day for an ObjectId in UTC with no crossing",
    ),
    ExpressionTestCase(
        "tz_olson_oid_tokyo_fwd",
        expression={
            "$dayOfYear": {"date": oid_from_args(2024, 6, 30, 22, 0, 0), "timezone": "Asia/Tokyo"}
        },
        expected=183,
        msg="$dayOfYear should cross forward to day 183 for an ObjectId in Asia/Tokyo",
    ),
    ExpressionTestCase(
        "tz_olson_oid_la_bwd",
        expression={
            "$dayOfYear": {
                "date": oid_from_args(2024, 7, 1, 3, 0, 0),
                "timezone": "America/Los_Angeles",
            }
        },
        expected=182,
        msg="$dayOfYear should cross backward to day 182 for an ObjectId in America/Los_Angeles",
    ),
    ExpressionTestCase(
        "tz_olson_oid_kolkata_fwd",
        expression={
            "$dayOfYear": {
                "date": oid_from_args(2024, 3, 31, 20, 0, 0),
                "timezone": "Asia/Kolkata",
            }
        },
        expected=92,
        msg="$dayOfYear should cross forward to day 92 for an ObjectId in Asia/Kolkata",
    ),
    ExpressionTestCase(
        "tz_olson_oid_ny_year_bwd",
        expression={
            "$dayOfYear": {
                "date": oid_from_args(2024, 1, 1, 3, 0, 0),
                "timezone": "America/New_York",
            }
        },
        expected=365,
        msg="$dayOfYear should cross the year boundary backward for an ObjectId in New York",
    ),
    ExpressionTestCase(
        "tz_olson_oid_helsinki_year_fwd",
        expression={
            "$dayOfYear": {
                "date": oid_from_args(2024, 12, 31, 23, 0, 0),
                "timezone": "Europe/Helsinki",
            }
        },
        expected=1,
        msg="$dayOfYear should cross the year boundary forward for an ObjectId in Europe/Helsinki",
    ),
    ExpressionTestCase(
        "tz_offset_oid_plus9_fwd",
        expression={
            "$dayOfYear": {"date": oid_from_args(2024, 6, 30, 22, 0, 0), "timezone": "+09:00"}
        },
        expected=183,
        msg="$dayOfYear should cross forward to day 183 for an ObjectId at a +09:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_oid_minus8_bwd",
        expression={
            "$dayOfYear": {"date": oid_from_args(2024, 7, 1, 3, 0, 0), "timezone": "-08:00"}
        },
        expected=182,
        msg="$dayOfYear should cross backward to day 182 for an ObjectId at a -08:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_oid_plus530_fwd",
        expression={
            "$dayOfYear": {"date": oid_from_args(2024, 3, 31, 20, 0, 0), "timezone": "+05:30"}
        },
        expected=92,
        msg="$dayOfYear should cross forward to day 92 for an ObjectId at a +05:30 offset",
    ),
    ExpressionTestCase(
        "tz_offset_oid_plus3_leap_fwd",
        expression={
            "$dayOfYear": {"date": oid_from_args(2024, 2, 29, 23, 30, 0), "timezone": "+03:00"}
        },
        expected=61,
        msg="$dayOfYear should cross the leap-day boundary forward for an ObjectId at +03:00",
    ),
]

DAYOFYEAR_TIMEZONE_INPUT_TYPES_TESTS: list[ExpressionTestCase] = (
    DAYOFYEAR_TIMESTAMP_ZONE_TESTS + DAYOFYEAR_OBJECTID_ZONE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DAYOFYEAR_TIMEZONE_INPUT_TYPES_TESTS))
def test_dayOfYear_timezone_input_types(collection, test_case: ExpressionTestCase):
    """Test $dayOfYear timezone application for Timestamp and ObjectId date inputs."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
