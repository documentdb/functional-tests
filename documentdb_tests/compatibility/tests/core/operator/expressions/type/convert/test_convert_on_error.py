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
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NAN,
    FLOAT_INFINITY,
    FLOAT_NAN,
    INT32_OVERFLOW,
    STRING_SIZE_LIMIT_BYTES,
)

# Property [onError Catches Conversion Errors]: when a conversion error occurs
# and onError is specified, the onError value is returned as-is regardless of
# its BSON type.
CONVERT_ON_ERROR_TESTS: list[ConvertTest] = [
    ConvertTest(
        "on_error_int_fallback_for_string_target",
        input="abc",
        to="objectId",
        on_error=42,
        expected=42,
        msg="$convert onError should return int without converting to target type",
    ),
    ConvertTest(
        "on_error_catches_overflow",
        input=Int64(INT32_OVERFLOW),
        to="int",
        on_error="caught",
        expected="caught",
        msg="$convert onError should catch int32 overflow",
    ),
    ConvertTest(
        "on_error_catches_nan_to_int",
        input=FLOAT_NAN,
        to="int",
        on_error="caught",
        expected="caught",
        msg="$convert onError should catch NaN to int conversion",
    ),
    ConvertTest(
        "on_error_catches_infinity_to_int",
        input=FLOAT_INFINITY,
        to="int",
        on_error="caught",
        expected="caught",
        msg="$convert onError should catch Infinity to int conversion",
    ),
    ConvertTest(
        "on_error_catches_decimal128_nan_to_int",
        input=DECIMAL128_NAN,
        to="int",
        on_error="caught",
        expected="caught",
        msg="$convert onError should catch Decimal128 NaN to int conversion",
    ),
    ConvertTest(
        "on_error_catches_unsupported_type_combo",
        input=[1, 2],
        to="int",
        on_error="caught",
        expected="caught",
        msg="$convert onError should catch unsupported source type for target",
    ),
    ConvertTest(
        "on_error_catches_bindata_wrong_length",
        input=Binary(b"\x01\x02\x03"),
        to="int",
        on_error="caught",
        expected="caught",
        msg="$convert onError should catch BinData with wrong byte length",
    ),
    ConvertTest(
        "on_error_catches_uuid_subtype_mismatch",
        input="550e8400-e29b-41d4-a716-446655440000",
        to={"type": "binData", "subtype": 0},
        format="uuid",
        on_error="caught",
        expected="caught",
        msg="$convert onError should catch uuid format with non-4 subtype",
    ),
    ConvertTest(
        "on_error_catches_invalid_date_string",
        input="\u20002024-06-15T12:30:45Z",
        to="date",
        on_error="caught",
        expected="caught",
        msg="$convert onError should catch invalid string to date conversion",
    ),
    ConvertTest(
        "on_error_catches_string_size_limit",
        input=Binary(b"A" * (STRING_SIZE_LIMIT_BYTES // 2)),
        to="string",
        format="hex",
        on_error="caught",
        expected="caught",
        msg="$convert onError should catch string size limit error for BinData-to-string",
    ),
]

# Property [onError Not Triggered]: onError is not triggered when conversion
# succeeds or when input is null (the onNull path takes precedence).
CONVERT_ON_ERROR_NOT_TRIGGERED_TESTS: list[ConvertTest] = [
    ConvertTest(
        "on_error_not_triggered_on_success",
        input="123",
        to="int",
        on_error="fallback",
        expected=123,
        msg="$convert onError should not trigger when conversion succeeds",
    ),
    ConvertTest(
        "on_error_not_triggered_on_null_input",
        input=None,
        to="int",
        on_error="error_fallback",
        on_null="null_fallback",
        expected="null_fallback",
        msg="$convert should take onNull path instead of onError when input is null",
    ),
]

CONVERT_ON_ERROR_SUCCESS_TESTS = CONVERT_ON_ERROR_TESTS + CONVERT_ON_ERROR_NOT_TRIGGERED_TESTS


@pytest.mark.parametrize("test_case", pytest_params(CONVERT_ON_ERROR_SUCCESS_TESTS))
def test_convert_on_error(collection, test_case: ConvertTest):
    """Test $convert onError behavior."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
