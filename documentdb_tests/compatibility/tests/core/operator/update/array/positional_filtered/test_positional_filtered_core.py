"""Tests for $[<identifier>] positional-filtered update operator core behavior.

Covers: matching elements via arrayFilters, no-match, all-match, and empty array.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.array.positional_filtered.utils.filtered_update_test_case import (  # noqa: E501
    FilteredUpdateTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

CORE_BEHAVIOR_TESTS: list[FilteredUpdateTestCase] = [
    FilteredUpdateTestCase(
        "set_matching_elements",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4, 5]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 0}},
        array_filters=[{"elem": {"$gte": 3}}],
        expected={"_id": 1, "arr": [1, 2, 0, 0, 0]},
        msg="$[<id>] should update only elements matching arrayFilters",
    ),
    FilteredUpdateTestCase(
        "no_match_noop",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": {"$gt": 100}}],
        expected={"_id": 1, "arr": [1, 2, 3]},
        msg="$[<id>] when no elements match should be no-op",
    ),
    FilteredUpdateTestCase(
        "all_match",
        setup_docs=[{"_id": 1, "arr": [10, 20, 30]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 0}},
        array_filters=[{"elem": {"$gte": 1}}],
        expected={"_id": 1, "arr": [0, 0, 0]},
        msg="$[<id>] when all elements match should update all",
    ),
    FilteredUpdateTestCase(
        "empty_array_noop",
        setup_docs=[{"_id": 1, "arr": []}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": {"$gte": 0}}],
        expected={"_id": 1, "arr": []},
        msg="$[<id>] on empty array should be no-op",
    ),
]


ALL_TESTS = CORE_BEHAVIOR_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_positional_filtered_core(collection, test: FilteredUpdateTestCase):
    """Test $[<identifier>] positional-filtered core behavior."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update, "arrayFilters": test.array_filters}],
        },
    )

    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": test.expected["_id"]}}
    )
    assertSuccess(result, [test.expected], msg=test.msg)
