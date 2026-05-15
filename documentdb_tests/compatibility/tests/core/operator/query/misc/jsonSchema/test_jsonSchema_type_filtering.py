"""
Tests for $jsonSchema document type matching.

Verifies that bsonType and type keywords correctly filter documents based on
field types, including single-type matching, array-of-types syntax, special
cases, and type distinction between similar BSON types.
"""

from datetime import datetime, timezone

import pytest
from bson import Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

TRIVIAL_SCHEMA_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="trivial_valid_object_schema",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": "int"}}}},
        doc=[{"_id": 1, "x": 1}, {"_id": 2, "x": "a"}],
        expected=[{"_id": 1, "x": 1}],
        msg="Valid object argument should succeed",
    ),
    QueryTestCase(
        id="trivial_empty_schema_matches_all",
        filter={"$jsonSchema": {}},
        doc=[{"_id": 1, "x": 1}, {"_id": 2, "x": "a"}],
        expected=[{"_id": 1, "x": 1}, {"_id": 2, "x": "a"}],
        msg="Empty object should match all documents",
    ),
    QueryTestCase(
        id="trivial_bsontype_object_matches_all",
        filter={"$jsonSchema": {"bsonType": "object"}},
        doc=[{"_id": 1, "x": 1}, {"_id": 2, "x": "a"}],
        expected=[{"_id": 1, "x": 1}, {"_id": 2, "x": "a"}],
        msg="bsonType object should match all documents",
    ),
    QueryTestCase(
        id="trivial_not_empty_matches_none",
        filter={"$jsonSchema": {"not": {}}},
        doc=[{"_id": 1, "x": 1}, {"_id": 2, "x": "a"}],
        expected=[],
        msg="not empty schema should match no documents",
    ),
    QueryTestCase(
        id="trivial_empty_properties_matches_all",
        filter={"$jsonSchema": {"properties": {}}},
        doc=[{"_id": 1, "x": 1}, {"_id": 2, "x": "a"}],
        expected=[{"_id": 1, "x": 1}, {"_id": 2, "x": "a"}],
        msg="Empty properties should match all documents",
    ),
    QueryTestCase(
        id="trivial_description_no_effect",
        filter={
            "$jsonSchema": {"description": "test schema", "properties": {"x": {"bsonType": "int"}}}
        },
        doc=[{"_id": 1, "x": 1}, {"_id": 2, "x": "a"}],
        expected=[{"_id": 1, "x": 1}],
        msg="Description keyword should have no effect on validation",
    ),
    QueryTestCase(
        id="trivial_title_no_effect",
        filter={"$jsonSchema": {"title": "test", "properties": {"x": {"bsonType": "int"}}}},
        doc=[{"_id": 1, "x": 1}, {"_id": 2, "x": "a"}],
        expected=[{"_id": 1, "x": 1}],
        msg="Title keyword should have no effect on validation",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TRIVIAL_SCHEMA_TESTS))
def test_jsonSchema_trivial_schemas(collection, test):
    """Test $jsonSchema with trivial/valid schemas."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected)


BSONTYPE_MATCH_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="match_double",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": "double"}}}},
        doc=[{"_id": 1, "x": 3.14}, {"_id": 2, "x": "str"}],
        expected=[{"_id": 1, "x": 3.14}],
        msg="bsonType double should match double values",
    ),
    QueryTestCase(
        id="match_string",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": "string"}}}},
        doc=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": 123}],
        expected=[{"_id": 1, "x": "hello"}],
        msg="bsonType string should match string values",
    ),
    QueryTestCase(
        id="match_object",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": "object"}}}},
        doc=[{"_id": 1, "x": {"nested": 1}}, {"_id": 2, "x": [1, 2]}],
        expected=[{"_id": 1, "x": {"nested": 1}}],
        msg="bsonType object should match object values",
    ),
    QueryTestCase(
        id="match_array",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": "array"}}}},
        doc=[{"_id": 1, "x": [1, 2, 3]}, {"_id": 2, "x": {"a": 1}}],
        expected=[{"_id": 1, "x": [1, 2, 3]}],
        msg="bsonType array should match array values",
    ),
    QueryTestCase(
        id="match_binData",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": "binData"}}}},
        doc=[{"_id": 1, "x": b"\x01\x02"}, {"_id": 2, "x": "str"}],
        expected=[{"_id": 1, "x": b"\x01\x02"}],
        msg="bsonType binData should match Binary values",
    ),
    QueryTestCase(
        id="match_objectId",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": "objectId"}}}},
        doc=[{"_id": 1, "x": ObjectId("000000000000000000000001")}, {"_id": 2, "x": 123}],
        expected=[{"_id": 1, "x": ObjectId("000000000000000000000001")}],
        msg="bsonType objectId should match ObjectId values",
    ),
    QueryTestCase(
        id="match_bool",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": "bool"}}}},
        doc=[{"_id": 1, "x": True}, {"_id": 2, "x": 0}],
        expected=[{"_id": 1, "x": True}],
        msg="bsonType bool should match boolean values",
    ),
    QueryTestCase(
        id="match_date",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": "date"}}}},
        doc=[
            {"_id": 1, "x": datetime(2024, 1, 1, tzinfo=timezone.utc)},
            {"_id": 2, "x": Timestamp(1, 1)},
        ],
        expected=[{"_id": 1, "x": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        msg="bsonType date should match datetime values",
    ),
    QueryTestCase(
        id="match_null",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": "null"}}}},
        doc=[{"_id": 1, "x": None}, {"_id": 2, "x": 0}],
        expected=[{"_id": 1, "x": None}],
        msg="bsonType null should match null values",
    ),
    QueryTestCase(
        id="match_regex",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": "regex"}}}},
        doc=[{"_id": 1, "x": Regex("^abc", "i")}, {"_id": 2, "x": "abc"}],
        expected=[{"_id": 1, "x": Regex("^abc", "i")}],
        msg="bsonType regex should match Regex values",
    ),
    QueryTestCase(
        id="match_javascript",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": "javascript"}}}},
        doc=[{"_id": 1, "x": Code("function(){}")}, {"_id": 2, "x": "str"}],
        expected=[{"_id": 1, "x": Code("function(){}")}],
        msg="bsonType javascript should match Code values",
    ),
    QueryTestCase(
        id="match_int",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": "int"}}}},
        doc=[{"_id": 1, "x": 42}, {"_id": 2, "x": 3.14}],
        expected=[{"_id": 1, "x": 42}],
        msg="bsonType int should match int values",
    ),
    QueryTestCase(
        id="match_timestamp",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": "timestamp"}}}},
        doc=[
            {"_id": 1, "x": Timestamp(1000, 1)},
            {"_id": 2, "x": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        ],
        expected=[{"_id": 1, "x": Timestamp(1000, 1)}],
        msg="bsonType timestamp should match Timestamp values",
    ),
    QueryTestCase(
        id="match_long",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": "long"}}}},
        doc=[{"_id": 1, "x": Int64(123456789)}, {"_id": 2, "x": 3.14}],
        expected=[{"_id": 1, "x": Int64(123456789)}],
        msg="bsonType long should match Int64 values",
    ),
    QueryTestCase(
        id="match_decimal",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": "decimal"}}}},
        doc=[{"_id": 1, "x": Decimal128("1.5")}, {"_id": 2, "x": 3.14}],
        expected=[{"_id": 1, "x": Decimal128("1.5")}],
        msg="bsonType decimal should match Decimal128 values",
    ),
    QueryTestCase(
        id="match_minKey",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": "minKey"}}}},
        doc=[{"_id": 1, "x": MinKey()}, {"_id": 2, "x": 0}],
        expected=[{"_id": 1, "x": MinKey()}],
        msg="bsonType minKey should match MinKey values",
    ),
    QueryTestCase(
        id="match_maxKey",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": "maxKey"}}}},
        doc=[{"_id": 1, "x": MaxKey()}, {"_id": 2, "x": 0}],
        expected=[{"_id": 1, "x": MaxKey()}],
        msg="bsonType maxKey should match MaxKey values",
    ),
]


@pytest.mark.parametrize("test", pytest_params(BSONTYPE_MATCH_TESTS))
def test_jsonSchema_bsontype_matches(collection, test):
    """Test bsonType matches the correct BSON type and rejects others."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected)


BSONTYPE_SPECIAL_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="special_number_matches_all_numeric",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": "number"}}}},
        doc=[
            {"_id": 1, "x": 42},
            {"_id": 2, "x": Int64(100)},
            {"_id": 3, "x": 3.14},
            {"_id": 4, "x": Decimal128("1.5")},
            {"_id": 5, "x": "not_number"},
        ],
        expected=[
            {"_id": 1, "x": 42},
            {"_id": 2, "x": Int64(100)},
            {"_id": 3, "x": 3.14},
            {"_id": 4, "x": Decimal128("1.5")},
        ],
        msg="bsonType number should match int, long, double, and decimal128",
    ),
    QueryTestCase(
        id="special_missing_field_passes",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": "double"}}}},
        doc=[{"_id": 1, "x": 3.14}, {"_id": 2}],
        expected=[{"_id": 1, "x": 3.14}, {"_id": 2}],
        msg="bsonType should pass when field is missing",
    ),
    QueryTestCase(
        id="special_array_top_level_no_match",
        filter={"$jsonSchema": {"bsonType": "array"}},
        doc=[{"_id": 1, "x": 1}],
        expected=[],
        msg="bsonType array at top level should not match (document is object)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(BSONTYPE_SPECIAL_TESTS))
def test_jsonSchema_bsontype_special(collection, test):
    """Test bsonType special cases."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected)


BSONTYPE_ARRAY_SYNTAX_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="array_syntax_string_or_int",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": ["string", "int"]}}}},
        doc=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": 42}, {"_id": 3, "x": 3.14}],
        expected=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": 42}],
        msg="bsonType array should match either type",
    ),
    QueryTestCase(
        id="array_syntax_null_or_string",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": ["null", "string"]}}}},
        doc=[{"_id": 1, "x": None}, {"_id": 2, "x": "hello"}, {"_id": 3, "x": 42}],
        expected=[{"_id": 1, "x": None}, {"_id": 2, "x": "hello"}],
        msg="bsonType array with null or string should match both",
    ),
    QueryTestCase(
        id="array_syntax_double_or_decimal",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": ["double", "decimal"]}}}},
        doc=[{"_id": 1, "x": 3.14}, {"_id": 2, "x": Decimal128("1.5")}, {"_id": 3, "x": 42}],
        expected=[{"_id": 1, "x": 3.14}, {"_id": 2, "x": Decimal128("1.5")}],
        msg="bsonType array with double or decimal should match both",
    ),
]


@pytest.mark.parametrize("test", pytest_params(BSONTYPE_ARRAY_SYNTAX_TESTS))
def test_jsonSchema_bsontype_array_syntax(collection, test):
    """Test bsonType array syntax matches either type."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected)


BSONTYPE_DISTINCTION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="distinction_bool_not_int_zero",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": "bool"}}}},
        doc=[{"_id": 1, "x": False}, {"_id": 2, "x": 0}],
        expected=[{"_id": 1, "x": False}],
        msg="bsonType bool should NOT match int 0",
    ),
    QueryTestCase(
        id="distinction_int_not_bool_false",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": "int"}}}},
        doc=[{"_id": 1, "x": 0}, {"_id": 2, "x": False}],
        expected=[{"_id": 1, "x": 0}],
        msg="bsonType int should NOT match bool false",
    ),
    QueryTestCase(
        id="distinction_string_not_null",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": "string"}}}},
        doc=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": None}],
        expected=[{"_id": 1, "x": "hello"}],
        msg="bsonType string should NOT match null",
    ),
    QueryTestCase(
        id="distinction_null_not_empty_string",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": "null"}}}},
        doc=[{"_id": 1, "x": None}, {"_id": 2, "x": ""}],
        expected=[{"_id": 1, "x": None}],
        msg="bsonType null should NOT match empty string",
    ),
    QueryTestCase(
        id="distinction_int_not_long",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": "int"}}}},
        doc=[{"_id": 1, "x": 42}, {"_id": 2, "x": Int64(42)}],
        expected=[{"_id": 1, "x": 42}],
        msg="bsonType int should NOT match NumberLong",
    ),
    QueryTestCase(
        id="distinction_long_not_int",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": "long"}}}},
        doc=[{"_id": 1, "x": Int64(42)}, {"_id": 2, "x": 42}],
        expected=[{"_id": 1, "x": Int64(42)}],
        msg="bsonType long should NOT match NumberInt",
    ),
    QueryTestCase(
        id="distinction_double_not_decimal",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": "double"}}}},
        doc=[{"_id": 1, "x": 1.0}, {"_id": 2, "x": Decimal128("1.0")}],
        expected=[{"_id": 1, "x": 1.0}],
        msg="bsonType double should NOT match Decimal128",
    ),
]


@pytest.mark.parametrize("test", pytest_params(BSONTYPE_DISTINCTION_TESTS))
def test_jsonSchema_bsontype_distinction(collection, test):
    """Test BSON type distinction — types are not interchangeable."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected)


TYPE_KEYWORD_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="type_object",
        filter={"$jsonSchema": {"properties": {"x": {"type": "object"}}}},
        doc=[{"_id": 1, "x": {"nested": 1}}, {"_id": 2, "x": [1]}],
        expected=[{"_id": 1, "x": {"nested": 1}}],
        msg="type object should match object values",
    ),
    QueryTestCase(
        id="type_array",
        filter={"$jsonSchema": {"properties": {"x": {"type": "array"}}}},
        doc=[{"_id": 1, "x": [1, 2]}, {"_id": 2, "x": {"a": 1}}],
        expected=[{"_id": 1, "x": [1, 2]}],
        msg="type array should match array values",
    ),
    QueryTestCase(
        id="type_number",
        filter={"$jsonSchema": {"properties": {"x": {"type": "number"}}}},
        doc=[{"_id": 1, "x": 42}, {"_id": 2, "x": "str"}],
        expected=[{"_id": 1, "x": 42}],
        msg="type number should match numeric values",
    ),
    QueryTestCase(
        id="type_boolean",
        filter={"$jsonSchema": {"properties": {"x": {"type": "boolean"}}}},
        doc=[{"_id": 1, "x": True}, {"_id": 2, "x": 0}],
        expected=[{"_id": 1, "x": True}],
        msg="type boolean should match boolean values",
    ),
    QueryTestCase(
        id="type_string",
        filter={"$jsonSchema": {"properties": {"x": {"type": "string"}}}},
        doc=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": 42}],
        expected=[{"_id": 1, "x": "hello"}],
        msg="type string should match string values",
    ),
    QueryTestCase(
        id="type_null",
        filter={"$jsonSchema": {"properties": {"x": {"type": "null"}}}},
        doc=[{"_id": 1, "x": None}, {"_id": 2, "x": 0}],
        expected=[{"_id": 1, "x": None}],
        msg="type null should match null values",
    ),
    QueryTestCase(
        id="type_number_all_numeric",
        filter={"$jsonSchema": {"properties": {"x": {"type": "number"}}}},
        doc=[
            {"_id": 1, "x": 42},
            {"_id": 2, "x": Int64(100)},
            {"_id": 3, "x": 3.14},
            {"_id": 4, "x": Decimal128("1.5")},
            {"_id": 5, "x": "str"},
        ],
        expected=[
            {"_id": 1, "x": 42},
            {"_id": 2, "x": Int64(100)},
            {"_id": 3, "x": 3.14},
            {"_id": 4, "x": Decimal128("1.5")},
        ],
        msg="type number should match int, long, double, decimal128",
    ),
    QueryTestCase(
        id="type_array_string_or_null",
        filter={"$jsonSchema": {"properties": {"x": {"type": ["string", "null"]}}}},
        doc=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": None}, {"_id": 3, "x": 42}],
        expected=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": None}],
        msg="type array should match either type",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TYPE_KEYWORD_TESTS))
def test_jsonSchema_type_keyword(collection, test):
    """Test JSON Schema type keyword matches correct types."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected)
