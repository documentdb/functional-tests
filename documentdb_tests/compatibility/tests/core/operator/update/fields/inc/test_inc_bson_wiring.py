"""
BSON type wiring tests for $inc update field operator.

Tests that $inc rejects all non-numeric BSON types and accepts all numeric
BSON types as both increment values and existing field values.
"""

import pytest
from bson import Int64

from documentdb_tests.framework.assertions import assertFailureCode, assertNotError
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.executor import execute_command

_NUMERIC_TYPES = [BsonType.DOUBLE, BsonType.INT, BsonType.LONG, BsonType.DECIMAL]

# Override LONG to avoid INT64_MAX overflow when adding to another value.
_SAFE_NUMERIC_INPUTS = {BsonType.LONG: Int64(5)}

# Property [Invalid Increment Types]: $inc rejects non-numeric increment values.
# Property [Valid Increment Types]: $inc accepts numeric increment values.
INC_VALUE_SPEC = BsonTypeTestCase(
    id="inc_value",
    msg="$inc increment value type",
    keyword="$inc",
    valid_types=_NUMERIC_TYPES,
    valid_inputs=_SAFE_NUMERIC_INPUTS,
)

# Property [Invalid Field Types]: $inc rejects incrementing non-numeric existing field values.
# Property [Valid Field Types]: $inc accepts incrementing numeric existing field values.
INC_FIELD_SPEC = BsonTypeTestCase(
    id="inc_field",
    msg="$inc existing field type",
    keyword="$inc",
    valid_types=_NUMERIC_TYPES,
    valid_inputs=_SAFE_NUMERIC_INPUTS,
)

INCREMENT_REJECTION_CASES = generate_bson_rejection_test_cases([INC_VALUE_SPEC])
FIELD_REJECTION_CASES = generate_bson_rejection_test_cases([INC_FIELD_SPEC])
INCREMENT_ACCEPTANCE_CASES = generate_bson_acceptance_test_cases([INC_VALUE_SPEC])
FIELD_ACCEPTANCE_CASES = generate_bson_acceptance_test_cases([INC_FIELD_SPEC])


@pytest.mark.parametrize("bson_type,sample_value,spec", INCREMENT_REJECTION_CASES)
def test_inc_rejects_non_numeric_increment(collection, bson_type, sample_value, spec):
    """Test $inc rejects non-numeric BSON types as increment values."""
    collection.insert_one({"_id": 1, "val": 10})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$inc": {"val": sample_value}}}],
        },
    )
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


@pytest.mark.parametrize("bson_type,sample_value,spec", FIELD_REJECTION_CASES)
def test_inc_rejects_non_numeric_field(collection, bson_type, sample_value, spec):
    """Test $inc rejects incrementing non-numeric existing field values."""
    collection.insert_one({"_id": 1, "val": sample_value})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$inc": {"val": 1}}}]},
    )
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


@pytest.mark.parametrize("bson_type,sample_value,spec", INCREMENT_ACCEPTANCE_CASES)
def test_inc_accepts_numeric_increment(collection, bson_type, sample_value, spec):
    """Test $inc accepts numeric BSON types as increment values."""
    collection.insert_one({"_id": 1, "val": 10})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$inc": {"val": sample_value}}}],
        },
    )
    assertNotError(result, msg=f"{spec.msg} should accept {bson_type.value}")


@pytest.mark.parametrize("bson_type,sample_value,spec", FIELD_ACCEPTANCE_CASES)
def test_inc_accepts_numeric_field(collection, bson_type, sample_value, spec):
    """Test $inc accepts incrementing numeric existing field values."""
    collection.insert_one({"_id": 1, "val": sample_value})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$inc": {"val": 1}}}]},
    )
    assertNotError(result, msg=f"{spec.msg} should accept {bson_type.value}")
