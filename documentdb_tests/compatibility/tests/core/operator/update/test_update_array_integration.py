"""Integration tests for array update operators.

Tests that verify interactions between array update operators and various
query operators, ensuring correct element matching and update behavior.
"""

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

POSITIONAL_ALL_INTEGRATION_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "inc_all_elements",
        setup_docs=[{"_id": 1, "arr": [10, 20, 30]}],
        query={"_id": 1},
        update={"$inc": {"arr.$[]": 5}},
        expected={"_id": 1, "arr": [15, 25, 35]},
        msg="$[] with $inc should increment all elements",
    ),
    UpdateTestCase(
        "inc_mixed_numeric",
        setup_docs=[{"_id": 1, "arr": [1, Int64(2), 3.0]}],
        query={"_id": 1},
        update={"$inc": {"arr.$[]": 10}},
        expected={"_id": 1, "arr": [11, Int64(12), 13.0]},
        msg="$[] with $inc on mixed numeric types should increment all",
    ),
    UpdateTestCase(
        "mul_all_elements",
        setup_docs=[{"_id": 1, "arr": [2, 3, 4]}],
        query={"_id": 1},
        update={"$mul": {"arr.$[]": 2}},
        expected={"_id": 1, "arr": [4, 6, 8]},
        msg="$[] with $mul should multiply all elements",
    ),
    UpdateTestCase(
        "addToSet_on_array_of_arrays",
        setup_docs=[{"_id": 1, "arr": [[1, 2], [3, 4]]}],
        query={"_id": 1},
        update={"$addToSet": {"arr.$[]": 99}},
        expected={"_id": 1, "arr": [[1, 2, 99], [3, 4, 99]]},
        msg="$[] with $addToSet on array of arrays should add to each sub-array",
    ),
    UpdateTestCase(
        "pop_on_array_of_arrays",
        setup_docs=[{"_id": 1, "arr": [[1, 2, 3], [4, 5, 6]]}],
        query={"_id": 1},
        update={"$pop": {"arr.$[]": 1}},
        expected={"_id": 1, "arr": [[1, 2], [4, 5]]},
        msg="$[] with $pop on array of arrays should pop from each sub-array",
    ),
    UpdateTestCase(
        "push_on_array_of_arrays",
        setup_docs=[{"_id": 1, "arr": [[1, 2], [3, 4]]}],
        query={"_id": 1},
        update={"$push": {"arr.$[]": 99}},
        expected={"_id": 1, "arr": [[1, 2, 99], [3, 4, 99]]},
        msg="$[] with $push on array of arrays should append to each sub-array",
    ),
    UpdateTestCase(
        "pull_on_array_of_arrays",
        setup_docs=[{"_id": 1, "arr": [[1, 2, 3], [2, 3, 4]]}],
        query={"_id": 1},
        update={"$pull": {"arr.$[]": 2}},
        expected={"_id": 1, "arr": [[1, 3], [3, 4]]},
        msg="$[] with $pull on array of arrays should remove matching from each sub-array",
    ),
    UpdateTestCase(
        "pullAll_on_array_of_arrays",
        setup_docs=[{"_id": 1, "arr": [[1, 2, 3], [2, 3, 4]]}],
        query={"_id": 1},
        update={"$pullAll": {"arr.$[]": [2, 3]}},
        expected={"_id": 1, "arr": [[1], [4]]},
        msg="$[] with $pullAll on array of arrays should remove values from each sub-array",
    ),
    UpdateTestCase(
        "unset_all_elements",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$unset": {"arr.$[]": ""}},
        expected={"_id": 1, "arr": [None, None, None]},
        msg="$[] with $unset should set all elements to null",
    ),
    UpdateTestCase(
        "min_all",
        setup_docs=[{"_id": 1, "arr": [10, 20, 30]}],
        query={"_id": 1},
        update={"$min": {"arr.$[]": 15}},
        expected={"_id": 1, "arr": [10, 15, 15]},
        msg="$[] with $min should conditionally update all elements",
    ),
    UpdateTestCase(
        "max_all",
        setup_docs=[{"_id": 1, "arr": [10, 20, 30]}],
        query={"_id": 1},
        update={"$max": {"arr.$[]": 25}},
        expected={"_id": 1, "arr": [25, 25, 30]},
        msg="$[] with $max should conditionally update all elements",
    ),
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

    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update}],
        },
    )

    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": test.expected["_id"]}}
    )
    assertSuccess(result, [test.expected], msg=test.msg)


POSITIONAL_INTEGRATION_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "gt_condition",
        setup_docs=[{"_id": 1, "arr": [5, 15, 25]}],
        query={"_id": 1, "arr": {"$gt": 10}},
        update={"$set": {"arr.$": 99}},
        expected={"_id": 1, "arr": [5, 99, 25]},
        msg="$ with $gt should match first element > value",
    ),
    UpdateTestCase(
        "lt_condition",
        setup_docs=[{"_id": 1, "arr": [5, 15, 25]}],
        query={"_id": 1, "arr": {"$lt": 20}},
        update={"$set": {"arr.$": 99}},
        expected={"_id": 1, "arr": [99, 15, 25]},
        msg="$ with $lt should match first element < value",
    ),
    UpdateTestCase(
        "gte_condition",
        setup_docs=[{"_id": 1, "arr": [5, 15, 25]}],
        query={"_id": 1, "arr": {"$gte": 15}},
        update={"$set": {"arr.$": 99}},
        expected={"_id": 1, "arr": [5, 99, 25]},
        msg="$ with $gte should match first element >= value",
    ),
    UpdateTestCase(
        "lte_condition",
        setup_docs=[{"_id": 1, "arr": [5, 15, 25]}],
        query={"_id": 1, "arr": {"$lte": 15}},
        update={"$set": {"arr.$": 99}},
        expected={"_id": 1, "arr": [99, 15, 25]},
        msg="$ with $lte should match first element <= value",
    ),
    UpdateTestCase(
        "in_condition",
        setup_docs=[{"_id": 1, "arr": [5, 15, 25]}],
        query={"_id": 1, "arr": {"$in": [15, 25]}},
        update={"$set": {"arr.$": 99}},
        expected={"_id": 1, "arr": [5, 99, 25]},
        msg="$ with $in should match first element in list",
    ),
    UpdateTestCase(
        "elemMatch_comparison_operators",
        setup_docs=[{"_id": 1, "arr": [{"v": 5}, {"v": 15}, {"v": 25}]}],
        query={"_id": 1, "arr": {"$elemMatch": {"v": {"$gt": 10, "$lt": 20}}}},
        update={"$set": {"arr.$.v": 99}},
        expected={"_id": 1, "arr": [{"v": 5}, {"v": 99}, {"v": 25}]},
        msg="$ with $elemMatch containing comparison operators should match correct position",
    ),
    UpdateTestCase(
        "elemMatch_with_regex",
        setup_docs=[{"_id": 1, "arr": [{"s": "abc"}, {"s": "xyz"}, {"s": "def"}]}],
        query={"_id": 1, "arr": {"$elemMatch": {"s": {"$regex": "^x"}}}},
        update={"$set": {"arr.$.s": "matched"}},
        expected={"_id": 1, "arr": [{"s": "abc"}, {"s": "matched"}, {"s": "def"}]},
        msg="$ with $elemMatch containing $regex should match correct position",
    ),
    UpdateTestCase(
        "negation_inside_elemMatch",
        setup_docs=[{"_id": 1, "arr": [{"x": 1}, {"x": 2}, {"x": 3}]}],
        query={"_id": 1, "arr": {"$elemMatch": {"x": {"$ne": 1}}}},
        update={"$set": {"arr.$.x": 99}},
        expected={"_id": 1, "arr": [{"x": 1}, {"x": 99}, {"x": 3}]},
        msg="$ with negation inside $elemMatch should succeed",
    ),
]


@pytest.mark.parametrize("test", pytest_params(POSITIONAL_INTEGRATION_TESTS))
def test_positional_query_operators(collection, test: UpdateTestCase):
    """Test $ positional with various query operators."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    execute_command(
        collection, {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]}
    )

    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": test.expected["_id"]}}
    )
    assertSuccess(result, [test.expected], msg=test.msg)
