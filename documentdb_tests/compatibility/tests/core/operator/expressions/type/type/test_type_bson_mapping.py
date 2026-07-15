"""$type BSON type mapping tests.

Tests that $type returns the correct type-name string for each BSON type,
including null/missing, core types, array-literal unwrapping, object
expressions, system variables, and large inputs.
"""

from __future__ import annotations

from datetime import datetime, timezone

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

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.lazy_payload import lazy
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DOUBLE_ONE_AND_HALF,
    MISSING,
    REGEX_PATTERN_LIMIT_BYTES,
    STRING_SIZE_LIMIT_BYTES,
)

# Property [Null and Missing Identification]: $type returns "null" for null
# values and "missing" for missing values, rather than propagating null.
TYPE_NULL_MISSING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_literal",
        expression={"$type": None},
        expected="null",
        msg="$type should return 'null' for a null literal",
    ),
    ExpressionTestCase(
        "missing_field",
        expression={"$type": MISSING},
        expected="missing",
        msg="$type should return 'missing' for a reference to a missing field",
    ),
]

# Property [Core BSON Type Mapping]: each BSON type produces a specific,
# distinct type name string.
TYPE_CORE_BSON_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "core_int",
        expression={"$type": 42},
        expected="int",
        msg="$type should return 'int' for an int32 value",
    ),
    ExpressionTestCase(
        "core_long",
        expression={"$type": Int64(42)},
        expected="long",
        msg="$type should return 'long' for an int64 value",
    ),
    ExpressionTestCase(
        "core_double",
        expression={"$type": DOUBLE_ONE_AND_HALF},
        expected="double",
        msg="$type should return 'double' for a double value",
    ),
    ExpressionTestCase(
        "core_decimal",
        expression={"$type": Decimal128("16")},
        expected="decimal",
        msg="$type should return 'decimal' for a Decimal128 value",
    ),
    ExpressionTestCase(
        "core_string",
        expression={"$type": "hello"},
        expected="string",
        msg="$type should return 'string' for a string value",
    ),
    ExpressionTestCase(
        "core_object",
        expression={"$type": {"a": 1}},
        expected="object",
        msg="$type should return 'object' for an object value",
    ),
    ExpressionTestCase(
        "core_array",
        expression={"$type": {"$literal": [1, 2, 3]}},
        expected="array",
        msg="$type should return 'array' for an array value",
    ),
    ExpressionTestCase(
        "core_bindata",
        expression={"$type": Binary(b"hello")},
        expected="binData",
        msg="$type should return 'binData' for a Binary value",
    ),
    ExpressionTestCase(
        "core_objectid",
        expression={"$type": ObjectId("507f1f77bcf86cd799439011")},
        expected="objectId",
        msg="$type should return 'objectId' for an ObjectId value",
    ),
    ExpressionTestCase(
        "core_bool_true",
        expression={"$type": True},
        expected="bool",
        msg="$type should return 'bool' for true",
    ),
    ExpressionTestCase(
        "core_bool_false",
        expression={"$type": False},
        expected="bool",
        msg="$type should return 'bool' for false",
    ),
    ExpressionTestCase(
        "core_date",
        expression={"$type": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        expected="date",
        msg="$type should return 'date' for a datetime value",
    ),
    ExpressionTestCase(
        "core_regex",
        expression={"$type": Regex("abc", "i")},
        expected="regex",
        msg="$type should return 'regex' for a Regex value",
    ),
    ExpressionTestCase(
        "core_javascript",
        expression={"$type": Code("function(){}")},
        expected="javascript",
        msg="$type should return 'javascript' for a Code value",
    ),
    ExpressionTestCase(
        "core_timestamp",
        expression={"$type": Timestamp(1, 1)},
        expected="timestamp",
        msg="$type should return 'timestamp' for a Timestamp value",
    ),
    ExpressionTestCase(
        "core_minkey",
        expression={"$type": MinKey()},
        expected="minKey",
        msg="$type should return 'minKey' for a MinKey value",
    ),
    ExpressionTestCase(
        "core_maxkey",
        expression={"$type": MaxKey()},
        expected="maxKey",
        msg="$type should return 'maxKey' for a MaxKey value",
    ),
]

# Property [Array Literal Unwrapping]: a literal single-element array is
# unwrapped by the parser, while $literal prevents unwrapping.
TYPE_ARRAY_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "array_single_element_literal_unwrap",
        expression={"$type": ["hello"]},
        expected="string",
        msg="$type should unwrap a literal single-element array and return the inner value's type",
    ),
    ExpressionTestCase(
        "array_literal_single_element_no_unwrap",
        expression={"$type": {"$literal": ["hello"]}},
        expected="array",
        msg="$type should return 'array' when $literal prevents single-element array unwrapping",
    ),
]

# Property [Object Expression Handling]: plain objects passed via $literal
# return "object" regardless of key names or count.
TYPE_OBJECT_EXPRESSION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "object_empty",
        expression={"$type": {"$literal": {}}},
        expected="object",
        msg="$type should return 'object' for an empty object",
    ),
    ExpressionTestCase(
        "object_non_empty",
        expression={"$type": {"$literal": {"key": 1}}},
        expected="object",
        msg="$type should return 'object' for a non-empty object",
    ),
]

# Property [System Variables]: system variables return the BSON type of their
# resolved value.
TYPE_SYSTEM_VARIABLE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "sysvar_root",
        expression={"$type": "$$ROOT"},
        expected="object",
        msg="$type should return 'object' for $$ROOT",
    ),
    ExpressionTestCase(
        "sysvar_current",
        expression={"$type": "$$CURRENT"},
        expected="object",
        msg="$type should return 'object' for $$CURRENT",
    ),
    ExpressionTestCase(
        "sysvar_now",
        expression={"$type": "$$NOW"},
        expected="date",
        msg="$type should return 'date' for $$NOW",
    ),
    ExpressionTestCase(
        "sysvar_remove",
        expression={"$type": "$$REMOVE"},
        expected="missing",
        msg="$type should return 'missing' for $$REMOVE",
    ),
]

# Property [Large Inputs]: $type returns the correct type name for large
# values of each BSON type.
TYPE_LARGE_INPUT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "large_string",
        expression=lazy(lambda: {"$type": "a" * (STRING_SIZE_LIMIT_BYTES - 1)}),
        expected="string",
        msg="$type should return 'string' for a string at the size limit",
    ),
    ExpressionTestCase(
        "large_binary",
        expression=lazy(lambda: {"$type": Binary(b"\x00" * (STRING_SIZE_LIMIT_BYTES - 1))}),
        expected="binData",
        msg="$type should return 'binData' for binary data at the size limit",
    ),
    ExpressionTestCase(
        "large_regex",
        expression={"$type": Regex("a" * REGEX_PATTERN_LIMIT_BYTES, "i")},
        expected="regex",
        msg="$type should return 'regex' for a regex pattern at the size limit",
    ),
    ExpressionTestCase(
        "large_array",
        expression={"$type": {"$literal": list(range(10_000))}},
        expected="array",
        msg="$type should return 'array' for a large array",
    ),
    ExpressionTestCase(
        "large_object",
        expression=lazy(lambda: {"$type": {"$literal": {f"k{i}": i for i in range(10_000)}}}),
        expected="object",
        msg="$type should return 'object' for a large object",
    ),
]

TYPE_BSON_MAPPING_TESTS = (
    TYPE_NULL_MISSING_TESTS
    + TYPE_CORE_BSON_TESTS
    + TYPE_ARRAY_LITERAL_TESTS
    + TYPE_OBJECT_EXPRESSION_TESTS
    + TYPE_SYSTEM_VARIABLE_TESTS
    + TYPE_LARGE_INPUT_TESTS
)


@pytest.mark.parametrize("test", pytest_params(TYPE_BSON_MAPPING_TESTS))
def test_type_bson_mapping(collection, test: ExpressionTestCase):
    """$type returns the correct type name for each BSON type."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
