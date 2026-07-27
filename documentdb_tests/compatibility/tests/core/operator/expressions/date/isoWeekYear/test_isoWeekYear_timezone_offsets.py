"""Tests for $isoWeekYear UTC-offset timezone application, including compact and unusual offsets."""

from datetime import datetime, timezone

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [UTC Offsets]: an explicit +HH:MM/-HH:MM offset shifts the instant before the ISO
# week-numbering year is taken, including compact, hour-only, half-hour, extreme, and
# out-of-range offsets the server still accepts, and offsets that cross a year boundary.
ISOWEEKYEAR_OFFSET_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_offset_plus530",
        doc={"date": datetime(2024, 6, 15, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": {"date": "$date", "timezone": "+05:30"}},
        expected=Int64(2024),
        msg="$isoWeekYear should accept a +05:30 offset with no year crossing",
    ),
    ExpressionTestCase(
        "tz_offset_minus5",
        doc={"date": datetime(2024, 6, 15, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": {"date": "$date", "timezone": "-05:00"}},
        expected=Int64(2024),
        msg="$isoWeekYear should accept a -05:00 offset with no year crossing",
    ),
    ExpressionTestCase(
        "tz_offset_zero",
        doc={"date": datetime(2024, 6, 15, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": {"date": "$date", "timezone": "+00:00"}},
        expected=Int64(2024),
        msg="$isoWeekYear should accept a +00:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus5_no_colon",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": {"date": "$date", "timezone": "-0500"}},
        expected=Int64(2024),
        msg="$isoWeekYear should accept a compact -0500 offset without a colon",
    ),
    ExpressionTestCase(
        "tz_offset_minus8_hour_only",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": {"date": "$date", "timezone": "-08"}},
        expected=Int64(2024),
        msg="$isoWeekYear should accept an hour-only -08 offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus13",
        doc={"date": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": {"date": "$date", "timezone": "-13:00"}},
        expected=Int64(2023),
        msg="$isoWeekYear should accept a -13:00 offset that crosses back into the prior ISO year",
    ),
    ExpressionTestCase(
        "tz_offset_plus15",
        doc={"date": datetime(2024, 12, 31, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": {"date": "$date", "timezone": "+15:00"}},
        expected=Int64(2025),
        msg="$isoWeekYear should accept a +15:00 offset that crosses into the next ISO year",
    ),
    ExpressionTestCase(
        "tz_offset_minus0330",
        doc={"date": datetime(2024, 1, 1, 2, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": {"date": "$date", "timezone": "-03:30"}},
        expected=Int64(2023),
        msg="$isoWeekYear should accept a -03:30 half-hour west offset that crosses back a year",
    ),
    ExpressionTestCase(
        "tz_offset_plus0570",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": {"date": "$date", "timezone": "+05:70"}},
        expected=Int64(2024),
        msg="$isoWeekYear should accept a +05:70 (70-minute) offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus0570",
        doc={"date": datetime(2024, 1, 1, 5, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": {"date": "$date", "timezone": "-05:70"}},
        expected=Int64(2023),
        msg="$isoWeekYear should accept a -05:70 (70-minute) offset that crosses back a year",
    ),
    ExpressionTestCase(
        "tz_offset_plus2500",
        doc={"date": datetime(2024, 12, 30, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": {"date": "$date", "timezone": "+25:00"}},
        expected=Int64(2025),
        msg="$isoWeekYear should accept a +25:00 (25-hour) offset that crosses forward a year",
    ),
    ExpressionTestCase(
        "tz_offset_minus2500",
        doc={"date": datetime(2024, 1, 2, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": {"date": "$date", "timezone": "-25:00"}},
        expected=Int64(2023),
        msg="$isoWeekYear should accept a -25:00 (25-hour) offset that crosses back a year",
    ),
    ExpressionTestCase(
        "tz_offset_utc_2017_baseline",
        doc={"date": datetime(2017, 1, 2, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": {"date": "$date", "timezone": "+00:00"}},
        expected=Int64(2017),
        msg="$isoWeekYear should return 2017 for a Jan 2 Monday at a +00:00 offset baseline",
    ),
    ExpressionTestCase(
        "tz_offset_minus5_2017_cross",
        doc={"date": datetime(2017, 1, 2, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": {"date": "$date", "timezone": "-0500"}},
        expected=Int64(2016),
        msg="$isoWeekYear should cross back to 2016 for a -0500 offset at a Jan 2 midnight",
    ),
    ExpressionTestCase(
        "tz_offset_minus5_shift_prev",
        doc={"date": datetime(2018, 1, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": {"date": "$date", "timezone": "-05:00"}},
        expected=Int64(2017),
        msg="$isoWeekYear should cross back to 2017 for a -05:00 offset at a Jan 1 midnight",
    ),
    ExpressionTestCase(
        "tz_offset_plus2_shift_next",
        doc={"date": datetime(2018, 12, 31, 23, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": {"date": "$date", "timezone": "+02:00"}},
        expected=Int64(2019),
        msg="$isoWeekYear should cross forward to 2019 for a +02:00 offset late on Dec 31",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(ISOWEEKYEAR_OFFSET_TESTS))
def test_isoWeekYear_timezone_offsets(collection, test_case: ExpressionTestCase):
    """Test $isoWeekYear UTC-offset timezone application, including edge and unusual offsets."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
