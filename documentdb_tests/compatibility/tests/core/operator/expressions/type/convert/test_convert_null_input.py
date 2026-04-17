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

# Property [Null Input]: when input is null or a value treated as null, the
# result is null for all target types.
_NULL_INPUT_PATTERNS: list[ConvertTest] = [
    ConvertTest(
        "input_to_bool",
        input=_PLACEHOLDER,
        to="bool",
        expected=None,
        msg="$convert should return null when input is {prefix} for bool target",
    ),
    ConvertTest(
        "input_to_int",
        input=_PLACEHOLDER,
        to="int",
        expected=None,
        msg="$convert should return null when input is {prefix} for int target",
    ),
    ConvertTest(
        "input_to_long",
        input=_PLACEHOLDER,
        to="long",
        expected=None,
        msg="$convert should return null when input is {prefix} for long target",
    ),
    ConvertTest(
        "input_to_double",
        input=_PLACEHOLDER,
        to="double",
        expected=None,
        msg="$convert should return null when input is {prefix} for double target",
    ),
    ConvertTest(
        "input_to_decimal",
        input=_PLACEHOLDER,
        to="decimal",
        expected=None,
        msg="$convert should return null when input is {prefix} for decimal target",
    ),
    ConvertTest(
        "input_to_date",
        input=_PLACEHOLDER,
        to="date",
        expected=None,
        msg="$convert should return null when input is {prefix} for date target",
    ),
    ConvertTest(
        "input_to_string",
        input=_PLACEHOLDER,
        to="string",
        expected=None,
        msg="$convert should return null when input is {prefix} for string target",
    ),
    ConvertTest(
        "input_to_objectId",
        input=_PLACEHOLDER,
        to="objectId",
        expected=None,
        msg="$convert should return null when input is {prefix} for objectId target",
    ),
    ConvertTest(
        "input_to_binData",
        input=_PLACEHOLDER,
        to="binData",
        expected=None,
        msg="$convert should return null when input is {prefix} for binData target",
    ),
    ConvertTest(
        "input_to_regex_unsupported",
        input=_PLACEHOLDER,
        to="regex",
        expected=None,
        msg="$convert should return null when input is {prefix} for unsupported target regex",
    ),
    ConvertTest(
        "input_to_timestamp_unsupported",
        input=_PLACEHOLDER,
        to="timestamp",
        expected=None,
        msg="$convert should return null when input is {prefix} for unsupported target timestamp",
    ),
    ConvertTest(
        "input_to_null_unsupported",
        input=_PLACEHOLDER,
        to="null",
        expected=None,
        msg="$convert should return null when input is {prefix} for unsupported target null",
    ),
    ConvertTest(
        "input_to_array_unsupported",
        input=_PLACEHOLDER,
        to="array",
        expected=None,
        msg="$convert should return null when input is {prefix} for unsupported target array",
    ),
    ConvertTest(
        "input_to_object_unsupported",
        input=_PLACEHOLDER,
        to="object",
        expected=None,
        msg="$convert should return null when input is {prefix} for unsupported target object",
    ),
    ConvertTest(
        "input_to_minKey_unsupported",
        input=_PLACEHOLDER,
        to="minKey",
        expected=None,
        msg="$convert should return null when input is {prefix} for unsupported target minKey",
    ),
    ConvertTest(
        "input_to_maxKey_unsupported",
        input=_PLACEHOLDER,
        to="maxKey",
        expected=None,
        msg="$convert should return null when input is {prefix} for unsupported target maxKey",
    ),
    ConvertTest(
        "input_to_javascript_unsupported",
        input=_PLACEHOLDER,
        to="javascript",
        expected=None,
        msg="$convert should return null when input is {prefix} for unsupported target javascript",
    ),
    ConvertTest(
        "input_to_javascriptWithScope_unsupported",
        input=_PLACEHOLDER,
        to="javascriptWithScope",
        expected=None,
        msg="$convert should return null when input is {prefix} for unsupported jsWithScope",
    ),
    ConvertTest(
        "input_to_symbol_unsupported",
        input=_PLACEHOLDER,
        to="symbol",
        expected=None,
        msg="$convert should return null when input is {prefix} for unsupported target symbol",
    ),
    ConvertTest(
        "input_to_undefined_unsupported",
        input=_PLACEHOLDER,
        to="undefined",
        expected=None,
        msg="$convert should return null when input is {prefix} for unsupported target undefined",
    ),
    ConvertTest(
        "input_to_dbPointer_unsupported",
        input=_PLACEHOLDER,
        to="dbPointer",
        expected=None,
        msg="$convert should return null when input is {prefix} for unsupported target dbPointer",
    ),
]

# Property [Null Input]: $convert returns onNull (or null) when input is null.
CONVERT_NULL_INPUT_TESTS = _build_null_tests(_NULL_INPUT_PATTERNS, None, "null")
# Property [Missing Input]: $convert returns onNull (or null) when input is missing.
CONVERT_MISSING_INPUT_TESTS = _build_null_tests(_NULL_INPUT_PATTERNS, MISSING, "missing")

CONVERT_NULL_INPUT_ALL_TESTS = CONVERT_NULL_INPUT_TESTS + CONVERT_MISSING_INPUT_TESTS


@pytest.mark.parametrize("test_case", pytest_params(CONVERT_NULL_INPUT_ALL_TESTS))
def test_convert_null_input(collection, test_case: ConvertTest):
    """Test $convert null/missing input returns null."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
