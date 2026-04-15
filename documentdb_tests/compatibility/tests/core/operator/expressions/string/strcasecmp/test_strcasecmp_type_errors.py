from __future__ import annotations

import pytest
from bson import Binary, Code, MaxKey, MinKey, ObjectId, Regex

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import BSON_TO_STRING_CONVERSION_ERROR
from documentdb_tests.framework.parametrize import pytest_params

from .utils.strcasecmp_common import (
    StrcasecmpTest,
    _expr,
)

# Property [Type Strictness]: boolean, array, object, Binary, MaxKey, MinKey,
# ObjectId, Regex, and Code with scope values in either position produce an error,
# even when the other argument is null.
STRCASECMP_TYPE_ERROR_TESTS: list[StrcasecmpTest] = [
    # Boolean in either position.
    StrcasecmpTest(
        "type_bool_first",
        string1=True,
        string2="hello",
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should reject boolean true in first position",
    ),
    StrcasecmpTest(
        "type_bool_second",
        string1="hello",
        string2=True,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should reject boolean true in second position",
    ),
    StrcasecmpTest(
        "type_bool_false_first",
        string1=False,
        string2="hello",
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should reject boolean false in first position",
    ),
    # Array in either position.
    StrcasecmpTest(
        "type_array_first",
        string1=[1, 2],
        string2="hello",
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should reject array in first position",
    ),
    StrcasecmpTest(
        "type_array_second",
        string1="hello",
        string2=[1, 2],
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should reject array in second position",
    ),
    # Object in either position.
    StrcasecmpTest(
        "type_object_first",
        string1={"a": 1},
        string2="hello",
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should reject object in first position",
    ),
    StrcasecmpTest(
        "type_object_second",
        string1="hello",
        string2={"a": 1},
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should reject object in second position",
    ),
    # Binary.
    StrcasecmpTest(
        "type_binary_first",
        string1=Binary(b"data"),
        string2="hello",
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should reject Binary in first position",
    ),
    StrcasecmpTest(
        "type_binary_second",
        string1="hello",
        string2=Binary(b"data"),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should reject Binary in second position",
    ),
    # MaxKey and MinKey in either position.
    StrcasecmpTest(
        "type_maxkey_first",
        string1=MaxKey(),
        string2="hello",
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should reject MaxKey in first position",
    ),
    StrcasecmpTest(
        "type_maxkey_second",
        string1="hello",
        string2=MaxKey(),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should reject MaxKey in second position",
    ),
    StrcasecmpTest(
        "type_minkey_first",
        string1=MinKey(),
        string2="hello",
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should reject MinKey in first position",
    ),
    StrcasecmpTest(
        "type_minkey_second",
        string1="hello",
        string2=MinKey(),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should reject MinKey in second position",
    ),
    # ObjectId in either position.
    StrcasecmpTest(
        "type_objectid_first",
        string1=ObjectId("507f1f77bcf86cd799439011"),
        string2="hello",
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should reject ObjectId in first position",
    ),
    StrcasecmpTest(
        "type_objectid_second",
        string1="hello",
        string2=ObjectId("507f1f77bcf86cd799439011"),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should reject ObjectId in second position",
    ),
    # Regex in either position.
    StrcasecmpTest(
        "type_regex_first",
        string1=Regex("pattern"),
        string2="hello",
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should reject Regex in first position",
    ),
    StrcasecmpTest(
        "type_regex_second",
        string1="hello",
        string2=Regex("pattern"),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should reject Regex in second position",
    ),
    # Code with scope in either position.
    StrcasecmpTest(
        "type_code_scope_first",
        string1=Code("function() {}", {"x": 1}),
        string2="hello",
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should reject Code with scope in first position",
    ),
    StrcasecmpTest(
        "type_code_scope_second",
        string1="hello",
        string2=Code("function() {}", {"x": 1}),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should reject Code with scope in second position",
    ),
    # Both arguments are invalid types.
    StrcasecmpTest(
        "type_both_booleans",
        string1=True,
        string2=False,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should reject both arguments as booleans",
    ),
    # Invalid type paired with an accepted non-string type.
    StrcasecmpTest(
        "type_bool_vs_number",
        string1=True,
        string2=42,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should reject boolean even when other arg is a number",
    ),
    StrcasecmpTest(
        "type_number_vs_bool",
        string1=42,
        string2=True,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should reject boolean in second position even with number first",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(STRCASECMP_TYPE_ERROR_TESTS))
def test_strcasecmp_type_errors_cases(collection, test_case: StrcasecmpTest):
    """Test $strcasecmp type strictness cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
