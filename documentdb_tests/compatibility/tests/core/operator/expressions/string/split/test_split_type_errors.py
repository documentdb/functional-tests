from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp
from bson.code import Code

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    SPLIT_DELIMITER_TYPE_ERROR,
    SPLIT_STRING_TYPE_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import FLOAT_NAN

from .utils.split_common import (
    SplitTest,
    _expr,
)

# Property [Type Strictness - String Argument]: any non-string, non-null first
# argument produces SPLIT_STRING_TYPE_ERROR.
SPLIT_STRING_TYPE_ERROR_TESTS: list[SplitTest] = [
    SplitTest(
        "type_string_int",
        string=42,
        delimiter="-",
        error_code=SPLIT_STRING_TYPE_ERROR,
        msg="$split should reject int as string argument",
    ),
    SplitTest(
        "type_string_float",
        string=3.14,
        delimiter="-",
        error_code=SPLIT_STRING_TYPE_ERROR,
        msg="$split should reject float as string argument",
    ),
    SplitTest(
        "type_string_long",
        string=Int64(1),
        delimiter="-",
        error_code=SPLIT_STRING_TYPE_ERROR,
        msg="$split should reject Int64 as string argument",
    ),
    SplitTest(
        "type_string_decimal",
        string=Decimal128("1"),
        delimiter="-",
        error_code=SPLIT_STRING_TYPE_ERROR,
        msg="$split should reject Decimal128 as string argument",
    ),
    SplitTest(
        "type_string_bool",
        string=True,
        delimiter="-",
        error_code=SPLIT_STRING_TYPE_ERROR,
        msg="$split should reject boolean as string argument",
    ),
    SplitTest(
        "type_string_array",
        string=["a"],
        delimiter="-",
        error_code=SPLIT_STRING_TYPE_ERROR,
        msg="$split should reject array as string argument",
    ),
    SplitTest(
        "type_string_object",
        string={"a": 1},
        delimiter="-",
        error_code=SPLIT_STRING_TYPE_ERROR,
        msg="$split should reject object as string argument",
    ),
    SplitTest(
        "type_string_binary",
        string=Binary(b"data"),
        delimiter="-",
        error_code=SPLIT_STRING_TYPE_ERROR,
        msg="$split should reject binary as string argument",
    ),
    SplitTest(
        "type_string_date",
        string=datetime(2024, 1, 1, tzinfo=timezone.utc),
        delimiter="-",
        error_code=SPLIT_STRING_TYPE_ERROR,
        msg="$split should reject datetime as string argument",
    ),
    SplitTest(
        "type_string_objectid",
        string=ObjectId("507f1f77bcf86cd799439011"),
        delimiter="-",
        error_code=SPLIT_STRING_TYPE_ERROR,
        msg="$split should reject ObjectId as string argument",
    ),
    SplitTest(
        "type_string_regex",
        string=Regex("pat"),
        delimiter="-",
        error_code=SPLIT_STRING_TYPE_ERROR,
        msg="$split should reject regex as string argument",
    ),
    SplitTest(
        "type_string_maxkey",
        string=MaxKey(),
        delimiter="-",
        error_code=SPLIT_STRING_TYPE_ERROR,
        msg="$split should reject MaxKey as string argument",
    ),
    SplitTest(
        "type_string_minkey",
        string=MinKey(),
        delimiter="-",
        error_code=SPLIT_STRING_TYPE_ERROR,
        msg="$split should reject MinKey as string argument",
    ),
    SplitTest(
        "type_string_timestamp",
        string=Timestamp(1, 1),
        delimiter="-",
        error_code=SPLIT_STRING_TYPE_ERROR,
        msg="$split should reject Timestamp as string argument",
    ),
    SplitTest(
        "type_string_code",
        string=Code("function() {}"),
        delimiter="-",
        error_code=SPLIT_STRING_TYPE_ERROR,
        msg="$split should reject Code as string argument",
    ),
    SplitTest(
        "type_string_code_scope",
        string=Code("function() {}", {"x": 1}),
        delimiter="-",
        error_code=SPLIT_STRING_TYPE_ERROR,
        msg="$split should reject Code with scope as string argument",
    ),
    SplitTest(
        "type_string_nan",
        string=FLOAT_NAN,
        delimiter="-",
        error_code=SPLIT_STRING_TYPE_ERROR,
        msg="$split should reject NaN as string argument",
    ),
]

# Property [Type Strictness - Delimiter Argument]: any non-string, non-null
# second argument produces SPLIT_DELIMITER_TYPE_ERROR.
SPLIT_DELIM_TYPE_ERROR_TESTS: list[SplitTest] = [
    SplitTest(
        "type_delim_int",
        string="hello",
        delimiter=42,
        error_code=SPLIT_DELIMITER_TYPE_ERROR,
        msg="$split should reject int as delimiter",
    ),
    SplitTest(
        "type_delim_float",
        string="hello",
        delimiter=3.14,
        error_code=SPLIT_DELIMITER_TYPE_ERROR,
        msg="$split should reject float as delimiter",
    ),
    SplitTest(
        "type_delim_long",
        string="hello",
        delimiter=Int64(1),
        error_code=SPLIT_DELIMITER_TYPE_ERROR,
        msg="$split should reject Int64 as delimiter",
    ),
    SplitTest(
        "type_delim_decimal",
        string="hello",
        delimiter=Decimal128("1"),
        error_code=SPLIT_DELIMITER_TYPE_ERROR,
        msg="$split should reject Decimal128 as delimiter",
    ),
    SplitTest(
        "type_delim_bool",
        string="hello",
        delimiter=True,
        error_code=SPLIT_DELIMITER_TYPE_ERROR,
        msg="$split should reject boolean as delimiter",
    ),
    SplitTest(
        "type_delim_array",
        string="hello",
        delimiter=["a"],
        error_code=SPLIT_DELIMITER_TYPE_ERROR,
        msg="$split should reject array as delimiter",
    ),
    SplitTest(
        "type_delim_object",
        string="hello",
        delimiter={"a": 1},
        error_code=SPLIT_DELIMITER_TYPE_ERROR,
        msg="$split should reject object as delimiter",
    ),
    SplitTest(
        "type_delim_binary",
        string="hello",
        delimiter=Binary(b"data"),
        error_code=SPLIT_DELIMITER_TYPE_ERROR,
        msg="$split should reject binary as delimiter",
    ),
    SplitTest(
        "type_delim_date",
        string="hello",
        delimiter=datetime(2024, 1, 1, tzinfo=timezone.utc),
        error_code=SPLIT_DELIMITER_TYPE_ERROR,
        msg="$split should reject datetime as delimiter",
    ),
    SplitTest(
        "type_delim_objectid",
        string="hello",
        delimiter=ObjectId("507f1f77bcf86cd799439011"),
        error_code=SPLIT_DELIMITER_TYPE_ERROR,
        msg="$split should reject ObjectId as delimiter",
    ),
    SplitTest(
        "type_delim_regex",
        string="hello",
        delimiter=Regex("pat"),
        error_code=SPLIT_DELIMITER_TYPE_ERROR,
        msg="$split should reject regex as delimiter",
    ),
    SplitTest(
        "type_delim_maxkey",
        string="hello",
        delimiter=MaxKey(),
        error_code=SPLIT_DELIMITER_TYPE_ERROR,
        msg="$split should reject MaxKey as delimiter",
    ),
    SplitTest(
        "type_delim_minkey",
        string="hello",
        delimiter=MinKey(),
        error_code=SPLIT_DELIMITER_TYPE_ERROR,
        msg="$split should reject MinKey as delimiter",
    ),
    SplitTest(
        "type_delim_timestamp",
        string="hello",
        delimiter=Timestamp(1, 1),
        error_code=SPLIT_DELIMITER_TYPE_ERROR,
        msg="$split should reject Timestamp as delimiter",
    ),
    SplitTest(
        "type_delim_code",
        string="hello",
        delimiter=Code("function() {}"),
        error_code=SPLIT_DELIMITER_TYPE_ERROR,
        msg="$split should reject Code as delimiter",
    ),
    SplitTest(
        "type_delim_code_scope",
        string="hello",
        delimiter=Code("function() {}", {"x": 1}),
        error_code=SPLIT_DELIMITER_TYPE_ERROR,
        msg="$split should reject Code with scope as delimiter",
    ),
    SplitTest(
        "type_delim_nan",
        string="hello",
        delimiter=FLOAT_NAN,
        error_code=SPLIT_DELIMITER_TYPE_ERROR,
        msg="$split should reject NaN as delimiter",
    ),
]

# Property [Type Error Precedence]: when both arguments are invalid types, the
# first argument's type error takes precedence.
SPLIT_TYPE_PRECEDENCE_TESTS: list[SplitTest] = [
    SplitTest(
        "type_precedence_both_invalid",
        string=42,
        delimiter=42,
        error_code=SPLIT_STRING_TYPE_ERROR,
        msg="$split should report string type error when both arguments have wrong type",
    ),
    SplitTest(
        "type_precedence_bool_float",
        string=True,
        delimiter=3.14,
        error_code=SPLIT_STRING_TYPE_ERROR,
        msg="$split should report string type error first when both arguments are non-string",
    ),
]

SPLIT_TYPE_ERROR_ALL_TESTS = (
    SPLIT_STRING_TYPE_ERROR_TESTS + SPLIT_DELIM_TYPE_ERROR_TESTS + SPLIT_TYPE_PRECEDENCE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SPLIT_TYPE_ERROR_ALL_TESTS))
def test_split_type_error_cases(collection, test_case: SplitTest):
    """Test $split type strictness cases."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
