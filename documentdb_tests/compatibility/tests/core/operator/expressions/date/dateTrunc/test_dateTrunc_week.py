"""$dateTrunc week truncation: startOfWeek values, casing, relevance, and non-week gating."""

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

# Property [StartOfWeek Case]: startOfWeek accepts full day names and three-letter abbreviations
# in any case.
DATETRUNC_STARTOFWEEK_ACCEPT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "sow_mixed_case_Monday",
        doc={"date": datetime(2021, 6, 16, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "Monday"}},
        expected=datetime(2021, 6, 14, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept a mixed-case Monday",
    ),
    ExpressionTestCase(
        "sow_uppercase_MONDAY",
        doc={"date": datetime(2021, 6, 16, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "MONDAY"}},
        expected=datetime(2021, 6, 14, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept an uppercase MONDAY",
    ),
    ExpressionTestCase(
        "sow_abbrev_MON",
        doc={"date": datetime(2021, 6, 16, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "MON"}},
        expected=datetime(2021, 6, 14, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept an uppercase abbreviation MON",
    ),
    ExpressionTestCase(
        "sow_mixed_case_Friday",
        doc={"date": datetime(2021, 6, 16, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "Friday"}},
        expected=datetime(2021, 6, 11, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept a mixed-case Friday",
    ),
    ExpressionTestCase(
        "sow_uppercase_FRIDAY",
        doc={"date": datetime(2021, 6, 16, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "FRIDAY"}},
        expected=datetime(2021, 6, 11, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept an uppercase FRIDAY",
    ),
    ExpressionTestCase(
        "sow_abbrev_FRI",
        doc={"date": datetime(2021, 6, 16, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "FRI"}},
        expected=datetime(2021, 6, 11, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept an uppercase abbreviation FRI",
    ),
    ExpressionTestCase(
        "sow_uppercase_SUNDAY",
        doc={"date": datetime(2021, 6, 16, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "SUNDAY"}},
        expected=datetime(2021, 6, 13, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept an uppercase SUNDAY",
    ),
    ExpressionTestCase(
        "sow_abbrev_SUN",
        doc={"date": datetime(2021, 6, 16, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "SUN"}},
        expected=datetime(2021, 6, 13, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept an uppercase abbreviation SUN",
    ),
]

# Property [StartOfWeek Relevance]: for a non-week unit a null startOfWeek is ignored when the date
# is a constant literal, but short-circuits the result to null when the date is a field reference.
DATETRUNC_STARTOFWEEK_RELEVANCE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "sow_relevance_literal_day",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc),
                "unit": "day",
                "startOfWeek": None,
            }
        },
        expected=datetime(2021, 3, 20, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should ignore a null startOfWeek for a non-week unit when the date is a "
        "constant",
    ),
    ExpressionTestCase(
        "sow_relevance_field_ref_day",
        doc={"date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "day", "startOfWeek": None}},
        expected=None,
        msg="$dateTrunc should return null for a null startOfWeek on a non-week unit when the date "
        "is a field reference",
    ),
]

# Property [Week Truncation]: the week unit truncates to the configured start of week, defaulting
# to Sunday.
DATETRUNC_WEEK_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "week_default_sun",
        doc={"date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week"}},
        expected=datetime(2021, 3, 14, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should default the week start to Sunday",
    ),
    ExpressionTestCase(
        "week_monday",
        doc={"date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "monday"}},
        expected=datetime(2021, 3, 15, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate the week to Monday",
    ),
    ExpressionTestCase(
        "week_friday",
        doc={"date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "friday"}},
        expected=datetime(2021, 3, 19, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate the week to Friday",
    ),
    ExpressionTestCase(
        "week_sunday",
        doc={"date": datetime(2021, 6, 16, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "sunday"}},
        expected=datetime(2021, 6, 13, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate the week to Sunday",
    ),
    ExpressionTestCase(
        "week_tuesday",
        doc={"date": datetime(2021, 6, 16, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "tuesday"}},
        expected=datetime(2021, 6, 15, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate the week to Tuesday",
    ),
    ExpressionTestCase(
        "week_wednesday",
        doc={"date": datetime(2021, 6, 16, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "wednesday"}},
        expected=datetime(2021, 6, 16, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate the week to Wednesday",
    ),
    ExpressionTestCase(
        "week_thursday",
        doc={"date": datetime(2021, 6, 16, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "thursday"}},
        expected=datetime(2021, 6, 10, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate the week to Thursday",
    ),
    ExpressionTestCase(
        "week_saturday",
        doc={"date": datetime(2021, 6, 16, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "saturday"}},
        expected=datetime(2021, 6, 12, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate the week to Saturday",
    ),
    ExpressionTestCase(
        "week_mon_abbrev",
        doc={"date": datetime(2021, 6, 16, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "mon"}},
        expected=datetime(2021, 6, 14, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept the mon abbreviation for startOfWeek",
    ),
    ExpressionTestCase(
        "week_monday_mixed_case",
        doc={"date": datetime(2021, 6, 16, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "Monday"}},
        expected=datetime(2021, 6, 14, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept a mixed-case Monday for startOfWeek",
    ),
]

# Property [StartOfWeek Ignored]: startOfWeek has no effect for a non-week unit.
DATETRUNC_SOW_IGNORED_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "sow_ignored_month",
        doc={"date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "month", "startOfWeek": "friday"}},
        expected=datetime(2021, 3, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should ignore startOfWeek for the month unit",
    ),
]

DATETRUNC_WEEK_ALL_TESTS: list[ExpressionTestCase] = (
    DATETRUNC_STARTOFWEEK_ACCEPT_TESTS
    + DATETRUNC_STARTOFWEEK_RELEVANCE_TESTS
    + DATETRUNC_WEEK_TESTS
    + DATETRUNC_SOW_IGNORED_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATETRUNC_WEEK_ALL_TESTS))
def test_dateTrunc_week(collection, test_case: ExpressionTestCase):
    """Test $dateTrunc week truncation honors startOfWeek and ignores it otherwise."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
