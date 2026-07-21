"""Tests for $week UTC-offset timezone application, including compact and unusual offsets."""

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

# Property [UTC Offsets]: an explicit +HH:MM/-HH:MM offset shifts the instant before the week is
# taken, including compact, hour-only, half-hour, extreme, and out-of-range offsets the server
# still accepts, and offsets that cross a week or year boundary.
WEEK_OFFSET_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_offset_zero_no_cross",
        doc={"date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "+00:00"}},
        expected=28,
        msg="$week should accept a +00:00 offset with no week crossing",
    ),
    ExpressionTestCase(
        "tz_offset_minus5_no_cross",
        doc={"date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "-05:00"}},
        expected=28,
        msg="$week should accept a -05:00 offset with no week crossing",
    ),
    ExpressionTestCase(
        "tz_offset_plus9_week_fwd",
        doc={"date": datetime(2024, 1, 6, 22, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "+09:00"}},
        expected=1,
        msg="$week should cross forward to week 1 for a +09:00 offset late on the Saturday",
    ),
    ExpressionTestCase(
        "tz_offset_minus8_week_bwd",
        doc={"date": datetime(2024, 1, 7, 3, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "-08:00"}},
        expected=0,
        msg="$week should cross back to week 0 for a -08:00 offset early on the Sunday",
    ),
    ExpressionTestCase(
        "tz_offset_minus5_year_bwd",
        doc={"date": datetime(2024, 1, 1, 3, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "-05:00"}},
        expected=53,
        msg="$week should cross back into the prior year's week 53 for a -05:00 offset on Jan 1",
    ),
    ExpressionTestCase(
        "tz_offset_plus2_year_fwd",
        doc={"date": datetime(2024, 12, 31, 23, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "+02:00"}},
        expected=0,
        msg="$week should cross forward into the next year's week 0 for a +02:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_plus530_week_fwd",
        doc={"date": datetime(2024, 1, 6, 20, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "+05:30"}},
        expected=1,
        msg="$week should cross forward to week 1 for a +05:30 half-hour offset",
    ),
    ExpressionTestCase(
        "tz_offset_plus14_week_fwd",
        doc={"date": datetime(2024, 1, 6, 11, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "+14:00"}},
        expected=1,
        msg="$week should cross forward to week 1 for a +14:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus12_week_bwd",
        doc={"date": datetime(2024, 1, 7, 11, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "-12:00"}},
        expected=0,
        msg="$week should cross back to week 0 for a -12:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_no_colon",
        doc={"date": datetime(2024, 1, 6, 22, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "+0900"}},
        expected=1,
        msg="$week should accept a compact +0900 offset without a colon",
    ),
    ExpressionTestCase(
        "tz_offset_hour_only",
        doc={"date": datetime(2024, 1, 7, 3, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "-08"}},
        expected=0,
        msg="$week should accept an hour-only -08 offset and cross back to week 0",
    ),
    ExpressionTestCase(
        "tz_offset_minus13",
        doc={"date": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "-13:00"}},
        expected=53,
        msg="$week should accept a -13:00 offset that crosses back into the prior year",
    ),
    ExpressionTestCase(
        "tz_offset_plus15",
        doc={"date": datetime(2024, 1, 6, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "+15:00"}},
        expected=1,
        msg="$week should accept a +15:00 offset that crosses forward to week 1",
    ),
    ExpressionTestCase(
        "tz_offset_minus0330",
        doc={"date": datetime(2024, 1, 7, 2, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "-03:30"}},
        expected=0,
        msg="$week should accept a -03:30 half-hour west offset that crosses back to week 0",
    ),
    ExpressionTestCase(
        "tz_offset_plus0570",
        doc={"date": datetime(2024, 1, 6, 17, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "+05:70"}},
        expected=0,
        msg="$week should accept a +05:70 (70-minute) offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus0570",
        doc={"date": datetime(2024, 1, 7, 5, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "-05:70"}},
        expected=0,
        msg="$week should accept a -05:70 (70-minute) offset",
    ),
    ExpressionTestCase(
        "tz_offset_plus2500",
        doc={"date": datetime(2024, 1, 5, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "+25:00"}},
        expected=0,
        msg="$week should accept a +25:00 (25-hour) offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus2500",
        doc={"date": datetime(2024, 1, 8, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "-25:00"}},
        expected=0,
        msg="$week should accept a -25:00 (25-hour) offset",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(WEEK_OFFSET_TESTS))
def test_week_timezone_offsets(collection, test_case: ExpressionTestCase):
    """Test $week UTC-offset timezone application, including edge and unusual offsets."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
