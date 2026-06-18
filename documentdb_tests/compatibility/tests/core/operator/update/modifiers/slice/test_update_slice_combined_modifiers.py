"""$slice push modifier combined with $sort and $position (modifier ordering).

Existing $slice modifier coverage exercises $slice on its own (with or without
$each). This file covers the documented modifier-processing order when $slice
is combined with $sort and $position in a single $push: the $each elements are
appended (at $position when present), the whole array is reordered by $sort,
and only then is it trimmed by $slice.

A $slice of 0 combined with these modifiers is a tracked engine divergence:
native MongoDB empties the array, while the engine under test leaves the array
unchanged.

Oracle: MongoDB 7.0 (functional-tests CI baseline).
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.update

# Property [Modifier Ordering]: in one $push, elements are appended (at
# $position), the array is reordered by $sort, then trimmed by $slice.
COMBINED_MODIFIER_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="sort_asc_then_slice_first_two",
        setup_docs=[{"_id": 1, "arr": [5, 4]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [3, 1, 2], "$sort": 1, "$slice": 2}}},
        expected=[{"_id": 1, "arr": [1, 2]}],
        msg="$sort ascending then $slice keeps the two smallest elements.",
    ),
    UpdateTestCase(
        id="sort_asc_then_slice_last_two",
        setup_docs=[{"_id": 1, "arr": [5, 4]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [3, 1, 2], "$sort": 1, "$slice": -2}}},
        expected=[{"_id": 1, "arr": [4, 5]}],
        msg="$sort ascending then negative $slice keeps the two largest elements.",
    ),
    UpdateTestCase(
        id="sort_desc_then_slice_first_three",
        setup_docs=[{"_id": 1, "arr": [5, 4]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [3, 1, 2], "$sort": -1, "$slice": 3}}},
        expected=[{"_id": 1, "arr": [5, 4, 3]}],
        msg="$sort descending then $slice keeps the three largest elements.",
    ),
    UpdateTestCase(
        id="position_then_slice_no_sort",
        setup_docs=[{"_id": 1, "arr": [5, 4]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [3, 1], "$position": 0, "$slice": 3}}},
        expected=[{"_id": 1, "arr": [3, 1, 5]}],
        msg="$position inserts at the head, then $slice keeps the first three.",
    ),
    UpdateTestCase(
        id="position_sort_then_slice",
        setup_docs=[{"_id": 1, "arr": [5, 4]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [3, 1], "$position": 0, "$sort": 1, "$slice": 3}}},
        expected=[{"_id": 1, "arr": [1, 3, 4]}],
        msg="$sort reorders the whole array regardless of $position before $slice trims it.",
    ),
    UpdateTestCase(
        id="sort_documents_then_slice_first_two",
        setup_docs=[{"_id": 1, "arr": [{"s": 5}, {"s": 4}]}],
        query={"_id": 1},
        update={
            "$push": {
                "arr": {"$each": [{"s": 3}, {"s": 1}], "$sort": {"s": 1}, "$slice": 2}
            }
        },
        expected=[{"_id": 1, "arr": [{"s": 1}, {"s": 3}]}],
        msg="$sort by subfield ascending then $slice keeps the two smallest documents.",
    ),
    UpdateTestCase(
        id="sort_documents_desc_then_slice_last_two",
        setup_docs=[{"_id": 1, "arr": [{"s": 5}, {"s": 4}]}],
        query={"_id": 1},
        update={
            "$push": {
                "arr": {"$each": [{"s": 3}, {"s": 1}], "$sort": {"s": -1}, "$slice": -2}
            }
        },
        expected=[{"_id": 1, "arr": [{"s": 3}, {"s": 1}]}],
        msg="$sort by subfield descending then negative $slice keeps the two smallest documents.",
    ),
    UpdateTestCase(
        id="missing_field_sort_then_slice",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [3, 1, 2], "$sort": 1, "$slice": 2}}},
        expected=[{"_id": 1, "arr": [1, 2]}],
        msg="On a missing field the array is created, sorted, then sliced.",
    ),
    UpdateTestCase(
        id="sort_then_slice_zero_empties",
        setup_docs=[{"_id": 1, "arr": [5, 4]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [3, 1, 2], "$sort": 1, "$slice": 0}}},
        expected=[{"_id": 1, "arr": []}],
        msg="$slice 0 empties the array after $each and $sort are applied.",
        marks=(
            pytest.mark.engine_xfail(
                engine="pgmongo",
                reason=(
                    "$push with $slice 0 is a no-op on this engine (the array keeps its "
                    "original contents), whereas native MongoDB empties the array. "
                    "Tracked: ADO #5371311"
                ),
                raises=AssertionError,
            ),
        ),
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(COMBINED_MODIFIER_TESTS))
def test_update_slice_combined_modifiers(collection, test_case: UpdateTestCase):
    """$slice trims the array after $each/$position/$sort modifiers are applied."""
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
