"""Tests for $[] positional-all update operator core behavior.

Covers: update all elements, empty array, single element, query filtering,
update command integration, and various update operators.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

CORE_BEHAVIOR_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "set_all_elements",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": 0}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] with $set should update all elements",
    ),
    UpdateTestCase(
        "inc_all_elements",
        setup_docs=[{"_id": 1, "arr": [10, 20, 30]}],
        query={"_id": 1},
        update={"$inc": {"arr.$[]": 5}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] with $inc should increment all elements",
    ),
    UpdateTestCase(
        "mul_all_elements",
        setup_docs=[{"_id": 1, "arr": [2, 3, 4]}],
        query={"_id": 1},
        update={"$mul": {"arr.$[]": 2}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] with $mul should multiply all elements",
    ),
    UpdateTestCase(
        "empty_array_noop",
        setup_docs=[{"_id": 1, "arr": []}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": 99}},
        expected={"n": 1, "nModified": 0, "ok": 1.0},
        msg="$[] on empty array should be no-op",
    ),
    UpdateTestCase(
        "single_element",
        setup_docs=[{"_id": 1, "arr": [42]}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": 99}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] on single element array should update that element",
    ),
]


# --- Query Filtering ---

QUERY_FILTERING_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "only_matched_docs_updated",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3], "x": 1}, {"_id": 2, "arr": [4, 5, 6], "x": 2}],
        query={"x": 1},
        update={"$set": {"arr.$[]": 0}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] should only update elements in matched documents",
    ),
    UpdateTestCase(
        "query_not_referencing_array",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3], "x": "a"}],
        query={"x": "a"},
        update={"$set": {"arr.$[]": 0}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] with query not referencing array field should update all elements in matched docs",
    ),
]


# --- Update Command Integration ---

COMMAND_INTEGRATION_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "update_one",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": 0}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] should work with updateOne",
    ),
]


# --- JS-based: $[] with various update operators ---

JS_UPDATE_OPERATORS_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "unset_all",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$unset": {"arr.$[]": ""}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] with $unset should set all elements to null",
    ),
    UpdateTestCase(
        "addToSet_on_array_of_arrays",
        setup_docs=[{"_id": 1, "arr": [[1, 2], [3, 4]]}],
        query={"_id": 1},
        update={"$addToSet": {"arr.$[]": 99}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] with $addToSet on array of arrays should add to each sub-array",
    ),
    UpdateTestCase(
        "pop_on_array_of_arrays",
        setup_docs=[{"_id": 1, "arr": [[1, 2, 3], [4, 5, 6]]}],
        query={"_id": 1},
        update={"$pop": {"arr.$[]": 1}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] with $pop on array of arrays should pop from each sub-array",
    ),
    UpdateTestCase(
        "push_on_array_of_arrays",
        setup_docs=[{"_id": 1, "arr": [[1, 2], [3, 4]]}],
        query={"_id": 1},
        update={"$push": {"arr.$[]": 99}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] with $push on array of arrays should append to each sub-array",
    ),
    UpdateTestCase(
        "pull_on_array_of_arrays",
        setup_docs=[{"_id": 1, "arr": [[1, 2, 3], [2, 3, 4]]}],
        query={"_id": 1},
        update={"$pull": {"arr.$[]": 2}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] with $pull on array of arrays should remove matching from each sub-array",
    ),
    UpdateTestCase(
        "pullAll_on_array_of_arrays",
        setup_docs=[{"_id": 1, "arr": [[1, 2, 3], [2, 3, 4]]}],
        query={"_id": 1},
        update={"$pullAll": {"arr.$[]": [2, 3]}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] with $pullAll on array of arrays should remove values from each sub-array",
    ),
]


# --- Update Operators ---

UPDATE_OPERATOR_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "min_all",
        setup_docs=[{"_id": 1, "arr": [10, 20, 30]}],
        query={"_id": 1},
        update={"$min": {"arr.$[]": 15}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] with $min should conditionally update all elements",
    ),
    UpdateTestCase(
        "max_all",
        setup_docs=[{"_id": 1, "arr": [10, 20, 30]}],
        query={"_id": 1},
        update={"$max": {"arr.$[]": 25}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] with $max should conditionally update all elements",
    ),
]


ALL_TESTS = (
    CORE_BEHAVIOR_TESTS
    + QUERY_FILTERING_TESTS
    + COMMAND_INTEGRATION_TESTS
    + JS_UPDATE_OPERATORS_TESTS
    + UPDATE_OPERATOR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_positional_all_core(collection, test: UpdateTestCase):
    """Test $[] positional-all update operator core behavior."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    command = {
        "update": collection.name,
        "updates": [{"q": test.query, "u": test.update}],
    }
    result = execute_command(collection, command)
    assertSuccess(result, test.expected, msg=test.msg, raw_res=True)
