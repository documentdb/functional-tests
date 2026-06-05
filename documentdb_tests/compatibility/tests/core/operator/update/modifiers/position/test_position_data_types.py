"""Tests for $position modifier data type handling.

Covers: valid $position value types (int, long, whole double, whole decimal128),
rejected $position value types, invalid numeric values (fractional, NaN, Infinity),
and BSON type insertion at position.
"""

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertNotError,
    assertResult,
)
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

POSITION_VALUE_PARAMS = [
    BsonTypeTestCase(
        id="position_value",
        msg="$position value type",
        keyword="$position",
        valid_types=[BsonType.INT, BsonType.LONG, BsonType.DOUBLE, BsonType.DECIMAL],
        valid_inputs={
            BsonType.DOUBLE: 2.0,
            BsonType.DECIMAL: Decimal128("1"),
        },
        default_error_code=BAD_VALUE_ERROR,
    ),
]

VALUE_ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(POSITION_VALUE_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", VALUE_ACCEPTANCE_CASES)
def test_position_value_type_accepted(collection, bson_type, sample_value, spec):
    """Test $position accepts valid numeric types."""
    collection.insert_one({"_id": 1, "arr": [10, 20, 30]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$push": {"arr": {"$each": [5], "$position": sample_value}}},
                }
            ],
        },
    )
    assertNotError(result, msg=f"{spec.msg} should accept {bson_type.value}")


VALUE_REJECTION_CASES = generate_bson_rejection_test_cases(POSITION_VALUE_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", VALUE_REJECTION_CASES)
def test_position_value_type_rejected(collection, bson_type, sample_value, spec):
    """Test $position rejects non-numeric types."""
    collection.insert_one({"_id": 1, "arr": [1]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$push": {"arr": {"$each": [2], "$position": sample_value}}},
                }
            ],
        },
    )
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


INVALID_NUMERIC_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="position_fractional_double",
        setup_docs=[{"_id": 1, "arr": [1]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [2], "$position": 1.5}}},
        error_code=BAD_VALUE_ERROR,
        msg="$position with fractional double should fail",
    ),
    UpdateTestCase(
        id="position_nan",
        setup_docs=[{"_id": 1, "arr": [1]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [2], "$position": float("nan")}}},
        error_code=BAD_VALUE_ERROR,
        msg="$position with NaN should fail",
    ),
    UpdateTestCase(
        id="position_infinity",
        setup_docs=[{"_id": 1, "arr": [1]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [2], "$position": float("inf")}}},
        error_code=BAD_VALUE_ERROR,
        msg="$position with Infinity should fail",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(INVALID_NUMERIC_TESTS))
def test_position_invalid_numeric_values(collection, test_case):
    """Test $position rejects fractional, NaN, and Infinity values."""
    collection.insert_many(test_case.setup_docs)
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test_case.query, "u": test_case.update}],
        },
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)
