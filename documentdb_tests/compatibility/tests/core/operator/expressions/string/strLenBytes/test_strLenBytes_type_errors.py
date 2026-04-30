from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp
from bson.code import Code

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import STRLENBYTES_TYPE_ERROR
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

from .utils.strLenBytes_common import (
    StrLenBytesTest,
    _expr,
)

# Property [Type Strictness]: any non-string argument produces an error.
STRLENBYTES_TYPE_ERROR_TESTS: list[StrLenBytesTest] = [
    StrLenBytesTest(
        "type_int",
        value=42,
        error_code=STRLENBYTES_TYPE_ERROR,
        msg="$strLenBytes should reject int",
    ),
    StrLenBytesTest(
        "type_long",
        value=Int64(42),
        error_code=STRLENBYTES_TYPE_ERROR,
        msg="$strLenBytes should reject Int64",
    ),
    StrLenBytesTest(
        "type_double",
        value=3.14,
        error_code=STRLENBYTES_TYPE_ERROR,
        msg="$strLenBytes should reject double",
    ),
    StrLenBytesTest(
        "type_decimal",
        value=DECIMAL128_ONE_AND_HALF,
        error_code=STRLENBYTES_TYPE_ERROR,
        msg="$strLenBytes should reject Decimal128",
    ),
    StrLenBytesTest(
        "type_bool",
        value=True,
        error_code=STRLENBYTES_TYPE_ERROR,
        msg="$strLenBytes should reject boolean",
    ),
    StrLenBytesTest(
        "type_date",
        value=datetime(2024, 1, 1, tzinfo=timezone.utc),
        error_code=STRLENBYTES_TYPE_ERROR,
        msg="$strLenBytes should reject datetime",
    ),
    StrLenBytesTest(
        "type_regex",
        value=Regex("abc"),
        error_code=STRLENBYTES_TYPE_ERROR,
        msg="$strLenBytes should reject regex",
    ),
    StrLenBytesTest(
        "type_objectid",
        value=ObjectId("507f1f77bcf86cd799439011"),
        error_code=STRLENBYTES_TYPE_ERROR,
        msg="$strLenBytes should reject ObjectId",
    ),
    StrLenBytesTest(
        "type_object",
        value={"a": 1},
        error_code=STRLENBYTES_TYPE_ERROR,
        msg="$strLenBytes should reject object",
    ),
    StrLenBytesTest(
        "type_binary",
        value=Binary(b"data"),
        error_code=STRLENBYTES_TYPE_ERROR,
        msg="$strLenBytes should reject binary",
    ),
    StrLenBytesTest(
        "type_maxkey",
        value=MaxKey(),
        error_code=STRLENBYTES_TYPE_ERROR,
        msg="$strLenBytes should reject MaxKey",
    ),
    StrLenBytesTest(
        "type_minkey",
        value=MinKey(),
        error_code=STRLENBYTES_TYPE_ERROR,
        msg="$strLenBytes should reject MinKey",
    ),
    StrLenBytesTest(
        "type_timestamp",
        value=Timestamp(1, 1),
        error_code=STRLENBYTES_TYPE_ERROR,
        msg="$strLenBytes should reject Timestamp",
    ),
    StrLenBytesTest(
        "type_code",
        value=Code("function() {}"),
        error_code=STRLENBYTES_TYPE_ERROR,
        msg="$strLenBytes should reject Code",
    ),
    StrLenBytesTest(
        "type_code_with_scope",
        value=Code("function() {}", {"x": 1}),
        error_code=STRLENBYTES_TYPE_ERROR,
        msg="$strLenBytes should reject Code with scope",
    ),
    StrLenBytesTest(
        "type_binary_uuid",
        value=Binary(b"data", 4),
        error_code=STRLENBYTES_TYPE_ERROR,
        msg="$strLenBytes should reject binary UUID",
    ),
    # Special float values.
    StrLenBytesTest(
        "type_nan",
        value=FLOAT_NAN,
        error_code=STRLENBYTES_TYPE_ERROR,
        msg="$strLenBytes should reject NaN",
    ),
    StrLenBytesTest(
        "type_inf",
        value=FLOAT_INFINITY,
        error_code=STRLENBYTES_TYPE_ERROR,
        msg="$strLenBytes should reject Infinity",
    ),
    StrLenBytesTest(
        "type_neg_inf",
        value=FLOAT_NEGATIVE_INFINITY,
        error_code=STRLENBYTES_TYPE_ERROR,
        msg="$strLenBytes should reject -Infinity",
    ),
    StrLenBytesTest(
        "type_decimal_nan",
        value=DECIMAL128_NAN,
        error_code=STRLENBYTES_TYPE_ERROR,
        msg="$strLenBytes should reject Decimal128 NaN",
    ),
    StrLenBytesTest(
        "type_decimal_inf",
        value=DECIMAL128_INFINITY,
        error_code=STRLENBYTES_TYPE_ERROR,
        msg="$strLenBytes should reject Decimal128 Infinity",
    ),
    StrLenBytesTest(
        "type_decimal_neg_inf",
        value=DECIMAL128_NEGATIVE_INFINITY,
        error_code=STRLENBYTES_TYPE_ERROR,
        msg="$strLenBytes should reject Decimal128 -Infinity",
    ),
    # Expression returning non-string type.
    StrLenBytesTest(
        "type_expr_returns_int",
        value={"$add": [1, 2]},
        error_code=STRLENBYTES_TYPE_ERROR,
        msg="$strLenBytes should reject expression resolving to int",
    ),
    # An expression returning an array fails the type check, unlike a literal array which is
    # parsed as an argument list.
    StrLenBytesTest(
        "type_expr_returns_array",
        value={"$split": ["hello", "-"]},
        error_code=STRLENBYTES_TYPE_ERROR,
        msg="$strLenBytes should reject expression resolving to array",
    ),
    # Runtime array via $literal produces type error, not arity error.
    StrLenBytesTest(
        "type_runtime_array",
        value={"$literal": ["hello"]},
        error_code=STRLENBYTES_TYPE_ERROR,
        msg="$strLenBytes should reject runtime array via $literal",
    ),
    # Array syntax with invalid types: single-element array is unwrapped, then type-checked.
    StrLenBytesTest(
        "type_array_int",
        value=[42],
        error_code=STRLENBYTES_TYPE_ERROR,
        msg="$strLenBytes should reject single-element array containing int",
    ),
    StrLenBytesTest(
        "type_array_bool",
        value=[True],
        error_code=STRLENBYTES_TYPE_ERROR,
        msg="$strLenBytes should reject single-element array containing boolean",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(STRLENBYTES_TYPE_ERROR_TESTS))
def test_strlenbytes_cases(collection, test_case: StrLenBytesTest):
    """Test $strLenBytes type error cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
