from __future__ import annotations

from datetime import datetime

import pytest
from bson import Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.set.utils.set_common import (
    STAGE_NAMES,
    replace_stage_name,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    CONFLICTING_PATH_ERROR,
    DOTTED_FIELD_IN_SUB_OBJECT_ERROR,
    FAILED_TO_PARSE_ERROR,
    FIELD_PATH_DOLLAR_PREFIX_ERROR,
    FIELD_PATH_EMPTY_COMPONENT_ERROR,
    FIELD_PATH_EMPTY_ERROR,
    FIELD_PATH_TRAILING_DOT_ERROR,
    INVALID_DOLLAR_FIELD_PATH,
    MULTIPLE_EXPRESSIONS_ERROR,
    SET_SPECIFICATION_NOT_OBJECT_ERROR,
    UNRECOGNIZED_EXPRESSION_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF

# Property [Specification Type Errors]: a non-document argument to $set
# produces an error.
SET_SPEC_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "spec_type_error_string",
        docs=[{"_id": 1}],
        pipeline=[{"$set": "not_a_doc"}],
        error_code=SET_SPECIFICATION_NOT_OBJECT_ERROR,
        msg="$set should reject a string specification",
    ),
    StageTestCase(
        "spec_type_error_int",
        docs=[{"_id": 1}],
        pipeline=[{"$set": 42}],
        error_code=SET_SPECIFICATION_NOT_OBJECT_ERROR,
        msg="$set should reject an integer specification",
    ),
    StageTestCase(
        "spec_type_error_int64",
        docs=[{"_id": 1}],
        pipeline=[{"$set": Int64(42)}],
        error_code=SET_SPECIFICATION_NOT_OBJECT_ERROR,
        msg="$set should reject an Int64 specification",
    ),
    StageTestCase(
        "spec_type_error_float",
        docs=[{"_id": 1}],
        pipeline=[{"$set": 3.14}],
        error_code=SET_SPECIFICATION_NOT_OBJECT_ERROR,
        msg="$set should reject a float specification",
    ),
    StageTestCase(
        "spec_type_error_decimal128",
        docs=[{"_id": 1}],
        pipeline=[{"$set": DECIMAL128_ONE_AND_HALF}],
        error_code=SET_SPECIFICATION_NOT_OBJECT_ERROR,
        msg="$set should reject a Decimal128 specification",
    ),
    StageTestCase(
        "spec_type_error_bool",
        docs=[{"_id": 1}],
        pipeline=[{"$set": True}],
        error_code=SET_SPECIFICATION_NOT_OBJECT_ERROR,
        msg="$set should reject a boolean specification",
    ),
    StageTestCase(
        "spec_type_error_null",
        docs=[{"_id": 1}],
        pipeline=[{"$set": None}],
        error_code=SET_SPECIFICATION_NOT_OBJECT_ERROR,
        msg="$set should reject a null specification",
    ),
    StageTestCase(
        "spec_type_error_array",
        docs=[{"_id": 1}],
        pipeline=[{"$set": [1, 2, 3]}],
        error_code=SET_SPECIFICATION_NOT_OBJECT_ERROR,
        msg="$set should reject an array specification",
    ),
    StageTestCase(
        "spec_type_error_objectid",
        docs=[{"_id": 1}],
        pipeline=[{"$set": ObjectId("507f1f77bcf86cd799439011")}],
        error_code=SET_SPECIFICATION_NOT_OBJECT_ERROR,
        msg="$set should reject an ObjectId specification",
    ),
    StageTestCase(
        "spec_type_error_datetime",
        docs=[{"_id": 1}],
        pipeline=[{"$set": datetime(2023, 1, 1)}],
        error_code=SET_SPECIFICATION_NOT_OBJECT_ERROR,
        msg="$set should reject a datetime specification",
    ),
    StageTestCase(
        "spec_type_error_timestamp",
        docs=[{"_id": 1}],
        pipeline=[{"$set": Timestamp(1, 1)}],
        error_code=SET_SPECIFICATION_NOT_OBJECT_ERROR,
        msg="$set should reject a Timestamp specification",
    ),
    StageTestCase(
        "spec_type_error_regex",
        docs=[{"_id": 1}],
        pipeline=[{"$set": Regex("abc", "i")}],
        error_code=SET_SPECIFICATION_NOT_OBJECT_ERROR,
        msg="$set should reject a Regex specification",
    ),
    StageTestCase(
        "spec_type_error_binary",
        docs=[{"_id": 1}],
        pipeline=[{"$set": b"\x01\x02"}],
        error_code=SET_SPECIFICATION_NOT_OBJECT_ERROR,
        msg="$set should reject a binary specification",
    ),
    StageTestCase(
        "spec_type_error_code",
        docs=[{"_id": 1}],
        pipeline=[{"$set": Code("function() {}")}],
        error_code=SET_SPECIFICATION_NOT_OBJECT_ERROR,
        msg="$set should reject a Code specification",
    ),
    StageTestCase(
        "spec_type_error_code_with_scope",
        docs=[{"_id": 1}],
        pipeline=[{"$set": Code("function() {}", {"x": 1})}],
        error_code=SET_SPECIFICATION_NOT_OBJECT_ERROR,
        msg="$set should reject a Code with scope specification",
    ),
    StageTestCase(
        "spec_type_error_minkey",
        docs=[{"_id": 1}],
        pipeline=[{"$set": MinKey()}],
        error_code=SET_SPECIFICATION_NOT_OBJECT_ERROR,
        msg="$set should reject a MinKey specification",
    ),
    StageTestCase(
        "spec_type_error_maxkey",
        docs=[{"_id": 1}],
        pipeline=[{"$set": MaxKey()}],
        error_code=SET_SPECIFICATION_NOT_OBJECT_ERROR,
        msg="$set should reject a MaxKey specification",
    ),
]

# Property [Field Name Validation Errors]: field names in the $set
# specification must be non-empty, must not start with $, and must not contain
# empty path components (leading, trailing, or consecutive dots).
SET_FIELD_NAME_VALIDATION_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "field_name_empty_string",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"": 1}}],
        error_code=FIELD_PATH_EMPTY_ERROR,
        msg="$set should reject an empty string as a field name",
    ),
    StageTestCase(
        "field_name_dollar_a",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"$a": 1}}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$set should reject a $-prefixed field name",
    ),
    StageTestCase(
        "field_name_nested_dollar_b",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"a.$b": 1}}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$set should reject a $-prefixed component in a dotted field name",
    ),
    StageTestCase(
        "field_name_dollar_only",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"$": 1}}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$set should reject a bare '$' as a field name",
    ),
    StageTestCase(
        "field_name_nested_dollar_only",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"a.$": 1}}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$set should reject a trailing '$' component in a dotted field name",
    ),
    StageTestCase(
        "field_name_leading_dot",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {".a": 1}}],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="$set should reject a field name with a leading dot",
    ),
    StageTestCase(
        "field_name_trailing_dot",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"a.": 1}}],
        error_code=FIELD_PATH_TRAILING_DOT_ERROR,
        msg="$set should reject a field name with a trailing dot",
    ),
    StageTestCase(
        "field_name_double_dot",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"a..b": 1}}],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="$set should reject a field name with a double dot",
    ),
    StageTestCase(
        "field_name_single_dot",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {".": 1}}],
        error_code=FIELD_PATH_TRAILING_DOT_ERROR,
        msg="$set should reject a single dot as a field name",
    ),
    StageTestCase(
        "field_name_double_dot_only",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"..": 1}}],
        error_code=FIELD_PATH_TRAILING_DOT_ERROR,
        msg="$set should reject a double dot as a field name",
    ),
    # Trailing dot validation takes precedence over $-prefix validation.
    StageTestCase(
        "field_name_dollar_dot",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"$.": 1}}],
        error_code=FIELD_PATH_TRAILING_DOT_ERROR,
        msg="$set should reject '$.' with a trailing dot error",
    ),
    StageTestCase(
        "field_name_dollar_dot_a",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"$.a": 1}}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$set should reject '$.a' with a $-prefix error",
    ),
]

# Property [Conflicting Path Errors]: parent-child path conflicts in the same
# specification produce an error regardless of field order.
SET_CONFLICTING_PATH_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "conflicting_parent_child",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"a": 1, "a.b": 2}}],
        error_code=CONFLICTING_PATH_ERROR,
        msg="$set should reject parent-child path conflict (parent first)",
    ),
    StageTestCase(
        "conflicting_child_parent",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"a.b": 2, "a": 1}}],
        error_code=CONFLICTING_PATH_ERROR,
        msg="$set should reject parent-child path conflict (child first)",
    ),
]

# Property [Dollar-Sign String Value Errors]: "$" and "$$" as field values
# produce errors because they are invalid field paths and variable names
# respectively.
SET_DOLLAR_SIGN_VALUE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "dollar_sign_value",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"a": "$"}}],
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$set should reject '$' as a field value because it is not a valid field path",
    ),
    StageTestCase(
        "double_dollar_sign_value",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"a": "$$"}}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$set should reject '$$' as a field value because it is an empty variable name",
    ),
]

# Property [Embedded Object Value Errors]: $-prefixed keys inside embedded
# objects are treated as expression operators and must be valid. Dotted field
# names and multiple operators in a single sub-document are rejected.
SET_EMBEDDED_OBJECT_VALUE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "embedded_unrecognized_expression",
        docs=[{"_id": 1, "a": {"x": 1}}],
        pipeline=[{"$set": {"a": {"$bogus": 1}}}],
        error_code=UNRECOGNIZED_EXPRESSION_ERROR,
        msg="$set should reject an unrecognized $-prefixed key inside an embedded object",
    ),
    StageTestCase(
        "embedded_dotted_field_name",
        docs=[{"_id": 1, "a": {"x": 1}}],
        pipeline=[{"$set": {"a": {"x.y": 1}}}],
        error_code=DOTTED_FIELD_IN_SUB_OBJECT_ERROR,
        msg="$set should reject a dotted field name inside an embedded object value",
    ),
    StageTestCase(
        "embedded_multiple_expressions",
        docs=[{"_id": 1, "a": {"x": 1}}],
        pipeline=[{"$set": {"a": {"$add": [1, 2], "$multiply": [3, 4]}}}],
        error_code=MULTIPLE_EXPRESSIONS_ERROR,
        msg="$set should reject multiple $-prefixed operators in a single sub-document value",
    ),
]

SET_ERROR_TESTS = (
    SET_SPEC_TYPE_ERROR_TESTS
    + SET_FIELD_NAME_VALIDATION_ERROR_TESTS
    + SET_CONFLICTING_PATH_ERROR_TESTS
    + SET_DOLLAR_SIGN_VALUE_ERROR_TESTS
    + SET_EMBEDDED_OBJECT_VALUE_ERROR_TESTS
)


@pytest.mark.parametrize("stage_name", STAGE_NAMES)
@pytest.mark.parametrize("test_case", pytest_params(SET_ERROR_TESTS))
def test_set_errors(collection, stage_name: str, test_case: StageTestCase):
    """Test $set / $addFields error cases."""
    populate_collection(collection, test_case)
    pipeline = replace_stage_name(test_case.pipeline, stage_name)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=f"{stage_name!r}: {test_case.msg!r}",
    )
