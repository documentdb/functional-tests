from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

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

# Group 2: fixed target type, vary onNull BSON type. Proves every BSON type
# round-trips through onNull unchanged.
_ON_NULL_VARY_VALUE_PATTERNS: list[ConvertTest] = [
    ConvertTest(
        "on_null_value_null",
        input=_PLACEHOLDER,
        to="int",
        on_null=None,
        expected=None,
        msg="$convert onNull should return null as-is ({prefix} input)",
    ),
    ConvertTest(
        "on_null_value_object",
        input=_PLACEHOLDER,
        to="int",
        on_null={"key": "val"},
        expected={"key": "val"},
        msg="$convert onNull should return object as-is ({prefix} input)",
    ),
    ConvertTest(
        "on_null_value_bool",
        input=_PLACEHOLDER,
        to="int",
        on_null=False,
        expected=False,
        msg="$convert onNull should return bool as-is ({prefix} input)",
    ),
    ConvertTest(
        "on_null_value_string",
        input=_PLACEHOLDER,
        to="int",
        on_null="fallback",
        expected="fallback",
        msg="$convert onNull should return string as-is ({prefix} input)",
    ),
    ConvertTest(
        "on_null_value_regex",
        input=_PLACEHOLDER,
        to="int",
        on_null=Regex("abc"),
        expected=Regex("abc"),
        msg="$convert onNull should return Regex as-is ({prefix} input)",
    ),
    ConvertTest(
        "on_null_value_binary",
        input=_PLACEHOLDER,
        to="int",
        on_null=Binary(b"hello"),
        expected=b"hello",
        msg="$convert onNull should return Binary as-is ({prefix} input)",
    ),
    ConvertTest(
        "on_null_value_objectid",
        input=_PLACEHOLDER,
        to="int",
        on_null=ObjectId("507f1f77bcf86cd799439011"),
        expected=ObjectId("507f1f77bcf86cd799439011"),
        msg="$convert onNull should return ObjectId as-is ({prefix} input)",
    ),
    ConvertTest(
        "on_null_value_date",
        input=_PLACEHOLDER,
        to="int",
        on_null=datetime(2024, 6, 15, tzinfo=timezone.utc),
        expected=datetime(2024, 6, 15, tzinfo=timezone.utc),
        msg="$convert onNull should return date as-is ({prefix} input)",
    ),
    ConvertTest(
        "on_null_value_long",
        input=_PLACEHOLDER,
        to="int",
        on_null=Int64(42),
        expected=Int64(42),
        msg="$convert onNull should return long as-is ({prefix} input)",
    ),
    ConvertTest(
        "on_null_value_decimal",
        input=_PLACEHOLDER,
        to="int",
        on_null=Decimal128("3.14"),
        expected=Decimal128("3.14"),
        msg="$convert onNull should return Decimal128 as-is ({prefix} input)",
    ),
    ConvertTest(
        "on_null_value_timestamp",
        input=_PLACEHOLDER,
        to="int",
        on_null=Timestamp(1, 1),
        expected=Timestamp(1, 1),
        msg="$convert onNull should return Timestamp as-is ({prefix} input)",
    ),
    ConvertTest(
        "on_null_value_minkey",
        input=_PLACEHOLDER,
        to="int",
        on_null=MinKey(),
        expected=MinKey(),
        msg="$convert onNull should return MinKey as-is ({prefix} input)",
    ),
    ConvertTest(
        "on_null_value_maxkey",
        input=_PLACEHOLDER,
        to="int",
        on_null=MaxKey(),
        expected=MaxKey(),
        msg="$convert onNull should return MaxKey as-is ({prefix} input)",
    ),
    ConvertTest(
        "on_null_value_code",
        input=_PLACEHOLDER,
        to="int",
        on_null=Code("function(){}"),
        expected=Code("function(){}"),
        msg="$convert onNull should return Code as-is ({prefix} input)",
    ),
    ConvertTest(
        "on_null_value_code_with_scope",
        input=_PLACEHOLDER,
        to="int",
        on_null=Code("function(){}", {"x": 1}),
        expected=Code("function(){}", {"x": 1}),
        msg="$convert onNull should return Code with scope as-is ({prefix} input)",
    ),
    ConvertTest(
        "on_null_value_array",
        input=_PLACEHOLDER,
        to="int",
        on_null=[1, 2, 3],
        expected=[1, 2, 3],
        msg="$convert onNull should return array as-is ({prefix} input)",
    ),
    ConvertTest(
        "on_null_value_int",
        input=_PLACEHOLDER,
        to="int",
        on_null=42,
        expected=42,
        msg="$convert onNull should return int as-is ({prefix} input)",
    ),
    ConvertTest(
        "on_null_value_double",
        input=_PLACEHOLDER,
        to="int",
        on_null=3.14,
        expected=3.14,
        msg="$convert onNull should return double as-is ({prefix} input)",
    ),
]

# Property [onNull Value Null]: onNull value is returned when input is null.
CONVERT_ON_NULL_VALUE_NULL_TESTS: list[ConvertTest] = _build_null_tests(
    _ON_NULL_VARY_VALUE_PATTERNS, None, "null"
)

# Property [onNull Value Missing]: onNull value is returned when input is missing.
CONVERT_ON_NULL_VALUE_MISSING_TESTS: list[ConvertTest] = _build_null_tests(
    _ON_NULL_VARY_VALUE_PATTERNS, MISSING, "missing"
)

CONVERT_ON_NULL_VALUE_ALL_TESTS = (
    CONVERT_ON_NULL_VALUE_NULL_TESTS + CONVERT_ON_NULL_VALUE_MISSING_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(CONVERT_ON_NULL_VALUE_ALL_TESTS))
def test_convert_on_null_value(collection, test_case: ConvertTest):
    """Test $convert onNull with varying value types."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
