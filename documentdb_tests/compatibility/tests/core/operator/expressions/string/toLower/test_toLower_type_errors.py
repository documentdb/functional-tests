from __future__ import annotations

import pytest
from bson import Binary, Code, MaxKey, MinKey, ObjectId, Regex

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import BSON_TO_STRING_CONVERSION_ERROR
from documentdb_tests.framework.parametrize import pytest_params

from .utils.toLower_common import (
    ToLowerTest,
    _expr,
)

# Property [Type Strictness]: non-coercible BSON types produce an error.
TOLOWER_TYPE_ERROR_TESTS: list[ToLowerTest] = [
    ToLowerTest(
        "type_bool_true",
        value=True,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$toLower should reject boolean true",
    ),
    ToLowerTest(
        "type_bool_false",
        value=False,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$toLower should reject boolean false",
    ),
    ToLowerTest(
        "type_object",
        value={"a": 1},
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$toLower should reject object",
    ),
    ToLowerTest(
        "type_objectid",
        value=ObjectId("000000000000000000000000"),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$toLower should reject ObjectId",
    ),
    ToLowerTest(
        "type_binary",
        value=Binary(b"\x00"),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$toLower should reject Binary",
    ),
    ToLowerTest(
        "type_binary_uuid",
        value=Binary(b"\x00" * 16, 4),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$toLower should reject Binary UUID",
    ),
    ToLowerTest(
        "type_regex",
        value=Regex("abc"),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$toLower should reject Regex",
    ),
    ToLowerTest(
        "type_code_with_scope",
        value=Code("x", {}),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$toLower should reject Code with scope",
    ),
    ToLowerTest(
        "type_minkey",
        value=MinKey(),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$toLower should reject MinKey",
    ),
    ToLowerTest(
        "type_maxkey",
        value=MaxKey(),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$toLower should reject MaxKey",
    ),
    ToLowerTest(
        "type_nested_array",
        value=[[1]],
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$toLower should reject nested array",
    ),
    # Expression that evaluates to an array at runtime.
    ToLowerTest(
        "type_runtime_array",
        value={"$literal": [1, 2]},
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$toLower should reject array from expression",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(TOLOWER_TYPE_ERROR_TESTS))
def test_tolower_type_errors(collection, test_case: ToLowerTest):
    """Test $toLower type strictness."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
