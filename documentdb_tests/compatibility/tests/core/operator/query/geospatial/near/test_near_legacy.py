"""Tests for $near legacy mode — 2d index, planar distance, coordinate pairs."""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

LEGACY_ERROR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="legacy_single_element",
        filter={"loc": {"$near": [-73.9667]}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject single element legacy array",
    ),
    QueryTestCase(
        id="legacy_empty_array",
        filter={"loc": {"$near": []}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject empty legacy array",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LEGACY_ERROR_TESTS))
def test_near_legacy_errors(collection, test):
    """Verifies $near rejects invalid legacy inputs."""
    collection.create_index([("loc", "2d")])
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertFailureCode(result, test.error_code, msg=test.msg)


def test_near_legacy_distance_ordering(collection):
    """Verifies $near with 2d index returns results in distance order."""
    collection.create_index([("loc", "2d")])
    collection.insert_many(
        [
            {"_id": 1, "loc": [5, 5]},
            {"_id": 2, "loc": [0, 0]},
            {"_id": 3, "loc": [1, 1]},
        ]
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"loc": {"$near": [0, 0]}}},
    )
    assertSuccess(
        result,
        [
            {"_id": 2, "loc": [0, 0]},
            {"_id": 3, "loc": [1, 1]},
            {"_id": 1, "loc": [5, 5]},
        ],
        msg="Should sort by distance with 2d index",
    )


LEGACY_BSON_PARAMS = [
    BsonTypeTestCase(
        id="legacy_coordinates",
        msg="legacy $near coordinates should reject non-numeric element types",
        keyword="legacy_coordinates",
        valid_types=[BsonType.DOUBLE, BsonType.INT, BsonType.LONG, BsonType.DECIMAL],
        valid_inputs={
            BsonType.DOUBLE: 0.0,
            BsonType.INT: 0,
            BsonType.LONG: Int64(0),
            BsonType.DECIMAL: Decimal128("0"),
        },
        default_error_code=BAD_VALUE_ERROR,
    ),
]

LEGACY_BSON_REJECTION = generate_bson_rejection_test_cases(LEGACY_BSON_PARAMS)
LEGACY_BSON_ACCEPTANCE = generate_bson_acceptance_test_cases(LEGACY_BSON_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", LEGACY_BSON_REJECTION)
def test_near_legacy_bson_type_rejected(collection, bson_type, sample_value, spec):
    """Verifies legacy $near rejects invalid BSON types."""
    collection.create_index([("loc", "2d")])
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"loc": {"$near": [sample_value, sample_value]}}},
    )
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


@pytest.mark.parametrize("bson_type,sample_value,spec", LEGACY_BSON_ACCEPTANCE)
def test_near_legacy_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Verifies legacy $near accepts valid BSON types."""
    collection.create_index([("loc", "2d")])
    collection.insert_one({"_id": 1, "loc": [0, 0]})
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"loc": {"$near": [sample_value, sample_value]}}},
    )
    assertSuccess(
        result,
        [{"_id": 1, "loc": [0, 0]}],
        msg=f"legacy $near should accept {bson_type.value}",
    )
