"""BSON type validation for the $pop update array operator.

Covers: $pop accepts numeric argument types and rejects all others, and accepts
an array target field while rejecting all other target BSON types.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import FAILED_TO_PARSE_ERROR, TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command

# Property [Argument Type]: $pop accepts only numeric argument types (int, long,
# double, decimal) and rejects every other BSON type. The generic numeric samples
# are not valid $pop arguments, so acceptance uses 1 for each numeric type.
ARGUMENT_TYPE_PARAMS = [
    BsonTypeTestCase(
        id="pop_argument",
        msg="$pop argument",
        keyword="arr",
        valid_types=[BsonType.INT, BsonType.LONG, BsonType.DOUBLE, BsonType.DECIMAL],
        valid_inputs={
            BsonType.INT: 1,
            BsonType.LONG: Int64(1),
            BsonType.DOUBLE: 1.0,
            BsonType.DECIMAL: Decimal128("1"),
        },
        default_error_code=FAILED_TO_PARSE_ERROR,
    ),
]

ARGUMENT_ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(ARGUMENT_TYPE_PARAMS)
ARGUMENT_REJECTION_CASES = generate_bson_rejection_test_cases(ARGUMENT_TYPE_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", ARGUMENT_ACCEPTANCE_CASES)
def test_pop_argument_type_accepted(collection, bson_type, sample_value, spec):
    """Test $pop accepts numeric argument types and removes the last element."""
    collection.insert_one({"_id": 1, "arr": [1, 2, 3]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pop": {"arr": sample_value}}}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(
        result, [{"_id": 1, "arr": [1, 2]}], msg=f"{spec.msg} should accept {bson_type.value}"
    )


@pytest.mark.parametrize("bson_type,sample_value,spec", ARGUMENT_REJECTION_CASES)
def test_pop_argument_type_rejected(collection, bson_type, sample_value, spec):
    """Test $pop rejects non-numeric argument types."""
    collection.insert_one({"_id": 1, "arr": [1, 2, 3]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pop": {"arr": sample_value}}}],
        },
    )
    assertFailureCode(
        result, spec.expected_code(bson_type), msg=f"{spec.msg} should reject {bson_type.value}"
    )


# Property [Target Type]: $pop accepts a field whose value is an array and rejects
# a field whose value is any other BSON type.
TARGET_TYPE_PARAMS = [
    BsonTypeTestCase(
        id="pop_target",
        msg="$pop target field",
        keyword="field",
        valid_types=[BsonType.ARRAY],
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
]

TARGET_ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(TARGET_TYPE_PARAMS)
TARGET_REJECTION_CASES = generate_bson_rejection_test_cases(TARGET_TYPE_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", TARGET_ACCEPTANCE_CASES)
def test_pop_target_type_accepted(collection, bson_type, sample_value, spec):
    """Test $pop accepts an array target field and removes the last element."""
    collection.insert_one({"_id": 1, "field": sample_value})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pop": {"field": 1}}}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1, "field": list(sample_value)[:-1]}],
        msg=f"{spec.msg} should accept {bson_type.value}",
    )


@pytest.mark.parametrize("bson_type,sample_value,spec", TARGET_REJECTION_CASES)
def test_pop_target_type_rejected(collection, bson_type, sample_value, spec):
    """Test $pop rejects non-array target fields."""
    collection.insert_one({"_id": 1, "field": sample_value})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pop": {"field": 1}}}],
        },
    )
    assertFailureCode(
        result, spec.expected_code(bson_type), msg=f"{spec.msg} should reject {bson_type.value}"
    )
