from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.type.convert.utils.convert_common import (  # noqa: E501
    _PLACEHOLDER,
    ConvertTest,
    _build_null_tests,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ZERO,
    DOUBLE_ZERO,
    MISSING,
)

# Property [Null Skips Validation]: when input is null or missing, format,
# byteOrder, and subtype validation is entirely skipped, even for invalid
# values and wrong types.
_NULL_SKIPS_VALIDATION_PATTERNS: list[ConvertTest] = [
    ConvertTest(
        "skips_invalid_format_string",
        input=_PLACEHOLDER,
        to="string",
        format="invalid_format",
        expected=None,
        msg="$convert should skip format validation when input is {prefix}",
    ),
    ConvertTest(
        "skips_invalid_format_type",
        input=_PLACEHOLDER,
        to="string",
        format=12345,
        expected=None,
        msg="$convert should skip format type validation when input is {prefix}",
    ),
    ConvertTest(
        "skips_invalid_byte_order_string",
        input=_PLACEHOLDER,
        to="string",
        byte_order="invalid_order",
        expected=None,
        msg="$convert should skip byteOrder validation when input is {prefix}",
    ),
    ConvertTest(
        "skips_invalid_byte_order_type",
        input=_PLACEHOLDER,
        to="string",
        byte_order=12345,
        expected=None,
        msg="$convert should skip byteOrder type validation when input is {prefix}",
    ),
    ConvertTest(
        "skips_invalid_subtype_value",
        input=_PLACEHOLDER,
        to={"type": "binData", "subtype": 999},
        expected=None,
        msg="$convert should skip subtype validation when input is {prefix}",
    ),
    ConvertTest(
        "skips_invalid_subtype_type",
        input=_PLACEHOLDER,
        to={"type": "binData", "subtype": "invalid"},
        expected=None,
        msg="$convert should skip subtype type validation when input is {prefix}",
    ),
]

# Property [Null Input Skips Validation]: null input bypasses to/format/byteOrder validation.
CONVERT_NULL_INPUT_SKIPS_VALIDATION_TESTS: list[ConvertTest] = _build_null_tests(
    _NULL_SKIPS_VALIDATION_PATTERNS, None, "null"
)

# Property [Missing Input Skips Validation]: missing input bypasses to/format/byteOrder validation.
CONVERT_MISSING_INPUT_SKIPS_VALIDATION_TESTS: list[ConvertTest] = _build_null_tests(
    _NULL_SKIPS_VALIDATION_PATTERNS, MISSING, "missing"
)

# Property [Null To Skips Validation]: when to is null or missing, format and
# byteOrder validation is skipped even for invalid values and wrong types.
_NULL_TO_SKIPS_VALIDATION_PATTERNS: list[ConvertTest] = [
    ConvertTest(
        "to_skips_invalid_byte_order",
        input="hello",
        to=_PLACEHOLDER,
        byte_order="invalid",
        expected=None,
        msg="$convert should skip byteOrder validation when to is {prefix}",
    ),
    ConvertTest(
        "to_skips_wrong_type_byte_order",
        input="hello",
        to=_PLACEHOLDER,
        byte_order=12345,
        expected=None,
        msg="$convert should skip byteOrder type validation when to is {prefix}",
    ),
    ConvertTest(
        "to_skips_invalid_format",
        input="hello",
        to=_PLACEHOLDER,
        format="invalid",
        expected=None,
        msg="$convert should skip format validation when to is {prefix}",
    ),
    ConvertTest(
        "to_skips_wrong_type_format",
        input="hello",
        to=_PLACEHOLDER,
        format=12345,
        expected=None,
        msg="$convert should skip format type validation when to is {prefix}",
    ),
]

# Property [Null To Skips Validation]: null to bypasses format/byteOrder validation.
CONVERT_NULL_TO_SKIPS_VALIDATION_TESTS: list[ConvertTest] = _build_null_tests(
    _NULL_TO_SKIPS_VALIDATION_PATTERNS, None, "null", field="to"
)

# Property [Missing To Skips Validation]: missing to bypasses format/byteOrder validation.
CONVERT_MISSING_TO_SKIPS_VALIDATION_TESTS: list[ConvertTest] = _build_null_tests(
    _NULL_TO_SKIPS_VALIDATION_PATTERNS, MISSING, "missing", field="to"
)

# Property [Falsy Values Do Not Trigger onNull]: falsy values proceed to normal
# conversion and do not trigger onNull.
CONVERT_FALSY_NOT_NULL_TESTS: list[ConvertTest] = [
    ConvertTest(
        "falsy_false_not_null",
        input=False,
        to="bool",
        on_null="fallback",
        expected=False,
        msg="$convert should not trigger onNull for false",
    ),
    ConvertTest(
        "falsy_zero_int_not_null",
        input=0,
        to="bool",
        on_null="fallback",
        expected=False,
        msg="$convert should not trigger onNull for int 0",
    ),
    ConvertTest(
        "falsy_zero_double_not_null",
        input=DOUBLE_ZERO,
        to="bool",
        on_null="fallback",
        expected=False,
        msg="$convert should not trigger onNull for double 0.0",
    ),
    ConvertTest(
        "falsy_empty_string_not_null",
        input="",
        to="string",
        on_null="fallback",
        expected="",
        msg="$convert should not trigger onNull for empty string",
    ),
    ConvertTest(
        "falsy_decimal_zero_not_null",
        input=DECIMAL128_ZERO,
        to="bool",
        on_null="fallback",
        expected=False,
        msg="$convert should not trigger onNull for Decimal128('0')",
    ),
    ConvertTest(
        "falsy_empty_array_not_null",
        input=[],
        to="bool",
        on_null="fallback",
        expected=True,
        msg="$convert should not trigger onNull for empty array",
    ),
]

# Property [Null To Precedence]: when to is null/missing and input is non-null,
# the result is null without triggering onError or onNull; when both input and
# to are null/missing, the onNull path is taken.
CONVERT_NULLISH_TO_PRECEDENCE_TESTS: list[ConvertTest] = [
    ConvertTest(
        "nullish_to_null_on_error_not_triggered",
        input="hello",
        to=None,
        on_error="error_fallback",
        expected=None,
        msg="$convert should not trigger onError when to is null",
    ),
    ConvertTest(
        "nullish_to_null_on_null_not_triggered",
        input="hello",
        to=None,
        on_null="null_fallback",
        expected=None,
        msg="$convert should not trigger onNull when to is null and input is non-null",
    ),
    ConvertTest(
        "nullish_to_both_null_on_null_triggered",
        input=None,
        to=None,
        on_null="null_fallback",
        expected="null_fallback",
        msg="$convert should take onNull path when both input and to are null",
    ),
    ConvertTest(
        "nullish_to_both_missing_on_null_triggered",
        input=MISSING,
        to=MISSING,
        on_null="null_fallback",
        expected="null_fallback",
        msg="$convert should take onNull path when both input and to are missing",
    ),
    ConvertTest(
        "nullish_to_input_null_to_missing_on_null_triggered",
        input=None,
        to=MISSING,
        on_null="null_fallback",
        expected="null_fallback",
        msg="$convert should take onNull path when input is null and to is missing",
    ),
    ConvertTest(
        "nullish_to_input_missing_to_null_on_null_triggered",
        input=MISSING,
        to=None,
        on_null="null_fallback",
        expected="null_fallback",
        msg="$convert should take onNull path when input is missing and to is null",
    ),
]

# Property [onNull Expression Evaluation]: onNull accepts expressions; an
# expression returning null triggers onNull, and the onNull value itself can be
# an expression that is evaluated before being returned.
CONVERT_ON_NULL_EXPRESSION_TESTS: list[ConvertTest] = [
    ConvertTest(
        "on_null_with_expression_returning_null",
        input={"$literal": None},
        to="bool",
        on_null="fallback",
        expected="fallback",
        msg="$convert onNull should trigger when input expression returns null",
    ),
    ConvertTest(
        "on_null_with_expression_value",
        input=None,
        to="bool",
        on_null={"$add": [1, 2]},
        expected=3,
        msg="$convert onNull should evaluate expression and return result",
    ),
]

CONVERT_NULL_VALIDATION_TESTS = (
    CONVERT_NULL_INPUT_SKIPS_VALIDATION_TESTS
    + CONVERT_MISSING_INPUT_SKIPS_VALIDATION_TESTS
    + CONVERT_NULL_TO_SKIPS_VALIDATION_TESTS
    + CONVERT_MISSING_TO_SKIPS_VALIDATION_TESTS
    + CONVERT_FALSY_NOT_NULL_TESTS
    + CONVERT_NULLISH_TO_PRECEDENCE_TESTS
    + CONVERT_ON_NULL_EXPRESSION_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(CONVERT_NULL_VALIDATION_TESTS))
def test_convert_null_validation(collection, test_case: ConvertTest):
    """Test $convert null validation edge cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
