"""Tests for geospatial-specific index option BSON type validation.

Verifies that 2d-specific (min, max, bits) and 2dsphere-specific
(2dsphereIndexVersion) options reject invalid BSON types and accept valid ones.
"""

import pytest
from bson import Decimal128

from documentdb_tests.framework.assertions import assertFailureCode, assertNotError
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import CANNOT_CREATE_INDEX_ERROR, INVALID_OPTIONS_ERROR
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.index

GEOSPATIAL_INDEX_PARAMS = [
    BsonTypeTestCase(
        id="min",
        msg="min should reject non-numeric types",
        keyword="min",
        valid_types=[BsonType.DOUBLE, BsonType.INT, BsonType.LONG, BsonType.DECIMAL],
        valid_inputs={
            BsonType.DOUBLE: -500.0,
            BsonType.INT: -500,
            BsonType.LONG: -500,
            BsonType.DECIMAL: Decimal128("-500"),
        },
    ),
    BsonTypeTestCase(
        id="max",
        msg="max should reject non-numeric types",
        keyword="max",
        valid_types=[BsonType.DOUBLE, BsonType.INT, BsonType.LONG, BsonType.DECIMAL],
        valid_inputs={
            BsonType.DOUBLE: 500.0,
            BsonType.INT: 500,
            BsonType.LONG: 500,
            BsonType.DECIMAL: Decimal128("500"),
        },
    ),
    BsonTypeTestCase(
        id="bits",
        msg="bits should reject non-numeric types",
        keyword="bits",
        valid_types=[BsonType.DOUBLE, BsonType.INT, BsonType.LONG],
        valid_inputs={BsonType.DOUBLE: 26.0, BsonType.INT: 26, BsonType.LONG: 26},
        error_code_overrides={BsonType.DECIMAL: INVALID_OPTIONS_ERROR},
    ),
    BsonTypeTestCase(
        id="2dsphereIndexVersion",
        msg="2dsphereIndexVersion should reject non-numeric types",
        keyword="2dsphereIndexVersion",
        valid_types=[BsonType.DOUBLE, BsonType.INT, BsonType.LONG],
        valid_inputs={BsonType.DOUBLE: 3.0, BsonType.INT: 3, BsonType.LONG: 3},
        error_code_overrides={BsonType.DECIMAL: CANNOT_CREATE_INDEX_ERROR},
    ),
]

_INDEX_TYPE_FOR_KEYWORD = {
    "min": "2d",
    "max": "2d",
    "bits": "2d",
    "2dsphereIndexVersion": "2dsphere",
}


def _build_index(keyword, value):
    """Build a createIndexes spec with the given option set to value."""
    key_type = _INDEX_TYPE_FOR_KEYWORD[keyword]
    index = {"key": {"loc": key_type}, "name": "test_idx"}
    index[keyword] = value
    return index


REJECTION_CASES = generate_bson_rejection_test_cases(GEOSPATIAL_INDEX_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", REJECTION_CASES)
def test_geospatial_index_option_rejected(collection, bson_type, sample_value, spec):
    """Test geospatial index creation rejects invalid BSON types for options."""
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [_build_index(spec.keyword, sample_value)]},
    )
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(GEOSPATIAL_INDEX_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_geospatial_index_option_accepted(collection, bson_type, sample_value, spec):
    """Test geospatial index creation accepts valid BSON types for options.

    Note: This is a type validation test, not a functional test. We only verify
    the command does not error — we do not check listIndexes to confirm the index
    was created with the correct option value.
    """
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [_build_index(spec.keyword, sample_value)]},
    )
    assertNotError(result, msg=f"{spec.keyword} should accept {bson_type.value}")
