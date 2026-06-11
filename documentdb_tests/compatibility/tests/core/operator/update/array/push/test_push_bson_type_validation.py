"""Tests for $push BSON type validation.

Verifies that $push rejects non-array target field types with error code 2,
and can push any BSON type as a value into an array.
"""

import pytest
from bson import Binary

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command

PUSH_PARAMS = [
    BsonTypeTestCase(
        id="target_field",
        msg="$push should reject non-array target field types",
        valid_types=[BsonType.ARRAY],
        default_error_code=BAD_VALUE_ERROR,
        expected=[{"_id": 1, "arr": [1, 2, 99]}],
        valid_inputs={BsonType.ARRAY: [1, 2]},
    ),
    BsonTypeTestCase(
        id="value_element",
        msg="$push should accept any BSON type as value to push",
        valid_types=list(BsonType),
        default_error_code=BAD_VALUE_ERROR,
        expected=[],
        valid_inputs={BsonType.BIN_DATA: Binary(b"\x00\x01\x02", 128)},
    ),
]


def _setup_doc(spec, sample_value) -> dict:
    """Build the setup document based on which aspect is being tested."""
    if spec.id == "target_field":
        return {"_id": 1, "arr": sample_value}
    return {"_id": 1, "arr": []}


def _build_update(spec, sample_value) -> dict:
    """Build the update command based on which aspect is being tested."""
    if spec.id == "target_field":
        return {"$push": {"arr": 99}}
    return {"$push": {"arr": sample_value}}


@pytest.mark.parametrize(
    "bson_type,sample_value,spec", generate_bson_rejection_test_cases(PUSH_PARAMS)
)
def test_push_bson_type_rejected(collection, bson_type, sample_value, spec):
    """Test $push rejects non-array target field types with error."""
    setup_doc = _setup_doc(spec, sample_value)
    update = _build_update(spec, sample_value)
    collection.insert_one(setup_doc)
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": update}],
        },
    )
    assertFailureCode(
        result,
        spec.expected_code(bson_type),
        msg=f"$push should reject {bson_type.value} for {spec.id}",
    )


@pytest.mark.parametrize(
    "bson_type,sample_value,spec", generate_bson_acceptance_test_cases(PUSH_PARAMS)
)
def test_push_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Test $push accepts valid BSON types for target field and value element."""
    setup_doc = _setup_doc(spec, sample_value)
    update = _build_update(spec, sample_value)
    collection.insert_one(setup_doc)
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": update}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    if spec.id == "target_field":
        expected = spec.expected
    else:
        expected = [{"_id": 1, "arr": [sample_value]}]
    assertSuccess(result, expected, msg=f"$push should accept {bson_type.value} for {spec.id}")
