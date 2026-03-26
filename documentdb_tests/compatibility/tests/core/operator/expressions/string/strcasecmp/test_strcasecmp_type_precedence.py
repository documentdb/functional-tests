from __future__ import annotations

import pytest
from bson import Binary, Code, MaxKey, MinKey, ObjectId, Regex

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import BSON_TO_STRING_CONVERSION_ERROR
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.framework.test_constants import MISSING
from documentdb_tests.compatibility.tests.core.operator.expressions.string.strcasecmp.utils.strcasecmp_common import (
    StrcasecmpTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import execute_expression

# Property [Type Error Precedence]: type errors take precedence over null or
# missing in the other position.
STRCASECMP_TYPE_PRECEDENCE_TESTS: list[StrcasecmpTest] = [
    # Each invalid type vs null.
    StrcasecmpTest(
        "precedence_bool_vs_null",
        string1=True,
        string2=None,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should error on boolean even when other arg is null",
    ),
    StrcasecmpTest(
        "precedence_null_vs_bool",
        string1=None,
        string2=True,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should error on boolean in second position even with null first",
    ),
    StrcasecmpTest(
        "precedence_array_vs_null",
        string1=[1],
        string2=None,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should error on array even when other arg is null",
    ),
    StrcasecmpTest(
        "precedence_null_vs_array",
        string1=None,
        string2=[1],
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should error on array in second position even with null first",
    ),
    StrcasecmpTest(
        "precedence_object_vs_null",
        string1={"a": 1},
        string2=None,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should error on object even when other arg is null",
    ),
    StrcasecmpTest(
        "precedence_null_vs_object",
        string1=None,
        string2={"a": 1},
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should error on object in second position even with null first",
    ),
    StrcasecmpTest(
        "precedence_binary_vs_null",
        string1=Binary(b"x"),
        string2=None,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should error on Binary even when other arg is null",
    ),
    StrcasecmpTest(
        "precedence_null_vs_binary",
        string1=None,
        string2=Binary(b"x"),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should error on Binary in second position even with null first",
    ),
    StrcasecmpTest(
        "precedence_maxkey_vs_null",
        string1=MaxKey(),
        string2=None,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should error on MaxKey even when other arg is null",
    ),
    StrcasecmpTest(
        "precedence_null_vs_maxkey",
        string1=None,
        string2=MaxKey(),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should error on MaxKey in second position even with null first",
    ),
    StrcasecmpTest(
        "precedence_minkey_vs_null",
        string1=MinKey(),
        string2=None,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should error on MinKey even when other arg is null",
    ),
    StrcasecmpTest(
        "precedence_null_vs_minkey",
        string1=None,
        string2=MinKey(),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should error on MinKey in second position even with null first",
    ),
    StrcasecmpTest(
        "precedence_objectid_vs_null",
        string1=ObjectId("507f1f77bcf86cd799439011"),
        string2=None,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should error on ObjectId even when other arg is null",
    ),
    StrcasecmpTest(
        "precedence_null_vs_objectid",
        string1=None,
        string2=ObjectId("507f1f77bcf86cd799439011"),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should error on ObjectId in second position even with null first",
    ),
    StrcasecmpTest(
        "precedence_regex_vs_null",
        string1=Regex("x"),
        string2=None,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should error on Regex even when other arg is null",
    ),
    StrcasecmpTest(
        "precedence_null_vs_regex",
        string1=None,
        string2=Regex("x"),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should error on Regex in second position even with null first",
    ),
    StrcasecmpTest(
        "precedence_code_scope_vs_null",
        string1=Code("function() {}", {"x": 1}),
        string2=None,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should error on Code with scope even when other arg is null",
    ),
    StrcasecmpTest(
        "precedence_null_vs_code_scope",
        string1=None,
        string2=Code("function() {}", {"x": 1}),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should error on Code with scope in second position even with null first",
    ),
    # Each invalid type vs missing.
    StrcasecmpTest(
        "precedence_bool_vs_missing",
        string1=True,
        string2=MISSING,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should error on boolean even when other arg is missing",
    ),
    StrcasecmpTest(
        "precedence_missing_vs_bool",
        string1=MISSING,
        string2=True,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should error on boolean in second position even with missing first",
    ),
    StrcasecmpTest(
        "precedence_array_vs_missing",
        string1=[1],
        string2=MISSING,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should error on array even when other arg is missing",
    ),
    StrcasecmpTest(
        "precedence_missing_vs_array",
        string1=MISSING,
        string2=[1],
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should error on array in second position even with missing first",
    ),
    StrcasecmpTest(
        "precedence_object_vs_missing",
        string1={"a": 1},
        string2=MISSING,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should error on object even when other arg is missing",
    ),
    StrcasecmpTest(
        "precedence_missing_vs_object",
        string1=MISSING,
        string2={"a": 1},
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should error on object in second position even with missing first",
    ),
    StrcasecmpTest(
        "precedence_binary_vs_missing",
        string1=Binary(b"x"),
        string2=MISSING,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should error on Binary even when other arg is missing",
    ),
    StrcasecmpTest(
        "precedence_missing_vs_binary",
        string1=MISSING,
        string2=Binary(b"x"),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should error on Binary in second position even with missing first",
    ),
    StrcasecmpTest(
        "precedence_maxkey_vs_missing",
        string1=MaxKey(),
        string2=MISSING,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should error on MaxKey even when other arg is missing",
    ),
    StrcasecmpTest(
        "precedence_missing_vs_maxkey",
        string1=MISSING,
        string2=MaxKey(),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should error on MaxKey in second position even with missing first",
    ),
    StrcasecmpTest(
        "precedence_minkey_vs_missing",
        string1=MinKey(),
        string2=MISSING,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should error on MinKey even when other arg is missing",
    ),
    StrcasecmpTest(
        "precedence_missing_vs_minkey",
        string1=MISSING,
        string2=MinKey(),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should error on MinKey in second position even with missing first",
    ),
    StrcasecmpTest(
        "precedence_objectid_vs_missing",
        string1=ObjectId("507f1f77bcf86cd799439011"),
        string2=MISSING,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should error on ObjectId even when other arg is missing",
    ),
    StrcasecmpTest(
        "precedence_missing_vs_objectid",
        string1=MISSING,
        string2=ObjectId("507f1f77bcf86cd799439011"),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should error on ObjectId in second position even with missing first",
    ),
    StrcasecmpTest(
        "precedence_regex_vs_missing",
        string1=Regex("x"),
        string2=MISSING,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should error on Regex even when other arg is missing",
    ),
    StrcasecmpTest(
        "precedence_missing_vs_regex",
        string1=MISSING,
        string2=Regex("x"),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should error on Regex in second position even with missing first",
    ),
    StrcasecmpTest(
        "precedence_code_scope_vs_missing",
        string1=Code("function() {}", {"x": 1}),
        string2=MISSING,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$strcasecmp should error on Code with scope even when other arg is missing",
    ),
    StrcasecmpTest(
        "precedence_missing_vs_code_scope",
        string1=MISSING,
        string2=Code("function() {}", {"x": 1}),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg=(
            "$strcasecmp should error on Code with scope in second position"
            " even with missing first"
        ),
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(STRCASECMP_TYPE_PRECEDENCE_TESTS))
def test_strcasecmp_type_precedence_cases(collection, test_case: StrcasecmpTest):
    """Test $strcasecmp type error precedence over null and missing."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
