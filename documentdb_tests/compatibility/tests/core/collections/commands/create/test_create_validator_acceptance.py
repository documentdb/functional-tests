"""Tests for the create command validator acceptance behavior."""

import functools
from typing import Any

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Validator Acceptance]: valid validator documents are accepted,
# including null and empty (treated as no validator).
CREATE_VALIDATOR_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="validator_document",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {"x": {"$exists": True}},
        },
        expected={"ok": 1.0},
        msg="Document validator should succeed",
    ),
    CommandTestCase(
        id="validator_null_treated_as_omitted",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": None,
        },
        expected={"ok": 1.0},
        msg="null validator is treated as no validator",
    ),
    CommandTestCase(
        id="validator_empty_document",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {},
        },
        expected={"ok": 1.0},
        msg="Empty {} validator is treated as no validator",
    ),
    CommandTestCase(
        id="validator_type",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {"x": {"$type": "string"}},
        },
        expected={"ok": 1.0},
        msg="$type operator in validator should succeed",
    ),
    CommandTestCase(
        id="validator_comparison_operators",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {
                "a": {"$gt": 0, "$lte": 100},
                "b": {"$gte": 1, "$lt": 50},
            },
        },
        expected={"ok": 1.0},
        msg="$gt/$gte/$lt/$lte operators in validator should succeed",
    ),
    CommandTestCase(
        id="validator_ne",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {"status": {"$ne": "deleted"}},
        },
        expected={"ok": 1.0},
        msg="$ne operator in validator should succeed",
    ),
    CommandTestCase(
        id="validator_in_nin",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {
                "status": {"$in": ["active", "pending"]},
                "role": {"$nin": ["banned"]},
            },
        },
        expected={"ok": 1.0},
        msg="$in/$nin operators in validator should succeed",
    ),
    CommandTestCase(
        id="validator_regex",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {"email": {"$regex": "^[a-z]+@"}},
        },
        expected={"ok": 1.0},
        msg="$regex operator in validator should succeed",
    ),
    CommandTestCase(
        id="validator_mod",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {"x": {"$mod": [2, 0]}},
        },
        expected={"ok": 1.0},
        msg="$mod operator in validator should succeed",
    ),
    CommandTestCase(
        id="validator_all",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {"tags": {"$all": ["a", "b"]}},
        },
        expected={"ok": 1.0},
        msg="$all operator in validator should succeed",
    ),
    CommandTestCase(
        id="validator_eq",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {"x": {"$eq": 5}},
        },
        expected={"ok": 1.0},
        msg="$eq operator in validator should succeed",
    ),
    CommandTestCase(
        id="validator_elem_match",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {"items": {"$elemMatch": {"qty": {"$gt": 0}}}},
        },
        expected={"ok": 1.0},
        msg="$elemMatch operator in validator should succeed",
    ),
    CommandTestCase(
        id="validator_size",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {"arr": {"$size": 3}},
        },
        expected={"ok": 1.0},
        msg="$size operator in validator should succeed",
    ),
    CommandTestCase(
        id="validator_bits_all_set",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {"x": {"$bitsAllSet": 3}},
        },
        expected={"ok": 1.0},
        msg="$bitsAllSet operator in validator should succeed",
    ),
    CommandTestCase(
        id="validator_bits_all_clear",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {"x": {"$bitsAllClear": 3}},
        },
        expected={"ok": 1.0},
        msg="$bitsAllClear operator in validator should succeed",
    ),
    CommandTestCase(
        id="validator_bits_any_set",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {"x": {"$bitsAnySet": 3}},
        },
        expected={"ok": 1.0},
        msg="$bitsAnySet operator in validator should succeed",
    ),
    CommandTestCase(
        id="validator_bits_any_clear",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {"x": {"$bitsAnyClear": 3}},
        },
        expected={"ok": 1.0},
        msg="$bitsAnyClear operator in validator should succeed",
    ),
    CommandTestCase(
        id="validator_geo_within",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {
                "loc": {
                    "$geoWithin": {
                        "$geometry": {
                            "type": "Polygon",
                            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                        }
                    }
                }
            },
        },
        expected={"ok": 1.0},
        msg="$geoWithin operator in validator should succeed",
    ),
    CommandTestCase(
        id="validator_geo_intersects",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {
                "loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}
            },
        },
        expected={"ok": 1.0},
        msg="$geoIntersects operator in validator should succeed",
    ),
    CommandTestCase(
        id="validator_not",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {"x": {"$not": {"$eq": 0}}},
        },
        expected={"ok": 1.0},
        msg="$not operator in validator should succeed",
    ),
    CommandTestCase(
        id="validator_and_or_nor",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {
                "$and": [
                    {"$or": [{"a": 1}, {"b": 2}]},
                    {"$nor": [{"c": 3}]},
                ]
            },
        },
        expected={"ok": 1.0},
        msg="$and/$or/$nor operators in validator should succeed",
    ),
    CommandTestCase(
        id="validator_expr",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {"$expr": {"$gt": ["$end", "$start"]}},
        },
        expected={"ok": 1.0},
        msg="$expr with aggregation expressions should succeed",
    ),
    CommandTestCase(
        id="validator_json_schema",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["name"],
                    "properties": {"name": {"bsonType": "string"}},
                }
            },
        },
        expected={"ok": 1.0},
        msg="$jsonSchema in validator should succeed",
    ),
    CommandTestCase(
        id="validator_100_levels_nesting",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": functools.reduce(
                lambda d, _: {"$and": [d]}, range(99), dict[str, Any]({"x": {"$exists": True}})
            ),
        },
        expected={"ok": 1.0},
        msg="100 levels of BSON nesting in validator should succeed",
    ),
    CommandTestCase(
        id="validator_500_fields",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {f"f{i}": {"$exists": True} for i in range(500)},
        },
        expected={"ok": 1.0},
        msg="Validator with 500 fields should succeed",
    ),
    CommandTestCase(
        id="validator_10k_and_conditions",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {"$and": [{"x": {"$gte": i}} for i in range(10_000)]},
        },
        expected={"ok": 1.0},
        msg="Validator with 10K $and conditions should succeed",
    ),
    CommandTestCase(
        id="validator_in_with_10k_values",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {"x": {"$in": list(range(10_000))}},
        },
        expected={"ok": 1.0},
        msg="Validator with $in containing 10K values should succeed",
    ),
    CommandTestCase(
        id="validator_with_collation",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validator": {"name": {"$type": "string"}},
            "collation": {"locale": "en"},
        },
        expected={"ok": 1.0},
        msg="Validator compatible with collation should succeed",
    ),
]

# Property [ValidationLevel and ValidationAction (Success)]: valid enum values
# for validationLevel and validationAction are accepted.
CREATE_VALIDATION_LEVEL_ACTION_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="validation_level_off",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validationLevel": "off",
        },
        expected={"ok": 1.0},
        msg="validationLevel 'off' should succeed",
    ),
    CommandTestCase(
        id="validation_level_strict",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validationLevel": "strict",
        },
        expected={"ok": 1.0},
        msg="validationLevel 'strict' should succeed",
    ),
    CommandTestCase(
        id="validation_level_moderate",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validationLevel": "moderate",
        },
        expected={"ok": 1.0},
        msg="validationLevel 'moderate' should succeed",
    ),
    CommandTestCase(
        id="validation_level_null",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validationLevel": None,
        },
        expected={"ok": 1.0},
        msg="validationLevel null is treated as omitted",
    ),
    CommandTestCase(
        id="validation_action_error",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validationAction": "error",
        },
        expected={"ok": 1.0},
        msg="validationAction 'error' should succeed",
    ),
    CommandTestCase(
        id="validation_action_warn",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validationAction": "warn",
        },
        expected={"ok": 1.0},
        msg="validationAction 'warn' should succeed",
    ),
    CommandTestCase(
        id="validation_action_null",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validationAction": None,
        },
        expected={"ok": 1.0},
        msg="validationAction null is treated as omitted",
    ),
    CommandTestCase(
        id="both_without_validator",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "validationLevel": "moderate",
            "validationAction": "warn",
        },
        expected={"ok": 1.0},
        msg="Both validationLevel and validationAction accepted without a validator",
    ),
]

CREATE_VALIDATOR_ACCEPTANCE_TESTS: list[CommandTestCase] = (
    CREATE_VALIDATOR_SUCCESS_TESTS + CREATE_VALIDATION_LEVEL_ACTION_SUCCESS_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(CREATE_VALIDATOR_ACCEPTANCE_TESTS))
def test_create_validator_acceptance(database_client, collection, test):
    """Test create command validator acceptance behavior."""
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
