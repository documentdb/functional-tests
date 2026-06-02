"""Integration tests for array update operators with $[] positional-all.

Tests that verify various update operators work correctly when applied
to all array elements via the $[] operator.
"""

import pytest

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


@pytest.mark.parametrize("test", pytest_params(POSITIONAL_ALL_INTEGRATION_TESTS))
def test_positional_all_integration(collection, test: UpdateTestCase):
    """Test various update operators with $[] positional-all."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    command = {
        "update": collection.name,
        "updates": [{"q": test.query, "u": test.update}],
    }
    result = execute_command(collection, command)
    assertSuccess(result, test.expected, msg=test.msg, raw_res=True)
