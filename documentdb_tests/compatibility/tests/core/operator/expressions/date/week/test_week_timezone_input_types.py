"""Tests for $week timezone application when the date is a Timestamp or ObjectId."""

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

# Property [Timestamp Input with Zones]: a Timestamp input honours the named zone or offset
# before the week is taken, which may cross a week or year boundary.
WEEK_TIMESTAMP_ZONE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "ts_utc_no_cross",
        doc={"date": ts_from_args(2024, 7, 15, 12, 0, 0)},
        expression={"$week": {"date": "$date", "timezone": "UTC"}},
        expected=28,
        msg="$week should return 28 for a mid-2024 Timestamp in UTC",
    ),
    ExpressionTestCase(
        "ts_tokyo_week_fwd",
        doc={"date": ts_from_args(2024, 1, 6, 22, 0, 0)},
        expression={"$week": {"date": "$date", "timezone": "Asia/Tokyo"}},
        expected=1,
        msg="$week should cross forward to week 1 for a Timestamp in Asia/Tokyo",
    ),
    ExpressionTestCase(
        "ts_la_week_bwd",
        doc={"date": ts_from_args(2024, 1, 7, 3, 0, 0)},
        expression={"$week": {"date": "$date", "timezone": "America/Los_Angeles"}},
        expected=0,
        msg="$week should cross back to week 0 for a Timestamp in America/Los_Angeles",
    ),
    ExpressionTestCase(
        "ts_ny_year_bwd",
        doc={"date": ts_from_args(2024, 1, 1, 3, 0, 0)},
        expression={"$week": {"date": "$date", "timezone": "America/New_York"}},
        expected=53,
        msg="$week should cross back into week 53 for a Timestamp in America/New_York on Jan 1",
    ),
    ExpressionTestCase(
        "ts_helsinki_year_fwd",
        doc={"date": ts_from_args(2024, 12, 31, 23, 0, 0)},
        expression={"$week": {"date": "$date", "timezone": "Europe/Helsinki"}},
        expected=0,
        msg="$week should cross forward into week 0 for a Timestamp in Europe/Helsinki",
    ),
    ExpressionTestCase(
        "ts_offset_plus9_week_fwd",
        doc={"date": ts_from_args(2024, 1, 6, 22, 0, 0)},
        expression={"$week": {"date": "$date", "timezone": "+09:00"}},
        expected=1,
        msg="$week should cross forward to week 1 for a Timestamp at a +09:00 offset",
    ),
    ExpressionTestCase(
        "ts_offset_minus8_week_bwd",
        doc={"date": ts_from_args(2024, 1, 7, 3, 0, 0)},
        expression={"$week": {"date": "$date", "timezone": "-08:00"}},
        expected=0,
        msg="$week should cross back to week 0 for a Timestamp at a -08:00 offset",
    ),
    ExpressionTestCase(
        "ts_offset_minus5_year_bwd",
        doc={"date": ts_from_args(2024, 1, 1, 3, 0, 0)},
        expression={"$week": {"date": "$date", "timezone": "-05:00"}},
        expected=53,
        msg="$week should cross back into week 53 for a Timestamp at a -05:00 offset",
    ),
    ExpressionTestCase(
        "ts_offset_plus530_week_fwd",
        doc={"date": ts_from_args(2024, 1, 6, 20, 0, 0)},
        expression={"$week": {"date": "$date", "timezone": "+05:30"}},
        expected=1,
        msg="$week should cross forward to week 1 for a Timestamp at a +05:30 offset",
    ),
]

# Property [ObjectId Input with Zones]: an ObjectId input honours the named zone or offset
# before the week is taken, which may cross a week or year boundary.
WEEK_OBJECTID_ZONE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "oid_utc_no_cross",
        doc={"date": oid_from_args(2024, 7, 15, 12, 0, 0)},
        expression={"$week": {"date": "$date", "timezone": "UTC"}},
        expected=28,
        msg="$week should return 28 for a mid-2024 ObjectId in UTC",
    ),
    ExpressionTestCase(
        "oid_tokyo_week_fwd",
        doc={"date": oid_from_args(2024, 1, 6, 22, 0, 0)},
        expression={"$week": {"date": "$date", "timezone": "Asia/Tokyo"}},
        expected=1,
        msg="$week should cross forward to week 1 for an ObjectId in Asia/Tokyo",
    ),
    ExpressionTestCase(
        "oid_la_week_bwd",
        doc={"date": oid_from_args(2024, 1, 7, 3, 0, 0)},
        expression={"$week": {"date": "$date", "timezone": "America/Los_Angeles"}},
        expected=0,
        msg="$week should cross back to week 0 for an ObjectId in America/Los_Angeles",
    ),
    ExpressionTestCase(
        "oid_ny_year_bwd",
        doc={"date": oid_from_args(2024, 1, 1, 3, 0, 0)},
        expression={"$week": {"date": "$date", "timezone": "America/New_York"}},
        expected=53,
        msg="$week should cross back into week 53 for an ObjectId in America/New_York on Jan 1",
    ),
    ExpressionTestCase(
        "oid_helsinki_year_fwd",
        doc={"date": oid_from_args(2024, 12, 31, 23, 0, 0)},
        expression={"$week": {"date": "$date", "timezone": "Europe/Helsinki"}},
        expected=0,
        msg="$week should cross forward into week 0 for an ObjectId in Europe/Helsinki",
    ),
    ExpressionTestCase(
        "oid_offset_plus9_week_fwd",
        doc={"date": oid_from_args(2024, 1, 6, 22, 0, 0)},
        expression={"$week": {"date": "$date", "timezone": "+09:00"}},
        expected=1,
        msg="$week should cross forward to week 1 for an ObjectId at a +09:00 offset",
    ),
    ExpressionTestCase(
        "oid_offset_minus8_week_bwd",
        doc={"date": oid_from_args(2024, 1, 7, 3, 0, 0)},
        expression={"$week": {"date": "$date", "timezone": "-08:00"}},
        expected=0,
        msg="$week should cross back to week 0 for an ObjectId at a -08:00 offset",
    ),
    ExpressionTestCase(
        "oid_offset_minus5_year_bwd",
        doc={"date": oid_from_args(2024, 1, 1, 3, 0, 0)},
        expression={"$week": {"date": "$date", "timezone": "-05:00"}},
        expected=53,
        msg="$week should cross back into week 53 for an ObjectId at a -05:00 offset",
    ),
    ExpressionTestCase(
        "oid_offset_plus530_week_fwd",
        doc={"date": oid_from_args(2024, 1, 6, 20, 0, 0)},
        expression={"$week": {"date": "$date", "timezone": "+05:30"}},
        expected=1,
        msg="$week should cross forward to week 1 for an ObjectId at a +05:30 offset",
    ),
]

WEEK_TIMEZONE_INPUT_TYPES_TESTS: list[ExpressionTestCase] = (
    WEEK_TIMESTAMP_ZONE_TESTS + WEEK_OBJECTID_ZONE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(WEEK_TIMEZONE_INPUT_TYPES_TESTS))
def test_week_timezone_input_types(collection, test_case: ExpressionTestCase):
    """Test $week timezone application for Timestamp and ObjectId date inputs."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
