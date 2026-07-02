"""Tests for cross-operator interactions between array update operators.

Covers: conflicting operators on same field (errors), and
non-conflicting operators on different fields (success).
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import CONFLICTING_UPDATE_OPERATORS_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

CONFLICT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "addToSet_and_push_same_field",
        setup_docs=[{"_id": 1, "arr": [1]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": 2}, "$push": {"arr": 3}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="Conflicting $addToSet and $push on same field should error",
    ),
    UpdateTestCase(
        "addToSet_and_pull_same_field",
        setup_docs=[{"_id": 1, "arr": [1, 2]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": 3}, "$pull": {"arr": 1}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="Conflicting $addToSet and $pull on same field should error",
    ),
    UpdateTestCase(
        "pull_and_push_same_field",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$pull": {"arr": 1}, "$push": {"arr": 4}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="Conflicting $pull and $push on same field should error",
    ),
    UpdateTestCase(
        "push_and_pop_same_field",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$push": {"arr": 4}, "$pop": {"arr": 1}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$push and $pop on same field should error",
    ),
    UpdateTestCase(
        "pullAll_and_push_same_field",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$pullAll": {"arr": [1]}, "$push": {"arr": 99}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="Conflicting $pullAll and $push on same field should error",
    ),
    UpdateTestCase(
        "pullAll_and_addToSet_same_field",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$pullAll": {"arr": [1]}, "$addToSet": {"arr": 99}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="Conflicting $pullAll and $addToSet on same field should error",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CONFLICT_TESTS))
def test_array_operator_conflict(collection, test: UpdateTestCase):
    """Test conflicting array update operators on same field errors."""
    collection.insert_many(test.setup_docs)
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update}],
        },
    )
    assertFailureCode(result, test.error_code, msg=test.msg)  # type: ignore[arg-type]


SUCCESS_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "pull_and_set_different_fields",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3], "x": 1}],
        query={"_id": 1},
        update={"$pull": {"arr": 2}, "$set": {"x": 99}},
        expected={"_id": 1, "arr": [1, 3], "x": 99},
        msg="Should allow $pull and $set on different fields",
    ),
    UpdateTestCase(
        "pull_and_push_different_fields",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3], "arr2": [10]}],
        query={"_id": 1},
        update={"$pull": {"arr": 2}, "$push": {"arr2": 20}},
        expected={"_id": 1, "arr": [1, 3], "arr2": [10, 20]},
        msg="Should allow $pull and $push on different fields",
    ),
    UpdateTestCase(
        "push_and_set_different_fields",
        setup_docs=[{"_id": 1, "arr": [1], "x": 0}],
        query={"_id": 1},
        update={"$push": {"arr": 2}, "$set": {"x": 99}},
        expected={"_id": 1, "arr": [1, 2], "x": 99},
        msg="Should allow $push and $set on different fields",
    ),
    UpdateTestCase(
        "pullAll_and_push_different_fields",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3], "arr2": [10]}],
        query={"_id": 1},
        update={"$pullAll": {"arr": [2]}, "$push": {"arr2": 20}},
        expected={"_id": 1, "arr": [1, 3], "arr2": [10, 20]},
        msg="Should allow $pullAll and $push on different fields",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SUCCESS_TESTS))
def test_array_operators_different_fields(collection, test: UpdateTestCase):
    """Test non-conflicting array update operators on different fields succeed."""
    collection.insert_many(test.setup_docs)
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": test.query})
    assertSuccess(result, [test.expected], msg=test.msg)
