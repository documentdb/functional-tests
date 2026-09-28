"""Tests for $second timezone application when the date is a Timestamp or ObjectId."""

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

# Property [Timestamp Input with Zones]: a Timestamp input honours the zone for parsing but
# the second is unchanged, because every zone offset is a whole number of minutes.
SECOND_TIMESTAMP_ZONE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_olson_ts_utc",
        expression={"$second": {"date": ts_from_args(2024, 7, 15, 12, 25, 37), "timezone": "UTC"}},
        expected=37,
        msg="$second should return 37 for a Timestamp in UTC",
    ),
    ExpressionTestCase(
        "tz_olson_ts_tokyo",
        expression={
            "$second": {"date": ts_from_args(2024, 7, 15, 12, 25, 37), "timezone": "Asia/Tokyo"}
        },
        expected=37,
        msg="$second should leave the second at 37 for a Timestamp in Asia/Tokyo",
    ),
    ExpressionTestCase(
        "tz_olson_ts_kolkata",
        expression={
            "$second": {"date": ts_from_args(2024, 3, 31, 20, 0, 37), "timezone": "Asia/Kolkata"}
        },
        expected=37,
        msg="$second should leave the second at 37 for a Timestamp in Asia/Kolkata (+05:30)",
    ),
    ExpressionTestCase(
        "tz_olson_ts_kathmandu",
        expression={
            "$second": {"date": ts_from_args(2024, 8, 31, 23, 0, 37), "timezone": "Asia/Kathmandu"}
        },
        expected=37,
        msg="$second should leave the second at 37 for a Timestamp in Asia/Kathmandu (+05:45)",
    ),
    ExpressionTestCase(
        "tz_offset_ts_plus9",
        expression={
            "$second": {"date": ts_from_args(2024, 7, 15, 12, 25, 37), "timezone": "+09:00"}
        },
        expected=37,
        msg="$second should leave the second at 37 for a Timestamp at a +09:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_ts_plus530",
        expression={
            "$second": {"date": ts_from_args(2024, 3, 31, 20, 0, 37), "timezone": "+05:30"}
        },
        expected=37,
        msg="$second should leave the second at 37 for a Timestamp at a +05:30 offset",
    ),
    ExpressionTestCase(
        "tz_offset_ts_plus545",
        expression={
            "$second": {"date": ts_from_args(2024, 8, 31, 23, 0, 37), "timezone": "+05:45"}
        },
        expected=37,
        msg="$second should leave the second at 37 for a Timestamp at a +05:45 offset",
    ),
    ExpressionTestCase(
        "tz_offset_ts_minus930",
        expression={
            "$second": {"date": ts_from_args(2024, 6, 15, 12, 0, 37), "timezone": "-09:30"}
        },
        expected=37,
        msg="$second should leave the second at 37 for a Timestamp at a -09:30 offset",
    ),
]

# Property [ObjectId Input with Zones]: an ObjectId input honours the zone for parsing but
# the second is unchanged, because every zone offset is a whole number of minutes.
SECOND_OBJECTID_ZONE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_olson_oid_utc",
        expression={"$second": {"date": oid_from_args(2024, 7, 15, 12, 25, 37), "timezone": "UTC"}},
        expected=37,
        msg="$second should return 37 for an ObjectId in UTC",
    ),
    ExpressionTestCase(
        "tz_olson_oid_tokyo",
        expression={
            "$second": {"date": oid_from_args(2024, 7, 15, 12, 25, 37), "timezone": "Asia/Tokyo"}
        },
        expected=37,
        msg="$second should leave the second at 37 for an ObjectId in Asia/Tokyo",
    ),
    ExpressionTestCase(
        "tz_olson_oid_kolkata",
        expression={
            "$second": {"date": oid_from_args(2024, 3, 31, 20, 0, 37), "timezone": "Asia/Kolkata"}
        },
        expected=37,
        msg="$second should leave the second at 37 for an ObjectId in Asia/Kolkata (+05:30)",
    ),
    ExpressionTestCase(
        "tz_olson_oid_kathmandu",
        expression={
            "$second": {"date": oid_from_args(2024, 8, 31, 23, 0, 37), "timezone": "Asia/Kathmandu"}
        },
        expected=37,
        msg="$second should leave the second at 37 for an ObjectId in Asia/Kathmandu (+05:45)",
    ),
    ExpressionTestCase(
        "tz_offset_oid_plus9",
        expression={
            "$second": {"date": oid_from_args(2024, 7, 15, 12, 25, 37), "timezone": "+09:00"}
        },
        expected=37,
        msg="$second should leave the second at 37 for an ObjectId at a +09:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_oid_plus530",
        expression={
            "$second": {"date": oid_from_args(2024, 3, 31, 20, 0, 37), "timezone": "+05:30"}
        },
        expected=37,
        msg="$second should leave the second at 37 for an ObjectId at a +05:30 offset",
    ),
    ExpressionTestCase(
        "tz_offset_oid_plus545",
        expression={
            "$second": {"date": oid_from_args(2024, 8, 31, 23, 0, 37), "timezone": "+05:45"}
        },
        expected=37,
        msg="$second should leave the second at 37 for an ObjectId at a +05:45 offset",
    ),
    ExpressionTestCase(
        "tz_offset_oid_minus930",
        expression={
            "$second": {"date": oid_from_args(2024, 6, 15, 12, 0, 37), "timezone": "-09:30"}
        },
        expected=37,
        msg="$second should leave the second at 37 for an ObjectId at a -09:30 offset",
    ),
]

SECOND_TIMEZONE_INPUT_TYPES_TESTS: list[ExpressionTestCase] = (
    SECOND_TIMESTAMP_ZONE_TESTS + SECOND_OBJECTID_ZONE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SECOND_TIMEZONE_INPUT_TYPES_TESTS))
def test_second_timezone_input_types(collection, test_case: ExpressionTestCase):
    """Test $second timezone application for Timestamp and ObjectId date inputs."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
