"""Tests for $dateToString argument handling, validation, and null/onNull propagation."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import ExpressionTestCase
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    DATETOSTRING_MISSING_DATE_ERROR,
    DATETOSTRING_NON_OBJECT_ERROR,
    DATETOSTRING_UNKNOWN_FIELD_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

# Property [Argument Handling]: a date is formatted, optionally with format, timezone, and onNull.
DATETOSTRING_ARG_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "date_only",
        doc={"date": datetime(2024, 6, 15, 10, 30, 45, 123000, tzinfo=timezone.utc)},
        expression={"$dateToString": {"date": "$date"}},
        expected="2024-06-15T10:30:45.123Z",
        msg="$dateToString should format a date with the default format when only date is given",
    ),
    ExpressionTestCase(
        "with_format",
        doc={"date": datetime(2024, 6, 15, 10, 30, 45, 123000, tzinfo=timezone.utc)},
        expression={"$dateToString": {"date": "$date", "format": "%Y-%m-%d"}},
        expected="2024-06-15",
        msg="$dateToString should apply an explicit format string",
    ),
    ExpressionTestCase(
        "with_tz",
        doc={"date": datetime(2024, 6, 15, 10, 30, 45, 123000, tzinfo=timezone.utc)},
        expression={"$dateToString": {"date": "$date", "timezone": "UTC"}},
        expected="2024-06-15T10:30:45.123Z",
        msg="$dateToString should accept a timezone argument",
    ),
    ExpressionTestCase(
        "with_onNull",
        doc={"date": datetime(2024, 6, 15, 10, 30, 45, 123000, tzinfo=timezone.utc)},
        expression={"$dateToString": {"date": "$date", "format": "%Y-%m-%d", "onNull": "N/A"}},
        expected="2024-06-15",
        msg="$dateToString should ignore onNull when the date is present",
    ),
    ExpressionTestCase(
        "all_fields",
        doc={"date": datetime(2024, 6, 15, 10, 30, 45, 123000, tzinfo=timezone.utc)},
        expression={
            "$dateToString": {
                "date": "$date",
                "format": "%Y-%m-%d %H:%M",
                "timezone": "UTC",
                "onNull": "N/A",
            }
        },
        expected="2024-06-15 10:30",
        msg="$dateToString should format when every argument is provided",
    ),
]

# Property [Argument Validation]: a missing date, unknown field, or non-object argument is rejected.
DATETOSTRING_ARG_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_date",
        expression={"$dateToString": {"format": "%Y"}},
        error_code=DATETOSTRING_MISSING_DATE_ERROR,
        msg="$dateToString should reject an argument with no date field",
    ),
    ExpressionTestCase(
        "empty_object",
        expression={"$dateToString": {}},
        error_code=DATETOSTRING_MISSING_DATE_ERROR,
        msg="$dateToString should reject an empty object argument",
    ),
    ExpressionTestCase(
        "unknown_field",
        expression={"$dateToString": {"date": datetime(2024, 1, 1, tzinfo=timezone.utc), "foo": 1}},
        error_code=DATETOSTRING_UNKNOWN_FIELD_ERROR,
        msg="$dateToString should reject an unknown field",
    ),
    ExpressionTestCase(
        "non_object_str",
        expression={"$dateToString": "string"},
        error_code=DATETOSTRING_NON_OBJECT_ERROR,
        msg="$dateToString should reject a string argument",
    ),
    ExpressionTestCase(
        "non_object_arr",
        expression={"$dateToString": [1, 2]},
        error_code=DATETOSTRING_NON_OBJECT_ERROR,
        msg="$dateToString should reject an array argument",
    ),
    ExpressionTestCase(
        "non_object_num",
        expression={"$dateToString": 123},
        error_code=DATETOSTRING_NON_OBJECT_ERROR,
        msg="$dateToString should reject a numeric argument",
    ),
]

# Property [Null and onNull]: a null or missing date yields null unless onNull supplies a value,
# and a missing format or timezone field reference yields null.
DATETOSTRING_NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_no_onNull",
        doc={"date": None},
        expression={"$dateToString": {"date": "$date", "format": "%Y"}},
        expected=None,
        msg="$dateToString should return null for a null date with no onNull",
    ),
    ExpressionTestCase(
        "null_onNull_str",
        doc={"date": None},
        expression={"$dateToString": {"date": "$date", "format": "%Y", "onNull": "N/A"}},
        expected="N/A",
        msg="$dateToString should return a string onNull value for a null date",
    ),
    ExpressionTestCase(
        "null_onNull_num",
        doc={"date": None},
        expression={"$dateToString": {"date": "$date", "format": "%Y", "onNull": 0}},
        expected=0,
        msg="$dateToString should return a numeric onNull value for a null date",
    ),
    ExpressionTestCase(
        "null_onNull_null",
        doc={"date": None},
        expression={"$dateToString": {"date": "$date", "format": "%Y", "onNull": None}},
        expected=None,
        msg="$dateToString should return a null onNull value for a null date",
    ),
    ExpressionTestCase(
        "null_onNull_bool",
        doc={"date": None},
        expression={"$dateToString": {"date": "$date", "format": "%Y", "onNull": False}},
        expected=False,
        msg="$dateToString should return a boolean onNull value for a null date",
    ),
    ExpressionTestCase(
        "null_onNull_obj",
        doc={"date": None},
        expression={"$dateToString": {"date": "$date", "format": "%Y", "onNull": {"msg": "none"}}},
        expected={"msg": "none"},
        msg="$dateToString should return an object onNull value for a null date",
    ),
    ExpressionTestCase(
        "null_onNull_arr",
        doc={"date": None},
        expression={"$dateToString": {"date": "$date", "format": "%Y", "onNull": []}},
        expected=[],
        msg="$dateToString should return an array onNull value for a null date",
    ),
    ExpressionTestCase(
        "missing_date_ref",
        expression={"$dateToString": {"date": MISSING, "format": "%Y"}},
        expected=None,
        msg="$dateToString should return null when the date field is missing",
    ),
    ExpressionTestCase(
        "missing_date_ref_onNull",
        expression={"$dateToString": {"date": MISSING, "format": "%Y", "onNull": "missing"}},
        expected="missing",
        msg="$dateToString should return the onNull value when the date field is missing",
    ),
    ExpressionTestCase(
        "missing_timezone_ref",
        expression={
            "$dateToString": {
                "date": datetime(2024, 6, 15, 10, 30, 45, 123000, tzinfo=timezone.utc),
                "format": "%Y",
                "timezone": MISSING,
            }
        },
        expected=None,
        msg="$dateToString should return null when the timezone field is missing",
    ),
    ExpressionTestCase(
        "missing_format_ref",
        expression={
            "$dateToString": {
                "date": datetime(2024, 6, 15, 10, 30, 45, 123000, tzinfo=timezone.utc),
                "format": MISSING,
            }
        },
        expected=None,
        msg="$dateToString should return null when the format field is missing",
    ),
]

DATETOSTRING_ARGUMENT_TESTS: list[ExpressionTestCase] = (
    DATETOSTRING_ARG_TESTS + DATETOSTRING_ARG_ERROR_TESTS + DATETOSTRING_NULL_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATETOSTRING_ARGUMENT_TESTS))
def test_dateToString_arguments(collection, test_case: ExpressionTestCase):
    """Test $dateToString argument handling and null/onNull."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
