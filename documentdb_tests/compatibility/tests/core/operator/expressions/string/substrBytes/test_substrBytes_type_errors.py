from __future__ import annotations

import pytest
from bson import Binary, Code, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BSON_TO_STRING_CONVERSION_ERROR,
    SUBSTR_LENGTH_TYPE_ERROR,
    SUBSTR_START_TYPE_ERROR,
)
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.framework.test_constants import MISSING
from documentdb_tests.compatibility.tests.core.operator.expressions.string.substrBytes.utils.substrBytes_common import (
    OPERATORS,
    SubstrBytesTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import execute_expression

# Property [String Parameter Type Strictness]: non-coercible types for the string parameter produce
# an error, including arrays, objects, and expressions evaluating to rejected types.
SUBSTRBYTES_STRING_TYPE_ERROR_TESTS: list[SubstrBytesTest] = [
    SubstrBytesTest(
        "string_type_bool",
        string=True,
        byte_index=0,
        byte_count=1,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$substrBytes should reject boolean string parameter",
    ),
    SubstrBytesTest(
        "string_type_empty_array",
        string=[],
        byte_index=0,
        byte_count=1,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$substrBytes should reject empty array string parameter",
    ),
    SubstrBytesTest(
        "string_type_single_array",
        string=["a"],
        byte_index=0,
        byte_count=1,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$substrBytes should reject single-element array string parameter",
    ),
    SubstrBytesTest(
        "string_type_nested_array",
        string=[["a"]],
        byte_index=0,
        byte_count=1,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$substrBytes should reject nested array string parameter",
    ),
    SubstrBytesTest(
        "string_type_array_with_null",
        string=[None],
        byte_index=0,
        byte_count=1,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$substrBytes should reject array with null string parameter",
    ),
    SubstrBytesTest(
        "string_type_object",
        string={"a": 1},
        byte_index=0,
        byte_count=1,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$substrBytes should reject object string parameter",
    ),
    SubstrBytesTest(
        "string_type_objectid",
        string=ObjectId(),
        byte_index=0,
        byte_count=1,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$substrBytes should reject ObjectId string parameter",
    ),
    SubstrBytesTest(
        "string_type_binary",
        string=Binary(b"data"),
        byte_index=0,
        byte_count=1,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$substrBytes should reject Binary string parameter",
    ),
    SubstrBytesTest(
        "string_type_binary_uuid",
        string=Binary(b"\x00" * 16, 4),
        byte_index=0,
        byte_count=1,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$substrBytes should reject Binary UUID string parameter",
    ),
    SubstrBytesTest(
        "string_type_regex",
        string=Regex("pattern"),
        byte_index=0,
        byte_count=1,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$substrBytes should reject Regex string parameter",
    ),
    SubstrBytesTest(
        "string_type_code_with_scope",
        string=Code("x", {"a": 1}),
        byte_index=0,
        byte_count=1,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$substrBytes should reject Code with scope string parameter",
    ),
    SubstrBytesTest(
        "string_type_minkey",
        string=MinKey(),
        byte_index=0,
        byte_count=1,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$substrBytes should reject MinKey string parameter",
    ),
    SubstrBytesTest(
        "string_type_maxkey",
        string=MaxKey(),
        byte_index=0,
        byte_count=1,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$substrBytes should reject MaxKey string parameter",
    ),
    # Expressions evaluating to rejected types.
    SubstrBytesTest(
        "string_type_expr_bool",
        string={"$gt": [1, 0]},
        byte_index=0,
        byte_count=1,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$substrBytes should reject expression evaluating to boolean",
    ),
    SubstrBytesTest(
        "string_type_expr_array",
        string={"$literal": ["a"]},
        byte_index=0,
        byte_count=1,
        error_code=BSON_TO_STRING_CONVERSION_ERROR,
        msg="$substrBytes should reject expression evaluating to array",
    ),
]

# Property [Index Type Strictness]: non-numeric types for byte_index produce an error, including
# expressions evaluating to non-numeric types.
SUBSTRBYTES_INDEX_TYPE_ERROR_TESTS: list[SubstrBytesTest] = [
    SubstrBytesTest(
        "index_type_null",
        string="hello",
        byte_index=None,
        byte_count=3,
        error_code=SUBSTR_START_TYPE_ERROR,
        msg="$substrBytes should reject null start index",
    ),
    SubstrBytesTest(
        "index_type_missing",
        string="hello",
        byte_index=MISSING,
        byte_count=3,
        error_code=SUBSTR_START_TYPE_ERROR,
        msg="$substrBytes should reject missing start index",
    ),
    SubstrBytesTest(
        "index_type_string",
        string="hello",
        byte_index="0",
        byte_count=3,
        error_code=SUBSTR_START_TYPE_ERROR,
        msg="$substrBytes should reject string start index",
    ),
    SubstrBytesTest(
        "index_type_bool",
        string="hello",
        byte_index=True,
        byte_count=3,
        error_code=SUBSTR_START_TYPE_ERROR,
        msg="$substrBytes should reject boolean start index",
    ),
    SubstrBytesTest(
        "index_type_array",
        string="hello",
        byte_index=[],
        byte_count=3,
        error_code=SUBSTR_START_TYPE_ERROR,
        msg="$substrBytes should reject array start index",
    ),
    SubstrBytesTest(
        "index_type_object",
        string="hello",
        byte_index={"a": 1},
        byte_count=3,
        error_code=SUBSTR_START_TYPE_ERROR,
        msg="$substrBytes should reject object start index",
    ),
    SubstrBytesTest(
        "index_type_objectid",
        string="hello",
        byte_index=ObjectId(),
        byte_count=3,
        error_code=SUBSTR_START_TYPE_ERROR,
        msg="$substrBytes should reject ObjectId start index",
    ),
    SubstrBytesTest(
        "index_type_datetime",
        string="hello",
        byte_index={"$toDate": "2024-01-01T00:00:00Z"},
        byte_count=3,
        error_code=SUBSTR_START_TYPE_ERROR,
        msg="$substrBytes should reject datetime start index",
    ),
    SubstrBytesTest(
        "index_type_timestamp",
        string="hello",
        byte_index=Timestamp(0, 1),
        byte_count=3,
        error_code=SUBSTR_START_TYPE_ERROR,
        msg="$substrBytes should reject Timestamp start index",
    ),
    SubstrBytesTest(
        "index_type_binary",
        string="hello",
        byte_index=Binary(b"data"),
        byte_count=3,
        error_code=SUBSTR_START_TYPE_ERROR,
        msg="$substrBytes should reject Binary start index",
    ),
    SubstrBytesTest(
        "index_type_binary_uuid",
        string="hello",
        byte_index=Binary(b"\x00" * 16, 4),
        byte_count=3,
        error_code=SUBSTR_START_TYPE_ERROR,
        msg="$substrBytes should reject Binary UUID start index",
    ),
    SubstrBytesTest(
        "index_type_regex",
        string="hello",
        byte_index=Regex("x"),
        byte_count=3,
        error_code=SUBSTR_START_TYPE_ERROR,
        msg="$substrBytes should reject Regex start index",
    ),
    SubstrBytesTest(
        "index_type_code",
        string="hello",
        byte_index=Code("x"),
        byte_count=3,
        error_code=SUBSTR_START_TYPE_ERROR,
        msg="$substrBytes should reject Code start index",
    ),
    SubstrBytesTest(
        "index_type_code_with_scope",
        string="hello",
        byte_index=Code("x", {"a": 1}),
        byte_count=3,
        error_code=SUBSTR_START_TYPE_ERROR,
        msg="$substrBytes should reject Code with scope start index",
    ),
    SubstrBytesTest(
        "index_type_minkey",
        string="hello",
        byte_index=MinKey(),
        byte_count=3,
        error_code=SUBSTR_START_TYPE_ERROR,
        msg="$substrBytes should reject MinKey start index",
    ),
    SubstrBytesTest(
        "index_type_maxkey",
        string="hello",
        byte_index=MaxKey(),
        byte_count=3,
        error_code=SUBSTR_START_TYPE_ERROR,
        msg="$substrBytes should reject MaxKey start index",
    ),
    # Expressions evaluating to non-numeric types.
    SubstrBytesTest(
        "index_type_expr_null",
        string="hello",
        byte_index={"$literal": None},
        byte_count=3,
        error_code=SUBSTR_START_TYPE_ERROR,
        msg="$substrBytes should reject expression evaluating to null start",
    ),
    SubstrBytesTest(
        "index_type_expr_string",
        string="hello",
        byte_index={"$concat": ["0"]},
        byte_count=3,
        error_code=SUBSTR_START_TYPE_ERROR,
        msg="$substrBytes should reject expression evaluating to string start",
    ),
    SubstrBytesTest(
        "index_type_expr_array",
        string="hello",
        byte_index={"$literal": [0]},
        byte_count=3,
        error_code=SUBSTR_START_TYPE_ERROR,
        msg="$substrBytes should reject expression evaluating to array start",
    ),
    SubstrBytesTest(
        "index_type_expr_cond_null",
        string="hello",
        byte_index={"$cond": [True, None, 0]},
        byte_count=3,
        error_code=SUBSTR_START_TYPE_ERROR,
        msg="$substrBytes should reject $cond evaluating to null start",
    ),
]

# Property [Count Type Strictness]: non-numeric types for byte_count produce an error, including
# expressions evaluating to non-numeric types.
SUBSTRBYTES_COUNT_TYPE_ERROR_TESTS: list[SubstrBytesTest] = [
    SubstrBytesTest(
        "count_type_null",
        string="hello",
        byte_index=0,
        byte_count=None,
        error_code=SUBSTR_LENGTH_TYPE_ERROR,
        msg="$substrBytes should reject null byte count",
    ),
    SubstrBytesTest(
        "count_type_missing",
        string="hello",
        byte_index=0,
        byte_count=MISSING,
        error_code=SUBSTR_LENGTH_TYPE_ERROR,
        msg="$substrBytes should reject missing byte count",
    ),
    SubstrBytesTest(
        "count_type_string",
        string="hello",
        byte_index=0,
        byte_count="3",
        error_code=SUBSTR_LENGTH_TYPE_ERROR,
        msg="$substrBytes should reject string byte count",
    ),
    SubstrBytesTest(
        "count_type_bool",
        string="hello",
        byte_index=0,
        byte_count=True,
        error_code=SUBSTR_LENGTH_TYPE_ERROR,
        msg="$substrBytes should reject boolean byte count",
    ),
    SubstrBytesTest(
        "count_type_array",
        string="hello",
        byte_index=0,
        byte_count=[],
        error_code=SUBSTR_LENGTH_TYPE_ERROR,
        msg="$substrBytes should reject array byte count",
    ),
    SubstrBytesTest(
        "count_type_object",
        string="hello",
        byte_index=0,
        byte_count={"a": 1},
        error_code=SUBSTR_LENGTH_TYPE_ERROR,
        msg="$substrBytes should reject object byte count",
    ),
    SubstrBytesTest(
        "count_type_objectid",
        string="hello",
        byte_index=0,
        byte_count=ObjectId(),
        error_code=SUBSTR_LENGTH_TYPE_ERROR,
        msg="$substrBytes should reject ObjectId byte count",
    ),
    SubstrBytesTest(
        "count_type_datetime",
        string="hello",
        byte_index=0,
        byte_count={"$toDate": "2024-01-01T00:00:00Z"},
        error_code=SUBSTR_LENGTH_TYPE_ERROR,
        msg="$substrBytes should reject datetime byte count",
    ),
    SubstrBytesTest(
        "count_type_timestamp",
        string="hello",
        byte_index=0,
        byte_count=Timestamp(0, 1),
        error_code=SUBSTR_LENGTH_TYPE_ERROR,
        msg="$substrBytes should reject Timestamp byte count",
    ),
    SubstrBytesTest(
        "count_type_binary",
        string="hello",
        byte_index=0,
        byte_count=Binary(b"data"),
        error_code=SUBSTR_LENGTH_TYPE_ERROR,
        msg="$substrBytes should reject Binary byte count",
    ),
    SubstrBytesTest(
        "count_type_binary_uuid",
        string="hello",
        byte_index=0,
        byte_count=Binary(b"\x00" * 16, 4),
        error_code=SUBSTR_LENGTH_TYPE_ERROR,
        msg="$substrBytes should reject Binary UUID byte count",
    ),
    SubstrBytesTest(
        "count_type_regex",
        string="hello",
        byte_index=0,
        byte_count=Regex("x"),
        error_code=SUBSTR_LENGTH_TYPE_ERROR,
        msg="$substrBytes should reject Regex byte count",
    ),
    SubstrBytesTest(
        "count_type_code",
        string="hello",
        byte_index=0,
        byte_count=Code("x"),
        error_code=SUBSTR_LENGTH_TYPE_ERROR,
        msg="$substrBytes should reject Code byte count",
    ),
    SubstrBytesTest(
        "count_type_code_with_scope",
        string="hello",
        byte_index=0,
        byte_count=Code("x", {"a": 1}),
        error_code=SUBSTR_LENGTH_TYPE_ERROR,
        msg="$substrBytes should reject Code with scope byte count",
    ),
    SubstrBytesTest(
        "count_type_minkey",
        string="hello",
        byte_index=0,
        byte_count=MinKey(),
        error_code=SUBSTR_LENGTH_TYPE_ERROR,
        msg="$substrBytes should reject MinKey byte count",
    ),
    SubstrBytesTest(
        "count_type_maxkey",
        string="hello",
        byte_index=0,
        byte_count=MaxKey(),
        error_code=SUBSTR_LENGTH_TYPE_ERROR,
        msg="$substrBytes should reject MaxKey byte count",
    ),
    # Expressions evaluating to non-numeric types.
    SubstrBytesTest(
        "count_type_expr_null",
        string="hello",
        byte_index=0,
        byte_count={"$literal": None},
        error_code=SUBSTR_LENGTH_TYPE_ERROR,
        msg="$substrBytes should reject expression evaluating to null count",
    ),
    SubstrBytesTest(
        "count_type_expr_string",
        string="hello",
        byte_index=0,
        byte_count={"$literal": "3"},
        error_code=SUBSTR_LENGTH_TYPE_ERROR,
        msg="$substrBytes should reject expression evaluating to string count",
    ),
    SubstrBytesTest(
        "count_type_expr_array",
        string="hello",
        byte_index=0,
        byte_count={"$literal": [3]},
        error_code=SUBSTR_LENGTH_TYPE_ERROR,
        msg="$substrBytes should reject expression evaluating to array count",
    ),
]


SUBSTRBYTES_TYPE_ERROR_ALL_TESTS = (
    SUBSTRBYTES_STRING_TYPE_ERROR_TESTS
    + SUBSTRBYTES_INDEX_TYPE_ERROR_TESTS
    + SUBSTRBYTES_COUNT_TYPE_ERROR_TESTS
)


@pytest.mark.parametrize("op", OPERATORS)
@pytest.mark.parametrize("test_case", pytest_params(SUBSTRBYTES_TYPE_ERROR_ALL_TESTS))
def test_substrbytes_type_errors(collection, op, test_case: SubstrBytesTest):
    """Test $substrBytes cases."""
    result = execute_expression(collection, _expr(test_case, op))
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
