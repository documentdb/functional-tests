"""
BSON type validation tests for $rename update operator.

Verifies that:
- the $rename operand itself must be a document (rejects all other types), and
- the new (target) name must be a string (rejects all other types, accepts string).
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR, FAILED_TO_PARSE_ERROR
from documentdb_tests.framework.executor import execute_command

# Two BSON-type constraints, differing only in where the sample is injected:
#   - operand:  {"$rename": <value>}        — must be a document
#   - new_name: {"$rename": {"a": <value>}} — must be a string
BSON_PARAMS = [
    BsonTypeTestCase(
        id="operand",
        msg="$rename operand should reject non-document types",
        keyword="operand",
        valid_types=[BsonType.OBJECT],
        valid_inputs={BsonType.OBJECT: {"a": "b"}},
        default_error_code=FAILED_TO_PARSE_ERROR,
    ),
    BsonTypeTestCase(
        id="new_name",
        msg="$rename new name should reject non-string types",
        keyword="new_name",
        valid_types=[BsonType.STRING],
        valid_inputs={BsonType.STRING: "b"},
        default_error_code=BAD_VALUE_ERROR,
    ),
]

REJECTION_TESTS = generate_bson_rejection_test_cases(BSON_PARAMS)
ACCEPTANCE_TESTS = generate_bson_acceptance_test_cases(BSON_PARAMS)


def _rename_update(spec, sample_value):
    """Build a $rename update with sample_value at the position this spec targets."""
    if spec.keyword == "operand":
        return {"$rename": sample_value}
    return {"$rename": {"a": sample_value}}


@pytest.mark.parametrize("bson_type,sample_value,spec", REJECTION_TESTS)
def test_rename_bson_type_rejected(collection, bson_type, sample_value, spec):
    """Verifies $rename rejects invalid BSON types for the operand and the new name."""
    collection.insert_one({"_id": 1, "a": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": _rename_update(spec, sample_value)}],
        },
    )
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_TESTS)
def test_rename_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Verifies $rename accepts a document operand and a string new name."""
    collection.insert_one({"_id": 1, "a": "value"})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": _rename_update(spec, sample_value)}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1, "b": "value"}],
        msg=f"$rename should accept {bson_type.value} for {spec.keyword}",
    )
