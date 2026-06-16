"""Tests for the create command validator error behavior."""

import functools
from datetime import datetime, timezone
from typing import Any

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

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    FAILED_TO_PARSE_ERROR,
    INVALID_OPTIONS_ERROR,
    NEAR_NOT_ALLOWED_ERROR,
    OVERFLOW_ERROR,
    REGEX_COMPILE_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_EXPRESSION_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Validator BSON Nesting Limit]: a validator exceeding the BSON
# nesting depth limit produces OVERFLOW_ERROR.
CREATE_VALIDATOR_NESTING_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="validator_101_levels_nesting",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": functools.reduce(
                lambda d, _: {"$and": [d]}, range(100), dict[str, Any]({"x": {"$exists": True}})
            ),
        },
        error_code=OVERFLOW_ERROR,
        msg="101 levels of BSON nesting in validator should fail",
    ),
]

# Property [Validator Type Validation]: non-document types for the
# validator option produce TYPE_MISMATCH_ERROR.
CREATE_VALIDATOR_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id=f"validator_{label}",
        command=lambda ctx, val=val: {
            "create": f"{ctx.collection}_custom",
            "validator": val,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"{label} validator should fail with type mismatch",
    )
    for label, val in [
        ("string", "not_a_doc"),
        ("int", 123),
        ("bool", True),
        ("array", [{"x": 1}]),
        ("double", 3.14),
        ("int64", Int64(42)),
        ("decimal128", Decimal128("1")),
        ("binary", Binary(b"hello")),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("regex", Regex("test")),
        ("code", Code("function(){}")),
        ("code_with_scope", Code("function(){}", {"x": 1})),
        ("timestamp", Timestamp(0, 0)),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Validator Disallowed Operators]: operators not permitted in
# validators produce errors.
CREATE_VALIDATOR_DISALLOWED_OPERATOR_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="validator_where",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {"$where": "true"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="$where in validator should fail",
    ),
    CommandTestCase(
        id="validator_text",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {"$text": {"$search": "hello"}},
        },
        error_code=BAD_VALUE_ERROR,
        msg="$text in validator should fail",
    ),
    CommandTestCase(
        id="validator_near",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {"loc": {"$near": [0, 0]}},
        },
        error_code=NEAR_NOT_ALLOWED_ERROR,
        msg="$near in validator should fail",
    ),
    CommandTestCase(
        id="validator_near_sphere",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {"loc": {"$nearSphere": [0, 0]}},
        },
        error_code=NEAR_NOT_ALLOWED_ERROR,
        msg="$nearSphere in validator should fail",
    ),
    CommandTestCase(
        id="validator_unknown_operator",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {"$badOp": 1},
        },
        error_code=BAD_VALUE_ERROR,
        msg="Unknown operator in validator should fail",
    ),
    CommandTestCase(
        id="validator_unknown_agg_op_in_expr",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {"$expr": {"$badAggOp": 1}},
        },
        error_code=UNRECOGNIZED_EXPRESSION_ERROR,
        msg="Unknown aggregation op in $expr should fail",
    ),
]

# Property [Validator Database Restriction]: validators on admin, local,
# and config databases produce INVALID_OPTIONS_ERROR; validators on
# system.* collections produce INVALID_OPTIONS_ERROR.
CREATE_VALIDATOR_DATABASE_RESTRICTION_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="validator_system_collection",
        command={"create": "system.js", "validator": {"x": {"$exists": True}}},
        error_code=INVALID_OPTIONS_ERROR,
        msg="Validator on allowed system.* collection should fail",
    ),
]

# Property [Validator $jsonSchema Errors]: unknown keywords, 'integer'
# type, and both 'type' and 'bsonType' in $jsonSchema produce
# FAILED_TO_PARSE_ERROR.
CREATE_VALIDATOR_JSON_SCHEMA_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="validator_json_schema_unknown_keyword",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {"$jsonSchema": {"unknownKeyword": True}},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$jsonSchema unknown keyword should fail",
    ),
    CommandTestCase(
        id="validator_json_schema_integer_type",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {"$jsonSchema": {"properties": {"x": {"type": "integer"}}}},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$jsonSchema 'integer' type should fail",
    ),
    CommandTestCase(
        id="validator_json_schema_type_and_bson_type",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {
                "$jsonSchema": {"properties": {"x": {"type": "string", "bsonType": "string"}}}
            },
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$jsonSchema with both 'type' and 'bsonType' should fail",
    ),
]

# Property [Validator Regex Pattern Limit]: a regex pattern exceeding
# 16384 bytes in the validator produces REGEX_COMPILE_ERROR.
CREATE_VALIDATOR_REGEX_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="validator_regex_pattern_too_long",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {"x": {"$regex": "a" * 16_385}},
        },
        error_code=REGEX_COMPILE_ERROR,
        msg="Regex pattern > 16384 bytes in validator should fail",
    ),
]

CREATE_VALIDATOR_ERROR_TESTS: list[CommandTestCase] = (
    CREATE_VALIDATOR_NESTING_ERROR_TESTS
    + CREATE_VALIDATOR_TYPE_ERROR_TESTS
    + CREATE_VALIDATOR_DISALLOWED_OPERATOR_ERROR_TESTS
    + CREATE_VALIDATOR_DATABASE_RESTRICTION_ERROR_TESTS
    + CREATE_VALIDATOR_JSON_SCHEMA_ERROR_TESTS
    + CREATE_VALIDATOR_REGEX_ERROR_TESTS
)

# Property [ValidationLevel Type Strictness]: non-string types for
# validationLevel or validationAction produce TYPE_MISMATCH_ERROR.
CREATE_VALIDATION_LEVEL_ACTION_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id=f"{field_id}_{label}",
        command=lambda ctx, field=field_key, val=val: {
            "create": f"{ctx.collection}_custom",
            field: val,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"{label} {field_key} should fail with type mismatch",
    )
    for field_id, field_key in [
        ("validation_level", "validationLevel"),
        ("validation_action", "validationAction"),
    ]
    for label, val in [
        ("int", 1),
        ("int64", Int64(1)),
        ("double", 1.0),
        ("decimal128", Decimal128("1")),
        ("bool", True),
        ("array", ["strict"]),
        ("object", {"level": "strict"}),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("binary", Binary(b"x")),
        ("regex", Regex("x")),
        ("code", Code("f()")),
        ("code_with_scope", Code("f()", {"x": 1})),
        ("timestamp", Timestamp(0, 0)),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [ValidationLevel Enum Validation]: invalid enum values for
# validationLevel or validationAction produce BAD_VALUE_ERROR; valid
# values are case-sensitive.
CREATE_VALIDATION_LEVEL_ACTION_ENUM_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="validation_level_invalid_string",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validationLevel": "invalid",
        },
        error_code=BAD_VALUE_ERROR,
        msg="Invalid validationLevel string should fail",
    ),
    CommandTestCase(
        id="validation_level_uppercase_off",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validationLevel": "Off",
        },
        error_code=BAD_VALUE_ERROR,
        msg="Uppercase 'Off' is not a valid validationLevel (case-sensitive)",
    ),
    CommandTestCase(
        id="validation_level_uppercase_strict",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validationLevel": "Strict",
        },
        error_code=BAD_VALUE_ERROR,
        msg="Uppercase 'Strict' is not a valid validationLevel (case-sensitive)",
    ),
    CommandTestCase(
        id="validation_level_all_caps",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validationLevel": "MODERATE",
        },
        error_code=BAD_VALUE_ERROR,
        msg="All-caps 'MODERATE' is not a valid validationLevel (case-sensitive)",
    ),
    CommandTestCase(
        id="validation_level_empty_string",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validationLevel": "",
        },
        error_code=BAD_VALUE_ERROR,
        msg="Empty string is not a valid validationLevel",
    ),
    CommandTestCase(
        id="validation_action_invalid_string",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validationAction": "invalid",
        },
        error_code=BAD_VALUE_ERROR,
        msg="Invalid validationAction string should fail",
    ),
    CommandTestCase(
        id="validation_action_uppercase_error",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validationAction": "Error",
        },
        error_code=BAD_VALUE_ERROR,
        msg="Uppercase 'Error' is not a valid validationAction (case-sensitive)",
    ),
    CommandTestCase(
        id="validation_action_uppercase_warn",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validationAction": "Warn",
        },
        error_code=BAD_VALUE_ERROR,
        msg="Uppercase 'Warn' is not a valid validationAction (case-sensitive)",
    ),
    CommandTestCase(
        id="validation_action_all_caps",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validationAction": "WARN",
        },
        error_code=BAD_VALUE_ERROR,
        msg="All-caps 'WARN' is not a valid validationAction (case-sensitive)",
    ),
    CommandTestCase(
        id="validation_action_empty_string",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validationAction": "",
        },
        error_code=BAD_VALUE_ERROR,
        msg="Empty string is not a valid validationAction",
    ),
]

CREATE_VALIDATION_LEVEL_ACTION_ERROR_TESTS: list[CommandTestCase] = (
    CREATE_VALIDATION_LEVEL_ACTION_TYPE_ERROR_TESTS
    + CREATE_VALIDATION_LEVEL_ACTION_ENUM_ERROR_TESTS
)

CREATE_VALIDATOR_ERROR_ALL_TESTS: list[CommandTestCase] = (
    CREATE_VALIDATOR_ERROR_TESTS + CREATE_VALIDATION_LEVEL_ACTION_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(CREATE_VALIDATOR_ERROR_ALL_TESTS))
def test_create_validator_errors(database_client, collection, test):
    """Test create command validator error behavior."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
