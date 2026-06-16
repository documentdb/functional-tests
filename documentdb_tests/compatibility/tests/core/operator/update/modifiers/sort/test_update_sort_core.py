"""Tests for $sort update modifier core behavior.

Covers: scalar sort ascending/descending, document field sort, interaction
with $each, empty $each with $sort, multi-key sort, and nested field sort.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

SCALAR_SORT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="ascending_sort_after_push",
        setup_docs=[{"_id": 1, "arr": [5, 3]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [1, 4, 2], "$sort": 1}}},
        expected=[{"_id": 1, "arr": [1, 2, 3, 4, 5]}],
        msg="$sort: 1 should sort entire array ascending after push",
    ),
    UpdateTestCase(
        id="descending_sort_after_push",
        setup_docs=[{"_id": 1, "arr": [5, 3]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [1, 4, 2], "$sort": -1}}},
        expected=[{"_id": 1, "arr": [5, 4, 3, 2, 1]}],
        msg="$sort: -1 should sort entire array descending after push",
    ),
    UpdateTestCase(
        id="empty_each_sort_ascending",
        setup_docs=[{"_id": 1, "arr": [3, 1, 4, 1, 5]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": 1}}},
        expected=[{"_id": 1, "arr": [1, 1, 3, 4, 5]}],
        msg="Empty $each with $sort: 1 should sort existing array ascending",
    ),
    UpdateTestCase(
        id="empty_each_sort_descending",
        setup_docs=[{"_id": 1, "arr": [3, 1, 4, 1, 5]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": -1}}},
        expected=[{"_id": 1, "arr": [5, 4, 3, 1, 1]}],
        msg="Empty $each with $sort: -1 should sort existing array descending",
    ),
    UpdateTestCase(
        id="sort_strings_ascending",
        setup_docs=[{"_id": 1, "arr": ["banana", "apple", "cherry"]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": 1}}},
        expected=[{"_id": 1, "arr": ["apple", "banana", "cherry"]}],
        msg="$sort: 1 on strings should sort lexicographically",
    ),
    UpdateTestCase(
        id="sort_strings_descending",
        setup_docs=[{"_id": 1, "arr": ["banana", "apple", "cherry"]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": -1}}},
        expected=[{"_id": 1, "arr": ["cherry", "banana", "apple"]}],
        msg="$sort: -1 on strings should sort reverse lexicographically",
    ),
]

DOCUMENT_SORT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="document_sort_ascending",
        setup_docs=[{"_id": 1, "arr": [{"score": 8}, {"score": 2}]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [{"score": 5}], "$sort": {"score": 1}}}},
        expected=[{"_id": 1, "arr": [{"score": 2}, {"score": 5}, {"score": 8}]}],
        msg="$sort by document field ascending should order by field value",
    ),
    UpdateTestCase(
        id="empty_each_document_sort_descending",
        setup_docs=[{"_id": 1, "arr": [{"x": 1}, {"x": 3}, {"x": 2}]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": {"x": -1}}}},
        expected=[{"_id": 1, "arr": [{"x": 3}, {"x": 2}, {"x": 1}]}],
        msg="Empty $each with document sort descending should sort existing array",
    ),
    UpdateTestCase(
        id="multi_key_sort",
        setup_docs=[
            {
                "_id": 1,
                "arr": [
                    {"a": 2, "b": 1},
                    {"a": 1, "b": 1},
                    {"a": 2, "b": 2},
                    {"a": 1, "b": 3},
                ],
            }
        ],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": {"a": 1, "b": -1}}}},
        expected=[
            {
                "_id": 1,
                "arr": [
                    {"a": 1, "b": 3},
                    {"a": 1, "b": 1},
                    {"a": 2, "b": 2},
                    {"a": 2, "b": 1},
                ],
            }
        ],
        msg="Multi-key sort should sort by first key, then second key",
    ),
    UpdateTestCase(
        id="nested_field_sort",
        setup_docs=[
            {
                "_id": 1,
                "arr": [
                    {"a": {"b": 3}},
                    {"a": {"b": 1}},
                    {"a": {"b": 2}},
                ],
            }
        ],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": {"a.b": 1}}}},
        expected=[
            {
                "_id": 1,
                "arr": [
                    {"a": {"b": 1}},
                    {"a": {"b": 2}},
                    {"a": {"b": 3}},
                ],
            }
        ],
        msg="$sort by nested field path should sort by nested value",
    ),
]

ALL_CORE_TESTS = SCALAR_SORT_TESTS + DOCUMENT_SORT_TESTS


@pytest.mark.parametrize("test_case", pytest_params(ALL_CORE_TESTS))
def test_update_sort_core(collection, test_case):
    """Test $sort modifier core behavior."""
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
