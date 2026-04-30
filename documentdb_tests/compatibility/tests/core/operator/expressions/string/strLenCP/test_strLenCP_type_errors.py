from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import STRLENCP_TYPE_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_ONE_AND_HALF,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

from .utils.strLenCP_common import (
    StrLenCPTest,
    _expr,
)

# Property [Type Strictness]: any non-string argument produces an error.
STRLENCP_TYPE_ERROR_TESTS: list[StrLenCPTest] = [
    StrLenCPTest(
        "type_int", value=42, error_code=STRLENCP_TYPE_ERROR, msg="$strLenCP should reject int"
    ),
    StrLenCPTest(
        "type_long",
        value=Int64(42),
        error_code=STRLENCP_TYPE_ERROR,
        msg="$strLenCP should reject Int64",
    ),
    StrLenCPTest(
        "type_double",
        value=3.14,
        error_code=STRLENCP_TYPE_ERROR,
        msg="$strLenCP should reject double",
    ),
    StrLenCPTest(
        "type_decimal",
        value=DECIMAL128_ONE_AND_HALF,
        error_code=STRLENCP_TYPE_ERROR,
        msg="$strLenCP should reject Decimal128",
    ),
    StrLenCPTest(
        "type_bool",
        value=True,
        error_code=STRLENCP_TYPE_ERROR,
        msg="$strLenCP should reject boolean",
    ),
    StrLenCPTest(
        "type_date",
        value=datetime(2024, 1, 1, tzinfo=timezone.utc),
        error_code=STRLENCP_TYPE_ERROR,
        msg="$strLenCP should reject datetime",
    ),
    StrLenCPTest(
        "type_regex",
        value=Regex("abc"),
        error_code=STRLENCP_TYPE_ERROR,
        msg="$strLenCP should reject regex",
    ),
    StrLenCPTest(
        "type_objectid",
        value=ObjectId("507f1f77bcf86cd799439011"),
        error_code=STRLENCP_TYPE_ERROR,
        msg="$strLenCP should reject ObjectId",
    ),
    StrLenCPTest(
        "type_object",
        value={"a": 1},
        error_code=STRLENCP_TYPE_ERROR,
        msg="$strLenCP should reject object",
    ),
    StrLenCPTest(
        "type_binary",
        value=Binary(b"data"),
        error_code=STRLENCP_TYPE_ERROR,
        msg="$strLenCP should reject binary",
    ),
    StrLenCPTest(
        "type_binary_uuid",
        value=Binary(b"data", 4),
        error_code=STRLENCP_TYPE_ERROR,
        msg="$strLenCP should reject binary UUID",
    ),
    StrLenCPTest(
        "type_maxkey",
        value=MaxKey(),
        error_code=STRLENCP_TYPE_ERROR,
        msg="$strLenCP should reject MaxKey",
    ),
    StrLenCPTest(
        "type_minkey",
        value=MinKey(),
        error_code=STRLENCP_TYPE_ERROR,
        msg="$strLenCP should reject MinKey",
    ),
    StrLenCPTest(
        "type_timestamp",
        value=Timestamp(1, 1),
        error_code=STRLENCP_TYPE_ERROR,
        msg="$strLenCP should reject Timestamp",
    ),
    StrLenCPTest(
        "type_code",
        value=Code("function() {}"),
        error_code=STRLENCP_TYPE_ERROR,
        msg="$strLenCP should reject Code",
    ),
    StrLenCPTest(
        "type_code_with_scope",
        value=Code("function() {}", {"x": 1}),
        error_code=STRLENCP_TYPE_ERROR,
        msg="$strLenCP should reject Code with scope",
    ),
    # Special float values.
    StrLenCPTest(
        "type_nan",
        value=FLOAT_NAN,
        error_code=STRLENCP_TYPE_ERROR,
        msg="$strLenCP should reject NaN",
    ),
    StrLenCPTest(
        "type_inf",
        value=FLOAT_INFINITY,
        error_code=STRLENCP_TYPE_ERROR,
        msg="$strLenCP should reject Infinity",
    ),
    StrLenCPTest(
        "type_neg_inf",
        value=FLOAT_NEGATIVE_INFINITY,
        error_code=STRLENCP_TYPE_ERROR,
        msg="$strLenCP should reject -Infinity",
    ),
    StrLenCPTest(
        "type_decimal_nan",
        value=DECIMAL128_NAN,
        error_code=STRLENCP_TYPE_ERROR,
        msg="$strLenCP should reject Decimal128 NaN",
    ),
    StrLenCPTest(
        "type_decimal_inf",
        value=DECIMAL128_INFINITY,
        error_code=STRLENCP_TYPE_ERROR,
        msg="$strLenCP should reject Decimal128 Infinity",
    ),
    StrLenCPTest(
        "type_decimal_neg_inf",
        value=DECIMAL128_NEGATIVE_INFINITY,
        error_code=STRLENCP_TYPE_ERROR,
        msg="$strLenCP should reject Decimal128 -Infinity",
    ),
    # Expression returning non-string type.
    StrLenCPTest(
        "type_expr_returns_int",
        value={"$add": [1, 2]},
        error_code=STRLENCP_TYPE_ERROR,
        msg="$strLenCP should reject expression resolving to int",
    ),
    # An expression returning an array fails the type check, unlike a literal array
    # which is parsed as an argument list.
    StrLenCPTest(
        "type_expr_returns_array",
        value={"$split": ["hello", "-"]},
        error_code=STRLENCP_TYPE_ERROR,
        msg="$strLenCP should reject expression resolving to array",
    ),
    # Runtime array via $literal produces type error, not arity error.
    StrLenCPTest(
        "type_runtime_array",
        value={"$literal": ["hello"]},
        error_code=STRLENCP_TYPE_ERROR,
        msg="$strLenCP should reject runtime array via $literal",
    ),
    # Array syntax with invalid types: single-element array is unwrapped, then type-checked.
    StrLenCPTest(
        "type_array_int",
        value=[42],
        error_code=STRLENCP_TYPE_ERROR,
        msg="$strLenCP should reject single-element array containing int",
    ),
    StrLenCPTest(
        "type_array_bool",
        value=[True],
        error_code=STRLENCP_TYPE_ERROR,
        msg="$strLenCP should reject single-element array containing boolean",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(STRLENCP_TYPE_ERROR_TESTS))
def test_strlencp_cases(collection, test_case: StrLenCPTest):
    """Test $strLenCP cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
