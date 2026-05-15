"""
Tests for $jsonSchema error handling.

Verifies that $jsonSchema rejects invalid argument types, unsupported keywords,
invalid schema constructs (negative values, empty arrays, duplicates, invalid regex,
invalid bsonType/type values), and invalid schemas in other commands.
Wrong-type errors are covered by test_jsonSchema_keyword_validation.py.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    FAILED_TO_PARSE_ERROR,
    REGEX_COMPILE_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

INVALID_ARGUMENT_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="arg_string",
        filter={"$jsonSchema": "invalid"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="String argument should error",
    ),
    QueryTestCase(
        id="arg_int",
        filter={"$jsonSchema": 1},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Int argument should error",
    ),
    QueryTestCase(
        id="arg_array",
        filter={"$jsonSchema": [1, 2]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Array argument should error",
    ),
    QueryTestCase(
        id="arg_null",
        filter={"$jsonSchema": None},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Null argument should error",
    ),
    QueryTestCase(
        id="arg_bool",
        filter={"$jsonSchema": True},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Bool argument should error",
    ),
]

UNSUPPORTED_KEYWORD_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="unsupported_ref",
        filter={"$jsonSchema": {"properties": {"a": {"$ref": "#/defs/x"}}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$ref keyword should error",
    ),
    QueryTestCase(
        id="unsupported_schema",
        filter={"$jsonSchema": {"$schema": "http://json-schema.org/draft-04/schema#"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$schema keyword should error",
    ),
    QueryTestCase(
        id="unsupported_default",
        filter={"$jsonSchema": {"properties": {"a": {"default": 0}}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="default keyword should error",
    ),
    QueryTestCase(
        id="unsupported_definitions",
        filter={"$jsonSchema": {"definitions": {"x": {"bsonType": "int"}}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="definitions keyword should error",
    ),
    QueryTestCase(
        id="unsupported_format",
        filter={"$jsonSchema": {"properties": {"a": {"format": "email"}}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="format keyword should error",
    ),
    QueryTestCase(
        id="unsupported_id",
        filter={"$jsonSchema": {"id": "myschema"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="id keyword should error",
    ),
    QueryTestCase(
        id="unsupported_unknown",
        filter={"$jsonSchema": {"unknownKeyword": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Unknown keyword should error",
    ),
]

INVALID_SCHEMA_CONSTRUCT_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="construct_required_non_string_elements",
        filter={"$jsonSchema": {"required": [1]}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="required with non-string elements should error",
    ),
    QueryTestCase(
        id="construct_required_duplicate_values",
        filter={"$jsonSchema": {"required": ["a", "a"]}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="required with duplicate values should error",
    ),
    QueryTestCase(
        id="construct_maxLength_negative",
        filter={"$jsonSchema": {"properties": {"x": {"maxLength": -1}}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="maxLength with negative value should error",
    ),
    QueryTestCase(
        id="construct_minLength_negative",
        filter={"$jsonSchema": {"properties": {"x": {"minLength": -1}}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="minLength with negative value should error",
    ),
    QueryTestCase(
        id="construct_pattern_invalid_regex",
        filter={"$jsonSchema": {"properties": {"x": {"pattern": "[invalid"}}}},
        error_code=REGEX_COMPILE_ERROR,
        msg="pattern with invalid regex should error",
    ),
    QueryTestCase(
        id="construct_allOf_non_object_element",
        filter={"$jsonSchema": {"allOf": [1]}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="allOf with non-object element should error",
    ),
    QueryTestCase(
        id="construct_anyOf_non_object_element",
        filter={"$jsonSchema": {"anyOf": ["str"]}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="anyOf with non-object element should error",
    ),
    QueryTestCase(
        id="construct_oneOf_non_object_element",
        filter={"$jsonSchema": {"oneOf": [None]}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="oneOf with non-object element should error",
    ),
    QueryTestCase(
        id="construct_minItems_negative",
        filter={"$jsonSchema": {"properties": {"x": {"minItems": -1}}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="minItems with negative value should error",
    ),
    QueryTestCase(
        id="construct_maxItems_negative",
        filter={"$jsonSchema": {"properties": {"x": {"maxItems": -1}}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="maxItems with negative value should error",
    ),
    QueryTestCase(
        id="construct_multipleOf_zero",
        filter={"$jsonSchema": {"properties": {"x": {"multipleOf": 0}}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="multipleOf with zero should error",
    ),
    QueryTestCase(
        id="construct_multipleOf_negative",
        filter={"$jsonSchema": {"properties": {"x": {"multipleOf": -3}}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="multipleOf with negative should error",
    ),
    QueryTestCase(
        id="construct_invalid_bsontype",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": "invalid"}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Invalid bsonType string should error",
    ),
    QueryTestCase(
        id="construct_invalid_bsontype_in_array",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": ["invalid"]}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Invalid bsonType in array form should error",
    ),
    QueryTestCase(
        id="construct_bsontype_invalid_alias_integer",
        filter={"$jsonSchema": {"properties": {"x": {"bsonType": "integer"}}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="bsonType 'integer' is not a valid alias",
    ),
    QueryTestCase(
        id="construct_invalid_type_string",
        filter={"$jsonSchema": {"properties": {"x": {"type": "invalid"}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Invalid type string should error",
    ),
    QueryTestCase(
        id="construct_invalid_type_in_array",
        filter={"$jsonSchema": {"properties": {"x": {"type": ["invalid"]}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Invalid type in array form should error",
    ),
    QueryTestCase(
        id="construct_dependencies_non_string_in_array",
        filter={"$jsonSchema": {"dependencies": {"a": [1]}}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="dependencies array with non-string element should error",
    ),
    QueryTestCase(
        id="construct_dependencies_empty_array",
        filter={"$jsonSchema": {"dependencies": {"a": []}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="dependencies with empty array should error",
    ),
    QueryTestCase(
        id="construct_patternProperties_invalid_regex_key",
        filter={"$jsonSchema": {"patternProperties": {"[invalid": {}}}},
        error_code=BAD_VALUE_ERROR,
        msg="patternProperties with invalid regex key should error",
    ),
    QueryTestCase(
        id="construct_items_non_object_in_array",
        filter={"$jsonSchema": {"properties": {"x": {"items": [1]}}}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="items tuple form with non-object element should error",
    ),
    QueryTestCase(
        id="construct_minProperties_negative",
        filter={"$jsonSchema": {"minProperties": -1}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="minProperties with negative should error",
    ),
    QueryTestCase(
        id="construct_maxProperties_negative",
        filter={"$jsonSchema": {"maxProperties": -1}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="maxProperties with negative should error",
    ),
]

TYPE_INVALID_BSON_ONLY = [
    "double",
    "binData",
    "objectId",
    "date",
    "regex",
    "javascript",
    "int",
    "timestamp",
    "long",
    "decimal",
]

INVALID_SCHEMA_CONSTRUCT_TESTS += [
    QueryTestCase(
        id=f"construct_type_bson_only_{t}",
        filter={"$jsonSchema": {"properties": {"x": {"type": t}}}},
        error_code=BAD_VALUE_ERROR,
        msg=f"type keyword should reject BSON-only alias '{t}'",
    )
    for t in TYPE_INVALID_BSON_ONLY
]

ALL_ERROR_TESTS = (
    INVALID_ARGUMENT_TESTS + UNSUPPORTED_KEYWORD_TESTS + INVALID_SCHEMA_CONSTRUCT_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_ERROR_TESTS))
def test_jsonSchema_errors(collection, test):
    """Test $jsonSchema rejects invalid inputs with correct error codes."""
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertFailureCode(result, test.error_code)


INVALID_SCHEMA_COMMAND_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="command_invalid_in_count",
        filter={"$jsonSchema": {"invalid_keyword": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Invalid $jsonSchema should fail in count command",
    ),
    QueryTestCase(
        id="command_invalid_in_distinct",
        filter={"$jsonSchema": {"invalid_keyword": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Invalid $jsonSchema should fail in distinct command",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_SCHEMA_COMMAND_TESTS))
def test_jsonSchema_invalid_schema_in_commands(collection, test):
    """Test invalid $jsonSchema fails in count and distinct commands."""
    if "count" in test.id:
        result = execute_command(collection, {"count": collection.name, "query": test.filter})
    else:
        result = execute_command(
            collection, {"distinct": collection.name, "key": "x", "query": test.filter}
        )
    assertFailureCode(result, test.error_code)
