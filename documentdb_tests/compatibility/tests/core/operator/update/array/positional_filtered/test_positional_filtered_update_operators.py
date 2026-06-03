"""Tests for $[<identifier>] with update operators.

Covers: $set, $inc, $mul, $min, $max, $unset with arrayFilters.
"""

from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class FilteredUpdateOpTest(BaseTestCase):
    """Test case for $[<identifier>] with update operators."""

    setup_docs: Any = None
    query: Any = None
    update: Any = None
    array_filters: Any = None


UPDATE_OPERATOR_TESTS: list[FilteredUpdateOpTest] = [
    FilteredUpdateOpTest(
        "set_matching",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4, 5]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 0}},
        array_filters=[{"elem": {"$gte": 4}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] with $set should replace matching elements",
    ),
    FilteredUpdateOpTest(
        "inc_matching",
        setup_docs=[{"_id": 1, "arr": [10, 20, 30, 40]}],
        query={"_id": 1},
        update={"$inc": {"arr.$[elem]": 100}},
        array_filters=[{"elem": {"$gte": 30}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] with $inc should increment matching elements",
    ),
    FilteredUpdateOpTest(
        "mul_matching",
        setup_docs=[{"_id": 1, "arr": [2, 4, 6, 8]}],
        query={"_id": 1},
        update={"$mul": {"arr.$[elem]": 10}},
        array_filters=[{"elem": {"$lte": 4}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] with $mul should multiply matching elements",
    ),
    FilteredUpdateOpTest(
        "min_matching",
        setup_docs=[{"_id": 1, "arr": [10, 20, 30, 40]}],
        query={"_id": 1},
        update={"$min": {"arr.$[elem]": 25}},
        array_filters=[{"elem": {"$gte": 1}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] with $min should update matching elements if new value is less",
    ),
    FilteredUpdateOpTest(
        "max_matching",
        setup_docs=[{"_id": 1, "arr": [10, 20, 30, 40]}],
        query={"_id": 1},
        update={"$max": {"arr.$[elem]": 25}},
        array_filters=[{"elem": {"$lte": 20}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] with $max should update matching elements if new value is greater",
    ),
    FilteredUpdateOpTest(
        "unset_matching",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4, 5]}],
        query={"_id": 1},
        update={"$unset": {"arr.$[elem]": ""}},
        array_filters=[{"elem": {"$gte": 4}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] with $unset should set matching elements to null",
    ),
    FilteredUpdateOpTest(
        "unset_field_in_embedded_docs",
        setup_docs=[
            {"_id": 1, "arr": [{"x": 1, "y": "a"}, {"x": 2, "y": "b"}, {"x": 3, "y": "c"}]}
        ],
        query={"_id": 1},
        update={"$unset": {"arr.$[elem].y": ""}},
        array_filters=[{"elem.x": {"$gte": 2}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] with $unset on embedded doc field should remove field from matching docs",
    ),
]


@pytest.mark.parametrize("test", pytest_params(UPDATE_OPERATOR_TESTS))
def test_positional_filtered_update_operators(collection, test: FilteredUpdateOpTest):
    """Test $[<identifier>] with various update operators."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    command = {
        "update": collection.name,
        "updates": [{"q": test.query, "u": test.update, "arrayFilters": test.array_filters}],
    }
    result = execute_command(collection, command)
    assertSuccess(result, test.expected, msg=test.msg, raw_res=True)
