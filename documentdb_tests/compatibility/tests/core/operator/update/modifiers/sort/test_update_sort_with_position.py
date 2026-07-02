"""$sort push modifier combined with the $position modifier.

Existing $sort modifier coverage exercises $sort on its own. This file covers
its interaction with $position: $position controls where the $each elements are
inserted, and when $sort is also present it reorders the entire array, making
the positional insert order irrelevant to the final result. Positional inserts
without $sort establish the baseline insert semantics (head, middle, negative
offset from the end, and an offset past the end).

Oracle: MongoDB 7.0 (functional-tests CI baseline). The engine under test
matches native behavior on every case in this file; no engine divergences are
tracked here.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.update

# Property [Positional Insert + Sort]: $position selects the insertion point for
# the $each elements; a co-present $sort then reorders the whole array.
SORT_POSITION_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="position_head_no_sort",
        setup_docs=[{"_id": 1, "arr": [5, 4]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [3, 1], "$position": 0}}},
        expected=[{"_id": 1, "arr": [3, 1, 5, 4]}],
        msg="$position 0 inserts the $each elements at the head.",
    ),
    UpdateTestCase(
        id="position_middle_no_sort",
        setup_docs=[{"_id": 1, "arr": [5, 4]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [9], "$position": 1}}},
        expected=[{"_id": 1, "arr": [5, 9, 4]}],
        msg="$position 1 inserts the $each element after the first element.",
    ),
    UpdateTestCase(
        id="position_negative_from_end",
        setup_docs=[{"_id": 1, "arr": [5, 4, 7]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [9], "$position": -1}}},
        expected=[{"_id": 1, "arr": [5, 4, 9, 7]}],
        msg="A negative $position counts the insertion point from the array end.",
    ),
    UpdateTestCase(
        id="position_past_end_appends",
        setup_docs=[{"_id": 1, "arr": [5, 4]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [9], "$position": 100}}},
        expected=[{"_id": 1, "arr": [5, 4, 9]}],
        msg="A $position past the end appends at the tail.",
    ),
    UpdateTestCase(
        id="position_then_sort_reorders_all",
        setup_docs=[{"_id": 1, "arr": [5, 4]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [3, 1], "$position": 0, "$sort": 1}}},
        expected=[{"_id": 1, "arr": [1, 3, 4, 5]}],
        msg="$sort reorders the entire array, overriding the $position insert order.",
    ),
    UpdateTestCase(
        id="position_then_sort_descending",
        setup_docs=[{"_id": 1, "arr": [5, 4]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [3, 1], "$position": 1, "$sort": -1}}},
        expected=[{"_id": 1, "arr": [5, 4, 3, 1]}],
        msg="$sort descending reorders the whole array regardless of $position.",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(SORT_POSITION_TESTS))
def test_update_sort_with_position(collection, test_case: UpdateTestCase):
    """$position controls insertion; a co-present $sort reorders the whole array."""
    collection.insert_many(test_case.setup_docs)
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test_case.query, "u": test_case.update}]},
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": test_case.query, "sort": {"_id": 1}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
