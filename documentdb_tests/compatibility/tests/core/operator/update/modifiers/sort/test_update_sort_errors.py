"""Tests for $sort update modifier error cases.

Covers: missing $each, $sort with $addToSet, target not array,
unrecognized modifiers, and containing array field path behavior.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccess
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

MISSING_EACH_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="sort_without_each_pushes_literal",
        setup_docs=[{"_id": 1, "arr": [3, 1, 2]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$sort": 1}}},
        expected=[{"_id": 1, "arr": [3, 1, 2, {"$sort": 1}]}],
        msg="$push with $sort but no $each should push literal document",
    ),
]

ADDTOSET_WITH_SORT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="addtoset_with_sort",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"$each": [4], "$sort": 1}}},
        error_code=BAD_VALUE_ERROR,
        msg="$addToSet with $sort should fail — $sort only works with $push",
    ),
]

TARGET_NOT_ARRAY_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="sort_target_not_array",
        setup_docs=[{"_id": 1, "arr": "not_an_array"}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [1], "$sort": 1}}},
        error_code=BAD_VALUE_ERROR,
        msg="$push $each $sort on non-array field should fail with BadValue",
    ),
]

UNRECOGNIZED_MODIFIER_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="unrecognized_modifier_with_sort",
        setup_docs=[{"_id": 1, "arr": [1]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [2], "$sort": 1, "$xxx": 1}}},
        error_code=BAD_VALUE_ERROR,
        msg="Unrecognized modifier alongside $sort should fail",
    ),
]

CONTAINING_ARRAY_FIELD_PATH_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="sort_by_containing_array_field_path",
        setup_docs=[
            {
                "_id": 1,
                "arr": [{"score": 3}, {"score": 1}, {"score": 2}],
            }
        ],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": {"arr.score": 1}}}},
        expected=[
            {
                "_id": 1,
                "arr": [{"score": 3}, {"score": 1}, {"score": 2}],
            }
        ],
        msg="Sort by containing array field path has no matching fields, order unchanged",
    ),
]

PUSH_WITHOUT_EACH_LITERAL_TESTS: list[UpdateTestCase] = []

ALL_ERROR_TESTS = ADDTOSET_WITH_SORT_TESTS + TARGET_NOT_ARRAY_TESTS + UNRECOGNIZED_MODIFIER_TESTS


@pytest.mark.parametrize("test_case", pytest_params(ALL_ERROR_TESTS))
def test_update_sort_errors(collection, test_case):
    """Test $sort modifier error cases."""
    collection.insert_many(test_case.setup_docs)
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test_case.query, "u": test_case.update}],
        },
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)


@pytest.mark.parametrize("test_case", pytest_params(MISSING_EACH_TESTS))
def test_update_sort_without_each(collection, test_case):
    """Test $push with $sort but no $each pushes literal document."""
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


@pytest.mark.parametrize("test_case", pytest_params(CONTAINING_ARRAY_FIELD_PATH_TESTS))
def test_update_sort_containing_array_path(collection, test_case):
    """Test $sort with field path referencing the containing array."""
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
