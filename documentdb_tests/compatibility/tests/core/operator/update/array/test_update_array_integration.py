"""Integration tests for array update operators.

Covers: cross-operator interactions between $, $[], $[<identifier>],
$push, $pull, $addToSet, $pop, and $pullAll in the same update.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.array.positional_filtered.utils.filtered_update_test_case import (  # noqa: E501
    FilteredUpdateTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# --- Positional Filtered ($[<identifier>]) ---

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
