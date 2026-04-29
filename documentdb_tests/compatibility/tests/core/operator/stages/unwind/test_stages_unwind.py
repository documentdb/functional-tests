"""Tests for $unwind stage."""

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
from documentdb_tests.framework.assertions import assertResult, assertSuccess
from documentdb_tests.framework.error_codes import (
    EXPRESSION_FIELD_PATH_NULL_BYTE_ERROR,
    FIELD_PATH_DOLLAR_PREFIX_ERROR,
    FIELD_PATH_EMPTY_COMPONENT_ERROR,
    FIELD_PATH_EMPTY_ERROR,
    FIELD_PATH_NULL_BYTE_ERROR,
    FIELD_PATH_TRAILING_DOT_ERROR,
    OVERFLOW_ERROR,
    UNWIND_INCLUDE_ARRAY_INDEX_DOLLAR_PREFIX_ERROR,
    UNWIND_INCLUDE_ARRAY_INDEX_TYPE_ERROR,
    UNWIND_MISSING_PATH_ERROR,
    UNWIND_PATH_NO_DOLLAR_ERROR,
    UNWIND_PATH_TYPE_ERROR,
    UNWIND_PRESERVE_NULL_TYPE_ERROR,
    UNWIND_SPEC_TYPE_ERROR,
    UNWIND_UNRECOGNIZED_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DOUBLE_ZERO, INT64_ZERO

# Property [Null and Missing Dropped by Default]: when preserveNullAndEmptyArrays
# is false or omitted, documents whose path value is null, missing, or an empty
# array are dropped from the output.
UNWIND_NULL_MISSING_DROPPED_TESTS: list[StageTestCase] = [
    StageTestCase(
        "dropped_null_document_form",
        docs=[{"_id": 1, "a": None, "x": 10}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[],
        msg="$unwind should drop document when path value is null (document form)",
    ),
    StageTestCase(
        "dropped_null_preserve_false",
        docs=[{"_id": 1, "a": None, "x": 10}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": False}}],
        expected=[],
        msg="$unwind should drop document when path value is null (preserve=false)",
    ),
    StageTestCase(
        "dropped_missing_document_form",
        docs=[{"_id": 1, "x": 10}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[],
        msg="$unwind should drop document when path field is missing (document form)",
    ),
    StageTestCase(
        "dropped_missing_preserve_false",
        docs=[{"_id": 1, "x": 10}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": False}}],
        expected=[],
        msg="$unwind should drop document when path field is missing (preserve=false)",
    ),
    StageTestCase(
        "dropped_empty_array_document_form",
        docs=[{"_id": 1, "a": [], "x": 10}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[],
        msg="$unwind should drop document when path value is empty array (document form)",
    ),
    StageTestCase(
        "dropped_empty_array_preserve_false",
        docs=[{"_id": 1, "a": [], "x": 10}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": False}}],
        expected=[],
        msg="$unwind should drop document when path is empty array (preserve=false)",
    ),
]

# Property [Null and Missing Preserved]: when preserveNullAndEmptyArrays is
# true, documents whose path value is null are emitted with the field set to
# null, and documents whose path field is missing or an empty array are emitted
# with the field omitted.
UNWIND_NULL_MISSING_PRESERVED_TESTS: list[StageTestCase] = [
    StageTestCase(
        "preserved_null",
        docs=[{"_id": 1, "a": None, "x": 10}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": True}}],
        expected=[{"_id": 1, "a": None, "x": 10}],
        msg=(
            "$unwind should emit document with field set to null when path"
            " value is null and preserve=true"
        ),
    ),
    StageTestCase(
        "preserved_missing",
        docs=[{"_id": 1, "x": 10}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": True}}],
        expected=[{"_id": 1, "x": 10}],
        msg=(
            "$unwind should emit document with field omitted when path field"
            " is missing and preserve=true"
        ),
    ),
    StageTestCase(
        "preserved_empty_array",
        docs=[{"_id": 1, "a": [], "x": 10}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": True}}],
        expected=[{"_id": 1, "x": 10}],
        msg=(
            "$unwind should emit document with field omitted when path value"
            " is empty array and preserve=true"
        ),
    ),
]

# Property [Core Unwinding]: each element of the array at the path produces a
# separate output document with the array field replaced by that element,
# retaining all other fields, in original array order, without deduplication.
UNWIND_CORE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "core_basic_array",
        docs=[{"_id": 1, "a": [1, 2, 3]}],
        pipeline=[{"$unwind": "$a"}],
        expected=[
            {"_id": 1, "a": 1},
            {"_id": 1, "a": 2},
            {"_id": 1, "a": 3},
        ],
        msg="$unwind should produce one document per array element",
    ),
    StageTestCase(
        "core_retains_other_fields",
        docs=[{"_id": 1, "a": [10, 20], "x": "keep", "y": 99}],
        pipeline=[{"$unwind": "$a"}],
        expected=[
            {"_id": 1, "a": 10, "x": "keep", "y": 99},
            {"_id": 1, "a": 20, "x": "keep", "y": 99},
        ],
        msg="$unwind should retain all other fields from the input document",
    ),
    StageTestCase(
        "core_preserves_array_order",
        docs=[{"_id": 1, "a": ["c", "a", "b"]}],
        pipeline=[{"$unwind": "$a"}],
        expected=[
            {"_id": 1, "a": "c"},
            {"_id": 1, "a": "a"},
            {"_id": 1, "a": "b"},
        ],
        msg="$unwind should emit elements in their original array order",
    ),
    StageTestCase(
        "core_duplicates_not_deduplicated",
        docs=[{"_id": 1, "a": [5, 5, 5]}],
        pipeline=[{"$unwind": "$a"}],
        expected=[
            {"_id": 1, "a": 5},
            {"_id": 1, "a": 5},
            {"_id": 1, "a": 5},
        ],
        msg="$unwind should produce one document per duplicate value without deduplication",
    ),
    StageTestCase(
        "core_mixed_type_array",
        docs=[{"_id": 1, "a": [1, "two", True, None, 3.5]}],
        pipeline=[{"$unwind": "$a"}],
        expected=[
            {"_id": 1, "a": 1},
            {"_id": 1, "a": "two"},
            {"_id": 1, "a": True},
            {"_id": 1, "a": None},
            {"_id": 1, "a": 3.5},
        ],
        msg="$unwind should preserve each element's type in a mixed-type array",
    ),
]

# Property [BSON Type Preservation]: all BSON types representable by pymongo
# are preserved exactly when unwound from array elements.
UNWIND_BSON_TYPE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "bson_bool",
        docs=[{"_id": 1, "a": [True, False]}],
        pipeline=[{"$unwind": "$a"}],
        expected=[{"_id": 1, "a": True}, {"_id": 1, "a": False}],
        msg="$unwind should preserve bool elements",
    ),
    StageTestCase(
        "bson_int32",
        docs=[{"_id": 1, "a": [1, 2]}],
        pipeline=[{"$unwind": "$a"}],
        expected=[{"_id": 1, "a": 1}, {"_id": 1, "a": 2}],
        msg="$unwind should preserve int32 elements",
    ),
    StageTestCase(
        "bson_int64",
        docs=[{"_id": 1, "a": [Int64(100), Int64(200)]}],
        pipeline=[{"$unwind": "$a"}],
        expected=[{"_id": 1, "a": Int64(100)}, {"_id": 1, "a": Int64(200)}],
        msg="$unwind should preserve Int64 elements",
    ),
    StageTestCase(
        "bson_double",
        docs=[{"_id": 1, "a": [1.5, 2.5]}],
        pipeline=[{"$unwind": "$a"}],
        expected=[{"_id": 1, "a": 1.5}, {"_id": 1, "a": 2.5}],
        msg="$unwind should preserve double elements",
    ),
    StageTestCase(
        "bson_decimal128",
        docs=[{"_id": 1, "a": [Decimal128("1.1"), Decimal128("2.2")]}],
        pipeline=[{"$unwind": "$a"}],
        expected=[
            {"_id": 1, "a": Decimal128("1.1")},
            {"_id": 1, "a": Decimal128("2.2")},
        ],
        msg="$unwind should preserve Decimal128 elements",
    ),
    StageTestCase(
        "bson_string",
        docs=[{"_id": 1, "a": ["hello", "world"]}],
        pipeline=[{"$unwind": "$a"}],
        expected=[{"_id": 1, "a": "hello"}, {"_id": 1, "a": "world"}],
        msg="$unwind should preserve string elements",
    ),
    StageTestCase(
        "bson_object",
        docs=[{"_id": 1, "a": [{"x": 1}, {"y": 2}]}],
        pipeline=[{"$unwind": "$a"}],
        expected=[{"_id": 1, "a": {"x": 1}}, {"_id": 1, "a": {"y": 2}}],
        msg="$unwind should preserve embedded document elements",
    ),
    StageTestCase(
        "bson_objectid",
        docs=[
            {
                "_id": 1,
                "a": [
                    ObjectId("000000000000000000000001"),
                    ObjectId("000000000000000000000002"),
                ],
            }
        ],
        pipeline=[{"$unwind": "$a"}],
        expected=[
            {"_id": 1, "a": ObjectId("000000000000000000000001")},
            {"_id": 1, "a": ObjectId("000000000000000000000002")},
        ],
        msg="$unwind should preserve ObjectId elements",
    ),
    StageTestCase(
        "bson_datetime",
        docs=[
            {
                "_id": 1,
                "a": [
                    datetime(2024, 1, 1),
                    datetime(2025, 6, 15),
                ],
            }
        ],
        pipeline=[{"$unwind": "$a"}],
        expected=[
            {"_id": 1, "a": datetime(2024, 1, 1)},
            {"_id": 1, "a": datetime(2025, 6, 15)},
        ],
        msg="$unwind should preserve datetime elements",
    ),
    StageTestCase(
        "bson_timestamp",
        docs=[{"_id": 1, "a": [Timestamp(1, 1), Timestamp(2, 2)]}],
        pipeline=[{"$unwind": "$a"}],
        expected=[
            {"_id": 1, "a": Timestamp(1, 1)},
            {"_id": 1, "a": Timestamp(2, 2)},
        ],
        msg="$unwind should preserve Timestamp elements",
    ),
    StageTestCase(
        "bson_binary",
        docs=[{"_id": 1, "a": [Binary(b"\x01"), Binary(b"\x02")]}],
        pipeline=[{"$unwind": "$a"}],
        expected=[
            {"_id": 1, "a": b"\x01"},
            {"_id": 1, "a": b"\x02"},
        ],
        msg="$unwind should preserve Binary elements",
    ),
    StageTestCase(
        "bson_binary_uuid",
        docs=[
            {
                "_id": 1,
                "a": [
                    Binary.from_uuid(UUID("12345678-1234-1234-1234-123456789abc")),
                    Binary.from_uuid(UUID("abcdefab-cdef-abcd-efab-cdefabcdefab")),
                ],
            }
        ],
        pipeline=[{"$unwind": "$a"}],
        expected=[
            {
                "_id": 1,
                "a": Binary.from_uuid(UUID("12345678-1234-1234-1234-123456789abc")),
            },
            {
                "_id": 1,
                "a": Binary.from_uuid(UUID("abcdefab-cdef-abcd-efab-cdefabcdefab")),
            },
        ],
        msg="$unwind should preserve Binary UUID elements",
    ),
    StageTestCase(
        "bson_regex",
        docs=[{"_id": 1, "a": [Regex("^a", "i"), Regex("^b")]}],
        pipeline=[{"$unwind": "$a"}],
        expected=[
            {"_id": 1, "a": Regex("^a", "i")},
            {"_id": 1, "a": Regex("^b")},
        ],
        msg="$unwind should preserve Regex elements",
    ),
    StageTestCase(
        "bson_code",
        docs=[{"_id": 1, "a": [Code("x"), Code("y")]}],
        pipeline=[{"$unwind": "$a"}],
        expected=[{"_id": 1, "a": Code("x")}, {"_id": 1, "a": Code("y")}],
        msg="$unwind should preserve Code elements",
    ),
    StageTestCase(
        "bson_code_with_scope",
        docs=[{"_id": 1, "a": [Code("x", {}), Code("y", {"z": 1})]}],
        pipeline=[{"$unwind": "$a"}],
        expected=[
            {"_id": 1, "a": Code("x", {})},
            {"_id": 1, "a": Code("y", {"z": 1})},
        ],
        msg="$unwind should preserve Code with scope elements",
    ),
    StageTestCase(
        "bson_minkey",
        docs=[{"_id": 1, "a": [MinKey(), 1]}],
        pipeline=[{"$unwind": "$a"}],
        expected=[{"_id": 1, "a": MinKey()}, {"_id": 1, "a": 1}],
        msg="$unwind should preserve MinKey elements",
    ),
    StageTestCase(
        "bson_maxkey",
        docs=[{"_id": 1, "a": [MaxKey(), 1]}],
        pipeline=[{"$unwind": "$a"}],
        expected=[{"_id": 1, "a": MaxKey()}, {"_id": 1, "a": 1}],
        msg="$unwind should preserve MaxKey elements",
    ),
    StageTestCase(
        "bson_null_element",
        docs=[{"_id": 1, "a": [None, 1]}],
        pipeline=[{"$unwind": "$a"}],
        expected=[{"_id": 1, "a": None}, {"_id": 1, "a": 1}],
        msg="$unwind should preserve null elements within an array",
    ),
]

# Property [Non-Array Scalar Passthrough]: when the value at the path is a
# non-array, non-null, non-missing scalar, $unwind outputs a single document
# with the value as-is, regardless of the preserveNullAndEmptyArrays setting.
UNWIND_SCALAR_PASSTHROUGH_TESTS: list[StageTestCase] = [
    StageTestCase(
        "scalar_bool",
        docs=[{"_id": 1, "a": True}],
        pipeline=[{"$unwind": "$a"}],
        expected=[{"_id": 1, "a": True}],
        msg="$unwind should pass through bool scalar as-is",
    ),
    StageTestCase(
        "scalar_int32",
        docs=[{"_id": 1, "a": 42}],
        pipeline=[{"$unwind": "$a"}],
        expected=[{"_id": 1, "a": 42}],
        msg="$unwind should pass through int32 scalar as-is",
    ),
    StageTestCase(
        "scalar_int64",
        docs=[{"_id": 1, "a": Int64(999)}],
        pipeline=[{"$unwind": "$a"}],
        expected=[{"_id": 1, "a": Int64(999)}],
        msg="$unwind should pass through Int64 scalar as-is",
    ),
    StageTestCase(
        "scalar_double",
        docs=[{"_id": 1, "a": 3.14}],
        pipeline=[{"$unwind": "$a"}],
        expected=[{"_id": 1, "a": 3.14}],
        msg="$unwind should pass through double scalar as-is",
    ),
    StageTestCase(
        "scalar_decimal128",
        docs=[{"_id": 1, "a": Decimal128("9.99")}],
        pipeline=[{"$unwind": "$a"}],
        expected=[{"_id": 1, "a": Decimal128("9.99")}],
        msg="$unwind should pass through Decimal128 scalar as-is",
    ),
    StageTestCase(
        "scalar_string",
        docs=[{"_id": 1, "a": "hello"}],
        pipeline=[{"$unwind": "$a"}],
        expected=[{"_id": 1, "a": "hello"}],
        msg="$unwind should pass through string scalar as-is",
    ),
    StageTestCase(
        "scalar_object",
        docs=[{"_id": 1, "a": {"x": 1}}],
        pipeline=[{"$unwind": "$a"}],
        expected=[{"_id": 1, "a": {"x": 1}}],
        msg="$unwind should pass through embedded document scalar as-is",
    ),
    StageTestCase(
        "scalar_objectid",
        docs=[{"_id": 1, "a": ObjectId("000000000000000000000001")}],
        pipeline=[{"$unwind": "$a"}],
        expected=[{"_id": 1, "a": ObjectId("000000000000000000000001")}],
        msg="$unwind should pass through ObjectId scalar as-is",
    ),
    StageTestCase(
        "scalar_datetime",
        docs=[{"_id": 1, "a": datetime(2024, 1, 1)}],
        pipeline=[{"$unwind": "$a"}],
        expected=[{"_id": 1, "a": datetime(2024, 1, 1)}],
        msg="$unwind should pass through datetime scalar as-is",
    ),
    StageTestCase(
        "scalar_timestamp",
        docs=[{"_id": 1, "a": Timestamp(1, 1)}],
        pipeline=[{"$unwind": "$a"}],
        expected=[{"_id": 1, "a": Timestamp(1, 1)}],
        msg="$unwind should pass through Timestamp scalar as-is",
    ),
    StageTestCase(
        "scalar_binary",
        docs=[{"_id": 1, "a": Binary(b"\x01\x02")}],
        pipeline=[{"$unwind": "$a"}],
        expected=[{"_id": 1, "a": b"\x01\x02"}],
        msg="$unwind should pass through Binary scalar as-is",
    ),
    StageTestCase(
        "scalar_binary_uuid",
        docs=[
            {
                "_id": 1,
                "a": Binary.from_uuid(UUID("12345678-1234-1234-1234-123456789abc")),
            }
        ],
        pipeline=[{"$unwind": "$a"}],
        expected=[
            {
                "_id": 1,
                "a": Binary.from_uuid(UUID("12345678-1234-1234-1234-123456789abc")),
            }
        ],
        msg="$unwind should pass through Binary UUID scalar as-is",
    ),
    StageTestCase(
        "scalar_regex",
        docs=[{"_id": 1, "a": Regex("^a", "i")}],
        pipeline=[{"$unwind": "$a"}],
        expected=[{"_id": 1, "a": Regex("^a", "i")}],
        msg="$unwind should pass through Regex scalar as-is",
    ),
    StageTestCase(
        "scalar_code",
        docs=[{"_id": 1, "a": Code("x")}],
        pipeline=[{"$unwind": "$a"}],
        expected=[{"_id": 1, "a": Code("x")}],
        msg="$unwind should pass through Code scalar as-is",
    ),
    StageTestCase(
        "scalar_code_with_scope",
        docs=[{"_id": 1, "a": Code("x", {"z": 1})}],
        pipeline=[{"$unwind": "$a"}],
        expected=[{"_id": 1, "a": Code("x", {"z": 1})}],
        msg="$unwind should pass through Code with scope scalar as-is",
    ),
    StageTestCase(
        "scalar_minkey",
        docs=[{"_id": 1, "a": MinKey()}],
        pipeline=[{"$unwind": "$a"}],
        expected=[{"_id": 1, "a": MinKey()}],
        msg="$unwind should pass through MinKey scalar as-is",
    ),
    StageTestCase(
        "scalar_maxkey",
        docs=[{"_id": 1, "a": MaxKey()}],
        pipeline=[{"$unwind": "$a"}],
        expected=[{"_id": 1, "a": MaxKey()}],
        msg="$unwind should pass through MaxKey scalar as-is",
    ),
    StageTestCase(
        "scalar_preserve_true_does_not_affect",
        docs=[{"_id": 1, "a": 42}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": True}}],
        expected=[{"_id": 1, "a": 42}],
        msg="$unwind should pass through scalar as-is when preserveNullAndEmptyArrays is true",
    ),
    StageTestCase(
        "scalar_preserve_false_does_not_affect",
        docs=[{"_id": 1, "a": 42}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": False}}],
        expected=[{"_id": 1, "a": 42}],
        msg="$unwind should pass through scalar as-is when preserveNullAndEmptyArrays is false",
    ),
]

# Property [Nested Arrays]: $unwind peels exactly one level of array nesting
# per invocation - inner arrays are preserved as elements, and successive
# $unwind stages on the same field flatten additional nesting levels.
UNWIND_NESTED_ARRAYS_TESTS: list[StageTestCase] = [
    StageTestCase(
        "nested_array_of_arrays",
        docs=[{"_id": 1, "a": [[1, 2], [3]]}],
        pipeline=[{"$unwind": "$a"}],
        expected=[
            {"_id": 1, "a": [1, 2]},
            {"_id": 1, "a": [3]},
        ],
        msg="$unwind should produce one document per inner array",
    ),
    StageTestCase(
        "nested_deeply_nested",
        docs=[{"_id": 1, "a": [[[1]], [[2, 3]]]}],
        pipeline=[{"$unwind": "$a"}],
        expected=[
            {"_id": 1, "a": [[1]]},
            {"_id": 1, "a": [[2, 3]]},
        ],
        msg="$unwind should peel only one level, preserving deeper nesting",
    ),
    StageTestCase(
        "nested_mixed_scalars_and_arrays",
        docs=[{"_id": 1, "a": [1, [2, 3], 4]}],
        pipeline=[{"$unwind": "$a"}],
        expected=[
            {"_id": 1, "a": 1},
            {"_id": 1, "a": [2, 3]},
            {"_id": 1, "a": 4},
        ],
        msg="$unwind should preserve inner arrays alongside scalar elements",
    ),
    StageTestCase(
        "nested_successive_unwind_flattens",
        docs=[{"_id": 1, "a": [[10, 20], [30]]}],
        pipeline=[{"$unwind": "$a"}, {"$unwind": "$a"}],
        expected=[
            {"_id": 1, "a": 10},
            {"_id": 1, "a": 20},
            {"_id": 1, "a": 30},
        ],
        msg="Successive $unwind stages on the same field should flatten additional nesting",
    ),
]

# Property [Dotted Path Traversal]: a dotted path traverses into nested
# documents to reach the array leaf and unwinds it normally, but does not
# traverse into array elements; numeric path components are treated as field
# names, not array indices; and when an intermediate component is a scalar,
# null, or missing, the path is treated as missing.
UNWIND_DOTTED_PATH_TESTS: list[StageTestCase] = [
    StageTestCase(
        "dotted_basic_nested_doc",
        docs=[{"_id": 1, "a": {"b": [1, 2, 3]}}],
        pipeline=[{"$unwind": "$a.b"}],
        expected=[
            {"_id": 1, "a": {"b": 1}},
            {"_id": 1, "a": {"b": 2}},
            {"_id": 1, "a": {"b": 3}},
        ],
        msg="$unwind with dotted path should traverse nested doc and unwind the leaf array",
    ),
    StageTestCase(
        "dotted_deep_nested_doc",
        docs=[{"_id": 1, "a": {"b": {"c": [10, 20]}}}],
        pipeline=[{"$unwind": "$a.b.c"}],
        expected=[
            {"_id": 1, "a": {"b": {"c": 10}}},
            {"_id": 1, "a": {"b": {"c": 20}}},
        ],
        msg="$unwind with deep dotted path should traverse multiple levels",
    ),
    StageTestCase(
        "dotted_preserves_sibling_fields",
        docs=[{"_id": 1, "a": {"b": [1, 2], "x": 99}}],
        pipeline=[{"$unwind": "$a.b"}],
        expected=[
            {"_id": 1, "a": {"b": 1, "x": 99}},
            {"_id": 1, "a": {"b": 2, "x": 99}},
        ],
        msg="$unwind with dotted path should preserve sibling fields in nested doc",
    ),
    StageTestCase(
        "dotted_intermediate_array_no_preserve",
        docs=[{"_id": 1, "a": [{"b": 1}, {"b": 2}]}],
        pipeline=[{"$unwind": "$a.b"}],
        expected=[],
        msg=(
            "$unwind with dotted path should not traverse into array elements"
            " and should drop the document when preserve is false"
        ),
    ),
    StageTestCase(
        "dotted_intermediate_array_preserve_true",
        docs=[{"_id": 1, "a": [{"b": 1}, {"b": 2}]}],
        pipeline=[{"$unwind": {"path": "$a.b", "preserveNullAndEmptyArrays": True}}],
        expected=[{"_id": 1, "a": [{"b": 1}, {"b": 2}]}],
        msg=(
            "$unwind with dotted path should preserve original value when"
            " intermediate is an array and preserve=true"
        ),
    ),
    StageTestCase(
        "dotted_numeric_component_as_field_name",
        docs=[{"_id": 1, "a": {"0": [10, 20]}}],
        pipeline=[{"$unwind": "$a.0"}],
        expected=[
            {"_id": 1, "a": {"0": 10}},
            {"_id": 1, "a": {"0": 20}},
        ],
        msg="$unwind should treat numeric path components as field names, not array indices",
    ),
    StageTestCase(
        "dotted_numeric_component_array_parent_no_preserve",
        docs=[{"_id": 1, "a": [[10, 20], [30]]}],
        pipeline=[{"$unwind": "$a.0"}],
        expected=[],
        msg=(
            "$unwind with numeric path component should not index into array"
            " and should drop when preserve is false"
        ),
    ),
    StageTestCase(
        "dotted_numeric_component_array_parent_preserve_true",
        docs=[{"_id": 1, "a": [[10, 20], [30]]}],
        pipeline=[{"$unwind": {"path": "$a.0", "preserveNullAndEmptyArrays": True}}],
        expected=[{"_id": 1, "a": [[10, 20], [30]]}],
        msg=(
            "$unwind with numeric path component should preserve original"
            " value when parent is array and preserve=true"
        ),
    ),
    StageTestCase(
        "dotted_empty_array_leaf_preserve_true",
        docs=[{"_id": 1, "a": {"b": []}}],
        pipeline=[{"$unwind": {"path": "$a.b", "preserveNullAndEmptyArrays": True}}],
        expected=[{"_id": 1, "a": {}}],
        msg=(
            "$unwind with dotted path and preserve=true should remove the"
            " leaf field from the nested object when the leaf is an empty array"
        ),
    ),
    StageTestCase(
        "dotted_intermediate_scalar_no_preserve",
        docs=[{"_id": 1, "a": 42}],
        pipeline=[{"$unwind": "$a.b"}],
        expected=[],
        msg="$unwind with dotted path should treat path as missing when intermediate is a scalar",
    ),
    StageTestCase(
        "dotted_intermediate_scalar_preserve_true",
        docs=[{"_id": 1, "a": 42}],
        pipeline=[{"$unwind": {"path": "$a.b", "preserveNullAndEmptyArrays": True}}],
        expected=[{"_id": 1, "a": 42}],
        msg=(
            "$unwind with dotted path should preserve document when"
            " intermediate is a scalar and preserve=true"
        ),
    ),
    StageTestCase(
        "dotted_intermediate_null_no_preserve",
        docs=[{"_id": 1, "a": None}],
        pipeline=[{"$unwind": "$a.b"}],
        expected=[],
        msg="$unwind with dotted path should treat path as missing when intermediate is null",
    ),
    StageTestCase(
        "dotted_intermediate_null_preserve_true",
        docs=[{"_id": 1, "a": None}],
        pipeline=[{"$unwind": {"path": "$a.b", "preserveNullAndEmptyArrays": True}}],
        expected=[{"_id": 1, "a": None}],
        msg=(
            "$unwind with dotted path should preserve document when"
            " intermediate is null and preserve=true"
        ),
    ),
    StageTestCase(
        "dotted_intermediate_missing_no_preserve",
        docs=[{"_id": 1, "x": 10}],
        pipeline=[{"$unwind": "$a.b"}],
        expected=[],
        msg=(
            "$unwind with dotted path should treat path as missing when"
            " intermediate field is missing"
        ),
    ),
    StageTestCase(
        "dotted_intermediate_missing_preserve_true",
        docs=[{"_id": 1, "x": 10}],
        pipeline=[{"$unwind": {"path": "$a.b", "preserveNullAndEmptyArrays": True}}],
        expected=[{"_id": 1, "x": 10}],
        msg=(
            "$unwind with dotted path should preserve document when"
            " intermediate field is missing and preserve=true"
        ),
    ),
    StageTestCase(
        "dotted_null_leaf_preserve_true",
        docs=[{"_id": 1, "a": {"b": None}}],
        pipeline=[{"$unwind": {"path": "$a.b", "preserveNullAndEmptyArrays": True}}],
        expected=[{"_id": 1, "a": {"b": None}}],
        msg=(
            "$unwind with dotted path and preserve=true should keep null"
            " leaf value in the nested object"
        ),
    ),
    StageTestCase(
        "dotted_missing_leaf_preserve_true",
        docs=[{"_id": 1, "a": {"x": 1}}],
        pipeline=[{"$unwind": {"path": "$a.b", "preserveNullAndEmptyArrays": True}}],
        expected=[{"_id": 1, "a": {"x": 1}}],
        msg=(
            "$unwind with dotted path and preserve=true should preserve"
            " document when leaf field is missing from nested object"
        ),
    ),
    StageTestCase(
        "dotted_path_depth_200_succeeds",
        docs=[],
        pipeline=[{"$unwind": {"path": "$" + ".".join(["a"] * 200)}}],
        expected=[],
        msg="$unwind should accept a path with exactly 200 components",
    ),
]

# Property [includeArrayIndex Behavior]: when includeArrayIndex is specified,
# each output document includes a field with the given name containing the
# element's zero-based Int64 index, sequential per input document; non-array
# scalars and preserved documents (null, missing, empty array) receive a null
# index; null elements within an array receive a sequential index; and the
# index field is appended at the end of the document field order.
UNWIND_INCLUDE_ARRAY_INDEX_TESTS: list[StageTestCase] = [
    StageTestCase(
        "index_zero_based_int64",
        docs=[{"_id": 1, "a": [10, 20, 30]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "idx"}}],
        expected=[
            {"_id": 1, "a": 10, "idx": INT64_ZERO},
            {"_id": 1, "a": 20, "idx": Int64(1)},
            {"_id": 1, "a": 30, "idx": Int64(2)},
        ],
        msg="$unwind includeArrayIndex should produce zero-based Int64 indices",
    ),
    StageTestCase(
        "index_resets_per_document",
        docs=[{"_id": 1, "a": [10, 20]}, {"_id": 2, "a": [30]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "idx"}}],
        expected=[
            {"_id": 1, "a": 10, "idx": INT64_ZERO},
            {"_id": 1, "a": 20, "idx": Int64(1)},
            {"_id": 2, "a": 30, "idx": INT64_ZERO},
        ],
        msg="$unwind includeArrayIndex should reset to 0 for each input document",
    ),
    StageTestCase(
        "index_scalar_is_null",
        docs=[{"_id": 1, "a": 42}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "idx"}}],
        expected=[{"_id": 1, "a": 42, "idx": None}],
        msg="$unwind includeArrayIndex should be null for non-array scalar values",
    ),
    StageTestCase(
        "index_preserved_null",
        docs=[{"_id": 1, "a": None}],
        pipeline=[
            {
                "$unwind": {
                    "path": "$a",
                    "includeArrayIndex": "idx",
                    "preserveNullAndEmptyArrays": True,
                }
            }
        ],
        expected=[{"_id": 1, "a": None, "idx": None}],
        msg="$unwind includeArrayIndex should be null for preserved null document",
    ),
    StageTestCase(
        "index_preserved_missing",
        docs=[{"_id": 1, "x": 10}],
        pipeline=[
            {
                "$unwind": {
                    "path": "$a",
                    "includeArrayIndex": "idx",
                    "preserveNullAndEmptyArrays": True,
                }
            }
        ],
        expected=[{"_id": 1, "x": 10, "idx": None}],
        msg="$unwind includeArrayIndex should be null for preserved missing document",
    ),
    StageTestCase(
        "index_preserved_empty_array",
        docs=[{"_id": 1, "a": []}],
        pipeline=[
            {
                "$unwind": {
                    "path": "$a",
                    "includeArrayIndex": "idx",
                    "preserveNullAndEmptyArrays": True,
                }
            }
        ],
        expected=[{"_id": 1, "idx": None}],
        msg="$unwind includeArrayIndex should be null for preserved empty array document",
    ),
    StageTestCase(
        "index_null_element_gets_sequential_index",
        docs=[{"_id": 1, "a": [10, None, 30]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "idx"}}],
        expected=[
            {"_id": 1, "a": 10, "idx": INT64_ZERO},
            {"_id": 1, "a": None, "idx": Int64(1)},
            {"_id": 1, "a": 30, "idx": Int64(2)},
        ],
        msg="$unwind includeArrayIndex should assign sequential index to null elements",
    ),
]

# Property [includeArrayIndex Field Name Collisions]: when includeArrayIndex
# names an existing field (_id, the unwound path, or a dotted path component),
# the index value overwrites the existing field; a dotted index name replaces
# a scalar parent with a nested document containing the index.
UNWIND_INDEX_FIELD_NAME_COLLISION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "index_collision_overwrites_id",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "_id"}}],
        expected=[
            {"_id": INT64_ZERO, "a": 10},
            {"_id": Int64(1), "a": 20},
        ],
        msg="$unwind includeArrayIndex should overwrite _id with the Int64 index",
    ),
    StageTestCase(
        "index_collision_overwrites_unwound_path",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "a"}}],
        expected=[
            {"_id": 1, "a": INT64_ZERO},
            {"_id": 1, "a": Int64(1)},
        ],
        msg="$unwind includeArrayIndex should overwrite the unwound value with the index",
    ),
    StageTestCase(
        "index_collision_dotted_overwrites_nested_field",
        docs=[{"_id": 1, "a": [10, 20], "x": {"y": "old", "z": 99}}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "x.y"}}],
        expected=[
            {"_id": 1, "a": 10, "x": {"y": INT64_ZERO, "z": 99}},
            {"_id": 1, "a": 20, "x": {"y": Int64(1), "z": 99}},
        ],
        msg=(
            "$unwind includeArrayIndex dotted name should overwrite the"
            " nested field while preserving siblings"
        ),
    ),
    StageTestCase(
        "index_collision_dotted_replaces_scalar_parent",
        docs=[{"_id": 1, "a": [10, 20], "x": "scalar"}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "x.y"}}],
        expected=[
            {"_id": 1, "a": 10, "x": {"y": INT64_ZERO}},
            {"_id": 1, "a": 20, "x": {"y": Int64(1)}},
        ],
        msg=(
            "$unwind includeArrayIndex dotted name should replace a scalar"
            " parent with a nested document containing the index"
        ),
    ),
    StageTestCase(
        "index_collision_simple_name_overwrites_dotted_path_parent",
        docs=[{"_id": 1, "a": {"b": [10, 20]}}],
        pipeline=[{"$unwind": {"path": "$a.b", "includeArrayIndex": "a"}}],
        expected=[
            {"_id": 1, "a": INT64_ZERO},
            {"_id": 1, "a": Int64(1)},
        ],
        msg=(
            "$unwind includeArrayIndex simple name matching the parent of"
            " the dotted unwound path should overwrite the entire nested document"
        ),
    ),
]

# Property [Multi-Stage Unwind]: chaining multiple $unwind stages composes
# correctly with independent state tracking, cross-product semantics, and
# preserve interactions.
UNWIND_MULTI_STAGE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "multi_stage_index_resets_per_subarray",
        docs=[{"_id": 1, "a": [[10, 20], [30]]}],
        pipeline=[
            {"$unwind": {"path": "$a", "includeArrayIndex": "i1"}},
            {"$unwind": {"path": "$a", "includeArrayIndex": "i2"}},
        ],
        expected=[
            {"_id": 1, "a": 10, "i1": INT64_ZERO, "i2": INT64_ZERO},
            {"_id": 1, "a": 20, "i1": INT64_ZERO, "i2": Int64(1)},
            {"_id": 1, "a": 30, "i1": Int64(1), "i2": INT64_ZERO},
        ],
        msg=(
            "Second $unwind includeArrayIndex should reset to 0 for each"
            " sub-array produced by the first $unwind"
        ),
    ),
    StageTestCase(
        "multi_stage_cross_product_different_fields",
        docs=[{"_id": 1, "a": [1, 2], "b": ["x", "y"]}],
        pipeline=[{"$unwind": "$a"}, {"$unwind": "$b"}],
        expected=[
            {"_id": 1, "a": 1, "b": "x"},
            {"_id": 1, "a": 1, "b": "y"},
            {"_id": 1, "a": 2, "b": "x"},
            {"_id": 1, "a": 2, "b": "y"},
        ],
        msg=(
            "Two $unwind stages on different array fields should produce"
            " a cross product of elements"
        ),
    ),
    StageTestCase(
        "multi_stage_preserve_first_filter_second",
        docs=[
            {"_id": 1, "a": [1, 2], "b": ["x"]},
            {"_id": 2, "a": [3], "b": None},
            {"_id": 3, "a": [4]},
            {"_id": 4, "a": None, "b": ["z"]},
        ],
        pipeline=[
            {"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": True}},
            {"$unwind": {"path": "$b", "preserveNullAndEmptyArrays": False}},
        ],
        expected=[
            {"_id": 1, "a": 1, "b": "x"},
            {"_id": 1, "a": 2, "b": "x"},
            {"_id": 4, "a": None, "b": "z"},
        ],
        msg=(
            "preserveNullAndEmptyArrays on first $unwind followed by false"
            " on second should filter documents where second path is null or missing"
        ),
    ),
]

# Property [includeArrayIndex Field Name Acceptance]: includeArrayIndex
# accepts arbitrary non-empty, non-dollar-prefixed field names regardless of
# character content, encoding, or length.
UNWIND_INDEX_FIELD_NAME_ACCEPTANCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "index_name_unicode_cjk",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "\u5b57\u6bb5"}}],
        expected=[
            {"_id": 1, "a": 10, "\u5b57\u6bb5": INT64_ZERO},
            {"_id": 1, "a": 20, "\u5b57\u6bb5": Int64(1)},
        ],
        msg="includeArrayIndex should accept CJK Unicode field name",
    ),
    StageTestCase(
        "index_name_emoji",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "\U0001f389"}}],
        expected=[
            {"_id": 1, "a": 10, "\U0001f389": INT64_ZERO},
            {"_id": 1, "a": 20, "\U0001f389": Int64(1)},
        ],
        msg="includeArrayIndex should accept emoji field name",
    ),
    StageTestCase(
        "index_name_space",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "a b"}}],
        expected=[
            {"_id": 1, "a": 10, "a b": INT64_ZERO},
            {"_id": 1, "a": 20, "a b": Int64(1)},
        ],
        msg="includeArrayIndex should accept field name with spaces",
    ),
    StageTestCase(
        "index_name_tab",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "a\tb"}}],
        expected=[
            {"_id": 1, "a": 10, "a\tb": INT64_ZERO},
            {"_id": 1, "a": 20, "a\tb": Int64(1)},
        ],
        msg="includeArrayIndex should accept field name with tab",
    ),
    StageTestCase(
        "index_name_newline",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "a\nb"}}],
        expected=[
            {"_id": 1, "a": 10, "a\nb": INT64_ZERO},
            {"_id": 1, "a": 20, "a\nb": Int64(1)},
        ],
        msg="includeArrayIndex should accept field name with newline",
    ),
    StageTestCase(
        "index_name_nbsp",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "a\u00a0b"}}],
        expected=[
            {"_id": 1, "a": 10, "a\u00a0b": INT64_ZERO},
            {"_id": 1, "a": 20, "a\u00a0b": Int64(1)},
        ],
        msg="includeArrayIndex should accept field name with NBSP",
    ),
    StageTestCase(
        "index_name_zero_width_joiner",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "a\u200db"}}],
        expected=[
            {"_id": 1, "a": 10, "a\u200db": INT64_ZERO},
            {"_id": 1, "a": 20, "a\u200db": Int64(1)},
        ],
        msg="includeArrayIndex should accept field name with zero-width joiner",
    ),
    StageTestCase(
        "index_name_zero_width_space",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "a\u200bb"}}],
        expected=[
            {"_id": 1, "a": 10, "a\u200bb": INT64_ZERO},
            {"_id": 1, "a": 20, "a\u200bb": Int64(1)},
        ],
        msg="includeArrayIndex should accept field name with zero-width space",
    ),
    StageTestCase(
        "index_name_control_char",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "a\x01b"}}],
        expected=[
            {"_id": 1, "a": 10, "a\x01b": INT64_ZERO},
            {"_id": 1, "a": 20, "a\x01b": Int64(1)},
        ],
        msg="includeArrayIndex should accept field name with control character",
    ),
    StageTestCase(
        "index_name_dunder_proto",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "__proto__"}}],
        expected=[
            {"_id": 1, "a": 10, "__proto__": INT64_ZERO},
            {"_id": 1, "a": 20, "__proto__": Int64(1)},
        ],
        msg="includeArrayIndex should accept __proto__ as field name",
    ),
    StageTestCase(
        "index_name_constructor",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "constructor"}}],
        expected=[
            {"_id": 1, "a": 10, "constructor": INT64_ZERO},
            {"_id": 1, "a": 20, "constructor": Int64(1)},
        ],
        msg="includeArrayIndex should accept constructor as field name",
    ),
    StageTestCase(
        "index_name_numeric_string",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "123"}}],
        expected=[
            {"_id": 1, "a": 10, "123": INT64_ZERO},
            {"_id": 1, "a": 20, "123": Int64(1)},
        ],
        msg="includeArrayIndex should accept numeric-looking string as field name",
    ),
    StageTestCase(
        "index_name_non_leading_dollar",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "a$b"}}],
        expected=[
            {"_id": 1, "a": 10, "a$b": INT64_ZERO},
            {"_id": 1, "a": 20, "a$b": Int64(1)},
        ],
        msg="includeArrayIndex should accept non-leading dollar sign in field name",
    ),
    StageTestCase(
        "index_name_very_long",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "x" * 10_000}}],
        expected=[
            {"_id": 1, "a": 10, "x" * 10_000: INT64_ZERO},
            {"_id": 1, "a": 20, "x" * 10_000: Int64(1)},
        ],
        msg="includeArrayIndex should accept very long field names (10,000+ characters)",
    ),
    StageTestCase(
        "index_name_special_punctuation",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "a!@#%&"}}],
        expected=[
            {"_id": 1, "a": 10, "a!@#%&": INT64_ZERO},
            {"_id": 1, "a": 20, "a!@#%&": Int64(1)},
        ],
        msg="includeArrayIndex should accept field name with special punctuation",
    ),
    StageTestCase(
        "index_name_dotted_creates_nested",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "x.y"}}],
        expected=[
            {"_id": 1, "a": 10, "x": {"y": INT64_ZERO}},
            {"_id": 1, "a": 20, "x": {"y": Int64(1)}},
        ],
        msg="includeArrayIndex dotted name should create nested document structure",
    ),
]

# Property [Unicode No Normalization]: precomposed and decomposed Unicode forms
# are treated as distinct field names with no normalization, for both the path
# and includeArrayIndex field names; special characters are accepted in field
# names referenced by the path.
UNWIND_UNICODE_ENCODING_TESTS: list[StageTestCase] = [
    StageTestCase(
        "unicode_precomposed_path_distinct_from_decomposed",
        docs=[{"_id": 1, "\u00e9": [1, 2], "e\u0301": [10, 20]}],
        pipeline=[{"$unwind": "$\u00e9"}],
        expected=[
            {"_id": 1, "\u00e9": 1, "e\u0301": [10, 20]},
            {"_id": 1, "\u00e9": 2, "e\u0301": [10, 20]},
        ],
        msg=(
            "$unwind on precomposed path should only unwind that field"
            " and leave the decomposed form intact"
        ),
    ),
    StageTestCase(
        "unicode_decomposed_path_distinct_from_precomposed",
        docs=[{"_id": 1, "\u00e9": [1, 2], "e\u0301": [10, 20]}],
        pipeline=[{"$unwind": "$e\u0301"}],
        expected=[
            {"_id": 1, "\u00e9": [1, 2], "e\u0301": 10},
            {"_id": 1, "\u00e9": [1, 2], "e\u0301": 20},
        ],
        msg=(
            "$unwind on decomposed path should only unwind that field"
            " and leave the precomposed form intact"
        ),
    ),
    StageTestCase(
        "unicode_precomposed_index_distinct_from_decomposed",
        docs=[{"_id": 1, "a": [10, 20], "\u00e9": "pre", "e\u0301": "dec"}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "\u00e9"}}],
        expected=[
            {"_id": 1, "a": 10, "\u00e9": INT64_ZERO, "e\u0301": "dec"},
            {"_id": 1, "a": 20, "\u00e9": Int64(1), "e\u0301": "dec"},
        ],
        msg=(
            "includeArrayIndex with precomposed name should overwrite only"
            " the precomposed field and leave the decomposed form intact"
        ),
    ),
    StageTestCase(
        "unicode_decomposed_index_distinct_from_precomposed",
        docs=[{"_id": 1, "a": [10, 20], "\u00e9": "pre", "e\u0301": "dec"}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "e\u0301"}}],
        expected=[
            {"_id": 1, "a": 10, "\u00e9": "pre", "e\u0301": INT64_ZERO},
            {"_id": 1, "a": 20, "\u00e9": "pre", "e\u0301": Int64(1)},
        ],
        msg=(
            "includeArrayIndex with decomposed name should overwrite only"
            " the decomposed field and leave the precomposed form intact"
        ),
    ),
    StageTestCase(
        "unicode_space_in_path",
        docs=[{"_id": 1, "a b": [1, 2]}],
        pipeline=[{"$unwind": "$a b"}],
        expected=[{"_id": 1, "a b": 1}, {"_id": 1, "a b": 2}],
        msg="$unwind should accept space in path field name",
    ),
    StageTestCase(
        "unicode_tab_in_path",
        docs=[{"_id": 1, "a\tb": [1, 2]}],
        pipeline=[{"$unwind": "$a\tb"}],
        expected=[{"_id": 1, "a\tb": 1}, {"_id": 1, "a\tb": 2}],
        msg="$unwind should accept tab in path field name",
    ),
    StageTestCase(
        "unicode_nbsp_in_path",
        docs=[{"_id": 1, "a\u00a0b": [1, 2]}],
        pipeline=[{"$unwind": "$a\u00a0b"}],
        expected=[{"_id": 1, "a\u00a0b": 1}, {"_id": 1, "a\u00a0b": 2}],
        msg="$unwind should accept NBSP in path field name",
    ),
    StageTestCase(
        "unicode_control_char_in_path",
        docs=[{"_id": 1, "a\x01b": [1, 2]}],
        pipeline=[{"$unwind": "$a\x01b"}],
        expected=[{"_id": 1, "a\x01b": 1}, {"_id": 1, "a\x01b": 2}],
        msg="$unwind should accept control character in path field name",
    ),
    StageTestCase(
        "unicode_emoji_in_path",
        docs=[{"_id": 1, "\U0001f389": [1, 2]}],
        pipeline=[{"$unwind": "$\U0001f389"}],
        expected=[{"_id": 1, "\U0001f389": 1}, {"_id": 1, "\U0001f389": 2}],
        msg="$unwind should accept emoji in path field name",
    ),
    StageTestCase(
        "unicode_zwj_sequence_in_path",
        docs=[{"_id": 1, "\U0001f468\u200d\U0001f469\u200d\U0001f467": [1, 2]}],
        pipeline=[{"$unwind": "$\U0001f468\u200d\U0001f469\u200d\U0001f467"}],
        expected=[
            {"_id": 1, "\U0001f468\u200d\U0001f469\u200d\U0001f467": 1},
            {"_id": 1, "\U0001f468\u200d\U0001f469\u200d\U0001f467": 2},
        ],
        msg="$unwind should accept ZWJ sequence in path field name",
    ),
]

# Property [Shorthand Document Form Equivalence]: the shorthand
# { $unwind: "$field" } and document form { $unwind: { path: "$field" } }
# produce identical results for all input types.
UNWIND_SHORTHAND_EQUIV_TESTS: list[StageTestCase] = [
    StageTestCase(
        "equiv_document_form_array",
        docs=[{"_id": 1, "a": [1, 2, 3]}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[
            {"_id": 1, "a": 1},
            {"_id": 1, "a": 2},
            {"_id": 1, "a": 3},
        ],
        msg="Document form should unwind array identically to shorthand form",
    ),
    StageTestCase(
        "equiv_document_form_scalar",
        docs=[{"_id": 1, "a": 42}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": 42}],
        msg="Document form should pass through scalar identically to shorthand form",
    ),
    StageTestCase(
        "equiv_shorthand_null",
        docs=[{"_id": 1, "a": None}],
        pipeline=[{"$unwind": "$a"}],
        expected=[],
        msg="Shorthand form should drop null identically to document form",
    ),
    StageTestCase(
        "equiv_shorthand_missing",
        docs=[{"_id": 1, "x": 10}],
        pipeline=[{"$unwind": "$a"}],
        expected=[],
        msg="Shorthand form should drop missing identically to document form",
    ),
    StageTestCase(
        "equiv_shorthand_empty_array",
        docs=[{"_id": 1, "a": []}],
        pipeline=[{"$unwind": "$a"}],
        expected=[],
        msg="Shorthand form should drop empty array identically to document form",
    ),
]

UNWIND_SUCCESS_TESTS = (
    UNWIND_NULL_MISSING_DROPPED_TESTS
    + UNWIND_NULL_MISSING_PRESERVED_TESTS
    + UNWIND_CORE_TESTS
    + UNWIND_BSON_TYPE_TESTS
    + UNWIND_SCALAR_PASSTHROUGH_TESTS
    + UNWIND_NESTED_ARRAYS_TESTS
    + UNWIND_DOTTED_PATH_TESTS
    + UNWIND_INCLUDE_ARRAY_INDEX_TESTS
    + UNWIND_INDEX_FIELD_NAME_COLLISION_TESTS
    + UNWIND_MULTI_STAGE_TESTS
    + UNWIND_INDEX_FIELD_NAME_ACCEPTANCE_TESTS
    + UNWIND_UNICODE_ENCODING_TESTS
    + UNWIND_SHORTHAND_EQUIV_TESTS
)

# Property [Shorthand Document Form Error Equivalence]: the shorthand and
# document forms produce identical error codes for invalid paths.
UNWIND_SHORTHAND_EQUIV_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "equiv_error_shorthand_empty_string",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": ""}],
        error_code=UNWIND_MISSING_PATH_ERROR,
        msg="Shorthand form should reject empty string path",
    ),
    StageTestCase(
        "equiv_error_document_form_empty_string",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": ""}}],
        error_code=UNWIND_MISSING_PATH_ERROR,
        msg="Document form should reject empty string path with same error as shorthand",
    ),
    StageTestCase(
        "equiv_error_shorthand_no_dollar",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": "a"}],
        error_code=UNWIND_PATH_NO_DOLLAR_ERROR,
        msg="Shorthand form should reject path without dollar prefix",
    ),
    StageTestCase(
        "equiv_error_document_form_no_dollar",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "a"}}],
        error_code=UNWIND_PATH_NO_DOLLAR_ERROR,
        msg="Document form should reject path without dollar prefix with same error as shorthand",
    ),
    StageTestCase(
        "equiv_error_shorthand_bare_dollar",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": "$"}],
        error_code=FIELD_PATH_EMPTY_ERROR,
        msg="Shorthand form should reject bare dollar path",
    ),
    StageTestCase(
        "equiv_error_document_form_bare_dollar",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$"}}],
        error_code=FIELD_PATH_EMPTY_ERROR,
        msg="Document form should reject bare dollar path with same error as shorthand",
    ),
]

# Property [Spec Type Shorthand Validation]: in shorthand form, all non-string,
# non-document BSON types are rejected as an invalid spec type.
UNWIND_SPEC_TYPE_SHORTHAND_TESTS: list[StageTestCase] = [
    StageTestCase(
        "spec_type_int32",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": 1}],
        error_code=UNWIND_SPEC_TYPE_ERROR,
        msg="$unwind shorthand should reject int32",
    ),
    StageTestCase(
        "spec_type_int64",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": Int64(1)}],
        error_code=UNWIND_SPEC_TYPE_ERROR,
        msg="$unwind shorthand should reject Int64",
    ),
    StageTestCase(
        "spec_type_double",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": 1.5}],
        error_code=UNWIND_SPEC_TYPE_ERROR,
        msg="$unwind shorthand should reject double",
    ),
    StageTestCase(
        "spec_type_decimal128",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": Decimal128("1")}],
        error_code=UNWIND_SPEC_TYPE_ERROR,
        msg="$unwind shorthand should reject Decimal128",
    ),
    StageTestCase(
        "spec_type_bool",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": True}],
        error_code=UNWIND_SPEC_TYPE_ERROR,
        msg="$unwind shorthand should reject bool",
    ),
    StageTestCase(
        "spec_type_null",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": None}],
        error_code=UNWIND_SPEC_TYPE_ERROR,
        msg="$unwind shorthand should reject null",
    ),
    StageTestCase(
        "spec_type_array_empty",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": []}],
        error_code=UNWIND_SPEC_TYPE_ERROR,
        msg="$unwind shorthand should reject empty array",
    ),
    StageTestCase(
        "spec_type_array_with_field_ref",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": ["$a"]}],
        error_code=UNWIND_SPEC_TYPE_ERROR,
        msg="$unwind shorthand should reject array containing field reference",
    ),
    StageTestCase(
        "spec_type_objectid",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": ObjectId("000000000000000000000001")}],
        error_code=UNWIND_SPEC_TYPE_ERROR,
        msg="$unwind shorthand should reject ObjectId",
    ),
    StageTestCase(
        "spec_type_datetime",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": datetime(2024, 1, 1)}],
        error_code=UNWIND_SPEC_TYPE_ERROR,
        msg="$unwind shorthand should reject datetime",
    ),
    StageTestCase(
        "spec_type_timestamp",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": Timestamp(1, 1)}],
        error_code=UNWIND_SPEC_TYPE_ERROR,
        msg="$unwind shorthand should reject Timestamp",
    ),
    StageTestCase(
        "spec_type_binary",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": Binary(b"\x01")}],
        error_code=UNWIND_SPEC_TYPE_ERROR,
        msg="$unwind shorthand should reject Binary",
    ),
    StageTestCase(
        "spec_type_regex",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": Regex("^a")}],
        error_code=UNWIND_SPEC_TYPE_ERROR,
        msg="$unwind shorthand should reject Regex",
    ),
    StageTestCase(
        "spec_type_code",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": Code("x")}],
        error_code=UNWIND_SPEC_TYPE_ERROR,
        msg="$unwind shorthand should reject Code",
    ),
    StageTestCase(
        "spec_type_code_with_scope",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": Code("x", {})}],
        error_code=UNWIND_SPEC_TYPE_ERROR,
        msg="$unwind shorthand should reject Code with scope",
    ),
    StageTestCase(
        "spec_type_minkey",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": MinKey()}],
        error_code=UNWIND_SPEC_TYPE_ERROR,
        msg="$unwind shorthand should reject MinKey",
    ),
    StageTestCase(
        "spec_type_maxkey",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": MaxKey()}],
        error_code=UNWIND_SPEC_TYPE_ERROR,
        msg="$unwind shorthand should reject MaxKey",
    ),
]

# Property [Path Type Validation (Document Form)]: in document form, all
# non-string BSON types for path are rejected with a path type error.
UNWIND_PATH_TYPE_DOC_FORM_TESTS: list[StageTestCase] = [
    StageTestCase(
        "path_type_int32",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": 1}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="$unwind document form should reject int32 path",
    ),
    StageTestCase(
        "path_type_int64",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": Int64(1)}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="$unwind document form should reject Int64 path",
    ),
    StageTestCase(
        "path_type_double",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": 1.5}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="$unwind document form should reject double path",
    ),
    StageTestCase(
        "path_type_decimal128",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": Decimal128("1")}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="$unwind document form should reject Decimal128 path",
    ),
    StageTestCase(
        "path_type_bool",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": True}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="$unwind document form should reject bool path",
    ),
    StageTestCase(
        "path_type_null",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": None}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="$unwind document form should reject null path",
    ),
    StageTestCase(
        "path_type_array",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": ["$a"]}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="$unwind document form should reject array path",
    ),
    StageTestCase(
        "path_type_objectid",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": ObjectId("000000000000000000000001")}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="$unwind document form should reject ObjectId path",
    ),
    StageTestCase(
        "path_type_datetime",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": datetime(2024, 1, 1)}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="$unwind document form should reject datetime path",
    ),
    StageTestCase(
        "path_type_timestamp",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": Timestamp(1, 1)}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="$unwind document form should reject Timestamp path",
    ),
    StageTestCase(
        "path_type_binary",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": Binary(b"\x01")}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="$unwind document form should reject Binary path",
    ),
    StageTestCase(
        "path_type_regex",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": Regex("^a")}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="$unwind document form should reject Regex path",
    ),
    StageTestCase(
        "path_type_code",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": Code("x")}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="$unwind document form should reject Code path",
    ),
    StageTestCase(
        "path_type_code_with_scope",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": Code("x", {})}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="$unwind document form should reject Code with scope path",
    ),
    StageTestCase(
        "path_type_minkey",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": MinKey()}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="$unwind document form should reject MinKey path",
    ),
    StageTestCase(
        "path_type_maxkey",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": MaxKey()}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="$unwind document form should reject MaxKey path",
    ),
]

# Property [Path Field Path Syntax]: the path string must be a valid field
# path starting with '$', containing no empty components, no trailing dot, no
# null bytes, no '$' in non-initial components, no system variables, and no
# more than 200 path components.
UNWIND_PATH_FIELD_PATH_SYNTAX_TESTS: list[StageTestCase] = [
    StageTestCase(
        "path_syntax_system_variable_root",
        docs=[],
        pipeline=[{"$unwind": {"path": "$$ROOT"}}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$unwind should reject $$ROOT system variable as path",
    ),
    StageTestCase(
        "path_syntax_system_variable_current",
        docs=[],
        pipeline=[{"$unwind": {"path": "$$CURRENT"}}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$unwind should reject $$CURRENT system variable as path",
    ),
    StageTestCase(
        "path_syntax_dollar_in_non_initial_component",
        docs=[],
        pipeline=[{"$unwind": {"path": "$a.$b"}}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$unwind should reject $ in a non-initial path component",
    ),
    StageTestCase(
        "path_syntax_empty_component_double_dot",
        docs=[],
        pipeline=[{"$unwind": {"path": "$a..b"}}],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="$unwind should reject empty path component from double dot",
    ),
    StageTestCase(
        "path_syntax_empty_component_leading_dot",
        docs=[],
        pipeline=[{"$unwind": {"path": "$.a"}}],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="$unwind should reject empty path component from leading dot",
    ),
    StageTestCase(
        "path_syntax_trailing_dot",
        docs=[],
        pipeline=[{"$unwind": {"path": "$a."}}],
        error_code=FIELD_PATH_TRAILING_DOT_ERROR,
        msg="$unwind should reject trailing dot in path",
    ),
    StageTestCase(
        "path_syntax_null_byte",
        docs=[],
        pipeline=[{"$unwind": {"path": "$a\x00b"}}],
        error_code=EXPRESSION_FIELD_PATH_NULL_BYTE_ERROR,
        msg="$unwind should reject null byte in path",
    ),
    StageTestCase(
        "path_syntax_depth_201_exceeds_limit",
        docs=[],
        pipeline=[{"$unwind": {"path": "$" + ".".join(["a"] * 201)}}],
        error_code=OVERFLOW_ERROR,
        msg="$unwind should reject path with 201 components (exceeds 200 limit)",
    ),
]

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

# Property [preserveNullAndEmptyArrays Type Validation]: all non-boolean BSON
# types for preserveNullAndEmptyArrays are rejected with a type error; no
# truthy/falsy coercion is performed, and expression objects and field
# references are rejected as their literal types.
UNWIND_PRESERVE_NULL_TYPE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "preserve_type_int32_zero",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": 0}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject int32 0 (no falsy coercion)",
    ),
    StageTestCase(
        "preserve_type_int32_one",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": 1}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject int32 1 (no truthy coercion)",
    ),
    StageTestCase(
        "preserve_type_int64",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": Int64(1)}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject Int64",
    ),
    StageTestCase(
        "preserve_type_double_zero",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": DOUBLE_ZERO}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject double 0.0 (no falsy coercion)",
    ),
    StageTestCase(
        "preserve_type_double_one",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": 1.0}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject double 1.0 (no truthy coercion)",
    ),
    StageTestCase(
        "preserve_type_decimal128",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": Decimal128("1")}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject Decimal128",
    ),
    StageTestCase(
        "preserve_type_string",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": "true"}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject string",
    ),
    StageTestCase(
        "preserve_type_null",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": None}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject null (not treated as default false)",
    ),
    StageTestCase(
        "preserve_type_array",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": []}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject array",
    ),
    StageTestCase(
        "preserve_type_object",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": {"x": 1}}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject object",
    ),
    StageTestCase(
        "preserve_type_objectid",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[
            {
                "$unwind": {
                    "path": "$a",
                    "preserveNullAndEmptyArrays": ObjectId("000000000000000000000001"),
                }
            }
        ],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject ObjectId",
    ),
    StageTestCase(
        "preserve_type_datetime",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": datetime(2024, 1, 1)}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject datetime",
    ),
    StageTestCase(
        "preserve_type_timestamp",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": Timestamp(1, 1)}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject Timestamp",
    ),
    StageTestCase(
        "preserve_type_binary",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": Binary(b"\x01")}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject Binary",
    ),
    StageTestCase(
        "preserve_type_regex",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": Regex("^a")}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject Regex",
    ),
    StageTestCase(
        "preserve_type_code",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": Code("x")}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject Code",
    ),
    StageTestCase(
        "preserve_type_code_with_scope",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": Code("x", {})}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject Code with scope",
    ),
    StageTestCase(
        "preserve_type_minkey",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": MinKey()}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject MinKey",
    ),
    StageTestCase(
        "preserve_type_maxkey",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": MaxKey()}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject MaxKey",
    ),
    StageTestCase(
        "preserve_type_expression_literal",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": {"$literal": True}}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject expression object {$literal: true}",
    ),
    StageTestCase(
        "preserve_type_field_reference",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": "$flag"}}],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg="preserveNullAndEmptyArrays should reject field reference string",
    ),
]

# Property [Missing Path]: omitting the path field in document form produces
# a missing path error.
UNWIND_MISSING_PATH_TESTS: list[StageTestCase] = [
    StageTestCase(
        "missing_path_empty_document",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {}}],
        error_code=UNWIND_MISSING_PATH_ERROR,
        msg="$unwind should reject document form with no path field",
    ),
    StageTestCase(
        "missing_path_only_options",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[
            {
                "$unwind": {
                    "includeArrayIndex": "idx",
                    "preserveNullAndEmptyArrays": True,
                }
            }
        ],
        error_code=UNWIND_MISSING_PATH_ERROR,
        msg="$unwind should reject document form with options but no path field",
    ),
]

# Property [Unrecognized Fields]: unrecognized fields in the document form
# produce an unrecognized field error, and this error takes precedence over
# a missing path error.
UNWIND_UNRECOGNIZED_FIELD_TESTS: list[StageTestCase] = [
    StageTestCase(
        "unrecognized_field_with_valid_path",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a", "badField": True}}],
        error_code=UNWIND_UNRECOGNIZED_FIELD_ERROR,
        msg="$unwind should reject unrecognized field in document form",
    ),
    StageTestCase(
        "unrecognized_field_precedes_missing_path",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"badField": True}}],
        error_code=UNWIND_UNRECOGNIZED_FIELD_ERROR,
        msg="$unwind unrecognized field error should take precedence over missing path error",
    ),
]

# Property [Error Precedence]: validation proceeds in two phases - phase 1
# iterates fields in BSON document order (path type, includeArrayIndex
# type/dollar, preserveNullAndEmptyArrays type, unrecognized field, missing
# path) and phase 2 performs post-iteration semantic validation (path
# no-dollar, path field path, includeArrayIndex field path); the first error
# encountered wins, and all validation errors fire even on empty and
# non-existent collections.
UNWIND_ERROR_PRECEDENCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "precedence_path_type_over_index_type",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": 123, "includeArrayIndex": 456}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="path type error should take precedence over includeArrayIndex type error",
    ),
    StageTestCase(
        "precedence_path_type_over_preserve_type",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": 123, "preserveNullAndEmptyArrays": "bad"}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="path type error should take precedence over preserveNullAndEmptyArrays type error",
    ),
    StageTestCase(
        "precedence_path_type_over_unrecognized",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": 123, "badField": True}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="path type error should take precedence over unrecognized field error",
    ),
    StageTestCase(
        "precedence_index_type_over_preserve_type",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[
            {
                "$unwind": {
                    "path": "$a",
                    "includeArrayIndex": 123,
                    "preserveNullAndEmptyArrays": "bad",
                }
            }
        ],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_TYPE_ERROR,
        msg=(
            "includeArrayIndex type error should take precedence over"
            " preserveNullAndEmptyArrays type error"
        ),
    ),
    StageTestCase(
        "precedence_index_type_over_path_no_dollar",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "no_dollar", "includeArrayIndex": 456}}],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_TYPE_ERROR,
        msg=(
            "includeArrayIndex type error (phase 1) should take precedence"
            " over path no-dollar (phase 2)"
        ),
    ),
    StageTestCase(
        "precedence_preserve_type_over_index_field_path",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[
            {
                "$unwind": {
                    "path": "$a",
                    "includeArrayIndex": "a..b",
                    "preserveNullAndEmptyArrays": "bad",
                }
            }
        ],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg=(
            "preserveNullAndEmptyArrays type error (phase 1) should take"
            " precedence over includeArrayIndex field path (phase 2)"
        ),
    ),
    StageTestCase(
        "precedence_path_no_dollar_over_index_field_path",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "no_dollar", "includeArrayIndex": "a..b"}}],
        error_code=UNWIND_PATH_NO_DOLLAR_ERROR,
        msg=(
            "path no-dollar error should take precedence over"
            " includeArrayIndex field path error in phase 2"
        ),
    ),
    StageTestCase(
        "precedence_bson_order_index_type_before_path_type",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"includeArrayIndex": 456, "path": 123}}],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_TYPE_ERROR,
        msg=(
            "When includeArrayIndex appears before path in BSON document order,"
            " includeArrayIndex type error should win over path type error"
        ),
    ),
    StageTestCase(
        "precedence_index_dollar_precedes_path_no_dollar",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[
            {
                "$unwind": {
                    "path": "a",
                    "includeArrayIndex": "$idx",
                }
            }
        ],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_DOLLAR_PREFIX_ERROR,
        msg=(
            "includeArrayIndex dollar prefix error should fire before"
            " path no-dollar semantic validation error"
        ),
    ),
    StageTestCase(
        "precedence_index_dollar_precedes_preserve_type",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[
            {
                "$unwind": {
                    "path": "$a",
                    "includeArrayIndex": "$idx",
                    "preserveNullAndEmptyArrays": "invalid",
                }
            }
        ],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_DOLLAR_PREFIX_ERROR,
        msg=(
            "includeArrayIndex dollar prefix error should fire before"
            " preserveNullAndEmptyArrays type error"
        ),
    ),
    StageTestCase(
        "precedence_path_field_path_over_index_field_path",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a..b", "includeArrayIndex": "x."}}],
        error_code=FIELD_PATH_TRAILING_DOT_ERROR,
        msg=(
            "path field path error should take precedence over"
            " includeArrayIndex field path error in phase 2"
        ),
    ),
    StageTestCase(
        "precedence_error_fires_on_empty_collection",
        docs=[],
        pipeline=[{"$unwind": {"path": 123}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="validation errors should fire on empty collections",
    ),
    StageTestCase(
        "precedence_error_fires_on_nonexistent_collection",
        docs=None,
        pipeline=[{"$unwind": {"path": 123}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="validation errors should fire on non-existent collections",
    ),
]

# Property [Expression Arguments Rejected]: path is a static field path
# string, not an expression - expression objects such as $literal are rejected
# as their literal BSON type (object).
UNWIND_EXPRESSION_ARGUMENTS_TESTS: list[StageTestCase] = [
    StageTestCase(
        "expr_arg_path_literal",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": {"$literal": "$a"}}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="path should reject $literal expression object as non-string type",
    ),
]

UNWIND_ERROR_TESTS = (
    UNWIND_SHORTHAND_EQUIV_ERROR_TESTS
    + UNWIND_SPEC_TYPE_SHORTHAND_TESTS
    + UNWIND_PATH_TYPE_DOC_FORM_TESTS
    + UNWIND_PATH_FIELD_PATH_SYNTAX_TESTS
    + UNWIND_INCLUDE_ARRAY_INDEX_TYPE_TESTS
    + UNWIND_INCLUDE_ARRAY_INDEX_DOLLAR_PREFIX_TESTS
    + UNWIND_INCLUDE_ARRAY_INDEX_FIELD_PATH_SYNTAX_TESTS
    + UNWIND_PRESERVE_NULL_TYPE_TESTS
    + UNWIND_MISSING_PATH_TESTS
    + UNWIND_UNRECOGNIZED_FIELD_TESTS
    + UNWIND_ERROR_PRECEDENCE_TESTS
    + UNWIND_EXPRESSION_ARGUMENTS_TESTS
)

UNWIND_TESTS = UNWIND_SUCCESS_TESTS + UNWIND_ERROR_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(UNWIND_TESTS))
def test_stages_unwind_cases(collection, test_case: StageTestCase):
    """Test $unwind cases."""
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


@pytest.mark.aggregate
def test_stages_unwind_index_field_order(collection):
    """Test $unwind includeArrayIndex field ordering."""
    collection.insert_many([{"_id": 1, "z": 99, "a": [10], "b": "keep"}])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$unwind": {"path": "$a", "includeArrayIndex": "idx"}}],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        expected=[["_id", "z", "a", "b", "idx"]],
        transform=lambda docs: [list(d.keys()) for d in docs],
        msg="includeArrayIndex field should be appended at end of document field order",
    )


@pytest.mark.aggregate
def test_stages_unwind_index_dotted_field_order(collection):
    """Test $unwind includeArrayIndex dotted name field ordering."""
    collection.insert_many([{"_id": 1, "z": 99, "a": [10], "b": "keep"}])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$unwind": {"path": "$a", "includeArrayIndex": "x.y"}}],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        expected=[["_id", "z", "a", "b", "x"]],
        transform=lambda docs: [list(d.keys()) for d in docs],
        msg=(
            "includeArrayIndex dotted name top-level key should be appended"
            " at end of document field order"
        ),
    )


# Property [Field Ordering]: document field order from the input is preserved
# in output documents, and other array fields are not unwound.
@pytest.mark.aggregate
def test_stages_unwind_field_ordering(collection):
    """Test $unwind preserves input document field order."""
    collection.insert_many([{"_id": 1, "z": 99, "a": [10, 20], "m": "mid", "b": "end"}])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$unwind": "$a"}],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        expected=[["_id", "z", "a", "m", "b"]],
        transform=lambda docs: [list(d.keys()) for d in docs[:1]],
        msg="$unwind should preserve input document field order in output",
    )


@pytest.mark.aggregate
def test_stages_unwind_other_arrays_not_unwound(collection):
    """Test $unwind does not unwind other array fields."""
    collection.insert_many([{"_id": 1, "a": [1, 2], "b": ["x", "y"], "c": [[3]]}])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$unwind": "$a"}],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        expected=[
            {"_id": 1, "a": 1, "b": ["x", "y"], "c": [[3]]},
            {"_id": 1, "a": 2, "b": ["x", "y"], "c": [[3]]},
        ],
        msg="$unwind should not unwind other array fields in the document",
    )


# Property [Large Arrays]: arrays with many elements produce the correct
# number of output documents with sequential indices and no off-by-one errors.
@pytest.mark.aggregate
def test_stages_unwind_large_array(collection):
    """Test $unwind with a large array."""
    collection.insert_many([{"_id": 1, "a": list(range(10_000))}])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$unwind": {"path": "$a", "includeArrayIndex": "idx"}}],
            "cursor": {"batchSize": 10_000},
        },
    )
    assertSuccess(
        result,
        expected=True,
        transform=lambda docs: (
            len(docs) == 10_000 and all(d["a"] == i and d["idx"] == i for i, d in enumerate(docs))
        ),
        msg="$unwind should produce 10,000 output documents with sequential values and indices",
    )
