"""
Tests for $type query operator with fields and arrays.

Verifies $type behavior with array fields (element-level matching, empty
arrays, nested arrays), array-of-types arguments, nested field paths
via dot notation, and _id field type matching.
"""

import pytest
from bson import Decimal128, Int64, ObjectId

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

ARRAY_TYPE_DOCS: list[dict] = [
    {"_id": 1, "x": 1.5},  # double
    {"_id": 2, "x": "hello"},  # string
    {"_id": 3, "x": 42},  # int
    {"_id": 4, "x": None},  # null
    {"_id": 5, "x": Int64(100)},  # long
    {"_id": 6, "x": Decimal128("1.5")},  # decimal
]

OID = ObjectId()

ARRAY_BEHAVIOR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="array_field_matches_type_array",
        filter={"x": {"$type": "array"}},
        doc=[{"_id": 1, "x": [1, 2]}, {"_id": 2, "x": "hello"}],
        expected=[{"_id": 1, "x": [1, 2]}],
        msg="$type: 'array' should match fields that are arrays",
    ),
    QueryTestCase(
        id="array_element_string_match",
        filter={"x": {"$type": "string"}},
        doc=[{"_id": 1, "x": ["a", "b"]}, {"_id": 2, "x": 42}],
        expected=[{"_id": 1, "x": ["a", "b"]}],
        msg="$type: 'string' should match array containing string elements",
    ),
    QueryTestCase(
        id="array_element_int_match",
        filter={"x": {"$type": "int"}},
        doc=[{"_id": 1, "x": [1, 2]}, {"_id": 2, "x": "hello"}],
        expected=[{"_id": 1, "x": [1, 2]}],
        msg="$type: 'int' should match array containing int elements",
    ),
    QueryTestCase(
        id="array_no_string_element_no_match",
        filter={"x": {"$type": "string"}},
        doc=[{"_id": 1, "x": [1, 2]}],
        expected=[],
        msg="$type: 'string' should NOT match array with no string elements",
    ),
    QueryTestCase(
        id="nested_array_matches_type_array",
        filter={"x": {"$type": "array"}},
        doc=[{"_id": 1, "x": [[1]]}, {"_id": 2, "x": "hello"}],
        expected=[{"_id": 1, "x": [[1]]}],
        msg="$type: 'array' should match nested array",
    ),
    QueryTestCase(
        id="empty_array_matches_type_array",
        filter={"x": {"$type": "array"}},
        doc=[{"_id": 1, "x": []}, {"_id": 2, "x": "hello"}],
        expected=[{"_id": 1, "x": []}],
        msg="$type: 'array' should match empty array (field is still array type)",
    ),
    QueryTestCase(
        id="empty_array_no_element_match",
        filter={"x": {"$type": "int"}},
        doc=[{"_id": 1, "x": []}],
        expected=[],
        msg="$type: 'int' should NOT match empty array (no elements)",
    ),
    QueryTestCase(
        id="mixed_array_string_element_match",
        filter={"x": {"$type": "string"}},
        doc=[{"_id": 1, "x": [1, "a", True]}],
        expected=[{"_id": 1, "x": [1, "a", True]}],
        msg="$type: 'string' should match mixed array containing string element",
    ),
    QueryTestCase(
        id="mixed_array_bool_element_match",
        filter={"x": {"$type": "bool"}},
        doc=[{"_id": 1, "x": [1, "a", True]}],
        expected=[{"_id": 1, "x": [1, "a", True]}],
        msg="$type: 'bool' should match mixed array containing bool element",
    ),
    QueryTestCase(
        id="mixed_array_no_double_no_match",
        filter={"x": {"$type": "double"}},
        doc=[{"_id": 1, "x": [1, "a", True]}],
        expected=[],
        msg="$type: 'double' should NOT match mixed array "
        "with no double element (1 is int, not double)",
    ),
    QueryTestCase(
        id="array_field_matches_numeric_code_4",
        filter={"x": {"$type": 4}},
        doc=[{"_id": 1, "x": [1, 2]}, {"_id": 2, "x": "hello"}],
        expected=[{"_id": 1, "x": [1, 2]}],
        msg="$type: 4 should match array fields",
    ),
    QueryTestCase(
        id="array_of_arrays_element_matching_int",
        filter={"x": {"$type": "int"}},
        doc=[{"_id": 1, "x": [[1, 2]]}, {"_id": 2, "x": "hello"}],
        expected=[],
        msg="$type: 'int' should NOT match array-of-arrays — elements are arrays, not ints",
    ),
]

ARRAY_OF_TYPES_ARG_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="type_array_arg_array_and_string",
        filter={"x": {"$type": ["array", "string"]}},
        doc=[{"_id": 1, "x": ["a"]}, {"_id": 2, "x": 42}],
        expected=[{"_id": 1, "x": ["a"]}],
        msg="$type: ['array', 'string'] on array ['a'] should match",
    ),
    QueryTestCase(
        id="type_array_arg_two_numeric_codes",
        filter={"x": {"$type": [1, 2]}},
        doc=ARRAY_TYPE_DOCS,
        expected=[ARRAY_TYPE_DOCS[0], ARRAY_TYPE_DOCS[1]],
        msg="$type: [1, 2] should match double OR string",
    ),
    QueryTestCase(
        id="type_array_arg_two_string_aliases",
        filter={"x": {"$type": ["double", "string"]}},
        doc=ARRAY_TYPE_DOCS,
        expected=[ARRAY_TYPE_DOCS[0], ARRAY_TYPE_DOCS[1]],
        msg="$type: ['double', 'string'] should match double OR string",
    ),
    QueryTestCase(
        id="type_array_arg_mixed_alias_and_code",
        filter={"x": {"$type": ["double", 16]}},
        doc=ARRAY_TYPE_DOCS,
        expected=[ARRAY_TYPE_DOCS[0], ARRAY_TYPE_DOCS[2]],
        msg="$type: ['double', 16] should match double OR int",
    ),
    QueryTestCase(
        id="type_array_arg_null_and_string",
        filter={"x": {"$type": ["null", "string"]}},
        doc=ARRAY_TYPE_DOCS,
        expected=[ARRAY_TYPE_DOCS[1], ARRAY_TYPE_DOCS[3]],
        msg="$type: ['null', 'string'] should match null OR string",
    ),
    QueryTestCase(
        id="type_array_arg_single_element",
        filter={"x": {"$type": [2]}},
        doc=ARRAY_TYPE_DOCS,
        expected=[ARRAY_TYPE_DOCS[1]],
        msg="$type: [2] should behave same as $type: 2",
    ),
    QueryTestCase(
        id="type_array_arg_number_and_string",
        filter={"x": {"$type": ["number", "string"]}},
        doc=ARRAY_TYPE_DOCS,
        expected=[
            ARRAY_TYPE_DOCS[0],
            ARRAY_TYPE_DOCS[1],
            ARRAY_TYPE_DOCS[2],
            ARRAY_TYPE_DOCS[4],
            ARRAY_TYPE_DOCS[5],
        ],
        msg="$type: ['number', 'string'] should match any numeric OR string",
    ),
    QueryTestCase(
        id="type_array_arg_all_numerics_eq_number",
        filter={"x": {"$type": ["double", "int", "long", "decimal"]}},
        doc=ARRAY_TYPE_DOCS,
        expected=[
            ARRAY_TYPE_DOCS[0],
            ARRAY_TYPE_DOCS[2],
            ARRAY_TYPE_DOCS[4],
            ARRAY_TYPE_DOCS[5],
        ],
        msg="$type: ['double', 'int', 'long', 'decimal'] " "should be equivalent to 'number'",
    ),
]

DOT_PATH_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="nested_dot_path",
        filter={"a.b.c": {"$type": "string"}},
        doc=[{"_id": 1, "a": {"b": {"c": "test"}}}, {"_id": 2, "a": {"b": {"c": 42}}}],
        expected=[{"_id": 1, "a": {"b": {"c": "test"}}}],
        msg="$type on nested field 'a.b.c' should match string value",
    ),
    QueryTestCase(
        id="array_index_dot_notation",
        filter={"a.0": {"$type": "string"}},
        doc=[{"_id": 1, "a": ["test", 1]}, {"_id": 2, "a": [1, 2]}],
        expected=[{"_id": 1, "a": ["test", 1]}],
        msg="$type on array element via 'a.0' should match element type",
    ),
    QueryTestCase(
        id="array_index_then_field",
        filter={"a.0.b": {"$type": "string"}},
        doc=[{"_id": 1, "a": [{"b": "test"}]}, {"_id": 2, "a": [{"b": 42}]}],
        expected=[{"_id": 1, "a": [{"b": "test"}]}],
        msg="$type on 'a.0.b' should index into array then access nested field",
    ),
    QueryTestCase(
        id="field_then_array_index",
        filter={"a.b.0": {"$type": "string"}},
        doc=[{"_id": 1, "a": {"b": ["test", 1]}}, {"_id": 2, "a": {"b": [1, 2]}}],
        expected=[{"_id": 1, "a": {"b": ["test", 1]}}],
        msg="$type on 'a.b.0' should access nested field then index into array",
    ),
    QueryTestCase(
        id="dot_path_traverses_array_of_objects",
        filter={"a.b": {"$type": "string"}},
        doc=[
            {"_id": 1, "a": [{"b": "test"}, {"b": 1}]},
            {"_id": 2, "a": [{"b": 1}, {"b": 2}]},
        ],
        expected=[{"_id": 1, "a": [{"b": "test"}, {"b": 1}]}],
        msg="$type on 'a.b' where a is array of objects should match via array traversal",
    ),
    QueryTestCase(
        id="array_index_path_type_array",
        filter={"a.0": {"$type": "array"}},
        doc=[{"_id": 1, "a": [[1, 2], 3]}, {"_id": 2, "a": [1, 2]}],
        expected=[{"_id": 1, "a": [[1, 2], 3]}],
        msg="$type: 'array' with array index path 'a.0' should match when element is an array",
    ),
]

ID_FIELD_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="id_field_objectId",
        filter={"_id": {"$type": "objectId"}},
        doc=[{"_id": OID, "x": 1}, {"_id": 1, "x": 2}],
        expected=[{"_id": OID, "x": 1}],
        msg="$type: 'objectId' on _id should match ObjectId _ids",
    ),
    QueryTestCase(
        id="id_field_int",
        filter={"_id": {"$type": "int"}},
        doc=[{"_id": OID, "x": 1}, {"_id": 1, "x": 2}],
        expected=[{"_id": 1, "x": 2}],
        msg="$type: 'int' on _id should match integer _ids",
    ),
    QueryTestCase(
        id="id_field_string",
        filter={"_id": {"$type": "string"}},
        doc=[{"_id": "abc", "x": 1}, {"_id": 1, "x": 2}],
        expected=[{"_id": "abc", "x": 1}],
        msg="$type: 'string' on _id should match string _ids",
    ),
    QueryTestCase(
        id="id_field_object",
        filter={"_id": {"$type": "object"}},
        doc=[{"_id": {"a": 1, "b": 2}, "x": 1}, {"_id": 1, "x": 2}],
        expected=[{"_id": {"a": 1, "b": 2}, "x": 1}],
        msg="$type: 'object' on _id should match compound _ids",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ARRAY_BEHAVIOR_TESTS))
def test_type_array_behavior(collection, test):
    """Test $type with array fields: element-level matching, empty arrays, nested arrays."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True, msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(ARRAY_OF_TYPES_ARG_TESTS))
def test_type_array_of_types_arg(collection, test):
    """Test $type with array-of-types arguments."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True, msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(DOT_PATH_TESTS))
def test_type_dot_paths(collection, test):
    """Test $type with nested field paths via dot notation."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True, msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(ID_FIELD_TESTS))
def test_type_id_field(collection, test):
    """Test $type on _id field with various types."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True, msg=test.msg)
