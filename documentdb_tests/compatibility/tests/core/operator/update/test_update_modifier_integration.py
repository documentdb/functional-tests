"""Integration tests for update modifier interactions.

Tests cross-modifier behavior where multiple $push modifiers ($slice,
$sort, $position) are combined in a single update operation.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

SLICE_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="sort_asc_then_slice_positive",
        setup_docs=[{"_id": 1, "arr": [5, 3]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [1, 4, 2], "$sort": 1, "$slice": 3}}},
        expected=[{"_id": 1, "arr": [1, 2, 3]}],
        msg="$sort asc then $slice 3 should keep first 3 of sorted",
    ),
    UpdateTestCase(
        id="sort_asc_then_slice_negative",
        setup_docs=[{"_id": 1, "arr": [5, 3]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [1, 4, 2], "$sort": 1, "$slice": -2}}},
        expected=[{"_id": 1, "arr": [4, 5]}],
        msg="$sort asc then $slice -2 should keep last 2 of sorted",
    ),
    UpdateTestCase(
        id="sort_desc_then_slice_positive",
        setup_docs=[{"_id": 1, "arr": [5, 3]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [1, 4, 2], "$sort": -1, "$slice": 3}}},
        expected=[{"_id": 1, "arr": [5, 4, 3]}],
        msg="$sort desc then $slice 3 should keep first 3 of desc sorted",
    ),
    UpdateTestCase(
        id="sort_desc_then_slice_negative",
        setup_docs=[{"_id": 1, "arr": [5, 3]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [1, 4, 2], "$sort": -1, "$slice": -2}}},
        expected=[{"_id": 1, "arr": [2, 1]}],
        msg="$sort desc then $slice -2 should keep last 2 of desc sorted",
    ),
    UpdateTestCase(
        id="sort_by_field_then_slice",
        setup_docs=[{"_id": 1, "arr": [{"x": 3}, {"x": 1}]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [{"x": 5}, {"x": 2}], "$sort": {"x": 1}, "$slice": -2}}},
        expected=[{"_id": 1, "arr": [{"x": 3}, {"x": 5}]}],
        msg="$sort by field then $slice -2 should keep last 2 sorted by field",
    ),
    UpdateTestCase(
        id="position_0_then_slice",
        setup_docs=[{"_id": 1, "arr": [20, 30, 40]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [10], "$position": 0, "$slice": 2}}},
        expected=[{"_id": 1, "arr": [10, 20]}],
        msg="$position 0 inserts at beginning, then $slice 2 keeps first 2",
    ),
    UpdateTestCase(
        id="position_sort_slice_combined",
        setup_docs=[{"_id": 1, "arr": [30, 10]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [20], "$position": 0, "$sort": 1, "$slice": 2}}},
        expected=[{"_id": 1, "arr": [10, 20]}],
        msg="Combined $position, $sort, $slice: position, then sort, then slice",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(SLICE_TESTS))
def test_update_slice_modifiers(collection, test_case):
    """Test $slice modifier interactions with $sort and $position."""
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
