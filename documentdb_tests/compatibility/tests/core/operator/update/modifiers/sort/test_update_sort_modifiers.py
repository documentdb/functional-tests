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
