"""Tests for $position interaction with other modifiers ($slice, $sort).

Covers: $position + $slice, $position + $sort, $position + $slice + $sort,
and null element preservation.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

MODIFIER_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="position_with_positive_slice",
        setup_docs=[{"_id": 1, "arr": [10, 20, 30]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [1, 2], "$position": 0, "$slice": 3}}},
        expected=[{"_id": 1, "arr": [1, 2, 10]}],
        msg="$position 0 + $slice 3 should insert then keep first 3",
    ),
    UpdateTestCase(
        id="position_with_negative_slice",
        setup_docs=[{"_id": 1, "arr": [10, 20, 30]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [1, 2], "$position": 0, "$slice": -3}}},
        expected=[{"_id": 1, "arr": [10, 20, 30]}],
        msg="$position 0 + $slice -3 should insert then keep last 3",
    ),
    UpdateTestCase(
        id="position_with_sort_ascending",
        setup_docs=[{"_id": 1, "arr": [30, 10, 20]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [5], "$position": 0, "$sort": 1}}},
        expected=[{"_id": 1, "arr": [5, 10, 20, 30]}],
        msg="$sort should override $position — array sorted ascending",
    ),
    UpdateTestCase(
        id="position_with_sort_descending",
        setup_docs=[{"_id": 1, "arr": [10, 30, 20]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [5], "$position": 0, "$sort": -1}}},
        expected=[{"_id": 1, "arr": [30, 20, 10, 5]}],
        msg="$sort descending should override $position",
    ),
    UpdateTestCase(
        id="position_sort_slice_combined",
        setup_docs=[{"_id": 1, "arr": [30, 10]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [20, 5], "$position": 0, "$sort": 1, "$slice": 3}}},
        expected=[{"_id": 1, "arr": [5, 10, 20]}],
        msg="All modifiers: insert, sort ascending, then slice first 3",
    ),
    UpdateTestCase(
        id="position_sort_negative_slice_combined",
        setup_docs=[{"_id": 1, "arr": [30, 10]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [20, 5], "$position": 0, "$sort": 1, "$slice": -2}}},
        expected=[{"_id": 1, "arr": [20, 30]}],
        msg="All modifiers: insert, sort ascending, then slice last 2",
    ),
    UpdateTestCase(
        id="null_elements_preserved",
        setup_docs=[{"_id": 1, "arr": ["a", "b"]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [None, 1, None], "$position": 0}}},
        expected=[{"_id": 1, "arr": [None, 1, None, "a", "b"]}],
        msg="Null elements in $each should be preserved at position",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(MODIFIER_TESTS))
def test_position_modifiers(collection, test_case):
    """Test $position interaction with $slice and $sort modifiers."""
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
