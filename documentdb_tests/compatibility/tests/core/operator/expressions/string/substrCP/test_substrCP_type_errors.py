from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, MaxKey, MinKey, ObjectId, Regex, Timestamp
from bson.code import Code

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BSON_TO_STRING_CONVERSION_ERROR,
    SUBSTRCP_COUNT_TYPE_ERROR,
    SUBSTRCP_INDEX_TYPE_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

from .utils.substrCP_common import SubstrCPTest, _expr

# Property [Type Strictness Param 1]: non-coercible types for the string expression produce an
# error.
SUBSTRCP_STRING_TYPE_TESTS: list[SubstrCPTest] = [
    SubstrCPTest(
        "type_string_bool",
        string=True,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$substrCP should reject bool as string expression",
    ),
    SubstrCPTest(
        "type_string_array",
        string=["a"],
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$substrCP should reject array as string expression",
    ),
    SubstrCPTest(
        "type_string_object",
        string={"a": 1},
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$substrCP should reject object as string expression",
    ),
    SubstrCPTest(
        "type_string_objectid",
        string=ObjectId("507f1f77bcf86cd799439011"),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$substrCP should reject ObjectId as string expression",
    ),
    SubstrCPTest(
        "type_string_binary",
        string=Binary(b"data"),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$substrCP should reject Binary as string expression",
    ),
    SubstrCPTest(
        "type_string_binary_uuid",
        string=Binary(b"data", 4),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$substrCP should reject Binary UUID as string expression",
    ),
    SubstrCPTest(
        "type_string_regex",
        string=Regex("pattern"),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$substrCP should reject Regex as string expression",
    ),
    SubstrCPTest(
        "type_string_code_scope",
        string=Code("function() {}", {"x": 1}),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$substrCP should reject Code with scope as string expression",
    ),
    SubstrCPTest(
        "type_string_minkey",
        string=MinKey(),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$substrCP should reject MinKey as string expression",
    ),
    SubstrCPTest(
        "type_string_maxkey",
        string=MaxKey(),
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$substrCP should reject MaxKey as string expression",
    ),
    SubstrCPTest(
        "type_string_expr_array",
        string={"$literal": [1, 2]},
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$substrCP should reject expression that evaluates to array at runtime",
    ),
]

# Property [Type Strictness Param 2]: non-numeric types for the index produce an error.
SUBSTRCP_INDEX_TYPE_TESTS: list[SubstrCPTest] = [
    SubstrCPTest(
        "type_index_string",
        string="hello",
        index="bad",
        error_code=SUBSTRCP_INDEX_TYPE_ERROR,
        msg="$substrCP should reject string as index",
    ),
    SubstrCPTest(
        "type_index_bool",
        string="hello",
        index=True,
        error_code=SUBSTRCP_INDEX_TYPE_ERROR,
        msg="$substrCP should reject bool as index",
    ),
    SubstrCPTest(
        "type_index_array",
        string="hello",
        index=[1],
        error_code=SUBSTRCP_INDEX_TYPE_ERROR,
        msg="$substrCP should reject array as index",
    ),
    SubstrCPTest(
        "type_index_object",
        string="hello",
        index={"a": 1},
        error_code=SUBSTRCP_INDEX_TYPE_ERROR,
        msg="$substrCP should reject object as index",
    ),
    SubstrCPTest(
        "type_index_objectid",
        string="hello",
        index=ObjectId("507f1f77bcf86cd799439011"),
        error_code=SUBSTRCP_INDEX_TYPE_ERROR,
        msg="$substrCP should reject ObjectId as index",
    ),
    SubstrCPTest(
        "type_index_datetime",
        string="hello",
        index=datetime(2024, 1, 1, tzinfo=timezone.utc),
        error_code=SUBSTRCP_INDEX_TYPE_ERROR,
        msg="$substrCP should reject datetime as index",
    ),
    SubstrCPTest(
        "type_index_timestamp",
        string="hello",
        index=Timestamp(1, 1),
        error_code=SUBSTRCP_INDEX_TYPE_ERROR,
        msg="$substrCP should reject Timestamp as index",
    ),
    SubstrCPTest(
        "type_index_binary",
        string="hello",
        index=Binary(b"data"),
        error_code=SUBSTRCP_INDEX_TYPE_ERROR,
        msg="$substrCP should reject Binary as index",
    ),
    SubstrCPTest(
        "type_index_regex",
        string="hello",
        index=Regex("pattern"),
        error_code=SUBSTRCP_INDEX_TYPE_ERROR,
        msg="$substrCP should reject Regex as index",
    ),
    SubstrCPTest(
        "type_index_code",
        string="hello",
        index=Code("function() {}"),
        error_code=SUBSTRCP_INDEX_TYPE_ERROR,
        msg="$substrCP should reject Code as index",
    ),
    SubstrCPTest(
        "type_index_code_scope",
        string="hello",
        index=Code("function() {}", {"x": 1}),
        error_code=SUBSTRCP_INDEX_TYPE_ERROR,
        msg="$substrCP should reject Code with scope as index",
    ),
    SubstrCPTest(
        "type_index_minkey",
        string="hello",
        index=MinKey(),
        error_code=SUBSTRCP_INDEX_TYPE_ERROR,
        msg="$substrCP should reject MinKey as index",
    ),
    SubstrCPTest(
        "type_index_maxkey",
        string="hello",
        index=MaxKey(),
        error_code=SUBSTRCP_INDEX_TYPE_ERROR,
        msg="$substrCP should reject MaxKey as index",
    ),
    SubstrCPTest(
        "type_index_null",
        string="hello",
        index=None,
        error_code=SUBSTRCP_INDEX_TYPE_ERROR,
        msg="$substrCP should reject null as index",
    ),
    SubstrCPTest(
        "type_index_missing",
        string="hello",
        index=MISSING,
        error_code=SUBSTRCP_INDEX_TYPE_ERROR,
        msg="$substrCP should reject missing field as index",
    ),
    SubstrCPTest(
        "type_index_expr_array",
        string="hello",
        index={"$literal": [1, 2]},
        error_code=SUBSTRCP_INDEX_TYPE_ERROR,
        msg="$substrCP should reject expression that evaluates to array as index",
    ),
]

# Property [Type Strictness Param 3]: non-numeric types for the count produce
# SUBSTRCP_COUNT_TYPE_ERROR.
SUBSTRCP_COUNT_TYPE_TESTS: list[SubstrCPTest] = [
    SubstrCPTest(
        "type_count_string",
        string="hello",
        index=0,
        count="bad",
        error_code=SUBSTRCP_COUNT_TYPE_ERROR,
        msg="$substrCP should reject string as count",
    ),
    SubstrCPTest(
        "type_count_bool",
        string="hello",
        index=0,
        count=True,
        error_code=SUBSTRCP_COUNT_TYPE_ERROR,
        msg="$substrCP should reject bool as count",
    ),
    SubstrCPTest(
        "type_count_array",
        string="hello",
        index=0,
        count=[1],
        error_code=SUBSTRCP_COUNT_TYPE_ERROR,
        msg="$substrCP should reject array as count",
    ),
    SubstrCPTest(
        "type_count_object",
        string="hello",
        index=0,
        count={"a": 1},
        error_code=SUBSTRCP_COUNT_TYPE_ERROR,
        msg="$substrCP should reject object as count",
    ),
    SubstrCPTest(
        "type_count_objectid",
        string="hello",
        index=0,
        count=ObjectId("507f1f77bcf86cd799439011"),
        error_code=SUBSTRCP_COUNT_TYPE_ERROR,
        msg="$substrCP should reject ObjectId as count",
    ),
    SubstrCPTest(
        "type_count_datetime",
        string="hello",
        index=0,
        count=datetime(2024, 1, 1, tzinfo=timezone.utc),
        error_code=SUBSTRCP_COUNT_TYPE_ERROR,
        msg="$substrCP should reject datetime as count",
    ),
    SubstrCPTest(
        "type_count_timestamp",
        string="hello",
        index=0,
        count=Timestamp(1, 1),
        error_code=SUBSTRCP_COUNT_TYPE_ERROR,
        msg="$substrCP should reject Timestamp as count",
    ),
    SubstrCPTest(
        "type_count_binary",
        string="hello",
        index=0,
        count=Binary(b"data"),
        error_code=SUBSTRCP_COUNT_TYPE_ERROR,
        msg="$substrCP should reject Binary as count",
    ),
    SubstrCPTest(
        "type_count_regex",
        string="hello",
        index=0,
        count=Regex("pattern"),
        error_code=SUBSTRCP_COUNT_TYPE_ERROR,
        msg="$substrCP should reject Regex as count",
    ),
    SubstrCPTest(
        "type_count_code",
        string="hello",
        index=0,
        count=Code("function() {}"),
        error_code=SUBSTRCP_COUNT_TYPE_ERROR,
        msg="$substrCP should reject Code as count",
    ),
    SubstrCPTest(
        "type_count_code_scope",
        string="hello",
        index=0,
        count=Code("function() {}", {"x": 1}),
        error_code=SUBSTRCP_COUNT_TYPE_ERROR,
        msg="$substrCP should reject Code with scope as count",
    ),
    SubstrCPTest(
        "type_count_minkey",
        string="hello",
        index=0,
        count=MinKey(),
        error_code=SUBSTRCP_COUNT_TYPE_ERROR,
        msg="$substrCP should reject MinKey as count",
    ),
    SubstrCPTest(
        "type_count_maxkey",
        string="hello",
        index=0,
        count=MaxKey(),
        error_code=SUBSTRCP_COUNT_TYPE_ERROR,
        msg="$substrCP should reject MaxKey as count",
    ),
    SubstrCPTest(
        "type_count_null",
        string="hello",
        index=0,
        count=None,
        error_code=SUBSTRCP_COUNT_TYPE_ERROR,
        msg="$substrCP should reject null as count",
    ),
    SubstrCPTest(
        "type_count_missing",
        string="hello",
        index=0,
        count=MISSING,
        error_code=SUBSTRCP_COUNT_TYPE_ERROR,
        msg="$substrCP should reject missing field as count",
    ),
    SubstrCPTest(
        "type_count_expr_array",
        string="hello",
        index=0,
        count={"$literal": [1, 2]},
        error_code=SUBSTRCP_COUNT_TYPE_ERROR,
        msg="$substrCP should reject expression that evaluates to array as count",
    ),
]


SUBSTRCP_TYPE_ERROR_ALL_TESTS = (
    SUBSTRCP_STRING_TYPE_TESTS + SUBSTRCP_INDEX_TYPE_TESTS + SUBSTRCP_COUNT_TYPE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SUBSTRCP_TYPE_ERROR_ALL_TESTS))
def test_substrcp_type_errors(collection, test_case: SubstrCPTest):
    """Test $substrCP type error cases."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
