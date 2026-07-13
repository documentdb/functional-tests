"""$dateTrunc rejection cases: invalid date, unit, timezone, startOfWeek, and argument shape."""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    DATETRUNC_MISSING_DATE_ERROR,
    DATETRUNC_MISSING_UNIT_ERROR,
    DATETRUNC_NON_OBJECT_ERROR,
    DATETRUNC_UNKNOWN_FIELD_ERROR,
    FAILED_TO_PARSE_ERROR,
    INVALID_DATE_UNIT_ERROR,
    INVALID_DATE_VALUE_ERROR,
    INVALID_STARTOFWEEK_ERROR,
    INVALID_STARTOFWEEK_TYPE_ERROR,
    INVALID_TIMEZONE_ERROR,
    INVALID_TIMEZONE_TYPE_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NEGATIVE_INFINITY,
)

# Property [Argument Shape]: a missing required field, an empty object, an unknown field, or a
# non-object argument is rejected.
DATETRUNC_ARG_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "arg_missing_date",
        expression={"$dateTrunc": {"unit": "day"}},
        error_code=DATETRUNC_MISSING_DATE_ERROR,
        msg="$dateTrunc should error when date is missing",
    ),
    ExpressionTestCase(
        "arg_missing_unit",
        expression={"$dateTrunc": {"date": datetime(2021, 1, 1, tzinfo=timezone.utc)}},
        error_code=DATETRUNC_MISSING_UNIT_ERROR,
        msg="$dateTrunc should error when unit is missing",
    ),
    ExpressionTestCase(
        "arg_empty_object",
        expression={"$dateTrunc": {}},
        error_code=DATETRUNC_MISSING_DATE_ERROR,
        msg="$dateTrunc should error for an empty argument object",
    ),
    ExpressionTestCase(
        "arg_unknown_field",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "unit": "day",
                "foo": 1,
            }
        },
        error_code=DATETRUNC_UNKNOWN_FIELD_ERROR,
        msg="$dateTrunc should error for an unknown field",
    ),
    ExpressionTestCase(
        "arg_non_object_string",
        expression={"$dateTrunc": "string"},
        error_code=DATETRUNC_NON_OBJECT_ERROR,
        msg="$dateTrunc should reject a string argument",
    ),
    ExpressionTestCase(
        "arg_non_object_array",
        expression={"$dateTrunc": [1, 2]},
        error_code=DATETRUNC_NON_OBJECT_ERROR,
        msg="$dateTrunc should reject an array argument",
    ),
    ExpressionTestCase(
        "arg_non_object_number",
        expression={"$dateTrunc": 123},
        error_code=DATETRUNC_NON_OBJECT_ERROR,
        msg="$dateTrunc should reject a numeric argument",
    ),
]

# Property [Date Type]: a non-date, non-ObjectId, non-Timestamp date value is rejected.
DATETRUNC_DATE_TYPE_ERROR_TESTS: list[ExpressionTestCase] = [
    *[
        ExpressionTestCase(
            f"date_{tid}",
            doc={"date": val},
            expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
            error_code=INVALID_DATE_VALUE_ERROR,
            msg=f"$dateTrunc should reject a {tid} date",
        )
        for tid, val in [
            ("string", "2021"),
            ("int", 123),
            ("int64", Int64(123)),
            ("double", 1.0),
            ("decimal128", Decimal128("1")),
            ("boolean", True),
            ("array", [1, 2]),
            ("empty_array", []),
            ("object", {"a": 1}),
            ("binary", Binary(b"\x01\x02\x03")),
            ("regex", Regex(".*")),
            ("javascript", Code("function() {}")),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    ExpressionTestCase(
        "date_boolean_false",
        doc={"date": False},
        expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
        error_code=INVALID_DATE_VALUE_ERROR,
        msg="$dateTrunc should reject a false boolean date",
    ),
    ExpressionTestCase(
        "date_single_date_array",
        doc={"date": [datetime(2021, 6, 15, tzinfo=timezone.utc)]},
        expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
        error_code=INVALID_DATE_VALUE_ERROR,
        msg="$dateTrunc should reject a single-element array containing a date",
    ),
    ExpressionTestCase(
        "date_decimal128_infinity",
        doc={"date": DECIMAL128_INFINITY},
        expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
        error_code=INVALID_DATE_VALUE_ERROR,
        msg="$dateTrunc should reject a Decimal128 Infinity date",
    ),
    ExpressionTestCase(
        "date_decimal128_neg_infinity",
        doc={"date": DECIMAL128_NEGATIVE_INFINITY},
        expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
        error_code=INVALID_DATE_VALUE_ERROR,
        msg="$dateTrunc should reject a Decimal128 -Infinity date",
    ),
]

# Property [Unit Type]: a non-string unit is rejected as an invalid date unit.
DATETRUNC_UNIT_TYPE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"unit_{tid}",
        expression={"$dateTrunc": {"date": datetime(2021, 1, 1, tzinfo=timezone.utc), "unit": val}},
        error_code=INVALID_DATE_UNIT_ERROR,
        msg=f"$dateTrunc should reject a {tid} unit",
    )
    for tid, val in [
        ("int", 1),
        ("int64", Int64(1)),
        ("double", 1.0),
        ("decimal128", Decimal128("1")),
        ("boolean", True),
        ("array", ["day"]),
        ("empty_array", []),
        ("object", {"t": "day"}),
        ("datetime", datetime(2021, 1, 1, tzinfo=timezone.utc)),
        ("objectid", ObjectId("600000000000000000000000")),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex("day")),
        ("javascript", Code("function() {}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Unit String]: an unrecognized unit string, including wrong case and plurals, is
# rejected at parse time.
DATETRUNC_UNIT_STRING_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"unit_{tid}",
        expression={"$dateTrunc": {"date": datetime(2021, 1, 1, tzinfo=timezone.utc), "unit": val}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg=f"$dateTrunc should reject the {desc}",
    )
    for tid, val, desc in [
        ("invalid_string", "invalid", "unrecognized unit string"),
        ("empty_string", "", "empty string unit"),
        ("mixed_case_Year", "Year", "mixed-case unit Year"),
        ("mixed_case_Day", "Day", "mixed-case unit Day"),
        ("mixed_case_Hour", "Hour", "mixed-case unit Hour"),
        ("mixed_case_Month", "Month", "mixed-case unit Month"),
        ("mixed_case_Quarter", "Quarter", "mixed-case unit Quarter"),
        ("mixed_case_Week", "Week", "mixed-case unit Week"),
        ("mixed_case_Second", "Second", "mixed-case unit Second"),
        ("mixed_case_Minute", "Minute", "mixed-case unit Minute"),
        ("mixed_case_Millisecond", "Millisecond", "mixed-case unit Millisecond"),
        ("uppercase_YEAR", "YEAR", "uppercase unit YEAR"),
        ("uppercase_DAY", "DAY", "uppercase unit DAY"),
        ("uppercase_HOUR", "HOUR", "uppercase unit HOUR"),
        ("uppercase_MONTH", "MONTH", "uppercase unit MONTH"),
        ("uppercase_MILLISECOND", "MILLISECOND", "uppercase unit MILLISECOND"),
        ("uppercase_QUARTER", "QUARTER", "uppercase unit QUARTER"),
        ("uppercase_WEEK", "WEEK", "uppercase unit WEEK"),
        ("uppercase_SECOND", "SECOND", "uppercase unit SECOND"),
        ("uppercase_MINUTE", "MINUTE", "uppercase unit MINUTE"),
        ("plural_years", "years", "plural unit years"),
        ("plural_months", "months", "plural unit months"),
        ("plural_days", "days", "plural unit days"),
        ("plural_hours", "hours", "plural unit hours"),
        ("plural_minutes", "minutes", "plural unit minutes"),
        ("plural_seconds", "seconds", "plural unit seconds"),
        ("plural_milliseconds", "milliseconds", "plural unit milliseconds"),
        ("plural_weeks", "weeks", "plural unit weeks"),
        ("plural_quarters", "quarters", "plural unit quarters"),
    ]
]

# Property [Array Path Rejection]: a field path resolving to an array is rejected as an invalid
# date value.
DATETRUNC_ARRAY_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "composite_array_path",
        doc={
            "a": [
                {"b": datetime(2021, 6, 15, tzinfo=timezone.utc)},
                {"b": datetime(2021, 7, 1, tzinfo=timezone.utc)},
            ]
        },
        expression={"$dateTrunc": {"date": "$a.b", "unit": "day"}},
        error_code=INVALID_DATE_VALUE_ERROR,
        msg="$dateTrunc should reject a composite array field path",
    ),
    ExpressionTestCase(
        "single_element_array_path",
        doc={"a": [{"b": datetime(2021, 6, 15, 12, 30, 0, tzinfo=timezone.utc)}]},
        expression={"$dateTrunc": {"date": "$a.b", "unit": "day"}},
        error_code=INVALID_DATE_VALUE_ERROR,
        msg="$dateTrunc should reject a single-element array field path",
    ),
]

# Property [Timezone Type]: a non-string timezone is rejected.
DATETRUNC_TIMEZONE_TYPE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"tz_{tid}",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 6, 15, tzinfo=timezone.utc),
                "unit": "day",
                "timezone": val,
            }
        },
        error_code=INVALID_TIMEZONE_TYPE_ERROR,
        msg=f"$dateTrunc should reject a {tid} timezone",
    )
    for tid, val in [
        ("int", 5),
        ("int64", Int64(5)),
        ("double", 5.0),
        ("decimal128", Decimal128("5")),
        ("boolean", True),
        ("array", ["UTC"]),
        ("empty_array", []),
        ("object", {"tz": "UTC"}),
        ("datetime", datetime(2021, 1, 1, tzinfo=timezone.utc)),
        ("objectid", ObjectId("600000000000000000000000")),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex("UTC")),
        ("javascript", Code("function() {}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Timezone String]: an unrecognized timezone string, including wrong-case Olson names and
# out-of-range offsets, is rejected.
DATETRUNC_TIMEZONE_STRING_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"tz_{tid}",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 6, 15, tzinfo=timezone.utc),
                "unit": "day",
                "timezone": val,
            }
        },
        error_code=INVALID_TIMEZONE_ERROR,
        msg=f"$dateTrunc should reject the {desc}",
    )
    for tid, val, desc in [
        ("invalid_string", "NotATimezone", "unrecognized timezone string"),
        ("empty_string", "", "empty timezone string"),
        ("olson_lowercase", "america/new_york", "all-lowercase Olson name"),
        ("olson_uppercase", "AMERICA/NEW_YORK", "all-uppercase Olson name"),
        ("offset_3digit_hours", "+100:00", "three-digit hour offset"),
    ]
]

# Property [StartOfWeek Type]: a non-string startOfWeek is rejected.
DATETRUNC_STARTOFWEEK_TYPE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"sow_{tid}",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 3, 20, tzinfo=timezone.utc),
                "unit": "week",
                "startOfWeek": val,
            }
        },
        error_code=INVALID_STARTOFWEEK_TYPE_ERROR,
        msg=f"$dateTrunc should reject a {tid} startOfWeek",
    )
    for tid, val in [
        ("int", 1),
        ("int64", Int64(1)),
        ("double", 1.0),
        ("decimal128", Decimal128("1")),
        ("boolean", True),
        ("array", ["monday"]),
        ("empty_array", []),
        ("object", {"day": "monday"}),
        ("datetime", datetime(2021, 1, 1, tzinfo=timezone.utc)),
        ("objectid", ObjectId("600000000000000000000000")),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex("monday")),
        ("javascript", Code("function() {}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [StartOfWeek String]: an unrecognized startOfWeek string is rejected.
DATETRUNC_STARTOFWEEK_STRING_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "sow_invalid_string",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 3, 20, tzinfo=timezone.utc),
                "unit": "week",
                "startOfWeek": "notaday",
            }
        },
        error_code=INVALID_STARTOFWEEK_ERROR,
        msg="$dateTrunc should reject an unrecognized startOfWeek string",
    ),
    ExpressionTestCase(
        "sow_empty_string",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 3, 20, tzinfo=timezone.utc),
                "unit": "week",
                "startOfWeek": "",
            }
        },
        error_code=INVALID_STARTOFWEEK_ERROR,
        msg="$dateTrunc should reject an empty startOfWeek string",
    ),
]

DATETRUNC_ERROR_TESTS: list[ExpressionTestCase] = (
    DATETRUNC_ARG_ERROR_TESTS
    + DATETRUNC_DATE_TYPE_ERROR_TESTS
    + DATETRUNC_UNIT_TYPE_ERROR_TESTS
    + DATETRUNC_UNIT_STRING_ERROR_TESTS
    + DATETRUNC_ARRAY_PATH_TESTS
    + DATETRUNC_TIMEZONE_TYPE_ERROR_TESTS
    + DATETRUNC_TIMEZONE_STRING_ERROR_TESTS
    + DATETRUNC_STARTOFWEEK_TYPE_ERROR_TESTS
    + DATETRUNC_STARTOFWEEK_STRING_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATETRUNC_ERROR_TESTS))
def test_dateTrunc_errors(collection, test_case: ExpressionTestCase):
    """Test $dateTrunc rejects invalid date, unit, timezone, startOfWeek, and shapes."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
