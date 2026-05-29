"""
Tests for $box BSON type comparison.

Verifies that $box coordinate values reject invalid BSON types with expected
error codes and accept valid numeric BSON types without error.
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
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command

BOX_COORDINATE_PARAMS = [
    BsonTypeTestCase(
        id="box_coordinate",
        msg="$box coordinates should reject non-numeric types",
        keyword="$box",
        valid_types=[BsonType.DOUBLE, BsonType.INT, BsonType.LONG, BsonType.DECIMAL],
        default_error_code=BAD_VALUE_ERROR,
        valid_inputs={
            BsonType.DOUBLE: 10.5,
            BsonType.INT: 10,
            BsonType.LONG: Int64(10),
            BsonType.DECIMAL: Decimal128("10"),
        },
    ),
]

REJECTION_CASES = generate_bson_rejection_test_cases(BOX_COORDINATE_PARAMS)


@pytest.mark.parametrize(
    "bson_type,sample_value,spec",
    REJECTION_CASES,
)
def test_box_bson_type_rejected(collection, bson_type, sample_value, spec):
    """Test $box rejects invalid BSON types as coordinate values."""
    query = {"loc": {"$geoWithin": {"$box": [[sample_value, sample_value], [10, 10]]}}}
    result = execute_command(collection, {"find": collection.name, "filter": query})
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(BOX_COORDINATE_PARAMS)


@pytest.mark.parametrize(
    "bson_type,sample_value,spec",
    ACCEPTANCE_CASES,
)
def test_box_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Test $box accepts valid numeric BSON types as coordinate values."""
    collection.insert_many(
        [
            {"_id": 1, "loc": [5, 5]},
            {"_id": 2, "loc": [-5, -5]},
        ]
    )
    query = {"loc": {"$geoWithin": {"$box": [[0, 0], [sample_value, sample_value]]}}}
    result = execute_command(collection, {"find": collection.name, "filter": query})
    assertSuccess(result, [{"_id": 1, "loc": [5, 5]}], ignore_doc_order=True)
