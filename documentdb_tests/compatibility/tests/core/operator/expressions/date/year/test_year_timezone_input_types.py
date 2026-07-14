"""Tests for $year timezone application when the date is a Timestamp or ObjectId."""

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
# before the calendar year is taken, which may cross a year boundary.
YEAR_TIMESTAMP_ZONE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "ts_utc_no_cross",
        doc={"date": ts_from_args(2024, 7, 15, 12, 0, 0)},
        expression={"$year": {"date": "$date", "timezone": "UTC"}},
        expected=2024,
        msg="$year should return 2024 for a mid-2024 Timestamp in UTC",
    ),
    ExpressionTestCase(
        "ts_ny_year_bwd",
        doc={"date": ts_from_args(2024, 1, 1, 3, 0, 0)},
        expression={"$year": {"date": "$date", "timezone": "America/New_York"}},
        expected=2023,
        msg="$year should cross back to 2023 for a Timestamp in America/New_York early on Jan 1",
    ),
    ExpressionTestCase(
        "ts_helsinki_year_fwd",
        doc={"date": ts_from_args(2024, 12, 31, 23, 0, 0)},
        expression={"$year": {"date": "$date", "timezone": "Europe/Helsinki"}},
        expected=2025,
        msg="$year should cross forward to 2025 for a Timestamp in Europe/Helsinki late on Dec 31",
    ),
    ExpressionTestCase(
        "ts_kolkata_year_fwd",
        doc={"date": ts_from_args(2024, 12, 31, 22, 0, 0)},
        expression={"$year": {"date": "$date", "timezone": "Asia/Kolkata"}},
        expected=2025,
        msg="$year should cross forward to 2025 for a Timestamp at the Asia/Kolkata offset",
    ),
    ExpressionTestCase(
        "ts_offset_minus5_year_bwd",
        doc={"date": ts_from_args(2024, 1, 1, 3, 0, 0)},
        expression={"$year": {"date": "$date", "timezone": "-05:00"}},
        expected=2023,
        msg="$year should cross back to 2023 for a Timestamp at a -05:00 offset",
    ),
    ExpressionTestCase(
        "ts_offset_plus2_year_fwd",
        doc={"date": ts_from_args(2024, 12, 31, 23, 0, 0)},
        expression={"$year": {"date": "$date", "timezone": "+02:00"}},
        expected=2025,
        msg="$year should cross forward to 2025 for a Timestamp at a +02:00 offset",
    ),
    ExpressionTestCase(
        "ts_offset_plus530_year_fwd",
        doc={"date": ts_from_args(2024, 12, 31, 22, 0, 0)},
        expression={"$year": {"date": "$date", "timezone": "+05:30"}},
        expected=2025,
        msg="$year should cross forward to 2025 for a Timestamp at a +05:30 offset",
    ),
]

# Property [ObjectId Input with Zones]: an ObjectId input honours the named zone or offset
# before the calendar year is taken, which may cross a year boundary.
YEAR_OBJECTID_ZONE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "oid_utc_no_cross",
        doc={"date": oid_from_args(2024, 7, 15, 12, 0, 0)},
        expression={"$year": {"date": "$date", "timezone": "UTC"}},
        expected=2024,
        msg="$year should return 2024 for a mid-2024 ObjectId in UTC",
    ),
    ExpressionTestCase(
        "oid_ny_year_bwd",
        doc={"date": oid_from_args(2024, 1, 1, 3, 0, 0)},
        expression={"$year": {"date": "$date", "timezone": "America/New_York"}},
        expected=2023,
        msg="$year should cross back to 2023 for an ObjectId in America/New_York early on Jan 1",
    ),
    ExpressionTestCase(
        "oid_helsinki_year_fwd",
        doc={"date": oid_from_args(2024, 12, 31, 23, 0, 0)},
        expression={"$year": {"date": "$date", "timezone": "Europe/Helsinki"}},
        expected=2025,
        msg="$year should cross forward to 2025 for an ObjectId in Europe/Helsinki late on Dec 31",
    ),
    ExpressionTestCase(
        "oid_kolkata_year_fwd",
        doc={"date": oid_from_args(2024, 12, 31, 22, 0, 0)},
        expression={"$year": {"date": "$date", "timezone": "Asia/Kolkata"}},
        expected=2025,
        msg="$year should cross forward to 2025 for an ObjectId at the Asia/Kolkata offset",
    ),
    ExpressionTestCase(
        "oid_offset_minus5_year_bwd",
        doc={"date": oid_from_args(2024, 1, 1, 3, 0, 0)},
        expression={"$year": {"date": "$date", "timezone": "-05:00"}},
        expected=2023,
        msg="$year should cross back to 2023 for an ObjectId at a -05:00 offset",
    ),
    ExpressionTestCase(
        "oid_offset_plus2_year_fwd",
        doc={"date": oid_from_args(2024, 12, 31, 23, 0, 0)},
        expression={"$year": {"date": "$date", "timezone": "+02:00"}},
        expected=2025,
        msg="$year should cross forward to 2025 for an ObjectId at a +02:00 offset",
    ),
    ExpressionTestCase(
        "oid_offset_plus530_year_fwd",
        doc={"date": oid_from_args(2024, 12, 31, 22, 0, 0)},
        expression={"$year": {"date": "$date", "timezone": "+05:30"}},
        expected=2025,
        msg="$year should cross forward to 2025 for an ObjectId at a +05:30 offset",
    ),
]

YEAR_TIMEZONE_INPUT_TYPES_TESTS: list[ExpressionTestCase] = (
    YEAR_TIMESTAMP_ZONE_TESTS + YEAR_OBJECTID_ZONE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(YEAR_TIMEZONE_INPUT_TYPES_TESTS))
def test_year_timezone_input_types(collection, test_case: ExpressionTestCase):
    """Test $year timezone application for Timestamp and ObjectId date inputs."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
