"""Tests for $isoWeek UTC-offset timezone application, including compact and unusual offsets."""

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

# Property [UTC Offsets]: an explicit +HH:MM/-HH:MM offset shifts the instant before the ISO
# week is taken, including compact, hour-only, half-hour, extreme, and out-of-range offsets
# the server still accepts, and offsets that cross a week boundary.
ISOWEEK_OFFSET_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_offset_plus530",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeek": {"date": "$date", "timezone": "+05:30"}},
        expected=24,
        msg="$isoWeek should accept a +05:30 offset with no week crossing",
    ),
    ExpressionTestCase(
        "tz_offset_minus5",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeek": {"date": "$date", "timezone": "-05:00"}},
        expected=24,
        msg="$isoWeek should accept a -05:00 offset with no week crossing",
    ),
    ExpressionTestCase(
        "tz_offset_plus530_no_colon",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeek": {"date": "$date", "timezone": "+0530"}},
        expected=24,
        msg="$isoWeek should accept a compact +0530 offset without a colon",
    ),
    ExpressionTestCase(
        "tz_offset_plus3_hour_only",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeek": {"date": "$date", "timezone": "+03"}},
        expected=24,
        msg="$isoWeek should accept an hour-only +03 offset",
    ),
    ExpressionTestCase(
        "tz_offset_zero",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeek": {"date": "$date", "timezone": "+00:00"}},
        expected=24,
        msg="$isoWeek should accept a +00:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus5_no_colon",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeek": {"date": "$date", "timezone": "-0500"}},
        expected=24,
        msg="$isoWeek should accept a compact -0500 offset without a colon",
    ),
    ExpressionTestCase(
        "tz_offset_minus8_hour_only",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeek": {"date": "$date", "timezone": "-08"}},
        expected=24,
        msg="$isoWeek should accept an hour-only -08 offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus13",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeek": {"date": "$date", "timezone": "-13:00"}},
        expected=24,
        msg="$isoWeek should accept a -13:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_plus15",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeek": {"date": "$date", "timezone": "+15:00"}},
        expected=24,
        msg="$isoWeek should accept a +15:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus0330",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeek": {"date": "$date", "timezone": "-03:30"}},
        expected=24,
        msg="$isoWeek should accept a -03:30 half-hour west offset",
    ),
    ExpressionTestCase(
        "tz_offset_plus0570",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeek": {"date": "$date", "timezone": "+05:70"}},
        expected=24,
        msg="$isoWeek should accept a +05:70 (70-minute) offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus0570",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeek": {"date": "$date", "timezone": "-05:70"}},
        expected=24,
        msg="$isoWeek should accept a -05:70 (70-minute) offset",
    ),
    ExpressionTestCase(
        "tz_offset_plus2500",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeek": {"date": "$date", "timezone": "+25:00"}},
        expected=24,
        msg="$isoWeek should accept a +25:00 (25-hour) offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus2500",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeek": {"date": "$date", "timezone": "-25:00"}},
        expected=24,
        msg="$isoWeek should accept a -25:00 (25-hour) offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus5_week_cross",
        doc={"date": datetime(1998, 11, 2, tzinfo=timezone.utc)},
        expression={"$isoWeek": {"date": "$date", "timezone": "-0500"}},
        expected=44,
        msg="$isoWeek should cross back to week 44 for a -0500 offset at a Monday midnight",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(ISOWEEK_OFFSET_TESTS))
def test_isoWeek_timezone_offsets(collection, test_case: ExpressionTestCase):
    """Test $isoWeek UTC-offset timezone application, including edge and unusual offsets."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
