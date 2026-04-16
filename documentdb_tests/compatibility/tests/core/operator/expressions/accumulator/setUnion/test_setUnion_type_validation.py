from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import SETUNION_TYPE_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

# Property [Type Strictness]: any argument that resolves to a non-array,
# non-null type produces a type error.
SETUNION_TYPE_STRICTNESS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "type_int32",
        expression={"$setUnion": ["$val"]},
        doc={"val": 42},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject an int32 argument",
    ),
    ExpressionTestCase(
        "type_int64",
        expression={"$setUnion": ["$val"]},
        doc={"val": Int64(42)},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject an int64 argument",
    ),
    ExpressionTestCase(
        "type_double",
        expression={"$setUnion": ["$val"]},
        doc={"val": 3.14},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject a double argument",
    ),
    ExpressionTestCase(
        "type_decimal128",
        expression={"$setUnion": ["$val"]},
        doc={"val": Decimal128("3.14")},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject a Decimal128 argument",
    ),
    ExpressionTestCase(
        "type_boolean",
        expression={"$setUnion": ["$val"]},
        doc={"val": True},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject a boolean argument",
    ),
    ExpressionTestCase(
        "type_string",
        expression={"$setUnion": ["$val"]},
        doc={"val": "hello"},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject a string argument",
    ),
    ExpressionTestCase(
        "type_object",
        expression={"$setUnion": ["$val"]},
        doc={"val": {"x": 1}},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject an object argument",
    ),
    ExpressionTestCase(
        "type_objectid",
        expression={"$setUnion": ["$val"]},
        doc={"val": ObjectId("507f1f77bcf86cd799439011")},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject an ObjectId argument",
    ),
    ExpressionTestCase(
        "type_datetime",
        expression={"$setUnion": ["$val"]},
        doc={"val": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject a datetime argument",
    ),
    ExpressionTestCase(
        "type_timestamp",
        expression={"$setUnion": ["$val"]},
        doc={"val": Timestamp(1, 1)},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject a Timestamp argument",
    ),
    ExpressionTestCase(
        "type_binary",
        expression={"$setUnion": ["$val"]},
        doc={"val": Binary(b"\x01")},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject a Binary argument",
    ),
    ExpressionTestCase(
        "type_regex",
        expression={"$setUnion": ["$val"]},
        doc={"val": Regex("abc", "i")},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject a Regex argument",
    ),
    ExpressionTestCase(
        "type_code",
        expression={"$setUnion": ["$val"]},
        doc={"val": Code("f()")},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject a Code argument",
    ),
    ExpressionTestCase(
        "type_code_with_scope",
        expression={"$setUnion": ["$val"]},
        doc={"val": Code("f()", {})},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject a CodeWithScope argument",
    ),
    ExpressionTestCase(
        "type_minkey",
        expression={"$setUnion": ["$val"]},
        doc={"val": MinKey()},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject a MinKey argument",
    ),
    ExpressionTestCase(
        "type_maxkey",
        expression={"$setUnion": ["$val"]},
        doc={"val": MaxKey()},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject a MaxKey argument",
    ),
    # Position tests: non-array before and after a valid array.
    ExpressionTestCase(
        "type_non_array_before_array",
        expression={"$setUnion": ["$val", "$a"]},
        doc={"val": "hello", "a": [1, 2]},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject a non-array argument before an array",
    ),
    ExpressionTestCase(
        "type_non_array_after_array",
        expression={"$setUnion": ["$a", "$val"]},
        doc={"a": [1, 2], "val": "hello"},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject a non-array argument after an array",
    ),
]

# Property [Bare Value Syntax]: bare (non-array-wrapped) values passed to
# $setUnion are handled based on what they resolve to.
SETUNION_BARE_VALUE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "bare_null",
        expression={"$setUnion": None},
        expected=None,
        msg="$setUnion should return null when given bare null",
    ),
    ExpressionTestCase(
        "bare_missing_field",
        expression={"$setUnion": MISSING},
        expected=None,
        msg="$setUnion should return null when given a bare missing field reference",
    ),
    ExpressionTestCase(
        "bare_array_field",
        expression={"$setUnion": "$arr"},
        doc={"arr": [3, 1, 2, 1, 3]},
        expected=[1, 2, 3],
        msg="$setUnion should deduplicate within a bare array field reference",
    ),
    ExpressionTestCase(
        "bare_nested_array_field",
        expression={"$setUnion": "$arr"},
        doc={"arr": [[1, 2], [2, 3]]},
        expected=[[1, 2], [2, 3]],
        msg="$setUnion should treat nested arrays as opaque elements in bare syntax",
    ),
    ExpressionTestCase(
        "bare_non_array_field_string",
        expression={"$setUnion": "$val"},
        doc={"val": "hello"},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject a bare field reference resolving to a string",
    ),
    ExpressionTestCase(
        "bare_non_array_field_int32",
        expression={"$setUnion": "$val"},
        doc={"val": 42},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject a bare field reference resolving to an int32",
    ),
    ExpressionTestCase(
        "bare_non_array_field_int64",
        expression={"$setUnion": "$val"},
        doc={"val": Int64(42)},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject a bare field reference resolving to an int64",
    ),
    ExpressionTestCase(
        "bare_non_array_field_double",
        expression={"$setUnion": "$val"},
        doc={"val": 3.14},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject a bare field reference resolving to a double",
    ),
    ExpressionTestCase(
        "bare_non_array_field_decimal128",
        expression={"$setUnion": "$val"},
        doc={"val": Decimal128("3.14")},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject a bare field reference resolving to a Decimal128",
    ),
    ExpressionTestCase(
        "bare_non_array_field_boolean",
        expression={"$setUnion": "$val"},
        doc={"val": True},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject a bare field reference resolving to a boolean",
    ),
    ExpressionTestCase(
        "bare_non_array_field_object",
        expression={"$setUnion": "$val"},
        doc={"val": {"x": 1}},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject a bare field reference resolving to an object",
    ),
    ExpressionTestCase(
        "bare_non_array_field_objectid",
        expression={"$setUnion": "$val"},
        doc={"val": ObjectId("507f1f77bcf86cd799439011")},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject a bare field reference resolving to an ObjectId",
    ),
    ExpressionTestCase(
        "bare_non_array_field_datetime",
        expression={"$setUnion": "$val"},
        doc={"val": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject a bare field reference resolving to a datetime",
    ),
    ExpressionTestCase(
        "bare_non_array_field_timestamp",
        expression={"$setUnion": "$val"},
        doc={"val": Timestamp(1, 1)},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject a bare field reference resolving to a Timestamp",
    ),
    ExpressionTestCase(
        "bare_non_array_field_binary",
        expression={"$setUnion": "$val"},
        doc={"val": Binary(b"\x01")},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject a bare field reference resolving to a Binary",
    ),
    ExpressionTestCase(
        "bare_non_array_field_regex",
        expression={"$setUnion": "$val"},
        doc={"val": Regex("abc", "i")},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject a bare field reference resolving to a Regex",
    ),
    ExpressionTestCase(
        "bare_non_array_field_code",
        expression={"$setUnion": "$val"},
        doc={"val": Code("f()")},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject a bare field reference resolving to a Code",
    ),
    ExpressionTestCase(
        "bare_non_array_field_code_with_scope",
        expression={"$setUnion": "$val"},
        doc={"val": Code("f()", {})},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject a bare field reference resolving to a CodeWithScope",
    ),
    ExpressionTestCase(
        "bare_non_array_field_minkey",
        expression={"$setUnion": "$val"},
        doc={"val": MinKey()},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject a bare field reference resolving to a MinKey",
    ),
    ExpressionTestCase(
        "bare_non_array_field_maxkey",
        expression={"$setUnion": "$val"},
        doc={"val": MaxKey()},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject a bare field reference resolving to a MaxKey",
    ),
]

SETUNION_TYPE_VALIDATION_TESTS_ALL = SETUNION_TYPE_STRICTNESS_TESTS + SETUNION_BARE_VALUE_TESTS


@pytest.mark.parametrize("test_case", pytest_params(SETUNION_TYPE_VALIDATION_TESTS_ALL))
def test_setunion_type_validation(collection, test_case: ExpressionTestCase):
    """Test $setUnion type validation cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc or {})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        ignore_order=True,
    )
