"""Tests for hidden index BSON type validation."""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertNotError
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import (
    INVALID_OPTIONS_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.index


HIDDEN_BSON_PARAMS = [
    BsonTypeTestCase(
        id="createIndexes_hidden",
        msg="createIndexes hidden should reject non-boolean types",
        keyword="hidden",
        valid_types=[BsonType.BOOL],
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
    BsonTypeTestCase(
        id="collMod_hidden",
        msg="collMod index.hidden should reject non-boolean/non-numeric types",
        keyword="hidden",
        valid_types=[BsonType.BOOL, BsonType.DOUBLE, BsonType.INT, BsonType.LONG, BsonType.DECIMAL],
        default_error_code=TYPE_MISMATCH_ERROR,
        error_code_overrides={BsonType.NULL: INVALID_OPTIONS_ERROR},
    ),
]

REJECTION_CASES = generate_bson_rejection_test_cases(HIDDEN_BSON_PARAMS)
ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(HIDDEN_BSON_PARAMS)


def _build_command(collection, spec, sample_value):
    """Build and execute the appropriate command for the given spec and sample value."""
    if spec.id == "createIndexes_hidden":
        return execute_command(
            collection,
            {
                "createIndexes": collection.name,
                "indexes": [{"key": {"b": 1}, "name": "idx", "hidden": sample_value}],
            },
        )
    else:
        return execute_command(
            collection,
            {"collMod": collection.name, "index": {"name": "a_1", "hidden": sample_value}},
        )


@pytest.mark.parametrize("bson_type,sample_value,spec", REJECTION_CASES)
def test_hidden_rejects_invalid_bson_type(collection, bson_type, sample_value, spec):
    """Test hidden-related options reject invalid BSON types."""
    collection.insert_one({"x": 1})
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"a": 1}, "name": "a_1"}]},
    )
    result = _build_command(collection, spec, sample_value)
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_hidden_accepts_valid_bson_type(collection, bson_type, sample_value, spec):
    """Test hidden-related options accept valid BSON types."""
    collection.insert_one({"x": 1})
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"a": 1}, "name": "a_1"}]},
    )
    result = _build_command(collection, spec, sample_value)
    assertNotError(result, msg=f"{spec.id} should accept {bson_type.value}")
