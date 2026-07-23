"""Tests for $isoWeek timezone application when the date is a Timestamp or ObjectId."""

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
# ISO week is taken.
ISOWEEK_TIMESTAMP_ZONE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "ts_utc",
        doc={"date": ts_from_args(2024, 1, 15, 0, 0, 0)},
        expression={"$isoWeek": {"date": "$date", "timezone": "UTC"}},
        expected=3,
        msg="$isoWeek should return 3 for a mid-January Timestamp in UTC",
    ),
    ExpressionTestCase(
        "ts_minus5_bwd",
        doc={"date": ts_from_args(2024, 1, 15, 0, 0, 0)},
        expression={"$isoWeek": {"date": "$date", "timezone": "-05:00"}},
        expected=2,
        msg="$isoWeek should cross back to week 2 for a Timestamp at a -05:00 offset",
    ),
]

# Property [ObjectId Input with Zones]: an ObjectId input honours the zone offset before the
# ISO week is taken.
ISOWEEK_OBJECTID_ZONE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "oid_utc",
        doc={"date": oid_from_args(2024, 1, 15, 0, 0, 0)},
        expression={"$isoWeek": {"date": "$date", "timezone": "UTC"}},
        expected=3,
        msg="$isoWeek should return 3 for a mid-January ObjectId in UTC",
    ),
    ExpressionTestCase(
        "oid_minus5_bwd",
        doc={"date": oid_from_args(2024, 1, 15, 0, 0, 0)},
        expression={"$isoWeek": {"date": "$date", "timezone": "-05:00"}},
        expected=2,
        msg="$isoWeek should cross back to week 2 for an ObjectId at a -05:00 offset",
    ),
]

ISOWEEK_TIMEZONE_INPUT_TYPES_TESTS: list[ExpressionTestCase] = (
    ISOWEEK_TIMESTAMP_ZONE_TESTS + ISOWEEK_OBJECTID_ZONE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(ISOWEEK_TIMEZONE_INPUT_TYPES_TESTS))
def test_isoWeek_timezone_input_types(collection, test_case: ExpressionTestCase):
    """Test $isoWeek timezone application for Timestamp and ObjectId date inputs."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
