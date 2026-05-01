"""Tests for $unwind stage — includeArrayIndex validation errors."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
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
    FIELD_PATH_DOLLAR_PREFIX_ERROR,
    FIELD_PATH_EMPTY_COMPONENT_ERROR,
    FIELD_PATH_NULL_BYTE_ERROR,
    FIELD_PATH_TRAILING_DOT_ERROR,
    UNWIND_INCLUDE_ARRAY_INDEX_DOLLAR_PREFIX_ERROR,
    UNWIND_INCLUDE_ARRAY_INDEX_TYPE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [includeArrayIndex Type Validation]: all non-string BSON types and
# the empty string for includeArrayIndex are rejected with a type error; null
# is not treated as "omit the option".
UNWIND_INCLUDE_ARRAY_INDEX_TYPE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "index_type_int32",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": 1}}],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_TYPE_ERROR,
        msg="includeArrayIndex should reject int32",
    ),
    StageTestCase(
        "index_type_int64",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": Int64(1)}}],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_TYPE_ERROR,
        msg="includeArrayIndex should reject Int64",
    ),
    StageTestCase(
        "index_type_double",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": 1.5}}],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_TYPE_ERROR,
        msg="includeArrayIndex should reject double",
    ),
    StageTestCase(
        "index_type_double_whole_number",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": 3.0}}],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_TYPE_ERROR,
        msg="includeArrayIndex should reject whole-number double 3.0",
    ),
    StageTestCase(
        "index_type_decimal128",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": Decimal128("1")}}],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_TYPE_ERROR,
        msg="includeArrayIndex should reject Decimal128",
    ),
    StageTestCase(
        "index_type_bool",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": True}}],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_TYPE_ERROR,
        msg="includeArrayIndex should reject bool",
    ),
    StageTestCase(
        "index_type_null",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": None}}],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_TYPE_ERROR,
        msg="includeArrayIndex should reject null (not treated as omit)",
    ),
    StageTestCase(
        "index_type_array",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": ["idx"]}}],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_TYPE_ERROR,
        msg="includeArrayIndex should reject array",
    ),
    StageTestCase(
        "index_type_object",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": {"x": 1}}}],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_TYPE_ERROR,
        msg="includeArrayIndex should reject object",
    ),
    StageTestCase(
        "index_type_objectid",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[
            {
                "$unwind": {
                    "path": "$a",
                    "includeArrayIndex": ObjectId("000000000000000000000001"),
                }
            }
        ],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_TYPE_ERROR,
        msg="includeArrayIndex should reject ObjectId",
    ),
    StageTestCase(
        "index_type_datetime",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": datetime(2024, 1, 1)}}],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_TYPE_ERROR,
        msg="includeArrayIndex should reject datetime",
    ),
    StageTestCase(
        "index_type_timestamp",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": Timestamp(1, 1)}}],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_TYPE_ERROR,
        msg="includeArrayIndex should reject Timestamp",
    ),
    StageTestCase(
        "index_type_binary",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": Binary(b"\x01")}}],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_TYPE_ERROR,
        msg="includeArrayIndex should reject Binary",
    ),
    StageTestCase(
        "index_type_binary_uuid",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[
            {
                "$unwind": {
                    "path": "$a",
                    "includeArrayIndex": Binary.from_uuid(
                        UUID("12345678-1234-1234-1234-123456789abc")
                    ),
                }
            }
        ],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_TYPE_ERROR,
        msg="includeArrayIndex should reject Binary UUID",
    ),
    StageTestCase(
        "index_type_regex",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": Regex("^a")}}],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_TYPE_ERROR,
        msg="includeArrayIndex should reject Regex",
    ),
    StageTestCase(
        "index_type_code",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": Code("x")}}],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_TYPE_ERROR,
        msg="includeArrayIndex should reject Code",
    ),
    StageTestCase(
        "index_type_code_with_scope",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": Code("x", {})}}],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_TYPE_ERROR,
        msg="includeArrayIndex should reject Code with scope",
    ),
    StageTestCase(
        "index_type_minkey",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": MinKey()}}],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_TYPE_ERROR,
        msg="includeArrayIndex should reject MinKey",
    ),
    StageTestCase(
        "index_type_maxkey",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": MaxKey()}}],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_TYPE_ERROR,
        msg="includeArrayIndex should reject MaxKey",
    ),
    StageTestCase(
        "index_type_empty_string",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": ""}}],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_TYPE_ERROR,
        msg="includeArrayIndex should reject empty string",
    ),
]

# Property [includeArrayIndex Dollar Prefix]: all $-prefixed strings for
# includeArrayIndex are rejected with a dollar prefix error, and this check
# fires before path semantic validation and preserveNullAndEmptyArrays type
# validation.
UNWIND_INCLUDE_ARRAY_INDEX_DOLLAR_PREFIX_TESTS: list[StageTestCase] = [
    StageTestCase(
        "index_dollar_prefix_field_ref",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "$idx"}}],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_DOLLAR_PREFIX_ERROR,
        msg="includeArrayIndex should reject $-prefixed string",
    ),
    StageTestCase(
        "index_dollar_prefix_bare_dollar",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "$"}}],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_DOLLAR_PREFIX_ERROR,
        msg="includeArrayIndex should reject bare dollar sign",
    ),
    StageTestCase(
        "index_dollar_prefix_double_dollar",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "$$"}}],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_DOLLAR_PREFIX_ERROR,
        msg="includeArrayIndex should reject double dollar sign",
    ),
    StageTestCase(
        "index_dollar_prefix_dotted",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "$a.b"}}],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_DOLLAR_PREFIX_ERROR,
        msg="includeArrayIndex should reject $-prefixed dotted string",
    ),
    StageTestCase(
        "index_dollar_prefix_with_null_byte",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "$a\x00b"}}],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_DOLLAR_PREFIX_ERROR,
        msg="includeArrayIndex should reject $-prefixed string containing null byte",
    ),
    StageTestCase(
        "index_dollar_prefix_leading_dot",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "$.a"}}],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_DOLLAR_PREFIX_ERROR,
        msg="includeArrayIndex should reject $-prefixed string with leading dot",
    ),
]

# Property [includeArrayIndex Field Path Syntax]: the includeArrayIndex value
# must be a valid field path with no null bytes, no empty components, no
# trailing dots, and no dollar signs in any component.
UNWIND_INCLUDE_ARRAY_INDEX_FIELD_PATH_SYNTAX_TESTS: list[StageTestCase] = [
    StageTestCase(
        "index_field_path_null_byte",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "x\x00y"}}],
        error_code=FIELD_PATH_NULL_BYTE_ERROR,
        msg="includeArrayIndex should reject null byte in value",
    ),
    StageTestCase(
        "index_field_path_leading_dot",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": ".a"}}],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="includeArrayIndex should reject leading dot (empty component)",
    ),
    StageTestCase(
        "index_field_path_double_dot",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "a..b"}}],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="includeArrayIndex should reject double dot (empty component)",
    ),
    StageTestCase(
        "index_field_path_trailing_dot",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "a."}}],
        error_code=FIELD_PATH_TRAILING_DOT_ERROR,
        msg="includeArrayIndex should reject trailing dot",
    ),
    StageTestCase(
        "index_field_path_dollar_in_component",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "a.$b"}}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="includeArrayIndex should reject dollar sign in a component",
    ),
]

UNWIND_INDEX_VALIDATION_ALL_TESTS = (
    UNWIND_INCLUDE_ARRAY_INDEX_TYPE_TESTS
    + UNWIND_INCLUDE_ARRAY_INDEX_DOLLAR_PREFIX_TESTS
    + UNWIND_INCLUDE_ARRAY_INDEX_FIELD_PATH_SYNTAX_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(UNWIND_INDEX_VALIDATION_ALL_TESTS))
def test_unwind_index_validation_errors(collection, test_case: StageTestCase):
    """Test $unwind includeArrayIndex validation errors."""
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
