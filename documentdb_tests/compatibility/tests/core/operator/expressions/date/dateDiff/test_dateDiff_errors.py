"""$dateDiff rejection cases: invalid operand types, unit, timezone, startOfWeek, and shape."""

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
    DATEDIFF_MISSING_ENDDATE_ERROR,
    DATEDIFF_MISSING_STARTDATE_ERROR,
    DATEDIFF_MISSING_UNIT_ERROR,
    DATEDIFF_NON_OBJECT_ERROR,
    DATEDIFF_UNKNOWN_FIELD_ERROR,
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

# Property [StartDate Type]: a non-date, non-Timestamp, non-ObjectId startDate is rejected.
DATEDIFF_STARTDATE_TYPE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"startDate_{tid}",
        expression={
            "$dateDiff": {
                "startDate": val,
                "endDate": datetime(2024, 6, 1, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        error_code=INVALID_DATE_VALUE_ERROR,
        msg=f"$dateDiff should reject a {tid} startDate",
    )
    for tid, val in [
        ("string", "2024-01-01"),
        ("int", 123),
        ("int64", Int64(123)),
        ("double", 1.0),
        ("decimal128", Decimal128("1")),
        ("boolean", True),
        ("array", [2024, 1, 1]),
        ("empty_array", []),
        ("single_date_array", [datetime(2024, 1, 1, tzinfo=timezone.utc)]),
        ("object", {"year": 2024}),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*")),
        ("javascript", Code("function() {}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("decimal128_infinity", DECIMAL128_INFINITY),
        ("decimal128_neg_infinity", DECIMAL128_NEGATIVE_INFINITY),
    ]
]

# Property [EndDate Type]: a non-date, non-Timestamp, non-ObjectId endDate is rejected.
DATEDIFF_ENDDATE_TYPE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"endDate_{tid}",
        expression={
            "$dateDiff": {
                "startDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "endDate": val,
                "unit": "day",
            }
        },
        error_code=INVALID_DATE_VALUE_ERROR,
        msg=f"$dateDiff should reject a {tid} endDate",
    )
    for tid, val in [
        ("string", "2024-06-01"),
        ("int", 123),
        ("int64", Int64(123)),
        ("double", 1.0),
        ("decimal128", Decimal128("1")),
        ("boolean", True),
        ("array", [2024, 6, 1]),
        ("empty_array", []),
        ("single_date_array", [datetime(2024, 6, 1, tzinfo=timezone.utc)]),
        ("object", {"year": 2024}),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*")),
        ("javascript", Code("function() {}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("decimal128_infinity", DECIMAL128_INFINITY),
        ("decimal128_neg_infinity", DECIMAL128_NEGATIVE_INFINITY),
    ]
]

# Property [Unit Type]: a non-string unit is rejected as an invalid date unit.
DATEDIFF_UNIT_TYPE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"unit_{tid}",
        expression={
            "$dateDiff": {
                "startDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2024, 6, 1, tzinfo=timezone.utc),
                "unit": val,
            }
        },
        error_code=INVALID_DATE_UNIT_ERROR,
        msg=f"$dateDiff should reject a {tid} unit",
    )
    for tid, val in [
        ("number", 1),
        ("int64", Int64(1)),
        ("double", 1.0),
        ("decimal128", Decimal128("1")),
        ("boolean", True),
        ("array", ["day"]),
        ("object", {"t": "day"}),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
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
DATEDIFF_UNIT_STRING_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"unit_{tid}",
        expression={
            "$dateDiff": {
                "startDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2024, 6, 1, tzinfo=timezone.utc),
                "unit": val,
            }
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg=f"$dateDiff should reject the {desc}",
    )
    for tid, val, desc in [
        ("invalid_string", "invalid", "unrecognized unit string"),
        ("empty_string", "", "empty string unit"),
        ("epoch_invalid", "epoch", "invalid unit epoch"),
        ("mixed_case_Day", "Day", "mixed-case unit Day"),
        ("mixed_case_Hour", "Hour", "mixed-case unit Hour"),
        ("mixed_case_Month", "Month", "mixed-case unit Month"),
        ("mixed_case_Quarter", "Quarter", "mixed-case unit Quarter"),
        ("mixed_case_Week", "Week", "mixed-case unit Week"),
        ("mixed_case_Second", "Second", "mixed-case unit Second"),
        ("mixed_case_Minute", "Minute", "mixed-case unit Minute"),
        ("mixed_case_Millisecond", "Millisecond", "mixed-case unit Millisecond"),
        ("mixed_case_Year", "Year", "mixed-case unit Year"),
        ("uppercase_DAY", "DAY", "uppercase unit DAY"),
        ("uppercase_YEAR", "YEAR", "uppercase unit YEAR"),
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

# Property [Array-Resolving Path]: a field path that resolves to an array is delivered to the
# operator, which rejects it under its date type contract.
DATEDIFF_ARRAY_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "composite_array_path",
        doc={
            "a": [
                {"b": datetime(2021, 1, 1, tzinfo=timezone.utc)},
                {"b": datetime(2021, 6, 1, tzinfo=timezone.utc)},
            ]
        },
        expression={
            "$dateDiff": {
                "startDate": "$a.b",
                "endDate": datetime(2021, 1, 2, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        error_code=INVALID_DATE_VALUE_ERROR,
        msg="$dateDiff should reject a composite array field path as startDate",
    ),
    ExpressionTestCase(
        "single_element_array_path",
        doc={"a": [{"b": datetime(2021, 6, 15, tzinfo=timezone.utc)}]},
        expression={
            "$dateDiff": {
                "startDate": "$a.b",
                "endDate": datetime(2021, 6, 16, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        error_code=INVALID_DATE_VALUE_ERROR,
        msg="$dateDiff should reject a single-element array field path as startDate",
    ),
    ExpressionTestCase(
        "array_index_path",
        doc={"a": [{"b": datetime(2021, 1, 1, tzinfo=timezone.utc)}]},
        expression={
            "$dateDiff": {
                "startDate": "$a.0.b",
                "endDate": datetime(2021, 1, 2, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        error_code=INVALID_DATE_VALUE_ERROR,
        msg="$dateDiff should reject an array-index field path resolving to an array as startDate",
    ),
]

# Property [Invalid Timezone]: an unrecognized or malformed timezone string is rejected.
DATEDIFF_TIMEZONE_INVALID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"tz_{tid}",
        expression={
            "$dateDiff": {
                "startDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2024, 6, 1, tzinfo=timezone.utc),
                "unit": "day",
                "timezone": tz,
            }
        },
        error_code=INVALID_TIMEZONE_ERROR,
        msg=f"$dateDiff should reject {desc}",
    )
    for tid, tz, desc in [
        ("offset_3digit_hours", "+100:00", "a 3-digit hour offset"),
        ("invalid_string", "NotATimezone", "an unrecognized Olson timezone"),
        ("empty_string", "", "an empty string timezone"),
        ("olson_wrong_case_lowercase", "america/new_york", "an all-lowercase Olson name"),
        ("olson_wrong_case_uppercase", "AMERICA/NEW_YORK", "an all-uppercase Olson name"),
    ]
]

# Property [Timezone Type]: a non-string timezone is rejected as an invalid type.
DATEDIFF_TIMEZONE_TYPE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"tz_{tid}",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2021, 1, 2, tzinfo=timezone.utc),
                "unit": "day",
                "timezone": val,
            }
        },
        error_code=INVALID_TIMEZONE_TYPE_ERROR,
        msg=f"$dateDiff should reject a {tid} timezone",
    )
    for tid, val in [
        ("number", 5),
        ("int64", Int64(5)),
        ("double", 5.0),
        ("decimal128", Decimal128("5")),
        ("boolean", True),
        ("array", ["UTC"]),
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

# Property [Invalid StartOfWeek]: an unrecognized startOfWeek string is rejected.
DATEDIFF_STARTOFWEEK_INVALID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"sow_{tid}",
        expression={
            "$dateDiff": {
                "startDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2024, 1, 31, tzinfo=timezone.utc),
                "unit": "week",
                "startOfWeek": sow,
            }
        },
        error_code=INVALID_STARTOFWEEK_ERROR,
        msg=f"$dateDiff should reject {desc}",
    )
    for tid, sow, desc in [
        ("invalid_string", "notaday", "an unrecognized startOfWeek string"),
        ("empty_string", "", "an empty startOfWeek string"),
    ]
]

# Property [StartOfWeek Type]: a non-string startOfWeek is rejected as an invalid type.
DATEDIFF_STARTOFWEEK_TYPE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"sow_{tid}",
        expression={
            "$dateDiff": {
                "startDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2024, 1, 31, tzinfo=timezone.utc),
                "unit": "week",
                "startOfWeek": val,
            }
        },
        error_code=INVALID_STARTOFWEEK_TYPE_ERROR,
        msg=f"$dateDiff should reject a {tid} startOfWeek",
    )
    for tid, val in [
        ("number", 1),
        ("int64", Int64(1)),
        ("double", 1.0),
        ("decimal128", Decimal128("1")),
        ("boolean", True),
        ("array", ["monday"]),
        ("object", {"day": "monday"}),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("objectid", ObjectId("600000000000000000000000")),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex("monday")),
        ("javascript", Code("function() {}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Argument Shape]: a missing required field, an unknown field, or a non-object
# argument is rejected.
DATEDIFF_ARGUMENT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "arg_missing_startDate",
        expression={
            "$dateDiff": {"endDate": datetime(2024, 6, 1, tzinfo=timezone.utc), "unit": "day"}
        },
        error_code=DATEDIFF_MISSING_STARTDATE_ERROR,
        msg="$dateDiff should error when startDate is missing",
    ),
    ExpressionTestCase(
        "arg_missing_endDate",
        expression={
            "$dateDiff": {"startDate": datetime(2024, 1, 1, tzinfo=timezone.utc), "unit": "day"}
        },
        error_code=DATEDIFF_MISSING_ENDDATE_ERROR,
        msg="$dateDiff should error when endDate is missing",
    ),
    ExpressionTestCase(
        "arg_missing_unit",
        expression={
            "$dateDiff": {
                "startDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2024, 6, 1, tzinfo=timezone.utc),
            }
        },
        error_code=DATEDIFF_MISSING_UNIT_ERROR,
        msg="$dateDiff should error when unit is missing",
    ),
    ExpressionTestCase(
        "arg_empty_object",
        expression={"$dateDiff": {}},
        error_code=DATEDIFF_MISSING_STARTDATE_ERROR,
        msg="$dateDiff should report a missing startDate for an empty argument object",
    ),
    ExpressionTestCase(
        "arg_unknown_field",
        expression={
            "$dateDiff": {
                "startDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2024, 6, 1, tzinfo=timezone.utc),
                "unit": "day",
                "foo": 1,
            }
        },
        error_code=DATEDIFF_UNKNOWN_FIELD_ERROR,
        msg="$dateDiff should error for an unknown field",
    ),
    ExpressionTestCase(
        "arg_non_object_string",
        expression={"$dateDiff": "string"},
        error_code=DATEDIFF_NON_OBJECT_ERROR,
        msg="$dateDiff should reject a string argument as a non-object",
    ),
    ExpressionTestCase(
        "arg_non_object_array",
        expression={"$dateDiff": [1, 2]},
        error_code=DATEDIFF_NON_OBJECT_ERROR,
        msg="$dateDiff should reject an array argument as a non-object",
    ),
    ExpressionTestCase(
        "arg_non_object_number",
        expression={"$dateDiff": 123},
        error_code=DATEDIFF_NON_OBJECT_ERROR,
        msg="$dateDiff should reject a number argument as a non-object",
    ),
]

DATEDIFF_ERROR_TESTS: list[ExpressionTestCase] = (
    DATEDIFF_STARTDATE_TYPE_ERROR_TESTS
    + DATEDIFF_ENDDATE_TYPE_ERROR_TESTS
    + DATEDIFF_UNIT_TYPE_ERROR_TESTS
    + DATEDIFF_UNIT_STRING_ERROR_TESTS
    + DATEDIFF_ARRAY_PATH_TESTS
    + DATEDIFF_TIMEZONE_INVALID_TESTS
    + DATEDIFF_TIMEZONE_TYPE_ERROR_TESTS
    + DATEDIFF_STARTOFWEEK_INVALID_TESTS
    + DATEDIFF_STARTOFWEEK_TYPE_ERROR_TESTS
    + DATEDIFF_ARGUMENT_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATEDIFF_ERROR_TESTS))
def test_dateDiff_errors(collection, test_case: ExpressionTestCase):
    """Test $dateDiff rejects invalid operand types, timezones, startOfWeek, and shapes."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
