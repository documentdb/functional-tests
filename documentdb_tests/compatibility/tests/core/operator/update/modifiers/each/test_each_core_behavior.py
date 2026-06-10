"""Tests for $each modifier core behavior with $addToSet and $push."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

CORE_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="addtoset_empty_array",
        setup_docs=[{"_id": 1, "arr": [1, 2]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"$each": []}}},
        expected=[{"_id": 1, "arr": [1, 2]}],
        msg="$addToSet $each with empty array should not modify",
    ),
    UpdateTestCase(
        id="addtoset_single_new",
        setup_docs=[{"_id": 1, "arr": [1]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"$each": [2]}}},
        expected=[{"_id": 1, "arr": [1, 2]}],
        msg="$addToSet $each should add new value",
    ),
    UpdateTestCase(
        id="addtoset_multiple_mixed",
        setup_docs=[{"_id": 1, "arr": [1, 3]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"$each": [1, 2, 3, 4]}}},
        expected=[{"_id": 1, "arr": [1, 3, 2, 4]}],
        msg="$addToSet $each should add only non-duplicate values",
    ),
    UpdateTestCase(
        id="push_empty_array",
        setup_docs=[{"_id": 1, "arr": [1, 2]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": []}}},
        expected=[{"_id": 1, "arr": [1, 2]}],
        msg="$push $each with empty array should not modify document",
    ),
    UpdateTestCase(
        id="push_single_element",
        setup_docs=[{"_id": 1, "arr": [1]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [2]}}},
        expected=[{"_id": 1, "arr": [1, 2]}],
        msg="$push $each with single element should append one element",
    ),
    UpdateTestCase(
        id="push_multiple_elements",
        setup_docs=[{"_id": 1, "arr": [1]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [2, 3, 4]}}},
        expected=[{"_id": 1, "arr": [1, 2, 3, 4]}],
        msg="$push $each with multiple elements should append all",
    ),
    UpdateTestCase(
        id="push_duplicates_allowed",
        setup_docs=[{"_id": 1, "arr": [1]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [1, 1, 2, 2, 3]}}},
        expected=[{"_id": 1, "arr": [1, 1, 1, 2, 2, 3]}],
        msg="$push $each should allow duplicate elements",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(CORE_TESTS))
def test_each_core_behavior(collection, test_case):
    """Test $each modifier core behavior with $addToSet and $push."""
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
