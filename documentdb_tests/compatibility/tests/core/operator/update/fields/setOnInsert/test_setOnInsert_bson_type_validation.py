"""
Tests for $setOnInsert update operator - BSON type validation.

Verifies that $setOnInsert accepts all BSON types as field values on insert path.
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

# $setOnInsert stores whatever value is given — all BSON types are valid.
SETONINSERT_BSON_PARAMS = [
    BsonTypeTestCase(
        id="setOnInsert_field_value",
        msg="$setOnInsert should accept all BSON types as field values",
        keyword="field",
        valid_types=list(BsonType),
        valid_inputs={BsonType.BIN_DATA: Binary(b"\x00\x01\x02", 128)},
    ),
]

ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(SETONINSERT_BSON_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_setOnInsert_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Test $setOnInsert accepts all BSON types as field values."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$setOnInsert": {"field": sample_value}}, "upsert": True}
            ],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1, "field": sample_value}],
        msg=f"$setOnInsert should accept {bson_type.value} as field value",
    )
