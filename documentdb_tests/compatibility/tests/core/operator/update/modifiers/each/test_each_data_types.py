"""Tests for $each modifier data type coverage.

Covers: BSON type validation for the $each value itself (must be array),
BSON type acceptance for elements within the $each array, and mixed-type
handling.
"""

import pytest

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
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR, TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# ---------------------------------------------------------------------------
# $each value type validation (the value of $each itself must be an array)
# ---------------------------------------------------------------------------

EACH_VALUE_PARAMS = [
    BsonTypeTestCase(
        id="addtoset_each_value",
        msg="$addToSet $each value type",
        keyword="$each",
        valid_types=[BsonType.ARRAY],
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
    BsonTypeTestCase(
        id="push_each_value",
        msg="$push $each value type",
        keyword="$each",
        valid_types=[BsonType.ARRAY],
        default_error_code=BAD_VALUE_ERROR,
    ),
]

VALUE_ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(EACH_VALUE_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", VALUE_ACCEPTANCE_CASES)
def test_each_value_type_accepted(collection, bson_type, sample_value, spec):
    """Test $each accepts array as its value type."""
    collection.insert_one({"_id": 1, "arr": []})
    if spec.id == "addtoset_each_value":
        update = {"$addToSet": {"arr": {"$each": sample_value}}}
    else:
        update = {"$push": {"arr": {"$each": sample_value}}}
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": update}],
        },
    )
    assertNotError(result, msg=f"{spec.msg} should accept {bson_type.value}")


VALUE_REJECTION_CASES = generate_bson_rejection_test_cases(EACH_VALUE_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", VALUE_REJECTION_CASES)
def test_each_value_type_rejected(collection, bson_type, sample_value, spec):
    """Test $each rejects non-array value types."""
    collection.insert_one({"_id": 1, "arr": []})
    if spec.id == "addtoset_each_value":
        update = {"$addToSet": {"arr": {"$each": sample_value}}}
    else:
        update = {"$push": {"arr": {"$each": sample_value}}}
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": update}],
        },
    )
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


# ---------------------------------------------------------------------------
# $each element type acceptance (types allowed inside the $each array)
# ---------------------------------------------------------------------------

EACH_ELEMENT_PARAMS = [
    BsonTypeTestCase(
        id="addtoset_each_element",
        msg="$addToSet $each element type",
        keyword="$each",
        valid_types=list(BsonType),
    ),
    BsonTypeTestCase(
        id="push_each_element",
        msg="$push $each element type",
        keyword="$each",
        valid_types=list(BsonType),
    ),
]

ELEMENT_ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(EACH_ELEMENT_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", ELEMENT_ACCEPTANCE_CASES)
def test_each_element_type_accepted(collection, bson_type, sample_value, spec):
    """Test $each accepts all BSON types as array elements."""
    collection.insert_one({"_id": 1, "arr": []})
    if spec.id == "addtoset_each_element":
        update = {"$addToSet": {"arr": {"$each": [sample_value]}}}
    else:
        update = {"$push": {"arr": {"$each": [sample_value]}}}
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": update}],
        },
    )
    assertNotError(result, msg=f"{spec.msg} should accept {bson_type.value}")


# ---------------------------------------------------------------------------
# Mixed BSON types in a single $each array
# ---------------------------------------------------------------------------

MIXED_TYPE_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="push_mixed_types",
        setup_docs=[{"_id": 1, "arr": []}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [1, "hello", None, {"a": 1}, [1, 2]]}}},
        expected=[{"_id": 1, "arr": [1, "hello", None, {"a": 1}, [1, 2]]}],
        msg="$push $each should handle mixed BSON types",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(MIXED_TYPE_TESTS))
def test_each_mixed_types(collection, test_case):
    """Test $each handles mixed BSON types in a single operation."""
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
