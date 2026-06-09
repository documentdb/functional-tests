"""Tests for $pull BSON type validation.

Verifies that $pull rejects non-array target field types with error code 2,
accepts array target fields, and can match any BSON type as a value to remove.
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

PULL_PARAMS = [
    BsonTypeTestCase(
        id="target_field",
        msg="$pull should reject non-array target field data types",
        valid_types=[BsonType.ARRAY],
        default_error_code=BAD_VALUE_ERROR,
        expected=[{"_id": 1, "arr": [2]}],
        valid_inputs={BsonType.ARRAY: [1, 2]},
    ),
    BsonTypeTestCase(
        id="value_element",
        msg="$pull should accept any BSON type as value to match and remove",
        valid_types=list(BsonType),
        default_error_code=BAD_VALUE_ERROR,
        expected=[{"_id": 1, "arr": []}],
        valid_inputs={BsonType.BIN_DATA: Binary(b"\x00\x01\x02", 128)},
    ),
]


def _build_update(spec, sample_value):
    """Build the setup doc and update command based on which aspect is being tested."""
    if spec.id == "target_field":
        return {"_id": 1, "arr": sample_value}, {"$pull": {"arr": 1}}
    return {"_id": 1, "arr": [sample_value]}, {"$pull": {"arr": sample_value}}


@pytest.mark.parametrize(
    "bson_type,sample_value,spec", generate_bson_rejection_test_cases(PULL_PARAMS)
)
def test_pull_target_field_rejected(collection, bson_type, sample_value, spec):
    """Test $pull rejects non-array target field types with error."""
    setup_doc, update = _build_update(spec, sample_value)
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
        msg=f"$pull should reject {bson_type.value} for {spec.id}",
    )


@pytest.mark.parametrize(
    "bson_type,sample_value,spec", generate_bson_acceptance_test_cases(PULL_PARAMS)
)
def test_pull_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Test $pull accepts valid BSON types for target field and value element."""
    setup_doc, update = _build_update(spec, sample_value)
    collection.insert_one(setup_doc)
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": update}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, spec.expected, msg=f"$pull should accept {bson_type.value} for {spec.id}")
