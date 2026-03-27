from __future__ import annotations

import pytest
from bson import Binary, Code, MaxKey, MinKey, ObjectId, Regex

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import BSON_TO_STRING_CONVERSION_ERROR
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.compatibility.tests.core.operator.expressions.string.toUpper.utils.toUpper_common import (
    ToUpperTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import execute_expression

# Property [Type Strictness]: non-coercible types produce an error.
TOUPPER_TYPE_ERROR_TESTS: list[ToUpperTest] = [
    ToUpperTest(
        "type_bool_true",
        value=True,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$toUpper should reject boolean true",
    ),
    ToUpperTest(
        "type_bool_false",
        value=False,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$toUpper should reject boolean false",
    ),
    ToUpperTest(
        "type_object",
        value={"key": "val"},
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$toUpper should reject object",
    ),
    ToUpperTest(
        "type_objectid",
        value=ObjectId("000000000000000000000000"),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$toUpper should reject ObjectId",
    ),
    ToUpperTest(
        "type_binary",
        value=Binary(b"\x00"),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$toUpper should reject Binary",
    ),
    ToUpperTest(
        "type_binary_uuid",
        value=Binary(b"\x00" * 16, 4),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$toUpper should reject Binary UUID",
    ),
    ToUpperTest(
        "type_regex",
        value=Regex("abc"),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$toUpper should reject Regex",
    ),
    ToUpperTest(
        "type_code_with_scope",
        value=Code("x", {}),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$toUpper should reject Code with scope",
    ),
    ToUpperTest(
        "type_minkey",
        value=MinKey(),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$toUpper should reject MinKey",
    ),
    ToUpperTest(
        "type_maxkey",
        value=MaxKey(),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$toUpper should reject MaxKey",
    ),
    ToUpperTest(
        "type_nested_array",
        value=[[1, 2]],
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$toUpper should reject nested array",
    ),
    ToUpperTest(
        "type_array_from_expression",
        value={"$literal": [1, 2]},
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$toUpper should reject array from expression",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(TOUPPER_TYPE_ERROR_TESTS))
def test_toupper_type_errors(collection, test_case: ToUpperTest):
    """Test $toUpper type strictness."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
