"""Tests for $year UTC-offset timezone application, including compact and unusual offsets."""

from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [UTC Offsets]: an explicit +HH:MM/-HH:MM offset shifts the instant before the
# calendar year is taken, including compact, hour-only, half-hour, extreme, and out-of-range
# offsets the server still accepts, and offsets that cross a year boundary.
YEAR_OFFSET_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_offset_zero_no_cross",
        doc={"date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": {"date": "$date", "timezone": "+00:00"}},
        expected=2024,
        msg="$year should accept a +00:00 offset with no year crossing",
    ),
    ExpressionTestCase(
        "tz_offset_minus5_no_cross",
        doc={"date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": {"date": "$date", "timezone": "-05:00"}},
        expected=2024,
        msg="$year should accept a -05:00 offset with no year crossing",
    ),
    ExpressionTestCase(
        "tz_offset_minus5_year_bwd",
        doc={"date": datetime(2024, 1, 1, 3, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": {"date": "$date", "timezone": "-05:00"}},
        expected=2023,
        msg="$year should cross back to 2023 for a -05:00 offset early on Jan 1",
    ),
    ExpressionTestCase(
        "tz_offset_plus2_year_fwd",
        doc={"date": datetime(2024, 12, 31, 23, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": {"date": "$date", "timezone": "+02:00"}},
        expected=2025,
        msg="$year should cross forward to 2025 for a +02:00 offset late on Dec 31",
    ),
    ExpressionTestCase(
        "tz_offset_plus530_year_fwd",
        doc={"date": datetime(2024, 12, 31, 22, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": {"date": "$date", "timezone": "+05:30"}},
        expected=2025,
        msg="$year should cross forward to 2025 for a +05:30 half-hour offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus12_year_bwd",
        doc={"date": datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": {"date": "$date", "timezone": "-12:00"}},
        expected=2023,
        msg="$year should cross back to 2023 for a -12:00 offset on Jan 1",
    ),
    ExpressionTestCase(
        "tz_offset_plus14_year_fwd",
        doc={"date": datetime(2024, 12, 31, 11, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": {"date": "$date", "timezone": "+14:00"}},
        expected=2025,
        msg="$year should cross forward to 2025 for a +14:00 offset on Dec 31",
    ),
    ExpressionTestCase(
        "tz_offset_minus5_no_colon",
        doc={"date": datetime(2024, 1, 1, 3, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": {"date": "$date", "timezone": "-0500"}},
        expected=2023,
        msg="$year should accept a compact -0500 offset without a colon and cross back a year",
    ),
    ExpressionTestCase(
        "tz_offset_minus8_hour_only",
        doc={"date": datetime(2024, 1, 1, 3, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": {"date": "$date", "timezone": "-08"}},
        expected=2023,
        msg="$year should accept an hour-only -08 offset and cross back a year",
    ),
    ExpressionTestCase(
        "tz_offset_minus13",
        doc={"date": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": {"date": "$date", "timezone": "-13:00"}},
        expected=2023,
        msg="$year should accept a -13:00 offset that crosses back into the prior year",
    ),
    ExpressionTestCase(
        "tz_offset_plus15",
        doc={"date": datetime(2024, 12, 31, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": {"date": "$date", "timezone": "+15:00"}},
        expected=2025,
        msg="$year should accept a +15:00 offset that crosses into the next year",
    ),
    ExpressionTestCase(
        "tz_offset_minus0330",
        doc={"date": datetime(2024, 1, 1, 2, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": {"date": "$date", "timezone": "-03:30"}},
        expected=2023,
        msg="$year should accept a -03:30 half-hour west offset that crosses back a year",
    ),
    ExpressionTestCase(
        "tz_offset_plus0570",
        doc={"date": datetime(2024, 12, 31, 17, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": {"date": "$date", "timezone": "+05:70"}},
        expected=2024,
        msg="$year should accept a +05:70 (70-minute) offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus0570",
        doc={"date": datetime(2024, 1, 1, 5, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": {"date": "$date", "timezone": "-05:70"}},
        expected=2023,
        msg="$year should accept a -05:70 (70-minute) offset that crosses back a year",
    ),
    ExpressionTestCase(
        "tz_offset_plus2500",
        doc={"date": datetime(2024, 12, 30, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": {"date": "$date", "timezone": "+25:00"}},
        expected=2024,
        msg="$year should accept a +25:00 (25-hour) offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus2500",
        doc={"date": datetime(2024, 1, 2, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": {"date": "$date", "timezone": "-25:00"}},
        expected=2023,
        msg="$year should accept a -25:00 (25-hour) offset that crosses back a year",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(YEAR_OFFSET_TESTS))
def test_year_timezone_offsets(collection, test_case: ExpressionTestCase):
    """Test $year UTC-offset timezone application, including edge and unusual offsets."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
