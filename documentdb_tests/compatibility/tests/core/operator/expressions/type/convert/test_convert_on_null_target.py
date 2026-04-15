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
from documentdb_tests.framework.test_constants import MISSING

# Property [onNull Override]: the onNull parameter overrides the null result
# with a custom value when input is null or missing, and the value is returned
# as-is without conversion to the target type.
# Group 1: fixed onNull value, vary target type. Proves the target type does
# not affect the onNull return path.
_ON_NULL_VARY_TARGET_PATTERNS: list[ConvertTest] = [
    ConvertTest(
        "on_null_target_bool",
        input=_PLACEHOLDER,
        to="bool",
        on_null="fallback",
        expected="fallback",
        msg="$convert onNull should return value as-is for bool target ({prefix} input)",
    ),
    ConvertTest(
        "on_null_target_int",
        input=_PLACEHOLDER,
        to="int",
        on_null="fallback",
        expected="fallback",
        msg="$convert onNull should return value as-is for int target ({prefix} input)",
    ),
    ConvertTest(
        "on_null_target_long",
        input=_PLACEHOLDER,
        to="long",
        on_null="fallback",
        expected="fallback",
        msg="$convert onNull should return value as-is for long target ({prefix} input)",
    ),
    ConvertTest(
        "on_null_target_double",
        input=_PLACEHOLDER,
        to="double",
        on_null="fallback",
        expected="fallback",
        msg="$convert onNull should return value as-is for double target ({prefix} input)",
    ),
    ConvertTest(
        "on_null_target_decimal",
        input=_PLACEHOLDER,
        to="decimal",
        on_null="fallback",
        expected="fallback",
        msg="$convert onNull should return value as-is for decimal target ({prefix} input)",
    ),
    ConvertTest(
        "on_null_target_date",
        input=_PLACEHOLDER,
        to="date",
        on_null="fallback",
        expected="fallback",
        msg="$convert onNull should return value as-is for date target ({prefix} input)",
    ),
    ConvertTest(
        "on_null_target_string",
        input=_PLACEHOLDER,
        to="string",
        on_null=42,
        expected=42,
        msg="$convert onNull should return value as-is for string target ({prefix} input)",
    ),
    ConvertTest(
        "on_null_target_objectId",
        input=_PLACEHOLDER,
        to="objectId",
        on_null="fallback",
        expected="fallback",
        msg="$convert onNull should return value as-is for objectId target ({prefix} input)",
    ),
    ConvertTest(
        "on_null_target_binData",
        input=_PLACEHOLDER,
        to="binData",
        on_null="fallback",
        expected="fallback",
        msg="$convert onNull should return value as-is for binData target ({prefix} input)",
    ),
    ConvertTest(
        "on_null_target_regex",
        input=_PLACEHOLDER,
        to="regex",
        on_null="fallback",
        expected="fallback",
        msg="$convert onNull should return value as-is for unsupported target regex ({prefix})",
    ),
    ConvertTest(
        "on_null_target_timestamp",
        input=_PLACEHOLDER,
        to="timestamp",
        on_null="fallback",
        expected="fallback",
        msg="$convert onNull should return value as-is for unsupported target timestamp ({prefix})",
    ),
    ConvertTest(
        "on_null_target_null",
        input=_PLACEHOLDER,
        to="null",
        on_null="fallback",
        expected="fallback",
        msg="$convert onNull should return value as-is for unsupported target null ({prefix})",
    ),
    ConvertTest(
        "on_null_target_array",
        input=_PLACEHOLDER,
        to="array",
        on_null="fallback",
        expected="fallback",
        msg="$convert onNull should return value as-is for unsupported target array ({prefix})",
    ),
    ConvertTest(
        "on_null_target_object",
        input=_PLACEHOLDER,
        to="object",
        on_null="fallback",
        expected="fallback",
        msg="$convert onNull should return value as-is for unsupported target object ({prefix})",
    ),
    ConvertTest(
        "on_null_target_minKey",
        input=_PLACEHOLDER,
        to="minKey",
        on_null="fallback",
        expected="fallback",
        msg="$convert onNull should return value as-is for unsupported target minKey ({prefix})",
    ),
    ConvertTest(
        "on_null_target_maxKey",
        input=_PLACEHOLDER,
        to="maxKey",
        on_null="fallback",
        expected="fallback",
        msg="$convert onNull should return value as-is for unsupported target maxKey ({prefix})",
    ),
    ConvertTest(
        "on_null_target_javascript",
        input=_PLACEHOLDER,
        to="javascript",
        on_null="fallback",
        expected="fallback",
        msg="$convert onNull should return value as-is for unsupported target js ({prefix})",
    ),
    ConvertTest(
        "on_null_target_javascriptWithScope",
        input=_PLACEHOLDER,
        to="javascriptWithScope",
        on_null="fallback",
        expected="fallback",
        msg="$convert onNull should return value as-is for unsupported jsWithScope ({prefix})",
    ),
    ConvertTest(
        "on_null_target_symbol",
        input=_PLACEHOLDER,
        to="symbol",
        on_null="fallback",
        expected="fallback",
        msg="$convert onNull should return value as-is for unsupported target symbol ({prefix})",
    ),
    ConvertTest(
        "on_null_target_undefined",
        input=_PLACEHOLDER,
        to="undefined",
        on_null="fallback",
        expected="fallback",
        msg="$convert onNull should return value as-is for unsupported target undefined ({prefix})",
    ),
    ConvertTest(
        "on_null_target_dbPointer",
        input=_PLACEHOLDER,
        to="dbPointer",
        on_null="fallback",
        expected="fallback",
        msg="$convert onNull should return value as-is for unsupported target dbPointer ({prefix})",
    ),
]

# Property [onNull Target Null]: onNull value is returned when target type is null.
CONVERT_ON_NULL_TARGET_NULL_TESTS: list[ConvertTest] = _build_null_tests(
    _ON_NULL_VARY_TARGET_PATTERNS, None, "null"
)

# Property [onNull Target Missing]: onNull value is returned when target type is missing.
CONVERT_ON_NULL_TARGET_MISSING_TESTS: list[ConvertTest] = _build_null_tests(
    _ON_NULL_VARY_TARGET_PATTERNS, MISSING, "missing"
)

CONVERT_ON_NULL_TARGET_ALL_TESTS = (
    CONVERT_ON_NULL_TARGET_NULL_TESTS + CONVERT_ON_NULL_TARGET_MISSING_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(CONVERT_ON_NULL_TARGET_ALL_TESTS))
def test_convert_on_null_target(collection, test_case: ConvertTest):
    """Test $convert onNull with varying target types."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
