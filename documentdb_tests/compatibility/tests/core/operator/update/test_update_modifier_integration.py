"""Integration tests for update modifier operators.

Tests that verify interactions between modifier operators ($position, $slice,
$sort) and other update operators, ensuring correct combined behavior.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

POSITION_TESTS: list[UpdateTestCase] = [
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
        id="set_treats_position_as_literal",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$set": {"arr": {"$each": [3], "$position": 0}}},
        expected=[{"_id": 1, "arr": {"$each": [3], "$position": 0}}],
        msg="$set should treat $position doc as a literal value",
    ),
    UpdateTestCase(
        id="unset_ignores_position_doc",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$unset": {"arr": {"$each": [3], "$position": 0}}},
        expected=[{"_id": 1}],
        msg="$unset should ignore $position doc and remove the field",
    ),
    UpdateTestCase(
        id="min_treats_position_as_literal",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$min": {"arr": {"$each": [3], "$position": 0}}},
        expected=[{"_id": 1, "arr": {"$each": [3], "$position": 0}}],
        msg="$min should treat $position doc as a literal value",
    ),
    UpdateTestCase(
        id="max_keeps_original_array",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$max": {"arr": {"$each": [3], "$position": 0}}},
        expected=[{"_id": 1, "arr": [1, 2, 3]}],
        msg="$max should keep original array (array > document in BSON comparison)",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(POSITION_TESTS))
def test_position_update_modifier_integration(collection, test_case):
    """Test $position interaction with modifiers and non-$push operators."""
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
