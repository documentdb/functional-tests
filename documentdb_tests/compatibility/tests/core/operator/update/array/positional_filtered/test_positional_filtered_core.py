"""Tests for $[<identifier>] positional-filtered update operator core behavior.

Covers: matching elements via arrayFilters, no-match, all-match, empty array,
update command integration, and various update operators.
"""

from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class PositionalFilteredTest(BaseTestCase):
    """Test case for $[<identifier>] positional-filtered operator."""

    setup_docs: Any = None
    query: Any = None
    update: Any = None
    array_filters: Any = None


CORE_BEHAVIOR_TESTS: list[PositionalFilteredTest] = [
    PositionalFilteredTest(
        "set_matching_elements",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4, 5]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 0}},
        array_filters=[{"elem": {"$gte": 3}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] should update only elements matching arrayFilters",
    ),
    PositionalFilteredTest(
        "inc_matching_elements",
        setup_docs=[{"_id": 1, "arr": [10, 20, 30, 40]}],
        query={"_id": 1},
        update={"$inc": {"arr.$[elem]": 100}},
        array_filters=[{"elem": {"$gt": 20}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] with $inc should increment matching elements",
    ),
    PositionalFilteredTest(
        "mul_matching_elements",
        setup_docs=[{"_id": 1, "arr": [2, 4, 6, 8]}],
        query={"_id": 1},
        update={"$mul": {"arr.$[elem]": 10}},
        array_filters=[{"elem": {"$lt": 5}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] with $mul should multiply matching elements",
    ),
    PositionalFilteredTest(
        "no_match_noop",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": {"$gt": 100}}],
        expected={"n": 1, "nModified": 0, "ok": 1.0},
        msg="$[<id>] when no elements match should be no-op",
    ),
    PositionalFilteredTest(
        "all_match",
        setup_docs=[{"_id": 1, "arr": [10, 20, 30]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 0}},
        array_filters=[{"elem": {"$gte": 1}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] when all elements match should update all",
    ),
    PositionalFilteredTest(
        "empty_array_noop",
        setup_docs=[{"_id": 1, "arr": []}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": {"$gte": 0}}],
        expected={"n": 1, "nModified": 0, "ok": 1.0},
        msg="$[<id>] on empty array should be no-op",
    ),
    PositionalFilteredTest(
        "non_matching_unchanged",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4, 5]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 0}},
        array_filters=[{"elem": {"$eq": 3}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] should leave non-matching elements unchanged",
    ),
]


# --- Update Command Integration ---

COMMAND_INTEGRATION_TESTS: list[PositionalFilteredTest] = [
    PositionalFilteredTest(
        "update_one",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 0}},
        array_filters=[{"elem": {"$gte": 2}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] should work with updateOne",
    ),
]


# --- JS-based: $[<identifier>] with various update operators ---

JS_UPDATE_OPERATORS_TESTS: list[PositionalFilteredTest] = [
    PositionalFilteredTest(
        "unset_matching",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4]}],
        query={"_id": 1},
        update={"$unset": {"arr.$[elem]": ""}},
        array_filters=[{"elem": {"$gte": 3}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] with $unset should set matching elements to null",
    ),
    PositionalFilteredTest(
        "addToSet_matching_subarrays",
        setup_docs=[{"_id": 1, "arr": [[1, 2], [3, 4], [5, 6]]}],
        query={"_id": 1},
        update={"$addToSet": {"arr.$[elem]": 99}},
        array_filters=[{"elem": {"$size": 2}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] with $addToSet should add to matching sub-arrays",
    ),
    PositionalFilteredTest(
        "push_matching_subarrays",
        setup_docs=[{"_id": 1, "arr": [[1], [2, 3], [4]]}],
        query={"_id": 1},
        update={"$push": {"arr.$[elem]": 99}},
        array_filters=[{"elem": {"$size": 1}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] with $push should append to matching sub-arrays",
    ),
]


# --- Update Operators ---

UPDATE_OPERATOR_TESTS: list[PositionalFilteredTest] = [
    PositionalFilteredTest(
        "min_matching",
        setup_docs=[{"_id": 1, "arr": [10, 20, 30]}],
        query={"_id": 1},
        update={"$min": {"arr.$[elem]": 15}},
        array_filters=[{"elem": {"$gte": 1}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] with $min should update matching elements if new value is less",
    ),
    PositionalFilteredTest(
        "max_matching",
        setup_docs=[{"_id": 1, "arr": [10, 20, 30]}],
        query={"_id": 1},
        update={"$max": {"arr.$[elem]": 25}},
        array_filters=[{"elem": {"$gte": 1}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] with $max should update matching elements if new value is greater",
    ),
]


ALL_TESTS = (
    CORE_BEHAVIOR_TESTS
    + COMMAND_INTEGRATION_TESTS
    + JS_UPDATE_OPERATORS_TESTS
    + UPDATE_OPERATOR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_positional_filtered_core(collection, test: PositionalFilteredTest):
    """Test $[<identifier>] positional-filtered core behavior."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    command = {
        "update": collection.name,
        "updates": [
            {
                "q": test.query,
                "u": test.update,
                "arrayFilters": test.array_filters,
            }
        ],
    }
    result = execute_command(collection, command)
    assertSuccess(result, test.expected, msg=test.msg, raw_res=True)
