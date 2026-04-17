from __future__ import annotations

import pytest
from bson import Binary, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.type.convert.utils.convert_common import (  # noqa: E501
    ConvertTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    CONVERSION_FAILURE_ERROR,
    CONVERT_MISSING_FORMAT_ERROR,
    DATETOSTRING_YEAR_RANGE_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Eager Constant Evaluation]: constant expressions in onNull and
# onError are evaluated eagerly at optimization time regardless of whether
# their path is triggered.
CONVERT_EAGER_EVAL_TESTS: list[ConvertTest] = [
    ConvertTest(
        "on_null_constant_error_with_non_null_input",
        input="hello",
        to="string",
        on_null={"$divide": [1, 0]},
        error_code=BAD_VALUE_ERROR,
        msg=(
            "$convert should eagerly evaluate constant onNull expression even"
            " when input is non-null"
        ),
    ),
    ConvertTest(
        "on_error_constant_error_with_successful_conversion",
        input="42",
        to="int",
        on_error={"$divide": [1, 0]},
        error_code=BAD_VALUE_ERROR,
        msg=(
            "$convert should eagerly evaluate constant onError expression even"
            " when conversion succeeds"
        ),
    ),
]

# Property [Format Parameter Required]: converting between string and binData
# without specifying the format parameter produces a missing-format error.
CONVERT_FORMAT_REQUIRED_ERROR_TESTS: list[ConvertTest] = [
    ConvertTest(
        "fmt_required_err_string_to_bindata",
        input="hello",
        to="binData",
        error_code=CONVERT_MISSING_FORMAT_ERROR,
        msg="$convert should reject string to binData without format",
    ),
    ConvertTest(
        "fmt_required_err_bindata_sub0_to_string",
        input=Binary(b"hello", 0),
        to="string",
        error_code=CONVERT_MISSING_FORMAT_ERROR,
        msg="$convert should reject subtype 0 binData to string without format",
    ),
    ConvertTest(
        "fmt_required_err_bindata_sub4_to_string",
        input=Binary(b"hello", 4),
        to="string",
        error_code=CONVERT_MISSING_FORMAT_ERROR,
        msg="$convert should reject subtype 4 binData to string without format",
    ),
    ConvertTest(
        "fmt_required_err_bindata_sub4_uuid_to_string",
        input=Binary(
            b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10",
            4,
        ),
        to="string",
        error_code=CONVERT_MISSING_FORMAT_ERROR,
        msg="$convert should reject subtype 4 UUID binData to string without format",
    ),
]

# Property [to Unsupported Target Type Errors]: recognized but unsupported
# target types produce a conversion failure error, which is caught by onError.
CONVERT_UNSUPPORTED_TARGET_ERROR_TESTS: list[ConvertTest] = [
    ConvertTest(
        "unsupported_target_null",
        input=42,
        to="null",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject unsupported target type null",
    ),
    ConvertTest(
        "unsupported_target_array",
        input=42,
        to="array",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject unsupported target type array",
    ),
    ConvertTest(
        "unsupported_target_object",
        input=42,
        to="object",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject unsupported target type object",
    ),
    ConvertTest(
        "unsupported_target_regex",
        input=42,
        to="regex",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject unsupported target type regex",
    ),
    ConvertTest(
        "unsupported_target_timestamp",
        input=42,
        to="timestamp",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject unsupported target type timestamp",
    ),
    ConvertTest(
        "unsupported_target_minkey",
        input=42,
        to="minKey",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject unsupported target type minKey",
    ),
    ConvertTest(
        "unsupported_target_maxkey",
        input=42,
        to="maxKey",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject unsupported target type maxKey",
    ),
    ConvertTest(
        "unsupported_target_javascript",
        input=42,
        to="javascript",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject unsupported target type javascript",
    ),
    ConvertTest(
        "unsupported_target_javascriptWithScope",
        input=42,
        to="javascriptWithScope",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject unsupported target type jsWithScope",
    ),
    ConvertTest(
        "unsupported_target_symbol",
        input=42,
        to="symbol",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject unsupported target type symbol",
    ),
    ConvertTest(
        "unsupported_target_undefined",
        input=42,
        to="undefined",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject unsupported target type undefined",
    ),
    ConvertTest(
        "unsupported_target_dbPointer",
        input=42,
        to="dbPointer",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject unsupported target type dbPointer",
    ),
]

# Property [Date to String Year Range Error]: converting a date with year
# outside 0-9999 to string produces a year range error, which is caught by
# onError.
# Note: $toDate is used because Python's datetime cannot represent years
# outside 1-9999, so the Date must be constructed server-side.
CONVERT_DATE_STRING_YEAR_RANGE_ERROR_TESTS: list[ConvertTest] = [
    ConvertTest(
        "date_str_year_0_success",
        input={"$toDate": Int64(-62167219200000)},
        to="string",
        expected="0000-01-01T00:00:00.000Z",
        msg="$convert should succeed for date-to-string at year 0",
    ),
    ConvertTest(
        "date_str_year_err_negative",
        input={"$toDate": Int64(-62167219200001)},
        to="string",
        error_code=DATETOSTRING_YEAR_RANGE_ERROR,
        msg="$convert should reject date-to-string when year is before 0",
    ),
    ConvertTest(
        "date_str_year_err_above_9999",
        input={"$toDate": Int64(253402300800000)},
        to="string",
        error_code=DATETOSTRING_YEAR_RANGE_ERROR,
        msg="$convert should reject date-to-string when year is above 9999",
    ),
    ConvertTest(
        "date_str_year_err_on_error_caught_negative",
        input={"$toDate": Int64(-62167219200001)},
        to="string",
        on_error="caught",
        expected="caught",
        msg="$convert onError should catch date-to-string year range error for negative year",
        marks=(
            pytest.mark.engine_xfail(
                engine="mongodb",
                reason="MongoDB evaluates year-range errors at optimize time, before onError fires",
                raises=AssertionError,
            ),
        ),
    ),
    ConvertTest(
        "date_str_year_err_on_error_caught_above_9999",
        input={"$toDate": Int64(253402300800000)},
        to="string",
        on_error="caught",
        expected="caught",
        msg="$convert onError should catch date-to-string year range error for year above 9999",
        marks=(
            pytest.mark.engine_xfail(
                engine="mongodb",
                reason="MongoDB evaluates year-range errors at optimize time, before onError fires",
                raises=AssertionError,
            ),
        ),
    ),
]

CONVERT_CONVERSION_ERROR_TESTS = (
    CONVERT_EAGER_EVAL_TESTS
    + CONVERT_FORMAT_REQUIRED_ERROR_TESTS
    + CONVERT_UNSUPPORTED_TARGET_ERROR_TESTS
    + CONVERT_DATE_STRING_YEAR_RANGE_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(CONVERT_CONVERSION_ERROR_TESTS))
def test_convert_conversion_errors(collection, test_case: ConvertTest):
    """Test $convert conversion errors."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
