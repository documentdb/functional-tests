"""Tests for $slice modifier error cases.

Covers: $slice with $addToSet, non-push operators with $slice doc,
and non-array target field rejection.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    FAILED_TO_PARSE_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

ERROR_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="slice_with_addToSet",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"$each": [4], "$slice": 2}}},
        error_code=BAD_VALUE_ERROR,
        msg="$slice with $addToSet should fail",
    ),
    # --- Non-push operators with $slice doc ---
    UpdateTestCase(
        id="slice_with_pop",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$pop": {"arr": {"$slice": -1}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$pop with $slice doc should fail",
    ),
    UpdateTestCase(
        id="slice_with_pull",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$pull": {"arr": {"$slice": -1}}},
        error_code=BAD_VALUE_ERROR,
        msg="$pull with $slice doc should fail",
    ),
    UpdateTestCase(
        id="slice_with_inc",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$inc": {"arr": {"$slice": -1}}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="$inc with $slice doc should fail",
    ),
    UpdateTestCase(
        id="slice_with_mul",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$mul": {"arr": {"$slice": -1}}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="$mul with $slice doc should fail",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(ERROR_TESTS))
def test_update_slice_errors(collection, test_case):
    """Test $slice modifier error cases."""
    collection.insert_many(test_case.setup_docs)
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test_case.query, "u": test_case.update}],
        },
    )
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)


# --- Non-array target field type rejection via BsonTypeValidator ---

TARGET_TYPE_PARAMS = [
    BsonTypeTestCase(
        id="slice_target",
        msg="$push with $slice target field type",
        keyword="$slice",
        valid_types=[BsonType.ARRAY],
        default_error_code=BAD_VALUE_ERROR,
    ),
]

TARGET_REJECTION_CASES = generate_bson_rejection_test_cases(TARGET_TYPE_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", TARGET_REJECTION_CASES)
def test_slice_target_type_rejected(collection, bson_type, sample_value, spec):
    """Test $push with $slice rejects non-array target fields."""
    collection.insert_one({"_id": 1, "arr": sample_value})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$push": {"arr": {"$each": [1], "$slice": -1}}},
                }
            ],
        },
    )
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)
