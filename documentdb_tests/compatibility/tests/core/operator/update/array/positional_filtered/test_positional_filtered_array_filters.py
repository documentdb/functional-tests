"""Tests for $[<identifier>] arrayFilters conditions.

Covers: comparison operators, logical operators, element operators,
and multiple arrayFilters.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.array.positional_filtered.utils.filtered_update_test_case import (  # noqa: E501
    FilteredUpdateTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

COMPARISON_TESTS: list[FilteredUpdateTestCase] = [
    FilteredUpdateTestCase(
        "eq",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 2]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": {"$eq": 2}}],
        expected={"_id": 1, "arr": [1, 99, 3, 99]},
        msg="arrayFilters with $eq should match equal elements",
    ),
    FilteredUpdateTestCase(
        "gt",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": {"$gt": 2}}],
        expected={"_id": 1, "arr": [1, 2, 99, 99]},
        msg="arrayFilters with $gt should match elements > value",
    ),
    FilteredUpdateTestCase(
        "gte",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": {"$gte": 3}}],
        expected={"_id": 1, "arr": [1, 2, 99, 99]},
        msg="arrayFilters with $gte should match elements >= value",
    ),
    FilteredUpdateTestCase(
        "lt",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": {"$lt": 3}}],
        expected={"_id": 1, "arr": [99, 99, 3, 4]},
        msg="arrayFilters with $lt should match elements < value",
    ),
    FilteredUpdateTestCase(
        "lte",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": {"$lte": 2}}],
        expected={"_id": 1, "arr": [99, 99, 3, 4]},
        msg="arrayFilters with $lte should match elements <= value",
    ),
    FilteredUpdateTestCase(
        "ne",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": {"$ne": 2}}],
        expected={"_id": 1, "arr": [99, 2, 99]},
        msg="arrayFilters with $ne should match elements != value",
    ),
    FilteredUpdateTestCase(
        "in",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4, 5]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": {"$in": [2, 4]}}],
        expected={"_id": 1, "arr": [1, 99, 3, 99, 5]},
        msg="arrayFilters with $in should match elements in list",
    ),
    FilteredUpdateTestCase(
        "nin",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4, 5]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": {"$nin": [2, 4]}}],
        expected={"_id": 1, "arr": [99, 2, 99, 4, 99]},
        msg="arrayFilters with $nin should match elements not in list",
    ),
]


LOGICAL_TESTS: list[FilteredUpdateTestCase] = [
    FilteredUpdateTestCase(
        "and_multiple_conditions",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4, 5]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": {"$gt": 2, "$lt": 5}}],
        expected={"_id": 1, "arr": [1, 2, 99, 99, 5]},
        msg="arrayFilters with implicit $and should match elements meeting all conditions",
    ),
    FilteredUpdateTestCase(
        "or",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4, 5]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"$or": [{"elem": {"$eq": 1}}, {"elem": {"$eq": 5}}]}],
        expected={"_id": 1, "arr": [99, 2, 3, 4, 99]},
        msg="arrayFilters with $or should match elements meeting any condition",
    ),
    FilteredUpdateTestCase(
        "not",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4, 5]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": {"$not": {"$gt": 3}}}],
        expected={"_id": 1, "arr": [99, 99, 99, 4, 5]},
        msg="arrayFilters with $not should match elements not meeting condition",
    ),
]


ELEMENT_TESTS: list[FilteredUpdateTestCase] = [
    FilteredUpdateTestCase(
        "exists",
        setup_docs=[{"_id": 1, "arr": [{"x": 1}, {"y": 2}, {"x": 3}]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem].x": 99}},
        array_filters=[{"elem.x": {"$exists": True}}],
        expected={"_id": 1, "arr": [{"x": 99}, {"y": 2}, {"x": 99}]},
        msg="arrayFilters with $exists should match elements with field",
    ),
    FilteredUpdateTestCase(
        "type",
        setup_docs=[{"_id": 1, "arr": [1, "two", 3, "four"]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": {"$type": "string"}}],
        expected={"_id": 1, "arr": [1, 99, 3, 99]},
        msg="arrayFilters with $type should match elements of specified type",
    ),
]


MULTIPLE_FILTERS_TESTS: list[FilteredUpdateTestCase] = [
    FilteredUpdateTestCase(
        "multiple_identifiers",
        setup_docs=[{"_id": 1, "arr": [{"a": 1, "b": 10}, {"a": 2, "b": 20}, {"a": 3, "b": 30}]}],
        query={"_id": 1},
        update={"$set": {"arr.$[x].a": 99, "arr.$[y].b": 99}},
        array_filters=[{"x.a": {"$gte": 2}}, {"y.b": {"$lte": 20}}],
        expected={
            "_id": 1,
            "arr": [{"a": 1, "b": 99}, {"a": 99, "b": 99}, {"a": 99, "b": 30}],
        },
        msg="Multiple arrayFilters with different identifiers should work",
    ),
]


ALL_SUCCESS_TESTS = COMPARISON_TESTS + LOGICAL_TESTS + ELEMENT_TESTS + MULTIPLE_FILTERS_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_SUCCESS_TESTS))
def test_positional_filtered_array_filters_success(collection, test: FilteredUpdateTestCase):
    """Test $[<identifier>] arrayFilters conditions."""
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
