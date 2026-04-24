"""Tests for $count aggregation stage — error handling."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    COUNT_FIELD_DOLLAR_PREFIX_ERROR,
    COUNT_FIELD_DOT_ERROR,
    COUNT_FIELD_EMPTY_ERROR,
    COUNT_FIELD_ID_RESERVED_ERROR,
    COUNT_FIELD_NULL_BYTE_ERROR,
    COUNT_FIELD_TYPE_ERROR,
    PIPELINE_STAGE_EXTRA_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_ZERO

# Property [Arity Errors]: the $count stage document must contain exactly one
# key, and the multi-key error fires before any validation of the value.
COUNT_ARITY_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "arity_extra_key",
        docs=[{"_id": 1}],
        pipeline=[{"$count": "total", "extra": 1}],
        error_code=PIPELINE_STAGE_EXTRA_FIELD_ERROR,
        msg="$count should reject a stage document with multiple keys",
    ),
]

# Property [Type Strictness]: any non-string type is rejected as the count field.
COUNT_TYPE_STRICTNESS_TESTS: list[StageTestCase] = [
    StageTestCase(
        "type_int32",
        docs=[{"_id": 1}],
        pipeline=[{"$count": 42}],
        error_code=COUNT_FIELD_TYPE_ERROR,
        msg="$count should reject int32 value",
    ),
    StageTestCase(
        "type_int64",
        docs=[{"_id": 1}],
        pipeline=[{"$count": Int64(42)}],
        error_code=COUNT_FIELD_TYPE_ERROR,
        msg="$count should reject int64 value",
    ),
    StageTestCase(
        "type_double",
        docs=[{"_id": 1}],
        pipeline=[{"$count": 3.14}],
        error_code=COUNT_FIELD_TYPE_ERROR,
        msg="$count should reject double value",
    ),
    StageTestCase(
        "type_decimal128",
        docs=[{"_id": 1}],
        pipeline=[{"$count": DECIMAL128_ZERO}],
        error_code=COUNT_FIELD_TYPE_ERROR,
        msg="$count should reject Decimal128 value",
    ),
    StageTestCase(
        "type_bool",
        docs=[{"_id": 1}],
        pipeline=[{"$count": True}],
        error_code=COUNT_FIELD_TYPE_ERROR,
        msg="$count should reject boolean value",
    ),
    StageTestCase(
        "type_null",
        docs=[{"_id": 1}],
        pipeline=[{"$count": None}],
        error_code=COUNT_FIELD_TYPE_ERROR,
        msg="$count should reject null value",
    ),
    StageTestCase(
        "type_array",
        docs=[{"_id": 1}],
        pipeline=[{"$count": ["x"]}],
        error_code=COUNT_FIELD_TYPE_ERROR,
        msg="$count should reject array value",
    ),
    StageTestCase(
        "type_object",
        docs=[{"_id": 1}],
        pipeline=[{"$count": {"x": 1}}],
        error_code=COUNT_FIELD_TYPE_ERROR,
        msg="$count should reject object value",
    ),
    StageTestCase(
        "type_objectid",
        docs=[{"_id": 1}],
        pipeline=[{"$count": ObjectId("000000000000000000000001")}],
        error_code=COUNT_FIELD_TYPE_ERROR,
        msg="$count should reject ObjectId value",
    ),
    StageTestCase(
        "type_datetime",
        docs=[{"_id": 1}],
        pipeline=[{"$count": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        error_code=COUNT_FIELD_TYPE_ERROR,
        msg="$count should reject datetime value",
    ),
    StageTestCase(
        "type_timestamp",
        docs=[{"_id": 1}],
        pipeline=[{"$count": Timestamp(1, 1)}],
        error_code=COUNT_FIELD_TYPE_ERROR,
        msg="$count should reject Timestamp value",
    ),
    StageTestCase(
        "type_binary",
        docs=[{"_id": 1}],
        pipeline=[{"$count": Binary(b"hello")}],
        error_code=COUNT_FIELD_TYPE_ERROR,
        msg="$count should reject Binary value",
    ),
    StageTestCase(
        "type_regex",
        docs=[{"_id": 1}],
        pipeline=[{"$count": Regex("abc")}],
        error_code=COUNT_FIELD_TYPE_ERROR,
        msg="$count should reject Regex value",
    ),
    StageTestCase(
        "type_code",
        docs=[{"_id": 1}],
        pipeline=[{"$count": Code("function(){}")}],
        error_code=COUNT_FIELD_TYPE_ERROR,
        msg="$count should reject Code value",
    ),
    StageTestCase(
        "type_code_with_scope",
        docs=[{"_id": 1}],
        pipeline=[{"$count": Code("function(){}", {"x": 1})}],
        error_code=COUNT_FIELD_TYPE_ERROR,
        msg="$count should reject CodeWithScope value",
    ),
    StageTestCase(
        "type_minkey",
        docs=[{"_id": 1}],
        pipeline=[{"$count": MinKey()}],
        error_code=COUNT_FIELD_TYPE_ERROR,
        msg="$count should reject MinKey value",
    ),
    StageTestCase(
        "type_maxkey",
        docs=[{"_id": 1}],
        pipeline=[{"$count": MaxKey()}],
        error_code=COUNT_FIELD_TYPE_ERROR,
        msg="$count should reject MaxKey value",
    ),
    StageTestCase(
        "type_expression_object",
        docs=[{"_id": 1}],
        pipeline=[{"$count": {"$literal": "x"}}],
        error_code=COUNT_FIELD_TYPE_ERROR,
        msg="$count should reject expression-like object without evaluating it",
    ),
]

# Property [String Validation Errors]: invalid string values are rejected
# with specific error codes depending on the violation.
COUNT_STRING_VALIDATION_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "string_empty",
        docs=[{"_id": 1}],
        pipeline=[{"$count": ""}],
        error_code=COUNT_FIELD_EMPTY_ERROR,
        msg="$count should reject empty string",
    ),
    StageTestCase(
        "string_dollar_prefix_bare",
        docs=[{"_id": 1}],
        pipeline=[{"$count": "$"}],
        error_code=COUNT_FIELD_DOLLAR_PREFIX_ERROR,
        msg="$count should reject string starting with $",
    ),
    StageTestCase(
        "string_dollar_prefix_word",
        docs=[{"_id": 1}],
        pipeline=[{"$count": "$foo"}],
        error_code=COUNT_FIELD_DOLLAR_PREFIX_ERROR,
        msg="$count should reject $-prefixed path",
    ),
    StageTestCase(
        "string_dollar_prefix_nested",
        docs=[{"_id": 1}],
        pipeline=[{"$count": "$$var"}],
        error_code=COUNT_FIELD_DOLLAR_PREFIX_ERROR,
        msg="$count should reject string starting with $$",
    ),
    StageTestCase(
        "string_null_byte_middle",
        docs=[{"_id": 1}],
        pipeline=[{"$count": "a\x00b"}],
        error_code=COUNT_FIELD_NULL_BYTE_ERROR,
        msg="$count should reject string containing null byte in middle",
    ),
    StageTestCase(
        "string_null_byte_start",
        docs=[{"_id": 1}],
        pipeline=[{"$count": "\x00abc"}],
        error_code=COUNT_FIELD_NULL_BYTE_ERROR,
        msg="$count should reject string starting with null byte",
    ),
    StageTestCase(
        "string_null_byte_end",
        docs=[{"_id": 1}],
        pipeline=[{"$count": "abc\x00"}],
        error_code=COUNT_FIELD_NULL_BYTE_ERROR,
        msg="$count should reject string ending with null byte",
    ),
    StageTestCase(
        "string_dot_bare",
        docs=[{"_id": 1}],
        pipeline=[{"$count": "."}],
        error_code=COUNT_FIELD_DOT_ERROR,
        msg="$count should reject a bare dot as field name",
    ),
    StageTestCase(
        "string_dot_double",
        docs=[{"_id": 1}],
        pipeline=[{"$count": ".."}],
        error_code=COUNT_FIELD_DOT_ERROR,
        msg="$count should reject double dot as field name",
    ),
    StageTestCase(
        "string_dot_middle",
        docs=[{"_id": 1}],
        pipeline=[{"$count": "a.b"}],
        error_code=COUNT_FIELD_DOT_ERROR,
        msg="$count should reject string containing dot",
    ),
    StageTestCase(
        "string_dot_start",
        docs=[{"_id": 1}],
        pipeline=[{"$count": ".abc"}],
        error_code=COUNT_FIELD_DOT_ERROR,
        msg="$count should reject string starting with dot",
    ),
    StageTestCase(
        "string_dot_end",
        docs=[{"_id": 1}],
        pipeline=[{"$count": "abc."}],
        error_code=COUNT_FIELD_DOT_ERROR,
        msg="$count should reject string ending with dot",
    ),
    StageTestCase(
        "string_id_exact",
        docs=[{"_id": 1}],
        pipeline=[{"$count": "_id"}],
        error_code=COUNT_FIELD_ID_RESERVED_ERROR,
        msg="$count should reject the exact string '_id'",
    ),
]

# Property [Error Precedence]: when multiple validation rules are violated
# simultaneously, errors are produced in strict priority order: multi-key >
# non-string type > $ prefix > null byte > dot > empty string > _id reserved.
COUNT_ERROR_PRECEDENCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "precedence_extra_key_over_invalid_value",
        docs=[{"_id": 1}],
        pipeline=[{"$count": 123, "extra": 1}],
        error_code=PIPELINE_STAGE_EXTRA_FIELD_ERROR,
        msg="$count multi-key error should fire before value validation",
    ),
    StageTestCase(
        "precedence_dollar_over_dot",
        docs=[{"_id": 1}],
        pipeline=[{"$count": "$."}],
        error_code=COUNT_FIELD_DOLLAR_PREFIX_ERROR,
        msg="$count $ prefix error should take precedence over dot error",
    ),
    StageTestCase(
        "precedence_dollar_over_null_byte",
        docs=[{"_id": 1}],
        pipeline=[{"$count": "$\x00"}],
        error_code=COUNT_FIELD_DOLLAR_PREFIX_ERROR,
        msg="$count $ prefix error should take precedence over null byte error",
    ),
    StageTestCase(
        "precedence_null_byte_over_dot_null_first",
        docs=[{"_id": 1}],
        pipeline=[{"$count": "\x00."}],
        error_code=COUNT_FIELD_NULL_BYTE_ERROR,
        msg="$count null byte error should take precedence over dot error when null byte is first",
    ),
    StageTestCase(
        "precedence_null_byte_over_dot_dot_first",
        docs=[{"_id": 1}],
        pipeline=[{"$count": ".\x00"}],
        error_code=COUNT_FIELD_NULL_BYTE_ERROR,
        msg="$count null byte error should take precedence over dot error when dot is first",
    ),
]

# Property [Errors on Non-Existent Collection]: every validation error fires
# even when the collection does not exist, confirming that the server rejects
# invalid $count parameters without requiring any input documents.
COUNT_NONEXISTENT_COLLECTION_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "timing_type_error_nonexistent_collection",
        docs=None,
        pipeline=[{"$count": 123}],
        error_code=COUNT_FIELD_TYPE_ERROR,
        msg="$count type error should fire on a non-existent collection",
    ),
    StageTestCase(
        "timing_empty_string_nonexistent_collection",
        docs=None,
        pipeline=[{"$count": ""}],
        error_code=COUNT_FIELD_EMPTY_ERROR,
        msg="$count empty string error should fire on a non-existent collection",
    ),
    StageTestCase(
        "timing_dollar_prefix_nonexistent_collection",
        docs=None,
        pipeline=[{"$count": "$bad"}],
        error_code=COUNT_FIELD_DOLLAR_PREFIX_ERROR,
        msg="$count $ prefix error should fire on a non-existent collection",
    ),
    StageTestCase(
        "timing_null_byte_nonexistent_collection",
        docs=None,
        pipeline=[{"$count": "a\x00b"}],
        error_code=COUNT_FIELD_NULL_BYTE_ERROR,
        msg="$count null byte error should fire on a non-existent collection",
    ),
    StageTestCase(
        "timing_dot_nonexistent_collection",
        docs=None,
        pipeline=[{"$count": "a.b"}],
        error_code=COUNT_FIELD_DOT_ERROR,
        msg="$count dot error should fire on a non-existent collection",
    ),
    StageTestCase(
        "timing_id_reserved_nonexistent_collection",
        docs=None,
        pipeline=[{"$count": "_id"}],
        error_code=COUNT_FIELD_ID_RESERVED_ERROR,
        msg="$count _id reserved error should fire on a non-existent collection",
    ),
]

# Property [Errors on Empty Collection]: every validation error fires even
# when the collection is empty, confirming that the server rejects invalid
# $count parameters without requiring any input documents.
COUNT_EMPTY_COLLECTION_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "timing_type_error_empty_collection",
        docs=[],
        pipeline=[{"$count": 123}],
        error_code=COUNT_FIELD_TYPE_ERROR,
        msg="$count type error should fire on empty collection",
    ),
    StageTestCase(
        "timing_empty_string_empty_collection",
        docs=[],
        pipeline=[{"$count": ""}],
        error_code=COUNT_FIELD_EMPTY_ERROR,
        msg="$count empty string error should fire on empty collection",
    ),
    StageTestCase(
        "timing_dollar_prefix_empty_collection",
        docs=[],
        pipeline=[{"$count": "$bad"}],
        error_code=COUNT_FIELD_DOLLAR_PREFIX_ERROR,
        msg="$count $ prefix error should fire on empty collection",
    ),
    StageTestCase(
        "timing_null_byte_empty_collection",
        docs=[],
        pipeline=[{"$count": "a\x00b"}],
        error_code=COUNT_FIELD_NULL_BYTE_ERROR,
        msg="$count null byte error should fire on empty collection",
    ),
    StageTestCase(
        "timing_dot_empty_collection",
        docs=[],
        pipeline=[{"$count": "a.b"}],
        error_code=COUNT_FIELD_DOT_ERROR,
        msg="$count dot error should fire on empty collection",
    ),
    StageTestCase(
        "timing_id_reserved_empty_collection",
        docs=[],
        pipeline=[{"$count": "_id"}],
        error_code=COUNT_FIELD_ID_RESERVED_ERROR,
        msg="$count _id reserved error should fire on empty collection",
    ),
]

COUNT_ERROR_TESTS = (
    COUNT_ARITY_ERROR_TESTS
    + COUNT_TYPE_STRICTNESS_TESTS
    + COUNT_STRING_VALIDATION_ERROR_TESTS
    + COUNT_ERROR_PRECEDENCE_TESTS
    + COUNT_NONEXISTENT_COLLECTION_ERROR_TESTS
    + COUNT_EMPTY_COLLECTION_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(COUNT_ERROR_TESTS))
def test_count_errors(collection, test_case: StageTestCase):
    """Test $count error handling."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
