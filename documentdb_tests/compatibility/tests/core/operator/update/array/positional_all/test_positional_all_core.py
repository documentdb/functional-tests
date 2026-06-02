"""Tests for $[] positional-all update operator core behavior.

Covers: update all elements, empty array, single element, and query filtering.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

CHANGED_DOC_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "set_all_elements",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": 0}},
        expected={"_id": 1, "arr": [0, 0, 0]},
        msg="$[] with $set should update all elements",
    ),
    UpdateTestCase(
        "single_element",
        setup_docs=[{"_id": 1, "arr": [42]}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": 99}},
        expected={"_id": 1, "arr": [99]},
        msg="$[] on single element array should update that element",
    ),
    UpdateTestCase(
        "query_not_referencing_array",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3], "x": "a"}],
        query={"x": "a"},
        update={"$set": {"arr.$[]": 0}},
        expected={"_id": 1, "arr": [0, 0, 0], "x": "a"},
        msg="$[] with query not referencing array field should update all elements in matched docs",
    ),
]


UPDATE_RESULT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "empty_array_noop",
        setup_docs=[{"_id": 1, "arr": []}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": 99}},
        expected={"n": 1, "nModified": 0, "ok": 1.0},
        msg="$[] on empty array should be no-op",
    ),
    UpdateTestCase(
        "only_matched_docs_updated",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3], "x": 1}, {"_id": 2, "arr": [4, 5, 6], "x": 2}],
        query={"x": 1},
        update={"$set": {"arr.$[]": 0}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] should only update elements in matched documents",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CHANGED_DOC_TESTS))
def test_positional_all_changed_doc(collection, test: UpdateTestCase):
    """Test $[] positional-all produces expected document."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )

    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": test.expected["_id"]}}
    )
    assertSuccess(result, [test.expected], msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(UPDATE_RESULT_TESTS))
def test_positional_all_update_result(collection, test: UpdateTestCase):
    """Test $[] positional-all update command returns expected n/nModified."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    assertSuccess(result, test.expected, msg=test.msg, raw_res=True)
