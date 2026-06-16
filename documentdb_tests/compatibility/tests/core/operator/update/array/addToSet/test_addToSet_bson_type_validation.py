"""Tests for $addToSet BSON type validation.

Verifies that $addToSet rejects non-array target field types with error code 2,
accepts array target fields, and can add any BSON type as a value element.
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

ADDTOSET_PARAMS = [
    BsonTypeTestCase(
        id="target_field",
        msg="$addToSet should reject non-array target field types",
        valid_types=[BsonType.ARRAY],
        default_error_code=BAD_VALUE_ERROR,
        expected=[{"_id": 1, "arr": [1, 99]}],
        valid_inputs={BsonType.ARRAY: [1]},
    ),
    BsonTypeTestCase(
        id="value_element",
        msg="$addToSet should accept any BSON type as value to add",
        valid_types=list(BsonType),
        default_error_code=BAD_VALUE_ERROR,
        expected=None,
        valid_inputs={BsonType.BIN_DATA: Binary(b"\x00\x01\x02", 128)},
    ),
    BsonTypeTestCase(
        id="duplicate",
        msg="$addToSet should detect duplicate for each BSON type",
        valid_types=list(BsonType),
        default_error_code=BAD_VALUE_ERROR,
        expected=None,
        valid_inputs={BsonType.BIN_DATA: Binary(b"\x00\x01\x02", 128)},
    ),
]


def _build_setup_doc(spec, sample_value):
    """Build the setup document based on which aspect is being tested."""
    if spec.id == "target_field":
        return {"_id": 1, "arr": sample_value}
    if spec.id == "duplicate":
        return {"_id": 1, "arr": [sample_value]}
    return {"_id": 1, "arr": []}


def _build_update(spec, sample_value):
    """Build the update command based on which aspect is being tested."""
    if spec.id == "target_field":
        return {"$addToSet": {"arr": 99}}
    return {"$addToSet": {"arr": sample_value}}


@pytest.mark.parametrize(
    "bson_type,sample_value,spec", generate_bson_rejection_test_cases(ADDTOSET_PARAMS)
)
def test_addToSet_target_field_rejected(collection, bson_type, sample_value, spec):
    """Test $addToSet rejects non-array target field types with error."""
    setup_doc = _build_setup_doc(spec, sample_value)
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
        msg=f"$addToSet should reject {bson_type.value} for {spec.id}",
    )


@pytest.mark.parametrize(
    "bson_type,sample_value,spec", generate_bson_acceptance_test_cases(ADDTOSET_PARAMS)
)
def test_addToSet_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Test $addToSet accepts valid BSON types for target field and value element."""
    setup_doc = _build_setup_doc(spec, sample_value)
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
    expected = spec.expected or [{"_id": 1, "arr": [sample_value]}]
    assertSuccess(result, expected, msg=f"$addToSet should accept {bson_type.value} for {spec.id}")
