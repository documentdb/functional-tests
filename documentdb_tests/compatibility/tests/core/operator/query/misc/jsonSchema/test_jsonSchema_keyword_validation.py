"""
Tests for $jsonSchema keyword value validation.

Verifies that each $jsonSchema keyword rejects invalid BSON types for its value
with expected error codes and accepts valid BSON types without error. Each keyword
is tested at both root level and nested inside properties.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertNotError
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import FAILED_TO_PARSE_ERROR
from documentdb_tests.framework.executor import execute_command

JSONSCHEMA_PARAMS = [
    BsonTypeTestCase(
        id="required",
        msg="required should reject non-array types",
        keyword="required",
        valid_types=[BsonType.ARRAY],
        valid_inputs={BsonType.ARRAY: ["x"]},
    ),
    BsonTypeTestCase(
        id="properties",
        msg="properties should reject non-object types",
        keyword="properties",
        valid_types=[BsonType.OBJECT],
        valid_inputs={BsonType.OBJECT: {"x": {}}},
    ),
    BsonTypeTestCase(
        id="additionalProperties",
        msg="additionalProperties should reject non-bool/object types",
        keyword="additionalProperties",
        valid_types=[BsonType.BOOL, BsonType.OBJECT],
        valid_inputs={BsonType.OBJECT: {"bsonType": "string"}},
    ),
    BsonTypeTestCase(
        id="bsonType",
        msg="bsonType should reject non-string/array types",
        keyword="bsonType",
        valid_types=[BsonType.STRING, BsonType.ARRAY],
        valid_inputs={BsonType.STRING: "object", BsonType.ARRAY: ["string", "int"]},
    ),
    BsonTypeTestCase(
        id="type",
        msg="type should reject non-string/array types",
        keyword="type",
        valid_types=[BsonType.STRING, BsonType.ARRAY],
        valid_inputs={BsonType.STRING: "object", BsonType.ARRAY: ["string", "number"]},
    ),
    BsonTypeTestCase(
        id="enum",
        msg="enum should reject non-array types",
        keyword="enum",
        valid_types=[BsonType.ARRAY],
        valid_inputs={BsonType.ARRAY: [1, 2, 3]},
    ),
    BsonTypeTestCase(
        id="title",
        msg="title should reject non-string types",
        keyword="title",
        valid_types=[BsonType.STRING],
    ),
    BsonTypeTestCase(
        id="description",
        msg="description should reject non-string types",
        keyword="description",
        valid_types=[BsonType.STRING],
    ),
    BsonTypeTestCase(
        id="minimum",
        msg="minimum should reject non-numeric types",
        keyword="minimum",
        valid_types=[BsonType.DOUBLE, BsonType.INT, BsonType.LONG, BsonType.DECIMAL],
    ),
    BsonTypeTestCase(
        id="maximum",
        msg="maximum should reject non-numeric types",
        keyword="maximum",
        valid_types=[BsonType.DOUBLE, BsonType.INT, BsonType.LONG, BsonType.DECIMAL],
    ),
    BsonTypeTestCase(
        id="exclusiveMinimum",
        msg="exclusiveMinimum should reject non-bool types",
        keyword="exclusiveMinimum",
        valid_types=[BsonType.BOOL],
        requires={"minimum": 0},
    ),
    BsonTypeTestCase(
        id="exclusiveMaximum",
        msg="exclusiveMaximum should reject non-bool types",
        keyword="exclusiveMaximum",
        valid_types=[BsonType.BOOL],
        requires={"maximum": 100},
    ),
    BsonTypeTestCase(
        id="minLength",
        msg="minLength should reject non-integer types",
        keyword="minLength",
        valid_types=[BsonType.INT, BsonType.LONG],
        default_error_code=FAILED_TO_PARSE_ERROR,
    ),
    BsonTypeTestCase(
        id="maxLength",
        msg="maxLength should reject non-integer types",
        keyword="maxLength",
        valid_types=[BsonType.INT, BsonType.LONG],
        default_error_code=FAILED_TO_PARSE_ERROR,
    ),
    BsonTypeTestCase(
        id="pattern",
        msg="pattern should reject non-string types",
        keyword="pattern",
        valid_types=[BsonType.STRING],
    ),
    BsonTypeTestCase(
        id="minItems",
        msg="minItems should reject non-integer types",
        keyword="minItems",
        valid_types=[BsonType.INT, BsonType.LONG],
        default_error_code=FAILED_TO_PARSE_ERROR,
    ),
    BsonTypeTestCase(
        id="maxItems",
        msg="maxItems should reject non-integer types",
        keyword="maxItems",
        valid_types=[BsonType.INT, BsonType.LONG],
        default_error_code=FAILED_TO_PARSE_ERROR,
    ),
    BsonTypeTestCase(
        id="uniqueItems",
        msg="uniqueItems should reject non-bool types",
        keyword="uniqueItems",
        valid_types=[BsonType.BOOL],
    ),
    BsonTypeTestCase(
        id="items",
        msg="items should reject non-object/array types",
        keyword="items",
        valid_types=[BsonType.OBJECT, BsonType.ARRAY],
        valid_inputs={BsonType.OBJECT: {"bsonType": "string"}, BsonType.ARRAY: [{}]},
    ),
    BsonTypeTestCase(
        id="minProperties",
        msg="minProperties should reject non-integer types",
        keyword="minProperties",
        valid_types=[BsonType.INT, BsonType.LONG],
        default_error_code=FAILED_TO_PARSE_ERROR,
    ),
    BsonTypeTestCase(
        id="maxProperties",
        msg="maxProperties should reject non-integer types",
        keyword="maxProperties",
        valid_types=[BsonType.INT, BsonType.LONG],
        default_error_code=FAILED_TO_PARSE_ERROR,
    ),
    BsonTypeTestCase(
        id="allOf",
        msg="allOf should reject non-array types",
        keyword="allOf",
        valid_types=[BsonType.ARRAY],
        valid_inputs={BsonType.ARRAY: [{}]},
    ),
    BsonTypeTestCase(
        id="anyOf",
        msg="anyOf should reject non-array types",
        keyword="anyOf",
        valid_types=[BsonType.ARRAY],
        valid_inputs={BsonType.ARRAY: [{}]},
    ),
    BsonTypeTestCase(
        id="oneOf",
        msg="oneOf should reject non-array types",
        keyword="oneOf",
        valid_types=[BsonType.ARRAY],
        valid_inputs={BsonType.ARRAY: [{}]},
    ),
    BsonTypeTestCase(
        id="not",
        msg="not should reject non-object types",
        keyword="not",
        valid_types=[BsonType.OBJECT],
        valid_inputs={BsonType.OBJECT: {"bsonType": "string"}},
    ),
    BsonTypeTestCase(
        id="dependencies",
        msg="dependencies should reject non-object types",
        keyword="dependencies",
        valid_types=[BsonType.OBJECT],
        valid_inputs={BsonType.OBJECT: {"x": ["y"]}},
    ),
    BsonTypeTestCase(
        id="patternProperties",
        msg="patternProperties should reject non-object types",
        keyword="patternProperties",
        valid_types=[BsonType.OBJECT],
        valid_inputs={BsonType.OBJECT: {"^x": {}}},
    ),
    BsonTypeTestCase(
        id="multipleOf",
        msg="multipleOf should reject non-numeric types",
        keyword="multipleOf",
        valid_types=[BsonType.DOUBLE, BsonType.INT, BsonType.LONG, BsonType.DECIMAL],
    ),
    BsonTypeTestCase(
        id="additionalItems",
        msg="additionalItems should reject non-bool/object types",
        keyword="additionalItems",
        valid_types=[BsonType.BOOL, BsonType.OBJECT],
        valid_inputs={BsonType.OBJECT: {"bsonType": "string"}},
    ),
]

TEST_CASES = generate_bson_rejection_test_cases(JSONSCHEMA_PARAMS)


@pytest.mark.parametrize(
    "bson_type,sample_value,spec",
    TEST_CASES,
)
def test_jsonschema_bson_type_root(collection, bson_type, sample_value, spec):
    """Test $jsonSchema rejects invalid BSON types at root level."""
    schema = {spec.keyword: sample_value, **(spec.requires or {})}
    result = execute_command(
        collection, {"find": collection.name, "filter": {"$jsonSchema": schema}}
    )
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


@pytest.mark.parametrize(
    "bson_type,sample_value,spec",
    TEST_CASES,
)
def test_jsonschema_bson_type_nested(collection, bson_type, sample_value, spec):
    """Test $jsonSchema rejects invalid BSON types nested in properties."""
    schema = {"properties": {"x": {spec.keyword: sample_value, **(spec.requires or {})}}}
    result = execute_command(
        collection, {"find": collection.name, "filter": {"$jsonSchema": schema}}
    )
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(JSONSCHEMA_PARAMS)


@pytest.mark.parametrize(
    "bson_type,sample_value,spec",
    ACCEPTANCE_CASES,
)
def test_jsonschema_bson_type_accepted_root(collection, bson_type, sample_value, spec):
    """Test $jsonSchema accepts valid BSON types at root level."""
    schema = {spec.keyword: sample_value, **(spec.requires or {})}
    result = execute_command(
        collection, {"find": collection.name, "filter": {"$jsonSchema": schema}}
    )
    assertNotError(result, msg=f"{spec.keyword} should accept {bson_type.value} at root")


@pytest.mark.parametrize(
    "bson_type,sample_value,spec",
    ACCEPTANCE_CASES,
)
def test_jsonschema_bson_type_accepted_nested(collection, bson_type, sample_value, spec):
    """Test $jsonSchema accepts valid BSON types nested in properties."""
    schema = {"properties": {"x": {spec.keyword: sample_value, **(spec.requires or {})}}}
    result = execute_command(
        collection, {"find": collection.name, "filter": {"$jsonSchema": schema}}
    )
    assertNotError(result, msg=f"{spec.keyword} should accept {bson_type.value} nested")
