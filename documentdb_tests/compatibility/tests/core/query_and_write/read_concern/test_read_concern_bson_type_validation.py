"""readConcern BSON type validation: field must be a document, level must be a string."""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command

READ_CONCERN_PARAMS = [
    BsonTypeTestCase(
        id="read_concern_field",
        msg="readConcern field should reject non-document BSON types",
        valid_types=[BsonType.OBJECT],
        skip_rejection_types=[BsonType.NULL],
        default_error_code=TYPE_MISMATCH_ERROR,
        expected=[{"_id": 1, "x": 1}],
        valid_inputs={BsonType.OBJECT: {"level": "local"}},
    ),
    BsonTypeTestCase(
        id="level_field",
        msg="readConcern.level should reject non-string BSON types",
        valid_types=[BsonType.STRING],
        skip_rejection_types=[BsonType.NULL],
        default_error_code=TYPE_MISMATCH_ERROR,
        expected=[{"_id": 1, "x": 1}],
        valid_inputs={BsonType.STRING: "local"},
    ),
]


def _build_read_concern(spec, sample_value):
    """Build the readConcern value based on which aspect is being tested."""
    if spec.id == "read_concern_field":
        return sample_value
    # level_field: wrap the sample as the level sub-field.
    return {"level": sample_value}


@pytest.mark.parametrize(
    "bson_type,sample_value,spec", generate_bson_rejection_test_cases(READ_CONCERN_PARAMS)
)
def test_read_concern_bson_type_rejected(collection, bson_type, sample_value, spec):
    """Test readConcern rejects invalid BSON types for the field and level sub-field."""
    collection.insert_one({"_id": 1, "x": 1})
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {},
            "readConcern": _build_read_concern(spec, sample_value),
        },
    )
    assertFailureCode(
        result,
        spec.expected_code(bson_type),
        msg=f"readConcern should reject {bson_type.value} for {spec.id}",
    )


@pytest.mark.parametrize(
    "bson_type,sample_value,spec", generate_bson_acceptance_test_cases(READ_CONCERN_PARAMS)
)
def test_read_concern_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Test readConcern accepts valid BSON types for the field and level sub-field."""
    collection.insert_one({"_id": 1, "x": 1})
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {},
            "readConcern": _build_read_concern(spec, sample_value),
        },
    )
    assertSuccess(
        result, spec.expected, msg=f"readConcern should accept {bson_type.value} for {spec.id}"
    )
