"""Tests for $slice modifier data type handling.

Covers: valid $slice value types (int, long, whole double, whole decimal128),
rejected $slice value types, invalid numeric values (fractional, NaN, Infinity),
array element type preservation after slicing, and BSON type distinction.
"""

import pytest
from bson import Decimal128

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

SLICE_VALUE_PARAMS = [
    BsonTypeTestCase(
        id="slice_value",
        msg="$slice value type",
        keyword="$slice",
        valid_types=[BsonType.INT, BsonType.LONG, BsonType.DOUBLE, BsonType.DECIMAL],
        valid_inputs={
            BsonType.DOUBLE: 2.0,
            BsonType.DECIMAL: Decimal128("2"),
        },
        default_error_code=BAD_VALUE_ERROR,
    ),
]

VALUE_ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(SLICE_VALUE_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", VALUE_ACCEPTANCE_CASES)
def test_slice_value_type_accepted(collection, bson_type, sample_value, spec):
    """Test $slice accepts valid numeric types as value."""
    collection.insert_one({"_id": 1, "arr": [1, 2, 3, 4, 5]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$push": {"arr": {"$each": [], "$slice": sample_value}}},
                }
            ],
        },
    )
    assertNotError(result, msg=f"{spec.msg} should accept {bson_type.value}")


VALUE_REJECTION_CASES = generate_bson_rejection_test_cases(SLICE_VALUE_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", VALUE_REJECTION_CASES)
def test_slice_value_type_rejected(collection, bson_type, sample_value, spec):
    """Test $slice rejects non-numeric types."""
    collection.insert_one({"_id": 1, "arr": [1, 2, 3]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$push": {"arr": {"$each": [], "$slice": sample_value}}},
                }
            ],
        },
    )
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


INVALID_NUMERIC_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="slice_fractional_double",
        setup_docs=[{"_id": 1, "arr": [1]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$slice": 2.5}}},
        error_code=BAD_VALUE_ERROR,
        msg="$slice with fractional double should fail",
    ),
    UpdateTestCase(
        id="slice_nan",
        setup_docs=[{"_id": 1, "arr": [1]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$slice": float("nan")}}},
        error_code=BAD_VALUE_ERROR,
        msg="$slice with NaN should fail",
    ),
    UpdateTestCase(
        id="slice_infinity",
        setup_docs=[{"_id": 1, "arr": [1]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$slice": float("inf")}}},
        error_code=BAD_VALUE_ERROR,
        msg="$slice with Infinity should fail",
    ),
    UpdateTestCase(
        id="slice_negative_infinity",
        setup_docs=[{"_id": 1, "arr": [1]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$slice": float("-inf")}}},
        error_code=BAD_VALUE_ERROR,
        msg="$slice with -Infinity should fail",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(INVALID_NUMERIC_TESTS))
def test_slice_invalid_numeric_values(collection, test_case):
    """Test $slice rejects fractional, NaN, and Infinity values."""
    collection.insert_many(test_case.setup_docs)
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test_case.query, "u": test_case.update}],
        },
    )
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)


ELEMENT_PRESERVATION_PARAMS = [
    BsonTypeTestCase(
        id="slice_element",
        msg="$slice element type preservation",
        keyword="$slice",
        valid_types=list(BsonType),
        valid_inputs={
            BsonType.BIN_DATA: b"\x00\x01",
        },
    ),
]

ELEMENT_PRESERVATION_CASES = generate_bson_acceptance_test_cases(ELEMENT_PRESERVATION_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", ELEMENT_PRESERVATION_CASES)
def test_slice_preserves_element_type(collection, bson_type, sample_value, spec):
    """Test array elements of all BSON types are preserved after $slice."""
    collection.insert_one({"_id": 1, "arr": ["sentinel", sample_value, "tail"]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$push": {"arr": {"$each": [], "$slice": -2}}}}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1, "arr": [sample_value, "tail"]}],
        msg=f"{spec.msg} should preserve {bson_type.value}",
    )


def test_slice_bson_type_distinction(collection):
    """Test distinct BSON types remain distinct after $slice."""
    collection.insert_one({"_id": 1, "arr": [0, False, None, ""]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$push": {"arr": {"$each": [], "$slice": -4}}}}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1, "arr": [0, False, None, ""]}],
        msg="0, false, null, empty string must remain distinct after slice",
    )
