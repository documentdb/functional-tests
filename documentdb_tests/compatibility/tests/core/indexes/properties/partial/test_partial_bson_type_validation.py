"""
Tests for partialFilterExpression BSON type validation.

Verifies that partialFilterExpression rejects invalid BSON types with expected
error codes and accepts valid BSON types (object) without error.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.index

PARTIAL_FILTER_PARAMS = [
    BsonTypeTestCase(
        id="partialFilterExpression",
        msg="partialFilterExpression should reject non-object types",
        keyword="partialFilterExpression",
        valid_types=[BsonType.OBJECT],
        valid_inputs={BsonType.OBJECT: {"a": {"$gt": 0}}},
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
]

REJECTION_CASES = generate_bson_rejection_test_cases(PARTIAL_FILTER_PARAMS)
ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(PARTIAL_FILTER_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", REJECTION_CASES)
def test_partial_filter_rejects_invalid_bson_type(collection, bson_type, sample_value, spec):
    """Test createIndexes rejects invalid BSON types for partialFilterExpression."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"a": 1}, "name": "idx_bson", "partialFilterExpression": sample_value}
            ],
        },
    )
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_partial_filter_accepts_valid_bson_type(collection, bson_type, sample_value, spec):
    """Test createIndexes accepts valid BSON types for partialFilterExpression
    and that the resulting index only includes documents matching the filter."""
    collection.insert_many(
        [
            {"_id": 1, "a": 10},  # matches a > 0 → indexed
            {"_id": 2, "a": 20},  # matches a > 0 → indexed
            {"_id": 3, "a": -5},  # doesn't match → NOT indexed
        ]
    )
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"a": 1}, "name": "idx_bson", "partialFilterExpression": sample_value}
            ],
        },
    )
    count_result = execute_command(
        collection,
        {"count": collection.name, "query": {}, "hint": {"a": 1}},
    )
    assertSuccessPartial(
        count_result,
        {"n": 2, "ok": 1.0},
        msg=f"Partial index ({bson_type.value}) should only include docs matching the filter",
    )
