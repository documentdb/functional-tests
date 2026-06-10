"""Tests for $ positional update operator core behavior.

Covers: first-match semantics, update command integration, upsert with
existing doc, and empty array edge case.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

CHANGED_DOC_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "set_first_match",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 2, 4]}],
        query={"_id": 1, "arr": 2},
        update={"$set": {"arr.$": 99}},
        expected={"_id": 1, "arr": [1, 99, 3, 2, 4]},
        msg="$ should update only the first matching element",
    ),
    UpdateTestCase(
        "match_last_element",
        setup_docs=[{"_id": 1, "arr": [10, 20, 30]}],
        query={"_id": 1, "arr": 30},
        update={"$set": {"arr.$": 99}},
        expected={"_id": 1, "arr": [10, 20, 99]},
        msg="$ should update last element when it matches",
    ),
    UpdateTestCase(
        "upsert_doc_exists_succeeds",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1, "arr": 2},
        update={"$set": {"arr.$": 99}},
        upsert=True,
        expected={"_id": 1, "arr": [1, 99, 3]},
        msg="$ in upsert when document exists and matches should work normally",
    ),
]


UPDATE_RESULT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "update_one",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}, {"_id": 2, "arr": [2, 3, 4]}],
        query={"arr": 2},
        update={"$set": {"arr.$": 99}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$ should work with updateOne (updates only one matched doc)",
    ),
    UpdateTestCase(
        "array_field_missing",
        setup_docs=[{"_id": 1, "x": 1}],
        query={"_id": 1, "arr": 5},
        update={"$set": {"arr.$": 99}},
        expected={"n": 0, "nModified": 0, "ok": 1.0},
        msg="$ when array field is missing should result in no match",
    ),
    UpdateTestCase(
        "empty_array_no_match",
        setup_docs=[{"_id": 1, "arr": []}],
        query={"_id": 1, "arr": 5},
        update={"$set": {"arr.$": 99}},
        expected={"n": 0, "nModified": 0, "ok": 1.0},
        msg="$ on empty array with no match should result in no update",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CHANGED_DOC_TESTS))
def test_positional_changed_doc(collection, test: UpdateTestCase):
    """Test $ positional update operator produces expected document."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    update_doc = {"q": test.query, "u": test.update}
    if test.upsert:
        update_doc["upsert"] = True
    execute_command(collection, {"update": collection.name, "updates": [update_doc]})

    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": test.expected["_id"]}}
    )
    assertSuccess(result, [test.expected], msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(UPDATE_RESULT_TESTS))
def test_positional_update_result(collection, test: UpdateTestCase):
    """Test $ positional update command returns expected n/nModified."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    result = execute_command(
        collection, {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]}
    )
    assertSuccess(result, test.expected, msg=test.msg, raw_res=True)
