"""
Tests for $unset update operator - BSON type validation.

Verifies that $unset accepts all BSON types as the field value (value is ignored).
"""

import pytest
from bson import Binary

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
)
from documentdb_tests.framework.executor import execute_command

# $unset ignores the field value — any BSON type is accepted, so all types are valid.
UNSET_BSON_PARAMS = [
    BsonTypeTestCase(
        id="unset_field_value",
        msg="$unset field value should accept all BSON types (value is ignored)",
        keyword="a",
        valid_types=list(BsonType),
        # Driver returns raw bytes when using Binary subtype 0
        valid_inputs={BsonType.BIN_DATA: Binary(b"\x00\x01\x02", 128)},
    ),
]

ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(UNSET_BSON_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_unset_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Test $unset accepts all BSON types as field value."""
    collection.insert_one({"_id": 1, "a": 1})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$unset": {"a": sample_value}}}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(
        result, [{"_id": 1}], msg=f"$unset should accept {bson_type.value} as field value"
    )
