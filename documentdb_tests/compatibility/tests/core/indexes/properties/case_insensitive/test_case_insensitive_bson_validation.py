"""Tests for case-insensitive index BSON type validation.

Verifies that createIndexes correctly rejects invalid BSON types for the
collation and key parameters, and accepts valid BSON types without error.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertNotError
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.index

BSON_PARAMS = [
    BsonTypeTestCase(
        id="collation",
        msg="collation should reject non-object types",
        keyword="collation",
        valid_types=[BsonType.OBJECT],
        valid_inputs={BsonType.OBJECT: {"locale": "en", "strength": 2}},
    ),
    BsonTypeTestCase(
        id="key",
        msg="key should reject non-object types",
        keyword="key",
        valid_types=[BsonType.OBJECT],
        valid_inputs={BsonType.OBJECT: {"name": 1}},
    ),
]

REJECTION_CASES = generate_bson_rejection_test_cases(BSON_PARAMS)
ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(BSON_PARAMS)

_DEFAULT_INDEX_SPEC = {
    "key": {"name": 1},
    "name": "idx_ci",
    "collation": {"locale": "en", "strength": 2},
}


@pytest.mark.parametrize("bson_type,sample_value,spec", REJECTION_CASES)
def test_case_insensitive_rejects_invalid_type(collection, bson_type, sample_value, spec):
    """Test createIndexes rejects invalid BSON types for collation and key."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{**_DEFAULT_INDEX_SPEC, spec.keyword: sample_value}],
        },
    )
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg=spec.msg)


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_case_insensitive_accepts_valid_type(collection, bson_type, sample_value, spec):
    """Test createIndexes accepts valid BSON types for collation and key."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{**_DEFAULT_INDEX_SPEC, spec.keyword: sample_value}],
        },
    )
    assertNotError(result, msg=f"{spec.keyword} should accept {bson_type.value}")
