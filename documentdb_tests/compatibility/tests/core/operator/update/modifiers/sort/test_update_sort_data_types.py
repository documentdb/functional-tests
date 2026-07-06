"""Tests for $sort update modifier data type behavior.

Covers: sort spec type validation and numeric equivalence across types.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertNotError,
    assertSuccess,
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

# --- Sort spec type validation (framework + manual) ---

SORT_SPEC_TYPE_PARAMS = [
    BsonTypeTestCase(
        id="sort_spec_value",
        msg="$sort spec value type",
        keyword="$sort",
        valid_types=[
            BsonType.INT,
            BsonType.LONG,
            BsonType.DOUBLE,
            BsonType.DECIMAL,
            BsonType.OBJECT,
        ],
        valid_inputs={
            BsonType.INT: 1,
            BsonType.LONG: Int64(1),
            BsonType.DOUBLE: 1.0,
            BsonType.DECIMAL: Decimal128("1"),
            BsonType.OBJECT: {"a": 1},
        },
        default_error_code=BAD_VALUE_ERROR,
    ),
]

SORT_SPEC_ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(SORT_SPEC_TYPE_PARAMS)
SORT_SPEC_REJECTION_CASES = generate_bson_rejection_test_cases(SORT_SPEC_TYPE_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", SORT_SPEC_ACCEPTANCE_CASES)
def test_update_sort_spec_type_accepted(collection, bson_type, sample_value, spec):
    """Test $sort accepts valid BSON types as sort spec value."""
    collection.insert_one({"_id": 1, "arr": [3, 1, 2]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$push": {"arr": {"$each": [], "$sort": sample_value}}},
                }
            ],
        },
    )
    assertNotError(result, msg=f"{spec.msg} should accept {bson_type.value}")


@pytest.mark.parametrize("bson_type,sample_value,spec", SORT_SPEC_REJECTION_CASES)
def test_update_sort_spec_type_rejected(collection, bson_type, sample_value, spec):
    """Test $sort rejects invalid BSON types as sort spec value."""
    collection.insert_one({"_id": 1, "arr": [3, 1, 2]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$push": {"arr": {"$each": [], "$sort": sample_value}}},
                }
            ],
        },
    )
    assertFailureCode(
        result,
        spec.expected_code(bson_type),
        msg=f"{spec.msg} should reject {bson_type.value}",
    )


NUMERIC_EQUIVALENCE_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="doubles_sort_ascending",
        setup_docs=[{"_id": 1, "arr": [3.5, 1.2, 4.8, 2.1]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": 1}}},
        expected=[{"_id": 1, "arr": [1.2, 2.1, 3.5, 4.8]}],
        msg="Array of doubles should sort numerically ascending",
    ),
    UpdateTestCase(
        id="cross_type_numeric_sort",
        setup_docs=[{"_id": 1, "arr": [Int64(3), 1, 2.0, Decimal128("4")]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": 1}}},
        expected=[{"_id": 1, "arr": [1, 2.0, Int64(3), Decimal128("4")]}],
        msg="Cross-type numeric values should sort by numeric value",
    ),
    UpdateTestCase(
        id="cross_type_numeric_document_sort",
        setup_docs=[
            {
                "_id": 1,
                "arr": [
                    {"val": Int64(3)},
                    {"val": 1.0},
                    {"val": 2},
                    {"val": Decimal128("4")},
                ],
            }
        ],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": {"val": 1}}}},
        expected=[
            {
                "_id": 1,
                "arr": [
                    {"val": 1.0},
                    {"val": 2},
                    {"val": Int64(3)},
                    {"val": Decimal128("4")},
                ],
            }
        ],
        msg="Document sort should order mixed numeric types by value",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(NUMERIC_EQUIVALENCE_TESTS))
def test_update_sort_data_types(collection, test_case):
    """Test $sort data type behavior."""
    collection.insert_many(test_case.setup_docs)
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test_case.query, "u": test_case.update}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": test_case.query})
    assertSuccess(result, test_case.expected, msg=test_case.msg)
