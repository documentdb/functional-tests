"""Tests for collMod validator."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

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
    REGEX_COMPILE_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_EXPRESSION_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.target_collection import (
    ExistingDatabase,
    SystemViewsCollection,
    TimeseriesCollection,
    ValidatedCollection,
    ViewCollection,
)
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
    REGEX_PATTERN_LIMIT_BYTES,
)

# Property [validator Success]: a validator value that is an object (including
# the empty document) or null (treated as omitted) is accepted, and any object
# expressing a well-formed match query, a valid $expr, or a valid $jsonSchema is
# accepted as a collection validator.
COLLMOD_VALIDATOR_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "empty_document",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {"collMod": ctx.collection, "validator": {}},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept an empty document validator",
    ),
    CommandTestCase(
        "null",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {"collMod": ctx.collection, "validator": None},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a null validator as an omitted field",
    ),
    CommandTestCase(
        "field_equality_query",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {"collMod": ctx.collection, "validator": {"a": 1}},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a simple field-equality query validator",
    ),
    CommandTestCase(
        "dotted_path_query",
        docs=[{"_id": 1, "a": {"b": 1}}],
        command=lambda ctx: {"collMod": ctx.collection, "validator": {"a.b": {"$exists": True}}},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a dotted-path query validator",
    ),
    CommandTestCase(
        "type_operator",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {"collMod": ctx.collection, "validator": {"a": {"$type": "int"}}},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a $type operator in a validator",
    ),
    CommandTestCase(
        "mod_operator",
        docs=[{"_id": 1, "a": 4}],
        command=lambda ctx: {"collMod": ctx.collection, "validator": {"a": {"$mod": [2, 0]}}},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a $mod operator in a validator",
    ),
    CommandTestCase(
        "large_string_value",
        docs=[{"_id": 1}],
        command=lambda ctx: {"collMod": ctx.collection, "validator": {"a": "x" * 10_000}},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a validator carrying a large string value",
    ),
    CommandTestCase(
        "expr_bare_true",
        docs=[{"_id": 1}],
        command=lambda ctx: {"collMod": ctx.collection, "validator": {"$expr": True}},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a bare $expr: true validator",
    ),
    CommandTestCase(
        "expr_comparison",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "validator": {"$expr": {"$gt": ["$a", 0]}},
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a $expr comparison validator",
    ),
    CommandTestCase(
        "expr_root_variable",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "validator": {"$expr": {"$eq": ["$$ROOT.a", "$a"]}},
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a $expr validator referencing the $$ROOT variable",
    ),
    CommandTestCase(
        "expr_now_variable",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "validator": {"$expr": {"$lte": ["$created", "$$NOW"]}},
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a $expr validator referencing the $$NOW variable",
    ),
    CommandTestCase(
        "json_schema_valid_bson_type",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "validator": {"$jsonSchema": {"properties": {"a": {"bsonType": "int"}}}},
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a $jsonSchema validator with a valid bsonType",
    ),
    CommandTestCase(
        "regex_pattern_at_limit",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "validator": {"a": {"$regex": "a" * REGEX_PATTERN_LIMIT_BYTES}},
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a validator regex pattern at the 16384-byte limit",
    ),
]

# Property [validator No Retroactive Validation]: setting a validator does not
# validate documents already present in the collection, so the command succeeds
# (ok:1.0) even when an existing document would fail the newly-set validator,
# including under an explicit strict/error validation mode.
COLLMOD_VALIDATOR_NO_RETROACTIVE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "json_schema_existing_doc_violates",
        docs=[{"_id": 1, "a": "not_an_int"}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "validator": {"$jsonSchema": {"properties": {"a": {"bsonType": "int"}}}},
            "validationLevel": "strict",
            "validationAction": "error",
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a $jsonSchema validator even when an existing document "
        "violates it, since existing documents are not validated retroactively",
    ),
]

# Property [validator Clears Previously-Set Validator]: an empty {} validator
# applied to a collection that already has a validator is accepted (ok:1.0),
# resetting it to no validation.
COLLMOD_VALIDATOR_CLEAR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "empty_clears_existing_validator",
        target_collection=ValidatedCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "validator": {}},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept an empty {} validator that clears a previously-set validator",
    ),
]

# Property [validator Type Rejection]: a validator value that is neither an
# object nor null produces a TypeMismatch error.
COLLMOD_VALIDATOR_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"type_{tid}",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx, v=val: {"collMod": ctx.collection, "validator": v},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"collMod should reject a {tid} validator as a non-object",
    )
    for tid, val in [
        ("string", "not_an_object"),
        ("int32", 42),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool_true", True),
        ("bool_false", False),
        ("array", [{"a": 1}]),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [validator Query Operator Rejection]: query operators that cannot be
# used in a collection validator are rejected, with the error code determined by
# the specific operator.
COLLMOD_VALIDATOR_OPERATOR_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "where_operator",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {"collMod": ctx.collection, "validator": {"$where": "true"}},
        error_code=BAD_VALUE_ERROR,
        msg="collMod should reject a $where operator in a validator",
    ),
    CommandTestCase(
        "text_operator",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "validator": {"$text": {"$search": "x"}},
        },
        error_code=BAD_VALUE_ERROR,
        msg="collMod should reject a $text operator in a validator",
    ),
    CommandTestCase(
        "unknown_dollar_operator",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {"collMod": ctx.collection, "validator": {"a": {"$badOp": 1}}},
        error_code=BAD_VALUE_ERROR,
        msg="collMod should reject an unknown query operator in a validator",
    ),
    CommandTestCase(
        "near_operator",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "validator": {"a": {"$near": [0, 0]}},
        },
        error_code=NEAR_NOT_ALLOWED_ERROR,
        msg="collMod should reject a $near operator in a validator",
    ),
    CommandTestCase(
        "near_sphere_operator",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "validator": {"a": {"$nearSphere": [0, 0]}},
        },
        error_code=NEAR_NOT_ALLOWED_ERROR,
        msg="collMod should reject a $nearSphere operator in a validator",
    ),
    CommandTestCase(
        "geo_near_operator",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "validator": {"a": {"$geoNear": [0, 0]}},
        },
        error_code=NEAR_NOT_ALLOWED_ERROR,
        msg="collMod should reject a $geoNear operator in a validator",
    ),
    CommandTestCase(
        "expr_unknown_aggregation_operator",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "validator": {"$expr": {"$unknownAggOp": [1, 2]}},
        },
        error_code=UNRECOGNIZED_EXPRESSION_ERROR,
        msg="collMod should reject an unknown aggregation operator inside $expr in a validator",
    ),
]

# Property [validator JSON Schema Rejection]: a $jsonSchema with an invalid
# keyword, an invalid type alias, or a conflicting type specification produces a
# FailedToParse error.
COLLMOD_VALIDATOR_JSON_SCHEMA_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "json_schema_unknown_keyword",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "validator": {"$jsonSchema": {"unknownKeyword": 1}},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="collMod should reject a $jsonSchema with an unknown keyword",
    ),
    CommandTestCase(
        "json_schema_type_integer",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "validator": {"$jsonSchema": {"properties": {"a": {"type": "integer"}}}},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="collMod should reject a $jsonSchema using the integer type alias",
    ),
    CommandTestCase(
        "json_schema_type_and_bson_type",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "validator": {
                "$jsonSchema": {"properties": {"a": {"type": "string", "bsonType": "int"}}}
            },
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="collMod should reject a $jsonSchema specifying both type and bsonType on a property",
    ),
]

# Property [validator Logical Operator Rejection]: a malformed top-level logical
# operator or an unknown dollar-prefixed top-level field produces a BadValue
# error.
COLLMOD_VALIDATOR_LOGICAL_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "empty_and",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {"collMod": ctx.collection, "validator": {"$and": []}},
        error_code=BAD_VALUE_ERROR,
        msg="collMod should reject an empty $and in a validator",
    ),
    CommandTestCase(
        "empty_or",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {"collMod": ctx.collection, "validator": {"$or": []}},
        error_code=BAD_VALUE_ERROR,
        msg="collMod should reject an empty $or in a validator",
    ),
    CommandTestCase(
        "non_array_or",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {"collMod": ctx.collection, "validator": {"$or": {"a": 1}}},
        error_code=BAD_VALUE_ERROR,
        msg="collMod should reject a non-array $or in a validator",
    ),
    CommandTestCase(
        "unknown_dollar_field",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {"collMod": ctx.collection, "validator": {"$nope": 1}},
        error_code=BAD_VALUE_ERROR,
        msg="collMod should reject an unknown dollar-prefixed top-level field in a validator",
    ),
]

# Property [validator Regex Limit Rejection]: a validator regex pattern one byte
# over the inclusive size limit fails to compile.
COLLMOD_VALIDATOR_REGEX_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "regex_pattern_over_limit",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "validator": {"a": {"$regex": "a" * (REGEX_PATTERN_LIMIT_BYTES + 1)}},
        },
        error_code=REGEX_COMPILE_ERROR,
        msg="collMod should reject a validator regex pattern one byte over the limit",
    ),
]

# Property [validator Restricted Namespace Rejection]: a validator applied to a
# collection in a restricted database (admin, config, local) or to a system.*
# collection is rejected, regardless of the validator's well-formedness.
COLLMOD_VALIDATOR_RESTRICTED_NAMESPACE_ERROR_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            f"restricted_db_{dbname}",
            target_collection=ExistingDatabase(db_name=dbname),
            # The local database does not support retryable writes, so the
            # collection is created empty rather than seeded with documents; its
            # existence alone is enough to trigger the validator rejection.
            docs=[] if dbname == "local" else [{"_id": 1, "a": 1}],
            command=lambda ctx: {"collMod": ctx.collection, "validator": {"a": 1}},
            error_code=INVALID_OPTIONS_ERROR,
            msg=f"collMod should reject a validator on a collection in the {dbname} database",
        )
        for dbname in ["admin", "config", "local"]
    ],
    CommandTestCase(
        "system_views",
        target_collection=SystemViewsCollection(),
        command=lambda ctx: {"collMod": ctx.collection, "validator": {"a": 1}},
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject a validator on a system.* collection",
    ),
]

# Property [validator Unsupported Collection Type Rejection]: a validator
# applied to a collection type that does not support validation (a view or a
# time series collection) is rejected.
COLLMOD_VALIDATOR_UNSUPPORTED_TARGET_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"unsupported_{target_id}",
        docs=[],
        target_collection=target,
        command=lambda ctx: {"collMod": ctx.collection, "validator": {"a": 1}},
        error_code=INVALID_OPTIONS_ERROR,
        msg=f"collMod should reject a validator on a {target_id}",
    )
    for target_id, target in [
        ("view", ViewCollection()),
        ("timeseries", TimeseriesCollection()),
    ]
]

COLLMOD_VALIDATOR_TESTS: list[CommandTestCase] = (
    COLLMOD_VALIDATOR_SUCCESS_TESTS
    + COLLMOD_VALIDATOR_NO_RETROACTIVE_TESTS
    + COLLMOD_VALIDATOR_CLEAR_TESTS
    + COLLMOD_VALIDATOR_TYPE_ERROR_TESTS
    + COLLMOD_VALIDATOR_OPERATOR_ERROR_TESTS
    + COLLMOD_VALIDATOR_JSON_SCHEMA_ERROR_TESTS
    + COLLMOD_VALIDATOR_LOGICAL_ERROR_TESTS
    + COLLMOD_VALIDATOR_REGEX_ERROR_TESTS
    + COLLMOD_VALIDATOR_RESTRICTED_NAMESPACE_ERROR_TESTS
    + COLLMOD_VALIDATOR_UNSUPPORTED_TARGET_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COLLMOD_VALIDATOR_TESTS))
def test_collMod_validator(database_client, collection, register_db_cleanup, test):
    """Test collMod validator acceptance and rejection."""
    collection = test.prepare(database_client, collection)
    if collection.database.name != database_client.name:
        register_db_cleanup(f"{collection.database.name}.{collection.name}")
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
