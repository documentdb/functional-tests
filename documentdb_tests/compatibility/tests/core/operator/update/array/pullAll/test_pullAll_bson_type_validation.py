"""Tests for $pullAll BSON type validation.

Verifies that $pullAll rejects non-array target field types with error code 2,
rejects non-array argument types with error code 2, and can match any BSON type
as values to remove from an array.
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

PULLALL_PARAMS = [
    BsonTypeTestCase(
        id="target_field",
        msg="$pullAll should error when the document field it targets is not an array",
        valid_types=[BsonType.ARRAY],
        default_error_code=BAD_VALUE_ERROR,
        expected=[{"_id": 1, "arr": [2]}],
        valid_inputs={BsonType.ARRAY: [1, 2]},
    ),
    BsonTypeTestCase(
        id="argument",
        msg="$pullAll should reject non-array argument types",
        valid_types=[BsonType.ARRAY],
        default_error_code=BAD_VALUE_ERROR,
        expected=[{"_id": 1, "arr": [1, 2, 3]}],
        valid_inputs={BsonType.ARRAY: [99]},
    ),
    BsonTypeTestCase(
        id="value_element",
        msg="$pullAll should accept any BSON type as value to match and remove",
        valid_types=list(BsonType),
        default_error_code=BAD_VALUE_ERROR,
        expected=[{"_id": 1, "arr": []}],
        valid_inputs={BsonType.BIN_DATA: Binary(b"\x00\x01\x02", 128)},
    ),
]


def _setup_doc(spec, sample_value) -> dict:
    """Build the setup document based on which aspect is being tested."""
    if spec.id == "target_field":
        return {"_id": 1, "arr": sample_value}
    if spec.id == "argument":
        return {"_id": 1, "arr": [1, 2, 3]}
    return {"_id": 1, "arr": [sample_value]}


def _build_update(spec, sample_value) -> dict:
    """Build the update command based on which aspect is being tested."""
    if spec.id == "target_field":
        return {"$pullAll": {"arr": [1]}}
    if spec.id == "argument":
        return {"$pullAll": {"arr": sample_value}}
    return {"$pullAll": {"arr": [sample_value]}}


@pytest.mark.parametrize(
    "bson_type,sample_value,spec", generate_bson_rejection_test_cases(PULLALL_PARAMS)
)
def test_pullAll_bson_type_rejected(collection, bson_type, sample_value, spec):
    """Test $pullAll rejects invalid BSON types with error."""
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
        msg=f"$pullAll should reject {bson_type.value} for {spec.id}",
    )


@pytest.mark.parametrize(
    "bson_type,sample_value,spec", generate_bson_acceptance_test_cases(PULLALL_PARAMS)
)
def test_pullAll_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Test $pullAll accepts valid BSON types."""
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
    assertSuccess(
        result, spec.expected, msg=f"$pullAll should accept {bson_type.value} for {spec.id}"
    )
