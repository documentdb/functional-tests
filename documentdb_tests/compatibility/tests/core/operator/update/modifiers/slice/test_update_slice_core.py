"""Tests for $slice modifier core behavior.

Covers: positive/negative/zero slice values, empty $each trimming,
edge cases (missing field, empty array, exact length), null handling,
multiple element push, and $push without $each literal behavior.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

CORE_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="positive_slice_1_keeps_first",
        setup_docs=[{"_id": 1, "arr": [10, 20, 30]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [40, 50], "$slice": 1}}},
        expected=[{"_id": 1, "arr": [10]}],
        msg="$slice 1 should keep only first element of combined array",
    ),
    UpdateTestCase(
        id="positive_slice_larger_than_array",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [4], "$slice": 10}}},
        expected=[{"_id": 1, "arr": [1, 2, 3, 4]}],
        msg="$slice larger than combined array should keep all",
    ),
    UpdateTestCase(
        id="negative_slice_1_keeps_last",
        setup_docs=[{"_id": 1, "arr": [10, 20, 30]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [40, 50], "$slice": -1}}},
        expected=[{"_id": 1, "arr": [50]}],
        msg="$slice -1 should keep only last element of combined array",
    ),
    UpdateTestCase(
        id="negative_slice_larger_than_array",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [4], "$slice": -100}}},
        expected=[{"_id": 1, "arr": [1, 2, 3, 4]}],
        msg="$slice with abs larger than combined array should keep all",
    ),
    UpdateTestCase(
        id="zero_slice_empties",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [4, 5], "$slice": 0}}},
        expected=[{"_id": 1, "arr": []}],
        msg="$slice 0 should empty the array",
    ),
    UpdateTestCase(
        id="empty_each_positive_slice",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4, 5]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$slice": 2}}},
        expected=[{"_id": 1, "arr": [1, 2]}],
        msg="Empty $each with $slice 2 should trim to first 2",
    ),
    UpdateTestCase(
        id="empty_each_negative_slice",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4, 5]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$slice": -2}}},
        expected=[{"_id": 1, "arr": [4, 5]}],
        msg="Empty $each with $slice -2 should trim to last 2",
    ),
    UpdateTestCase(
        id="empty_each_zero_slice",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$slice": 0}}},
        expected=[{"_id": 1, "arr": []}],
        msg="Empty $each with $slice 0 should empty the array",
    ),
    UpdateTestCase(
        id="missing_field_creates_then_slices",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [1, 2, 3], "$slice": 2}}},
        expected=[{"_id": 1, "arr": [1, 2]}],
        msg="$slice on missing field should create array then slice",
    ),
    UpdateTestCase(
        id="missing_field_negative_slice",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [1, 2, 3], "$slice": -1}}},
        expected=[{"_id": 1, "arr": [3]}],
        msg="$slice -1 on missing field should create then keep last",
    ),
    UpdateTestCase(
        id="empty_array_sliced",
        setup_docs=[{"_id": 1, "arr": []}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [1, 2, 3], "$slice": 2}}},
        expected=[{"_id": 1, "arr": [1, 2]}],
        msg="$slice on empty array should slice pushed elements",
    ),
    UpdateTestCase(
        id="empty_array_negative_slice",
        setup_docs=[{"_id": 1, "arr": []}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [1, 2, 3], "$slice": -2}}},
        expected=[{"_id": 1, "arr": [2, 3]}],
        msg="$slice -2 on empty array should keep last 2 of pushed",
    ),
    UpdateTestCase(
        id="slice_equals_combined_length",
        setup_docs=[{"_id": 1, "arr": [1, 2]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [3], "$slice": 3}}},
        expected=[{"_id": 1, "arr": [1, 2, 3]}],
        msg="$slice equal to combined length should keep all",
    ),
    UpdateTestCase(
        id="slice_negative_equals_combined_length",
        setup_docs=[{"_id": 1, "arr": [1, 2]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [3], "$slice": -3}}},
        expected=[{"_id": 1, "arr": [1, 2, 3]}],
        msg="$slice -N equal to combined length should keep all",
    ),
    UpdateTestCase(
        id="null_elements_counted_in_slice",
        setup_docs=[{"_id": 1, "arr": [None, 1, None, 2]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$slice": 2}}},
        expected=[{"_id": 1, "arr": [None, 1]}],
        msg="Null elements should be counted and preserved during slice",
    ),
    UpdateTestCase(
        id="push_null_then_slice",
        setup_docs=[{"_id": 1, "arr": [1, 2]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [None, 3], "$slice": -2}}},
        expected=[{"_id": 1, "arr": [None, 3]}],
        msg="Pushed null elements participate in combined array before slice",
    ),
    UpdateTestCase(
        id="without_each_pushes_literal",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$slice": -2}}},
        expected=[{"_id": 1, "arr": [1, 2, 3, {"$slice": -2}]}],
        msg="$push without $each should treat modifier doc as literal element",
    ),
    UpdateTestCase(
        id="push_3_slice_first_3",
        setup_docs=[{"_id": 1, "arr": [89, 90]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [91, 92, 93], "$slice": 3}}},
        expected=[{"_id": 1, "arr": [89, 90, 91]}],
        msg="Push 3 elements to 2-element array, slice first 3",
    ),
    UpdateTestCase(
        id="push_3_slice_last_2",
        setup_docs=[{"_id": 1, "arr": [89, 90]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [91, 92, 93], "$slice": -2}}},
        expected=[{"_id": 1, "arr": [92, 93]}],
        msg="Push 3 elements to 2-element array, slice last 2",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(CORE_TESTS))
def test_update_slice_core(collection, test_case):
    """Test $slice modifier core behavior."""
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
