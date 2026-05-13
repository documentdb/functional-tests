"""
Tests for $jsonSchema object validation keywords.

Validates required, properties, additionalProperties, minProperties, maxProperties,
dependencies, patternProperties, null/missing handling, nested schemas, and field name edge cases.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

OBJECT_VALIDATION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="required_matches",
        filter={"$jsonSchema": {"required": ["a", "b"]}},
        doc=[{"_id": 1, "a": 1, "b": 2}, {"_id": 2, "a": 1}],
        expected=[{"_id": 1, "a": 1, "b": 2}],
        msg="required should match documents with all required fields",
    ),
    QueryTestCase(
        id="required_null_field_matches",
        filter={"$jsonSchema": {"required": ["a"]}},
        doc=[{"_id": 1, "a": None}, {"_id": 2}],
        expected=[{"_id": 1, "a": None}],
        msg="required on field with null value should match",
    ),
    QueryTestCase(
        id="properties_validates_type",
        filter={"$jsonSchema": {"properties": {"a": {"bsonType": "string"}}}},
        doc=[{"_id": 1, "a": "hello"}, {"_id": 2, "a": 42}],
        expected=[{"_id": 1, "a": "hello"}],
        msg="properties should validate bsonType of specified fields",
    ),
    QueryTestCase(
        id="properties_missing_field_passes",
        filter={"$jsonSchema": {"properties": {"a": {"bsonType": "string"}}}},
        doc=[{"_id": 1, "a": "hello"}, {"_id": 2, "b": 42}],
        expected=[{"_id": 1, "a": "hello"}, {"_id": 2, "b": 42}],
        msg="properties on non-existent field should pass",
    ),
    QueryTestCase(
        id="properties_null_field_type_check",
        filter={"$jsonSchema": {"properties": {"a": {"bsonType": "null"}}}},
        doc=[{"_id": 1, "a": None}, {"_id": 2, "a": "hello"}],
        expected=[{"_id": 1, "a": None}],
        msg="properties bsonType null should match null field",
    ),
    QueryTestCase(
        id="properties_nested",
        filter={
            "$jsonSchema": {"properties": {"addr": {"properties": {"zip": {"bsonType": "string"}}}}}
        },
        doc=[{"_id": 1, "addr": {"zip": "12345"}}, {"_id": 2, "addr": {"zip": 12345}}],
        expected=[{"_id": 1, "addr": {"zip": "12345"}}],
        msg="Nested properties should validate nested object fields",
    ),
    QueryTestCase(
        id="properties_non_object_field_passes",
        filter={
            "$jsonSchema": {"properties": {"addr": {"properties": {"zip": {"bsonType": "string"}}}}}
        },
        doc=[{"_id": 1, "addr": "not_object"}, {"_id": 2, "addr": {"zip": "12345"}}],
        expected=[{"_id": 1, "addr": "not_object"}, {"_id": 2, "addr": {"zip": "12345"}}],
        msg="properties should not apply when field is not an object",
    ),
    QueryTestCase(
        id="additionalProperties_false",
        filter={"$jsonSchema": {"properties": {"_id": {}, "a": {}}, "additionalProperties": False}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 1, "b": 2}],
        expected=[{"_id": 1, "a": 1}],
        msg="additionalProperties false should reject extra fields",
    ),
    QueryTestCase(
        id="additionalProperties_schema",
        filter={
            "$jsonSchema": {
                "properties": {"_id": {}, "a": {}},
                "additionalProperties": {"bsonType": "int"},
            }
        },
        doc=[{"_id": 1, "a": 1, "b": 2}, {"_id": 2, "a": 1, "b": "str"}],
        expected=[{"_id": 1, "a": 1, "b": 2}],
        msg="additionalProperties as schema should validate extra fields",
    ),
    QueryTestCase(
        id="minProperties_matches",
        filter={"$jsonSchema": {"minProperties": 3}},
        doc=[{"_id": 1, "a": 1, "b": 2}, {"_id": 2, "a": 1}],
        expected=[{"_id": 1, "a": 1, "b": 2}],
        msg="minProperties should match documents with enough properties",
    ),
    QueryTestCase(
        id="maxProperties_matches",
        filter={"$jsonSchema": {"maxProperties": 2}},
        doc=[{"_id": 1, "a": 1, "b": 2}, {"_id": 2, "a": 1}],
        expected=[{"_id": 2, "a": 1}],
        msg="maxProperties should match documents within property limit",
    ),
    QueryTestCase(
        id="dependencies_property",
        filter={"$jsonSchema": {"dependencies": {"a": ["b"]}}},
        doc=[{"_id": 1, "a": 1, "b": 2}, {"_id": 2, "a": 1}, {"_id": 3, "c": 1}],
        expected=[{"_id": 1, "a": 1, "b": 2}, {"_id": 3, "c": 1}],
        msg="Property dependency — if a exists, b must exist",
    ),
    QueryTestCase(
        id="dependencies_absent_passes",
        filter={"$jsonSchema": {"dependencies": {"a": ["b"]}}},
        doc=[{"_id": 1, "b": 2}, {"_id": 2, "a": 1}],
        expected=[{"_id": 1, "b": 2}],
        msg="Dependency should pass when dependent field is absent",
    ),
    QueryTestCase(
        id="dependencies_schema",
        filter={"$jsonSchema": {"dependencies": {"a": {"properties": {"b": {"minimum": 0}}}}}},
        doc=[{"_id": 1, "a": 1, "b": 5}, {"_id": 2, "a": 1, "b": -1}, {"_id": 3, "c": 1}],
        expected=[{"_id": 1, "a": 1, "b": 5}, {"_id": 3, "c": 1}],
        msg="Schema dependency — if a exists, schema must be satisfied",
    ),
    QueryTestCase(
        id="patternProperties_matches",
        filter={"$jsonSchema": {"patternProperties": {"^S_": {"bsonType": "string"}}}},
        doc=[
            {"_id": 1, "S_name": "hello", "S_age": "young"},
            {"_id": 2, "S_name": 42, "other": "val"},
        ],
        expected=[{"_id": 1, "S_name": "hello", "S_age": "young"}],
        msg="patternProperties should validate fields matching regex pattern",
    ),
    QueryTestCase(
        id="patternProperties_combined_with_properties",
        filter={
            "$jsonSchema": {
                "properties": {"name": {"bsonType": "string"}},
                "patternProperties": {"^S_": {"bsonType": "string"}},
            }
        },
        doc=[{"_id": 1, "name": "hello", "S_val": "x"}, {"_id": 2, "name": 42, "S_val": "x"}],
        expected=[{"_id": 1, "name": "hello", "S_val": "x"}],
        msg="patternProperties combined with properties — both must be satisfied",
    ),
    QueryTestCase(
        id="deep_nested_properties",
        filter={
            "$jsonSchema": {
                "properties": {
                    "a": {"properties": {"b": {"properties": {"c": {"bsonType": "string"}}}}}
                }
            }
        },
        doc=[{"_id": 1, "a": {"b": {"c": "hello"}}}, {"_id": 2, "a": {"b": {"c": 42}}}],
        expected=[{"_id": 1, "a": {"b": {"c": "hello"}}}],
        msg="3 levels deep nested properties should work",
    ),
    QueryTestCase(
        id="items_array_of_objects",
        filter={
            "$jsonSchema": {
                "properties": {"arr": {"items": {"properties": {"name": {"bsonType": "string"}}}}}
            }
        },
        doc=[{"_id": 1, "arr": [{"name": "a"}, {"name": "b"}]}, {"_id": 2, "arr": [{"name": 1}]}],
        expected=[{"_id": 1, "arr": [{"name": "a"}, {"name": "b"}]}],
        msg="items should validate objects within array",
    ),
    QueryTestCase(
        id="items_array_of_arrays",
        filter={"$jsonSchema": {"properties": {"matrix": {"items": {"bsonType": "array"}}}}},
        doc=[{"_id": 1, "matrix": [[1, 2], [3, 4]]}, {"_id": 2, "matrix": [[1, 2], "not_array"]}],
        expected=[{"_id": 1, "matrix": [[1, 2], [3, 4]]}],
        msg="items should validate arrays within array",
    ),
    QueryTestCase(
        id="empty_field_name_in_required",
        filter={"$jsonSchema": {"required": [""]}},
        doc=[{"_id": 1, "": "val"}, {"_id": 2, "a": 1}],
        expected=[{"_id": 1, "": "val"}],
        msg="required with empty string field name should work",
    ),
    QueryTestCase(
        id="empty_field_name_in_properties",
        filter={"$jsonSchema": {"properties": {"": {"bsonType": "string"}}}},
        doc=[{"_id": 1, "": "val"}, {"_id": 2, "": 42}],
        expected=[{"_id": 1, "": "val"}],
        msg="properties with empty string field name should validate bsonType",
    ),
    QueryTestCase(
        id="required_dollar_prefixed_field",
        filter={"$jsonSchema": {"required": ["$field"]}},
        doc=[{"_id": 1, "$field": "val"}, {"_id": 2, "a": 1}],
        expected=[{"_id": 1, "$field": "val"}],
        msg="required with dollar-prefixed field name should match",
    ),
    QueryTestCase(
        id="properties_dollar_prefixed_field",
        filter={"$jsonSchema": {"properties": {"$field": {"bsonType": "string"}}}},
        doc=[{"_id": 1, "$field": "val"}, {"_id": 2, "$field": 42}],
        expected=[{"_id": 1, "$field": "val"}],
        msg="properties with dollar-prefixed field should validate bsonType",
    ),
]


@pytest.mark.parametrize("test", pytest_params(OBJECT_VALIDATION_TESTS))
def test_jsonSchema_object_validation(collection, test):
    """Test $jsonSchema object validation keywords."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected)
