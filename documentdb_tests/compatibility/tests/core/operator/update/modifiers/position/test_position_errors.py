"""Tests for $position modifier error cases.

Covers: $position rejection by unsupported update operators and non-array
target field rejection.
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
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    FAILED_TO_PARSE_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

ERROR_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="position_with_addToSet",
        setup_docs=[{"_id": 1, "arr": [1, 2]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"$each": [3], "$position": 0}}},
        error_code=BAD_VALUE_ERROR,
        msg="$position with $addToSet should fail",
    ),
    UpdateTestCase(
        id="position_with_pop",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$pop": {"arr": {"$each": [1], "$position": 0}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$position with $pop should fail",
    ),
    UpdateTestCase(
        id="position_with_pull",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$pull": {"arr": {"$each": [1], "$position": 0}}},
        error_code=BAD_VALUE_ERROR,
        msg="$position with $pull should fail",
    ),
    UpdateTestCase(
        id="position_with_pullAll",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$pullAll": {"arr": {"$each": [1], "$position": 0}}},
        error_code=BAD_VALUE_ERROR,
        msg="$position with $pullAll should fail",
    ),
    UpdateTestCase(
        id="position_with_inc",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$inc": {"arr": {"$each": [3], "$position": 0}}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="$position with $inc should fail",
    ),
    UpdateTestCase(
        id="position_with_mul",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$mul": {"arr": {"$each": [3], "$position": 0}}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="$position with $mul should fail",
    ),
    UpdateTestCase(
        id="rename_rejects_position_doc",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$rename": {"arr": {"$each": [3], "$position": 0}}},
        error_code=BAD_VALUE_ERROR,
        msg="$rename should reject $position doc (expects a string)",
    ),
    UpdateTestCase(
        id="currentDate_rejects_position_doc",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$currentDate": {"arr": {"$each": [3], "$position": 0}}},
        error_code=BAD_VALUE_ERROR,
        msg="$currentDate should reject $position doc",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(ERROR_TESTS))
def test_position_errors(collection, test_case):
    """Test $position modifier error cases."""
    collection.insert_many(test_case.setup_docs)
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test_case.query, "u": test_case.update}],
        },
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)


TARGET_TYPE_PARAMS = [
    BsonTypeTestCase(
        id="position_target",
        msg="$position target field type",
        keyword="$position",
        valid_types=[BsonType.ARRAY],
        default_error_code=BAD_VALUE_ERROR,
    ),
]

TARGET_REJECTION_CASES = generate_bson_rejection_test_cases(TARGET_TYPE_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", TARGET_REJECTION_CASES)
def test_position_target_type_rejected(collection, bson_type, sample_value, spec):
    """Test $push with $position rejects non-array target fields."""
    collection.insert_one({"_id": 1, "arr": sample_value})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$push": {"arr": {"$each": [1], "$position": 0}}},
                }
            ],
        },
    )
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)
