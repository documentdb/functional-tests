"""Tests for $dateFromParts type validation of the year and optional numeric fields."""

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
    DATEFROMPARTS_INVALID_TYPE_ERROR,
    DATEFROMPARTS_YEAR_OUT_OF_RANGE_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [Year Type Acceptance]: year accepts any integer-valued numeric type.
DATEFROMPARTS_YEAR_TYPE_ACCEPT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_year",
        doc={"year": 2017},
        expression={"$dateFromParts": {"year": "$year"}},
        expected=datetime(2017, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should accept an int32 year",
    ),
    ExpressionTestCase(
        "int64_year",
        doc={"year": Int64(2017)},
        expression={"$dateFromParts": {"year": "$year"}},
        expected=datetime(2017, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should accept an int64 year",
    ),
    ExpressionTestCase(
        "double_year",
        doc={"year": 2017.0},
        expression={"$dateFromParts": {"year": "$year"}},
        expected=datetime(2017, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should accept an integer-valued double year",
    ),
    ExpressionTestCase(
        "decimal128_year",
        doc={"year": Decimal128("2017")},
        expression={"$dateFromParts": {"year": "$year"}},
        expected=datetime(2017, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should accept a decimal128 year",
    ),
]

# Property [Year Type Rejection]: a non-numeric year is rejected.
DATEFROMPARTS_YEAR_TYPE_ERROR_TESTS: list[ExpressionTestCase] = [
    *[
        ExpressionTestCase(
            f"year_type_{tid}",
            doc={"year": val},
            expression={"$dateFromParts": {"year": "$year"}},
            error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
            msg=f"$dateFromParts should reject a {tid} year",
        )
        for tid, val in [
            ("string", "2017"),
            ("bool", True),
            ("array", [2017]),
            ("object", {"y": 2017}),
            ("datetime", datetime(2017, 1, 1, tzinfo=timezone.utc)),
            ("regex", Regex(".*")),
            ("binary", Binary(b"\x01")),
            ("code", Code("function(){}")),
            ("timestamp", Timestamp(0, 1)),
            ("objectid", ObjectId("000000000000000000000000")),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    ExpressionTestCase(
        "single_element_array_year",
        doc={"year": [2020]},
        expression={"$dateFromParts": {"year": "$year"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject a single-element array year without unwrapping it",
    ),
]

# Property [Invalid Numeric Year]: a non-integral, NaN, or infinite year is rejected.
DATEFROMPARTS_YEAR_NUMERIC_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "non_integral_double_year",
        doc={"year": 2017.9},
        expression={"$dateFromParts": {"year": "$year"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject a non-integral double year",
    ),
    ExpressionTestCase(
        "nan_year",
        doc={"year": FLOAT_NAN},
        expression={"$dateFromParts": {"year": "$year"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject a NaN double year",
    ),
    ExpressionTestCase(
        "infinity_year",
        doc={"year": FLOAT_INFINITY},
        expression={"$dateFromParts": {"year": "$year"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject an infinite double year",
    ),
    ExpressionTestCase(
        "neg_infinity_year",
        doc={"year": FLOAT_NEGATIVE_INFINITY},
        expression={"$dateFromParts": {"year": "$year"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject a negative-infinite double year",
    ),
    ExpressionTestCase(
        "decimal128_nan_year",
        doc={"year": DECIMAL128_NAN},
        expression={"$dateFromParts": {"year": "$year"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject a NaN decimal128 year",
    ),
    ExpressionTestCase(
        "decimal128_infinity_year",
        doc={"year": DECIMAL128_INFINITY},
        expression={"$dateFromParts": {"year": "$year"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject an infinite decimal128 year",
    ),
    ExpressionTestCase(
        "decimal128_neg_infinity_year",
        doc={"year": DECIMAL128_NEGATIVE_INFINITY},
        expression={"$dateFromParts": {"year": "$year"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject a negative-infinite decimal128 year",
    ),
]

# Property [Negative Zero Year]: a negative-zero year is rejected as out of range.
DATEFROMPARTS_YEAR_NEG_ZERO_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "double_negative_zero_year",
        doc={"year": DOUBLE_NEGATIVE_ZERO},
        expression={"$dateFromParts": {"year": "$year"}},
        error_code=DATEFROMPARTS_YEAR_OUT_OF_RANGE_ERROR,
        msg="$dateFromParts should reject a double negative-zero year as out of range",
    ),
    ExpressionTestCase(
        "decimal128_negative_zero_year",
        doc={"year": DECIMAL128_NEGATIVE_ZERO},
        expression={"$dateFromParts": {"year": "$year"}},
        error_code=DATEFROMPARTS_YEAR_OUT_OF_RANGE_ERROR,
        msg="$dateFromParts should reject a decimal128 negative-zero year as out of range",
    ),
]

# Property [Optional Field Type Acceptance]: optional fields accept any integer-valued numeric type.
DATEFROMPARTS_OPTIONAL_TYPE_ACCEPT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int64_month",
        doc={"year": 2020, "month": Int64(6)},
        expression={"$dateFromParts": {"year": "$year", "month": "$month"}},
        expected=datetime(2020, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should accept an int64 month",
    ),
    ExpressionTestCase(
        "int64_day",
        doc={"year": 2020, "day": Int64(15)},
        expression={"$dateFromParts": {"year": "$year", "day": "$day"}},
        expected=datetime(2020, 1, 15, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should accept an int64 day",
    ),
    ExpressionTestCase(
        "int64_hour",
        doc={"year": 2020, "hour": Int64(10)},
        expression={"$dateFromParts": {"year": "$year", "hour": "$hour"}},
        expected=datetime(2020, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should accept an int64 hour",
    ),
    ExpressionTestCase(
        "int64_minute",
        doc={"year": 2020, "minute": Int64(30)},
        expression={"$dateFromParts": {"year": "$year", "minute": "$minute"}},
        expected=datetime(2020, 1, 1, 0, 30, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should accept an int64 minute",
    ),
    ExpressionTestCase(
        "int64_second",
        doc={"year": 2020, "second": Int64(45)},
        expression={"$dateFromParts": {"year": "$year", "second": "$second"}},
        expected=datetime(2020, 1, 1, 0, 0, 45, tzinfo=timezone.utc),
        msg="$dateFromParts should accept an int64 second",
    ),
    ExpressionTestCase(
        "int64_millisecond",
        doc={"year": 2020, "millisecond": Int64(500)},
        expression={"$dateFromParts": {"year": "$year", "millisecond": "$millisecond"}},
        expected=datetime(2020, 1, 1, 0, 0, 0, 500000, tzinfo=timezone.utc),
        msg="$dateFromParts should accept an int64 millisecond",
    ),
    ExpressionTestCase(
        "double_month",
        doc={"year": 2020, "month": 6.0},
        expression={"$dateFromParts": {"year": "$year", "month": "$month"}},
        expected=datetime(2020, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should accept an integer-valued double month",
    ),
    ExpressionTestCase(
        "decimal128_month",
        doc={"year": 2020, "month": Decimal128("6")},
        expression={"$dateFromParts": {"year": "$year", "month": "$month"}},
        expected=datetime(2020, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should accept a decimal128 month",
    ),
    ExpressionTestCase(
        "int64_isoWeekYear",
        doc={"isoWeekYear": Int64(2020)},
        expression={"$dateFromParts": {"isoWeekYear": "$isoWeekYear"}},
        expected=datetime(2019, 12, 30, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should accept an int64 isoWeekYear",
    ),
    ExpressionTestCase(
        "int64_isoWeek",
        doc={"isoWeekYear": 2020, "isoWeek": Int64(10)},
        expression={"$dateFromParts": {"isoWeekYear": "$isoWeekYear", "isoWeek": "$isoWeek"}},
        expected=datetime(2020, 3, 2, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should accept an int64 isoWeek",
    ),
    ExpressionTestCase(
        "int64_isoDayOfWeek",
        doc={"isoWeekYear": 2020, "isoWeek": 1, "isoDayOfWeek": Int64(3)},
        expression={
            "$dateFromParts": {
                "isoWeekYear": "$isoWeekYear",
                "isoWeek": "$isoWeek",
                "isoDayOfWeek": "$isoDayOfWeek",
            }
        },
        expected=datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should accept an int64 isoDayOfWeek",
    ),
]

# Property [Optional Field Type Rejection]: a non-numeric optional field is rejected. The month
# field is covered exhaustively; the other optional fields confirm the shared rejection is wired.
DATEFROMPARTS_OPTIONAL_TYPE_ERROR_TESTS: list[ExpressionTestCase] = [
    *[
        ExpressionTestCase(
            f"month_type_{tid}",
            doc={"year": 2020, "month": val},
            expression={"$dateFromParts": {"year": "$year", "month": "$month"}},
            error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
            msg=f"$dateFromParts should reject a {tid} month",
        )
        for tid, val in [
            ("string", "June"),
            ("bool", True),
            ("array", [6]),
            ("object", {"m": 6}),
            ("datetime", datetime(2020, 1, 1, tzinfo=timezone.utc)),
            ("objectid", ObjectId("000000000000000000000000")),
            ("timestamp", Timestamp(0, 1)),
            ("binary", Binary(b"\x01")),
            ("regex", Regex(".*")),
            ("code", Code("function(){}")),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    ExpressionTestCase(
        "string_day",
        doc={"year": 2020, "day": "15"},
        expression={"$dateFromParts": {"year": "$year", "day": "$day"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject a string day",
    ),
    ExpressionTestCase(
        "string_hour",
        doc={"year": 2020, "hour": "10"},
        expression={"$dateFromParts": {"year": "$year", "hour": "$hour"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject a string hour",
    ),
    ExpressionTestCase(
        "string_minute",
        doc={"year": 2020, "minute": "30"},
        expression={"$dateFromParts": {"year": "$year", "minute": "$minute"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject a string minute",
    ),
    ExpressionTestCase(
        "string_second",
        doc={"year": 2020, "second": "45"},
        expression={"$dateFromParts": {"year": "$year", "second": "$second"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject a string second",
    ),
    ExpressionTestCase(
        "string_millisecond",
        doc={"year": 2020, "millisecond": "500"},
        expression={"$dateFromParts": {"year": "$year", "millisecond": "$millisecond"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject a string millisecond",
    ),
    ExpressionTestCase(
        "bool_day",
        doc={"year": 2020, "day": True},
        expression={"$dateFromParts": {"year": "$year", "day": "$day"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject a bool day",
    ),
    ExpressionTestCase(
        "bool_hour",
        doc={"year": 2020, "hour": False},
        expression={"$dateFromParts": {"year": "$year", "hour": "$hour"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject a bool hour",
    ),
    ExpressionTestCase(
        "object_day",
        doc={"year": 2020, "day": {"d": 15}},
        expression={"$dateFromParts": {"year": "$year", "day": "$day"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject an object day",
    ),
    ExpressionTestCase(
        "string_isoWeekYear",
        doc={"isoWeekYear": "2020"},
        expression={"$dateFromParts": {"isoWeekYear": "$isoWeekYear"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject a string isoWeekYear",
    ),
    ExpressionTestCase(
        "bool_isoWeekYear",
        doc={"isoWeekYear": True},
        expression={"$dateFromParts": {"isoWeekYear": "$isoWeekYear"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject a bool isoWeekYear",
    ),
    ExpressionTestCase(
        "string_isoWeek",
        doc={"isoWeekYear": 2020, "isoWeek": "10"},
        expression={"$dateFromParts": {"isoWeekYear": "$isoWeekYear", "isoWeek": "$isoWeek"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject a string isoWeek",
    ),
    ExpressionTestCase(
        "string_isoDayOfWeek",
        doc={"isoWeekYear": 2020, "isoDayOfWeek": "3"},
        expression={
            "$dateFromParts": {"isoWeekYear": "$isoWeekYear", "isoDayOfWeek": "$isoDayOfWeek"}
        },
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject a string isoDayOfWeek",
    ),
]

# Property [Non-Integral Optional Field]: a non-integral double optional field is rejected.
DATEFROMPARTS_OPTIONAL_NON_INTEGRAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "non_integral_double_month",
        doc={"year": 2020, "month": 6.5},
        expression={"$dateFromParts": {"year": "$year", "month": "$month"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject a non-integral double month",
    ),
    ExpressionTestCase(
        "non_integral_double_day",
        doc={"year": 2020, "day": 15.5},
        expression={"$dateFromParts": {"year": "$year", "day": "$day"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject a non-integral double day",
    ),
    ExpressionTestCase(
        "non_integral_double_hour",
        doc={"year": 2020, "hour": 10.5},
        expression={"$dateFromParts": {"year": "$year", "hour": "$hour"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject a non-integral double hour",
    ),
    ExpressionTestCase(
        "non_integral_double_minute",
        doc={"year": 2020, "minute": 30.5},
        expression={"$dateFromParts": {"year": "$year", "minute": "$minute"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject a non-integral double minute",
    ),
    ExpressionTestCase(
        "non_integral_double_second",
        doc={"year": 2020, "second": 45.5},
        expression={"$dateFromParts": {"year": "$year", "second": "$second"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject a non-integral double second",
    ),
    ExpressionTestCase(
        "non_integral_double_millisecond",
        doc={"year": 2020, "millisecond": 500.5},
        expression={"$dateFromParts": {"year": "$year", "millisecond": "$millisecond"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject a non-integral double millisecond",
    ),
    ExpressionTestCase(
        "non_integral_double_isoWeekYear",
        doc={"isoWeekYear": 2020.5},
        expression={"$dateFromParts": {"isoWeekYear": "$isoWeekYear"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject a non-integral double isoWeekYear",
    ),
    ExpressionTestCase(
        "non_integral_double_isoWeek",
        doc={"isoWeekYear": 2020, "isoWeek": 10.5},
        expression={"$dateFromParts": {"isoWeekYear": "$isoWeekYear", "isoWeek": "$isoWeek"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject a non-integral double isoWeek",
    ),
    ExpressionTestCase(
        "non_integral_double_isoDayOfWeek",
        doc={"isoWeekYear": 2020, "isoDayOfWeek": 3.5},
        expression={
            "$dateFromParts": {"isoWeekYear": "$isoWeekYear", "isoDayOfWeek": "$isoDayOfWeek"}
        },
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject a non-integral double isoDayOfWeek",
    ),
]

# Property [Non-Finite Optional Field]: a NaN or infinite double or decimal128 optional field is
# rejected.
DATEFROMPARTS_OPTIONAL_NON_FINITE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "double_infinity_month",
        doc={"year": 2020, "month": FLOAT_INFINITY},
        expression={"$dateFromParts": {"year": "$year", "month": "$month"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject an infinite double month",
    ),
    ExpressionTestCase(
        "double_neg_infinity_month",
        doc={"year": 2020, "month": FLOAT_NEGATIVE_INFINITY},
        expression={"$dateFromParts": {"year": "$year", "month": "$month"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject a negative-infinite double month",
    ),
    ExpressionTestCase(
        "double_nan_month",
        doc={"year": 2020, "month": FLOAT_NAN},
        expression={"$dateFromParts": {"year": "$year", "month": "$month"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject a NaN double month",
    ),
    ExpressionTestCase(
        "decimal128_infinity_month",
        doc={"year": 2020, "month": DECIMAL128_INFINITY},
        expression={"$dateFromParts": {"year": "$year", "month": "$month"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject an infinite decimal128 month",
    ),
    ExpressionTestCase(
        "decimal128_neg_infinity_month",
        doc={"year": 2020, "month": DECIMAL128_NEGATIVE_INFINITY},
        expression={"$dateFromParts": {"year": "$year", "month": "$month"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject a negative-infinite decimal128 month",
    ),
    ExpressionTestCase(
        "decimal128_nan_month",
        doc={"year": 2020, "month": DECIMAL128_NAN},
        expression={"$dateFromParts": {"year": "$year", "month": "$month"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject a NaN decimal128 month",
    ),
    ExpressionTestCase(
        "decimal128_infinity_isoWeekYear",
        doc={"isoWeekYear": DECIMAL128_INFINITY},
        expression={"$dateFromParts": {"isoWeekYear": "$isoWeekYear"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject an infinite decimal128 isoWeekYear",
    ),
    ExpressionTestCase(
        "decimal128_neg_infinity_isoWeekYear",
        doc={"isoWeekYear": DECIMAL128_NEGATIVE_INFINITY},
        expression={"$dateFromParts": {"isoWeekYear": "$isoWeekYear"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject a negative-infinite decimal128 isoWeekYear",
    ),
]

DATEFROMPARTS_TYPE_TESTS: list[ExpressionTestCase] = (
    DATEFROMPARTS_YEAR_TYPE_ACCEPT_TESTS
    + DATEFROMPARTS_YEAR_TYPE_ERROR_TESTS
    + DATEFROMPARTS_YEAR_NUMERIC_ERROR_TESTS
    + DATEFROMPARTS_YEAR_NEG_ZERO_TESTS
    + DATEFROMPARTS_OPTIONAL_TYPE_ACCEPT_TESTS
    + DATEFROMPARTS_OPTIONAL_TYPE_ERROR_TESTS
    + DATEFROMPARTS_OPTIONAL_NON_INTEGRAL_TESTS
    + DATEFROMPARTS_OPTIONAL_NON_FINITE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATEFROMPARTS_TYPE_TESTS))
def test_dateFromParts_types(collection, test_case: ExpressionTestCase):
    """Test $dateFromParts type validation."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
