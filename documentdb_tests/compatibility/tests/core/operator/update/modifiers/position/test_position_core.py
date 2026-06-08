"""Tests for $position modifier core behavior.

Covers: positive position, negative position, boundary values,
position on empty array, and without-$each literal push.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import INT32_MAX

CORE_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="position_0_inserts_at_beginning",
        setup_docs=[{"_id": 1, "arr": [100]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [50, 60, 70], "$position": 0}}},
        expected=[{"_id": 1, "arr": [50, 60, 70, 100]}],
        msg="$position 0 should insert all elements at beginning",
    ),
    UpdateTestCase(
        id="position_2_in_middle",
        setup_docs=[{"_id": 1, "arr": [50, 60, 70, 100]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [20, 30], "$position": 2}}},
        expected=[{"_id": 1, "arr": [50, 60, 20, 30, 70, 100]}],
        msg="$position 2 should insert at index 2",
    ),
    UpdateTestCase(
        id="position_exceeds_length_appends",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [4], "$position": 10}}},
        expected=[{"_id": 1, "arr": [1, 2, 3, 4]}],
        msg="$position beyond array length should append to end",
    ),
    UpdateTestCase(
        id="position_equals_length_appends",
        setup_docs=[{"_id": 1, "arr": ["a", "b", "c"]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": ["d"], "$position": 3}}},
        expected=[{"_id": 1, "arr": ["a", "b", "c", "d"]}],
        msg="$position equal to array length should append to end",
    ),
    UpdateTestCase(
        id="negative_1_before_last",
        setup_docs=[{"_id": 1, "arr": [50, 60, 70]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [10, 20], "$position": -1}}},
        expected=[{"_id": 1, "arr": [50, 60, 10, 20, 70]}],
        msg="$position -1 should insert before last element",
    ),
    UpdateTestCase(
        id="negative_2_before_second_to_last",
        setup_docs=[{"_id": 1, "arr": ["a", "b", "c", "d"]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": ["x"], "$position": -2}}},
        expected=[{"_id": 1, "arr": ["a", "b", "x", "c", "d"]}],
        msg="$position -2 should insert before second-to-last element",
    ),
    UpdateTestCase(
        id="negative_exceeds_length_inserts_at_beginning",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [0], "$position": -10}}},
        expected=[{"_id": 1, "arr": [0, 1, 2, 3]}],
        msg="$position with abs > length should insert at beginning",
    ),
    UpdateTestCase(
        id="position_0_on_empty_array",
        setup_docs=[{"_id": 1, "arr": []}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [1], "$position": 0}}},
        expected=[{"_id": 1, "arr": [1]}],
        msg="$position 0 on empty array should create single-element array",
    ),
    UpdateTestCase(
        id="negative_zero_same_as_zero",
        setup_docs=[{"_id": 1, "arr": [10, 20]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [5], "$position": -0.0}}},
        expected=[{"_id": 1, "arr": [5, 10, 20]}],
        msg="$position -0 should behave the same as 0",
    ),
    UpdateTestCase(
        id="negative_int32_max_inserts_at_beginning",
        setup_docs=[{"_id": 1, "arr": [1, 2]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [0], "$position": -INT32_MAX}}},
        expected=[{"_id": 1, "arr": [0, 1, 2]}],
        msg="$position -INT32_MAX on small array should insert at beginning",
    ),
    UpdateTestCase(
        id="negative_position_on_empty_array",
        setup_docs=[{"_id": 1, "arr": []}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [1, 2], "$position": -1}}},
        expected=[{"_id": 1, "arr": [1, 2]}],
        msg="Negative position on empty array should insert at beginning",
    ),
    UpdateTestCase(
        id="without_each_pushes_literal",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$position": 0}}},
        expected=[{"_id": 1, "arr": [1, 2, 3, {"$position": 0}]}],
        msg="$push without $each should treat modifier doc as literal element",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(CORE_TESTS))
def test_position_core(collection, test_case):
    """Test $position modifier core positioning behavior."""
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
