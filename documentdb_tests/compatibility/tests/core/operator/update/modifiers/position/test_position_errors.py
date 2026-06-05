"""Tests for $position modifier error cases.

Covers: missing $each requirement, $addToSet rejection, non-array target field,
and null target field.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
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
        id="target_is_integer",
        setup_docs=[{"_id": 1, "arr": 42}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [1], "$position": 0}}},
        error_code=BAD_VALUE_ERROR,
        msg="$push with $position on integer field should fail",
    ),
    UpdateTestCase(
        id="target_is_string",
        setup_docs=[{"_id": 1, "arr": "hello"}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [1], "$position": 0}}},
        error_code=BAD_VALUE_ERROR,
        msg="$push with $position on string field should fail",
    ),
    UpdateTestCase(
        id="target_is_object",
        setup_docs=[{"_id": 1, "arr": {"key": "val"}}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [1], "$position": 0}}},
        error_code=BAD_VALUE_ERROR,
        msg="$push with $position on object field should fail",
    ),
    UpdateTestCase(
        id="target_is_null",
        setup_docs=[{"_id": 1, "arr": None}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [1], "$position": 0}}},
        error_code=BAD_VALUE_ERROR,
        msg="$push with $position on null field should fail",
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
