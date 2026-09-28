"""Tests for $isoWeekYear timezone application when the date is a Timestamp or ObjectId."""

import pytest
from bson import Int64

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
# ISO week-numbering year is taken.
ISOWEEKYEAR_TIMESTAMP_ZONE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "ts_utc",
        doc={"date": ts_from_args(2024, 1, 1, 2, 0, 0)},
        expression={"$isoWeekYear": {"date": "$date", "timezone": "UTC"}},
        expected=Int64(2024),
        msg="$isoWeekYear should return 2024 for an early-Jan-1 Timestamp in UTC",
    ),
    ExpressionTestCase(
        "ts_minus5_cross",
        doc={"date": ts_from_args(2024, 1, 1, 2, 0, 0)},
        expression={"$isoWeekYear": {"date": "$date", "timezone": "-05:00"}},
        expected=Int64(2023),
        msg="$isoWeekYear should cross back to 2023 for a Timestamp at a -05:00 offset",
    ),
]

# Property [ObjectId Input with Zones]: an ObjectId input honours the zone offset before the
# ISO week-numbering year is taken.
ISOWEEKYEAR_OBJECTID_ZONE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "oid_utc",
        doc={"date": oid_from_args(2024, 1, 1, 2, 0, 0)},
        expression={"$isoWeekYear": {"date": "$date", "timezone": "UTC"}},
        expected=Int64(2024),
        msg="$isoWeekYear should return 2024 for an early-Jan-1 ObjectId in UTC",
    ),
    ExpressionTestCase(
        "oid_minus5_cross",
        doc={"date": oid_from_args(2024, 1, 1, 2, 0, 0)},
        expression={"$isoWeekYear": {"date": "$date", "timezone": "-05:00"}},
        expected=Int64(2023),
        msg="$isoWeekYear should cross back to 2023 for an ObjectId at a -05:00 offset",
    ),
]

ISOWEEKYEAR_TIMEZONE_INPUT_TYPES_TESTS: list[ExpressionTestCase] = (
    ISOWEEKYEAR_TIMESTAMP_ZONE_TESTS + ISOWEEKYEAR_OBJECTID_ZONE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(ISOWEEKYEAR_TIMEZONE_INPUT_TYPES_TESTS))
def test_isoWeekYear_timezone_input_types(collection, test_case: ExpressionTestCase):
    """Test $isoWeekYear timezone application for Timestamp and ObjectId date inputs."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
