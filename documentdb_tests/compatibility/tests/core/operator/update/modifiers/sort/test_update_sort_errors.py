"""Tests for $sort update modifier error cases.

Covers: missing $each, $sort with incompatible operators ($addToSet, $pull,
$pullAll, $pop), target not array, and containing array field path behavior.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccess
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

SORT_VALUE_VALIDATION_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="sort_direction_zero",
        setup_docs=[{"_id": 1, "arr": [3, 1, 2]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": 0}}},
        error_code=BAD_VALUE_ERROR,
        msg="$sort: 0 should fail with BadValue",
    ),
    UpdateTestCase(
        id="sort_direction_two",
        setup_docs=[{"_id": 1, "arr": [3, 1, 2]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": 2}}},
        error_code=BAD_VALUE_ERROR,
        msg="$sort: 2 should fail with BadValue",
    ),
    UpdateTestCase(
        id="sort_field_direction_zero",
        setup_docs=[{"_id": 1, "arr": [{"a": 1}]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": {"a": 0}}}},
        error_code=BAD_VALUE_ERROR,
        msg="$sort: {a: 0} should fail with BadValue",
    ),
    UpdateTestCase(
        id="sort_field_direction_string",
        setup_docs=[{"_id": 1, "arr": [{"a": 1}]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": {"a": "asc"}}}},
        error_code=BAD_VALUE_ERROR,
        msg="$sort: {a: 'asc'} should fail with BadValue",
    ),
    UpdateTestCase(
        id="sort_empty_object",
        setup_docs=[{"_id": 1, "arr": [{"a": 1}]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": {}}}},
        error_code=BAD_VALUE_ERROR,
        msg="$sort: {} (empty object) should fail with BadValue",
    ),
    UpdateTestCase(
        id="sort_trailing_dot_key",
        setup_docs=[{"_id": 1, "arr": [{"a": 1}]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": {"a.": 1}}}},
        error_code=BAD_VALUE_ERROR,
        msg="$sort with trailing dot in key path should fail",
    ),
    UpdateTestCase(
        id="sort_empty_string_key",
        setup_docs=[{"_id": 1, "arr": [{"a": 1}]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": {"": 1}}}},
        error_code=BAD_VALUE_ERROR,
        msg="$sort with empty string key should fail",
    ),
]

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

INCOMPATIBLE_OPERATOR_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="addtoset_with_sort",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"$each": [4], "$sort": 1}}},
        error_code=BAD_VALUE_ERROR,
        msg="$addToSet with $sort should fail — $sort only works with $push",
    ),
    UpdateTestCase(
        id="pull_with_each_sort",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$pull": {"arr": {"$each": [1], "$sort": 1}}},
        error_code=BAD_VALUE_ERROR,
        msg="$pull with $each/$sort should fail — $sort only works with $push",
    ),
    UpdateTestCase(
        id="pullAll_with_each_sort",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$pullAll": {"arr": {"$each": [1], "$sort": 1}}},
        error_code=BAD_VALUE_ERROR,
        msg="$pullAll with $each/$sort should fail — $sort only works with $push",
    ),
    UpdateTestCase(
        id="pop_with_each_sort",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$pop": {"arr": {"$each": [1], "$sort": 1}}},
        error_code=BAD_VALUE_ERROR,
        msg="$pop with $each/$sort should fail — $sort only works with $push",
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

ALL_ERROR_TESTS = INCOMPATIBLE_OPERATOR_TESTS + TARGET_NOT_ARRAY_TESTS + SORT_VALUE_VALIDATION_TESTS

ALL_SUCCESS_TESTS = MISSING_EACH_TESTS + CONTAINING_ARRAY_FIELD_PATH_TESTS


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


@pytest.mark.parametrize("test_case", pytest_params(ALL_SUCCESS_TESTS))
def test_update_sort_edge_cases(collection, test_case):
    """Test $sort modifier edge cases and special behavior."""
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
