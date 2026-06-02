"""Tests for $[] positional-all update operator core behavior.

Covers: update all elements, empty array, single element, and query filtering.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

CORE_BEHAVIOR_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "set_all_elements",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": 0}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] with $set should update all elements",
    ),
    UpdateTestCase(
        "empty_array_noop",
        setup_docs=[{"_id": 1, "arr": []}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": 99}},
        expected={"n": 1, "nModified": 0, "ok": 1.0},
        msg="$[] on empty array should be no-op",
    ),
    UpdateTestCase(
        "single_element",
        setup_docs=[{"_id": 1, "arr": [42]}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": 99}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] on single element array should update that element",
    ),
]


# --- Query Filtering ---

QUERY_FILTERING_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "only_matched_docs_updated",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3], "x": 1}, {"_id": 2, "arr": [4, 5, 6], "x": 2}],
        query={"x": 1},
        update={"$set": {"arr.$[]": 0}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] should only update elements in matched documents",
    ),
    UpdateTestCase(
        "query_not_referencing_array",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3], "x": "a"}],
        query={"x": "a"},
        update={"$set": {"arr.$[]": 0}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] with query not referencing array field should update all elements in matched docs",
    ),
]


ALL_TESTS = CORE_BEHAVIOR_TESTS + QUERY_FILTERING_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_positional_all_core(collection, test: UpdateTestCase):
    """Test $[] positional-all update operator core behavior."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    command = {
        "update": collection.name,
        "updates": [{"q": test.query, "u": test.update}],
    }
    result = execute_command(collection, command)
    assertSuccess(result, test.expected, msg=test.msg, raw_res=True)
