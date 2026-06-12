"""Integration tests for array update operators.

Tests that verify interactions between array update operators and various
query operators, ensuring correct element matching and update behavior.
"""

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.update.array.positional_filtered.utils.filtered_update_test_case import (  # noqa: E501
    FilteredUpdateTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
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

POSITIONAL_FILTERED_TESTS: list[FilteredUpdateTestCase] = [
    FilteredUpdateTestCase(
        "inc_matching_elements",
        setup_docs=[{"_id": 1, "arr": [10, 20, 30, 40]}],
        query={"_id": 1},
        update={"$inc": {"arr.$[elem]": 100}},
        array_filters=[{"elem": {"$gt": 20}}],
        expected={"_id": 1, "arr": [10, 20, 130, 140]},
        msg="$[<id>] with $inc should increment matching elements",
    ),
    FilteredUpdateTestCase(
        "mul_matching_elements",
        setup_docs=[{"_id": 1, "arr": [2, 4, 6, 8]}],
        query={"_id": 1},
        update={"$mul": {"arr.$[elem]": 10}},
        array_filters=[{"elem": {"$lt": 5}}],
        expected={"_id": 1, "arr": [20, 40, 6, 8]},
        msg="$[<id>] with $mul should multiply matching elements",
    ),
    FilteredUpdateTestCase(
        "unset_matching",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4]}],
        query={"_id": 1},
        update={"$unset": {"arr.$[elem]": ""}},
        array_filters=[{"elem": {"$gte": 3}}],
        expected={"_id": 1, "arr": [1, 2, None, None]},
        msg="$[<id>] with $unset should set matching elements to null",
    ),
    FilteredUpdateTestCase(
        "addToSet_matching_subarrays",
        setup_docs=[{"_id": 1, "arr": [[1, 2], [3, 4], [5, 6]]}],
        query={"_id": 1},
        update={"$addToSet": {"arr.$[elem]": 99}},
        array_filters=[{"elem": {"$size": 2}}],
        expected={"_id": 1, "arr": [[1, 2, 99], [3, 4, 99], [5, 6, 99]]},
        msg="$[<id>] with $addToSet should add to matching sub-arrays",
    ),
    FilteredUpdateTestCase(
        "push_matching_subarrays",
        setup_docs=[{"_id": 1, "arr": [[1], [2, 3], [4]]}],
        query={"_id": 1},
        update={"$push": {"arr.$[elem]": 99}},
        array_filters=[{"elem": {"$size": 1}}],
        expected={"_id": 1, "arr": [[1, 99], [2, 3], [4, 99]]},
        msg="$[<id>] with $push should append to matching sub-arrays",
    ),
    FilteredUpdateTestCase(
        "pop_matching_subarrays",
        setup_docs=[{"_id": 1, "arr": [[1, 2, 3], [4, 5, 6]]}],
        query={"_id": 1},
        update={"$pop": {"arr.$[elem]": -1}},
        array_filters=[{"elem": {"$exists": True}}],
        expected={"_id": 1, "arr": [[2, 3], [5, 6]]},
        msg="$[<id>] with $pop should pop the first element from each matching sub-array",
    ),
    FilteredUpdateTestCase(
        "min_matching",
        setup_docs=[{"_id": 1, "arr": [10, 20, 30]}],
        query={"_id": 1},
        update={"$min": {"arr.$[elem]": 15}},
        array_filters=[{"elem": {"$gte": 1}}],
        expected={"_id": 1, "arr": [10, 15, 15]},
        msg="$[<id>] with $min should update matching elements if new value is less",
    ),
    FilteredUpdateTestCase(
        "max_matching",
        setup_docs=[{"_id": 1, "arr": [10, 20, 30]}],
        query={"_id": 1},
        update={"$max": {"arr.$[elem]": 25}},
        array_filters=[{"elem": {"$gte": 1}}],
        expected={"_id": 1, "arr": [25, 25, 30]},
        msg="$[<id>] with $max should update matching elements if new value is greater",
    ),
    FilteredUpdateTestCase(
        "unset_field_in_embedded_docs",
        setup_docs=[
            {"_id": 1, "arr": [{"x": 1, "y": "a"}, {"x": 2, "y": "b"}, {"x": 3, "y": "c"}]}
        ],
        query={"_id": 1},
        update={"$unset": {"arr.$[elem].y": ""}},
        array_filters=[{"elem.x": {"$gte": 2}}],
        expected={"_id": 1, "arr": [{"x": 1, "y": "a"}, {"x": 2}, {"x": 3}]},
        msg="$[<id>] with $unset on embedded doc field should remove field from matching docs",
    ),
    FilteredUpdateTestCase(
        "nested_with_all_bracket",
        setup_docs=[{"_id": 1, "arr": [{"sub": [1, 2, 3]}, {"sub": [4, 5, 6]}]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem].sub.$[]": 0}},
        array_filters=[{"elem.sub": {"$size": 3}}],
        expected={"_id": 1, "arr": [{"sub": [0, 0, 0]}, {"sub": [0, 0, 0]}]},
        msg="$[<id>] combined with $[] for nested arrays should work",
    ),
    FilteredUpdateTestCase(
        "filtered_and_positional_different_fields",
        setup_docs=[{"_id": 1, "a": [1, 2, 3], "b": [10, 20, 30]}],
        query={"_id": 1, "a": 2},
        update={"$set": {"a.$": 99, "b.$[elem]": 0}},
        array_filters=[{"elem": {"$gte": 20}}],
        expected={"_id": 1, "a": [1, 99, 3], "b": [10, 0, 0]},
        msg="$ and $[<id>] on different fields in same update should both work",
    ),
    FilteredUpdateTestCase(
        "filtered_and_all_different_fields",
        setup_docs=[{"_id": 1, "a": [1, 2, 3], "b": [10, 20, 30]}],
        query={"_id": 1},
        update={"$set": {"a.$[]": 0, "b.$[elem]": 99}},
        array_filters=[{"elem": {"$gte": 20}}],
        expected={"_id": 1, "a": [0, 0, 0], "b": [10, 99, 99]},
        msg="$[] and $[<id>] on different fields in same update should both work",
    ),
]

POSITIONAL_FILTERED_ERROR_TESTS: list[FilteredUpdateTestCase] = [
    FilteredUpdateTestCase(
        "rename_with_filtered_positional",
        setup_docs=[{"_id": 1, "arr": [{"a": 1}, {"a": 2}]}],
        query={"_id": 1},
        update={"$rename": {"arr.$[elem].a": "arr.$[elem].b"}},
        array_filters=[{"elem.a": {"$gte": 1}}],
        error_code=BAD_VALUE_ERROR,
        msg="$rename with $[<id>] should fail (source field may not be dynamic)",
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


@pytest.mark.parametrize("test", pytest_params(POSITIONAL_FILTERED_TESTS))
def test_positional_filtered_integration(collection, test: FilteredUpdateTestCase):
    """Test $[<identifier>] integration with other update operators."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update, "arrayFilters": test.array_filters}],
        },
    )

    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": test.expected["_id"]}}
    )
    assertSuccess(result, [test.expected], msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(POSITIONAL_FILTERED_ERROR_TESTS))
def test_positional_filtered_integration_errors(collection, test):
    """Test $[<identifier>] integration error cases."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    command = {
        "update": collection.name,
        "updates": [{"q": test.query, "u": test.update, "arrayFilters": test.array_filters}],
    }
    result = execute_command(collection, command)
    assertFailureCode(result, test.error_code, msg=test.msg)


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
    UpdateTestCase(
        "pop_matched_subarray",
        setup_docs=[{"_id": 1, "arr": [[1, 2, 3], [4, 5, 6]]}],
        query={"_id": 1, "arr": [4, 5, 6]},
        update={"$pop": {"arr.$": 1}},
        expected={"_id": 1, "arr": [[1, 2, 3], [4, 5]]},
        msg="$ with $pop should pop the last element from the matched sub-array",
    ),
]


@pytest.mark.parametrize("test", pytest_params(POSITIONAL_INTEGRATION_TESTS))
def test_positional_query_operators(collection, test: UpdateTestCase):
    """Test $ positional with various query operators and update operators."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    execute_command(
        collection, {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]}
    )

    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": test.expected["_id"]}}
    )
    assertSuccess(result, [test.expected], msg=test.msg)


POP_COMBINATION_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "pop_and_set_different_fields",
        setup_docs=[{"_id": 1, "a": [1, 2, 3], "b": 1}],
        query={"_id": 1},
        update={"$pop": {"a": 1}, "$set": {"b": 99}},
        expected={"_id": 1, "a": [1, 2], "b": 99},
        msg="$pop and $set on different fields should both succeed",
    ),
    UpdateTestCase(
        "pop_and_push_different_fields",
        setup_docs=[{"_id": 1, "a": [1, 2, 3], "b": [10]}],
        query={"_id": 1},
        update={"$pop": {"a": 1}, "$push": {"b": 99}},
        expected={"_id": 1, "a": [1, 2], "b": [10, 99]},
        msg="$pop on one field and $push on another should both succeed",
    ),
]


@pytest.mark.parametrize("test", pytest_params(POP_COMBINATION_TESTS))
def test_pop_combination(collection, test: UpdateTestCase):
    """Test $pop combined with other update operators on different fields."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    execute_command(
        collection, {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]}
    )

    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": test.expected["_id"]}}
    )
    assertSuccess(result, [test.expected], msg=test.msg)
