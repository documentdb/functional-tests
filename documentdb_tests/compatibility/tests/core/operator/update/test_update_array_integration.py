"""Integration tests for array update operators with $[] positional-all.

Tests that verify various update operators work correctly when applied
to all array elements via the $[] operator.
"""

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

POSITIONAL_ALL_INTEGRATION_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "inc_all_elements",
        setup_docs=[{"_id": 1, "arr": [10, 20, 30]}],
        query={"_id": 1},
        update={"$inc": {"arr.$[]": 5}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] with $inc should increment all elements",
    ),
    UpdateTestCase(
        "inc_mixed_numeric",
        setup_docs=[{"_id": 1, "arr": [1, Int64(2), 3.0]}],
        query={"_id": 1},
        update={"$inc": {"arr.$[]": 10}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] with $inc on mixed numeric types should increment all",
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


POSITIONAL_ALL_INTERACTION_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "positional_all_and_set_different_fields",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3], "x": 10}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": 0, "x": 99}},
        expected={"_id": 1, "arr": [0, 0, 0], "x": 99},
        msg="$[] on one field and $set on another should both succeed",
    ),
    UpdateTestCase(
        "positional_all_and_positional_different_fields",
        setup_docs=[{"_id": 1, "a": [1, 2, 3], "b": [10, 20, 30]}],
        query={"_id": 1, "b": 20},
        update={"$set": {"a.$[]": 0, "b.$": 99}},
        expected={"_id": 1, "a": [0, 0, 0], "b": [10, 99, 30]},
        msg="$[] and $ on different fields in same update should both work",
    ),
]


@pytest.mark.parametrize("test", pytest_params(POSITIONAL_ALL_INTEGRATION_TESTS))
def test_positional_all_operator_integration(collection, test: UpdateTestCase):
    """Test various update operators with $[] positional-all."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    command = {
        "update": collection.name,
        "updates": [{"q": test.query, "u": test.update}],
    }
    result = execute_command(collection, command)
    assertSuccess(result, test.expected, msg=test.msg, raw_res=True)


@pytest.mark.parametrize("test", pytest_params(POSITIONAL_ALL_INTERACTION_TESTS))
def test_positional_all_interaction(collection, test: UpdateTestCase):
    """Test $[] positional-all alongside other operators in same update."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )

    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": test.expected["_id"]}}
    )
    assertSuccess(result, [test.expected], msg=test.msg)
