"""
Tests for $set update operator - BSON type validation.

Verifies that $set rejects non-object BSON types for its operand
and accepts all BSON types as field values.
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
from documentdb_tests.framework.error_codes import FAILED_TO_PARSE_ERROR
from documentdb_tests.framework.executor import execute_command

SET_BSON_PARAMS = [
    BsonTypeTestCase(
        id="set_operand",
        msg="$set operand should reject non-object types",
        keyword="$set",
        valid_types=[BsonType.OBJECT],
        default_error_code=FAILED_TO_PARSE_ERROR,
        valid_inputs={BsonType.OBJECT: {"b": 2}},
    ),
    BsonTypeTestCase(
        id="set_field_value",
        msg="$set field value should accept all BSON types",
        keyword="field",
        valid_types=list(BsonType),
        # Driver returns raw bytes when using Binary subtype 0
        valid_inputs={BsonType.BIN_DATA: Binary(b"\x00\x01\x02", 128)},
    ),
]


def _build_set_cmd(collection, spec, sample_value):
    """Build the update command document."""
    if spec.id == "set_operand":
        update = {"$set": sample_value}
    else:
        update = {"$set": {spec.keyword: sample_value}}
    return {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": update}]}


REJECTION_CASES = generate_bson_rejection_test_cases(SET_BSON_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", REJECTION_CASES)
def test_set_bson_type_rejected(collection, bson_type, sample_value, spec):
    """Test $set rejects invalid BSON types."""
    collection.insert_one({"_id": 1, "a": 1})
    result = execute_command(collection, _build_set_cmd(collection, spec, sample_value))
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(SET_BSON_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_set_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Test $set accepts valid BSON types."""
    collection.insert_one({"_id": 1})
    execute_command(collection, _build_set_cmd(collection, spec, sample_value))
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    expected = (
        [{"_id": 1, **sample_value}]
        if spec.id == "set_operand"
        else [{"_id": 1, "field": sample_value}]
    )
    assertSuccess(result, expected, msg=f"$set should accept {bson_type.value}")
