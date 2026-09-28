"""Tests for $isoDayOfWeek timezone application when the date is a Timestamp or ObjectId."""

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

# Property [Timestamp Input with Zones]: a Timestamp input honours the zone offset before the
# ISO day is taken.
ISODAYOFWEEK_TIMESTAMP_ZONE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "ts_utc_no_cross",
        expression={
            "$isoDayOfWeek": {"date": ts_from_args(2024, 1, 15, 0, 0, 0), "timezone": "UTC"}
        },
        expected=1,
        msg="$isoDayOfWeek should return 1 for a Monday Timestamp in UTC with no crossing",
    ),
    ExpressionTestCase(
        "ts_minus5_bwd",
        expression={
            "$isoDayOfWeek": {"date": ts_from_args(2024, 1, 15, 0, 0, 0), "timezone": "-05:00"}
        },
        expected=7,
        msg="$isoDayOfWeek should cross backward to Sunday for a Timestamp at a -05:00 offset",
    ),
]

# Property [ObjectId Input with Zones]: an ObjectId input honours the zone offset before the
# ISO day is taken.
ISODAYOFWEEK_OBJECTID_ZONE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "oid_utc_no_cross",
        expression={
            "$isoDayOfWeek": {"date": oid_from_args(2024, 1, 15, 0, 0, 0), "timezone": "UTC"}
        },
        expected=1,
        msg="$isoDayOfWeek should return 1 for a Monday ObjectId in UTC with no crossing",
    ),
    ExpressionTestCase(
        "oid_minus5_bwd",
        expression={
            "$isoDayOfWeek": {"date": oid_from_args(2024, 1, 15, 0, 0, 0), "timezone": "-05:00"}
        },
        expected=7,
        msg="$isoDayOfWeek should cross backward to Sunday for an ObjectId at a -05:00 offset",
    ),
]

ISODAYOFWEEK_TIMEZONE_INPUT_TYPES_TESTS: list[ExpressionTestCase] = (
    ISODAYOFWEEK_TIMESTAMP_ZONE_TESTS + ISODAYOFWEEK_OBJECTID_ZONE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(ISODAYOFWEEK_TIMEZONE_INPUT_TYPES_TESTS))
def test_isoDayOfWeek_timezone_input_types(collection, test_case: ExpressionTestCase):
    """Test $isoDayOfWeek timezone application for Timestamp and ObjectId date inputs."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
