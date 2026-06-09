"""Tests for $sort update modifier interaction with other modifiers.

Covers: $sort with $position, $sort with $slice, all modifiers combined,
and modifier application order verification.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

SORT_WITH_SLICE_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="sort_asc_slice_positive",
        setup_docs=[{"_id": 1, "arr": [5, 3]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [1, 4, 2], "$sort": 1, "$slice": 3}}},
        expected=[{"_id": 1, "arr": [1, 2, 3]}],
        msg="$sort: 1 with $slice: 3 should sort then keep first 3",
    ),
    UpdateTestCase(
        id="sort_desc_slice_negative",
        setup_docs=[{"_id": 1, "arr": [5, 3]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [1, 4, 2], "$sort": -1, "$slice": -2}}},
        expected=[{"_id": 1, "arr": [2, 1]}],
        msg="$sort: -1 with $slice: -2 should sort desc then keep last 2",
    ),
    UpdateTestCase(
        id="sort_asc_slice_larger_than_array",
        setup_docs=[{"_id": 1, "arr": [5, 3]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [1, 4, 2], "$sort": 1, "$slice": 10}}},
        expected=[{"_id": 1, "arr": [1, 2, 3, 4, 5]}],
        msg="$sort with $slice larger than array should keep all sorted elements",
    ),
    UpdateTestCase(
        id="document_sort_with_slice",
        setup_docs=[{"_id": 1, "arr": [{"score": 8}, {"score": 2}]}],
        query={"_id": 1},
        update={
            "$push": {
                "arr": {
                    "$each": [{"score": 5}],
                    "$sort": {"score": 1},
                    "$slice": -2,
                }
            }
        },
        expected=[{"_id": 1, "arr": [{"score": 5}, {"score": 8}]}],
        msg="Document sort with $slice should sort by field then trim",
    ),
    UpdateTestCase(
        id="nested_field_sort_with_slice",
        setup_docs=[
            {
                "_id": 1,
                "arr": [
                    {"a": {"b": 3}},
                    {"a": {"b": 1}},
                ],
            }
        ],
        query={"_id": 1},
        update={
            "$push": {
                "arr": {
                    "$each": [{"a": {"b": 2}}],
                    "$sort": {"a.b": 1},
                    "$slice": -2,
                }
            }
        },
        expected=[{"_id": 1, "arr": [{"a": {"b": 2}}, {"a": {"b": 3}}]}],
        msg="Nested field sort with slice should sort then trim",
    ),
]

SORT_WITH_POSITION_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="sort_overrides_position",
        setup_docs=[{"_id": 1, "arr": [3, 1]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [5], "$position": 0, "$sort": 1}}},
        expected=[{"_id": 1, "arr": [1, 3, 5]}],
        msg="$sort should override $position — final array is sorted regardless of insertion point",
    ),
]

ALL_MODIFIERS_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="all_modifiers_combined",
        setup_docs=[{"_id": 1, "arr": [4, 2]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [5, 1, 3], "$position": 0, "$sort": 1, "$slice": 3}}},
        expected=[{"_id": 1, "arr": [1, 2, 3]}],
        msg="All modifiers: position insert, then sort, then slice",
    ),
    UpdateTestCase(
        id="sort_desc_position_slice_neg",
        setup_docs=[{"_id": 1, "arr": [2, 4]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [5, 1, 3], "$position": 0, "$sort": -1, "$slice": -3}}},
        expected=[{"_id": 1, "arr": [3, 2, 1]}],
        msg="Sort descending with negative slice should keep last 3 of sorted desc array",
    ),
]

SORT_WITH_MIXED_ELEMENTS_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="integers_with_document_sort",
        setup_docs=[{"_id": 1, "arr": [{"score": 3}, 1, {"score": 1}]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [{"score": 2}], "$sort": {"score": 1}, "$slice": 4}}},
        expected=[{"_id": 1, "arr": [1, {"score": 1}, {"score": 2}, {"score": 3}]}],
        msg="Mixed elements (int + documents) with document sort and slice should succeed",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(SORT_WITH_SLICE_TESTS))
def test_update_sort_with_slice(collection, test_case):
    """Test $sort modifier combined with $slice."""
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


@pytest.mark.parametrize("test_case", pytest_params(SORT_WITH_POSITION_TESTS))
def test_update_sort_with_position(collection, test_case):
    """Test $sort interaction with $position modifier."""
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


@pytest.mark.parametrize("test_case", pytest_params(ALL_MODIFIERS_TESTS))
def test_update_sort_all_modifiers(collection, test_case):
    """Test $sort with all modifiers combined ($each, $position, $sort, $slice)."""
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


@pytest.mark.parametrize("test_case", pytest_params(SORT_WITH_MIXED_ELEMENTS_TESTS))
def test_update_sort_mixed_elements(collection, test_case):
    """Test $sort with mixed document and non-document elements."""
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
