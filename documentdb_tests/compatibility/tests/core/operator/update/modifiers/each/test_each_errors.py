"""Tests for $each modifier error cases.

Covers: non-array target fields and invalid modifier values.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertResult
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# ---------------------------------------------------------------------------
# Target field type validation (the field $each operates on must be an array)
# ---------------------------------------------------------------------------

TARGET_TYPE_PARAMS = [
    BsonTypeTestCase(
        id="addtoset_each_target",
        msg="$addToSet $each target field type",
        keyword="$each",
        valid_types=[BsonType.ARRAY],
        default_error_code=BAD_VALUE_ERROR,
    ),
    BsonTypeTestCase(
        id="push_each_target",
        msg="$push $each target field type",
        keyword="$each",
        valid_types=[BsonType.ARRAY],
        default_error_code=BAD_VALUE_ERROR,
    ),
]

TARGET_REJECTION_CASES = generate_bson_rejection_test_cases(TARGET_TYPE_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", TARGET_REJECTION_CASES)
def test_each_target_type_rejected(collection, bson_type, sample_value, spec):
    """Test $each rejects non-array target fields."""
    collection.insert_one({"_id": 1, "arr": sample_value})
    if spec.id == "addtoset_each_target":
        update = {"$addToSet": {"arr": {"$each": [1]}}}
    else:
        update = {"$push": {"arr": {"$each": [1]}}}
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": update}],
        },
    )
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


# ---------------------------------------------------------------------------
# Modifier error cases ($sort, $slice, $position validation)
# ---------------------------------------------------------------------------

MODIFIER_ERROR_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="unrecognized_modifier",
        setup_docs=[{"_id": 1, "arr": [1]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [2], "$xxx": 1}}},
        error_code=BAD_VALUE_ERROR,
        msg="$push $each with unrecognized modifier should fail",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(MODIFIER_ERROR_TESTS))
def test_each_modifier_errors(collection, test_case):
    """Test $each modifier error cases."""
    if test_case.setup_docs:
        collection.insert_many(test_case.setup_docs)
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test_case.query, "u": test_case.update}],
        },
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)
