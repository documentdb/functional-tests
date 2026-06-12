"""
Core behavior tests for the $pop update array operator.

Tests removal of the first and last element, empty and single-element arrays,
no-op on missing fields, content preservation across mixed types,
upsert behavior, and update result metadata (n, nModified).
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Core Removal]: $pop with 1 removes the last element and with -1 removes the first,
# leaving an empty array when the last element is removed and a no-op on empty or missing arrays
# or an empty operand.
TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "remove_last",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$pop": {"arr": 1}},
        expected={"_id": 1, "arr": [1, 2]},
        msg="$pop with 1 should remove the last element",
    ),
    UpdateTestCase(
        "remove_first",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$pop": {"arr": -1}},
        expected={"_id": 1, "arr": [2, 3]},
        msg="$pop with -1 should remove the first element",
    ),
    UpdateTestCase(
        "empty_array_last_noop",
        setup_docs=[{"_id": 1, "arr": []}],
        query={"_id": 1},
        update={"$pop": {"arr": 1}},
        expected={"_id": 1, "arr": []},
        msg="$pop with 1 on an empty array should be a no-op",
    ),
    UpdateTestCase(
        "removing_last_item_leaves_empty_array_field",
        setup_docs=[{"_id": 1, "arr": [42], "other": "keep"}],
        query={"_id": 1},
        update={"$pop": {"arr": 1}},
        expected={"_id": 1, "arr": [], "other": "keep"},
        msg="$pop removing the last item should keep the field as an empty array",
    ),
    UpdateTestCase(
        "missing_field_noop",
        setup_docs=[{"_id": 1, "x": 1}],
        query={"_id": 1},
        update={"$pop": {"arr": 1}},
        expected={"_id": 1, "x": 1},
        msg="$pop on a missing field should be a no-op",
    ),
    UpdateTestCase(
        "empty_operand_noop",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$pop": {}},
        expected={"_id": 1, "arr": [1, 2, 3]},
        msg="$pop with an empty operand should be a no-op",
    ),
    UpdateTestCase(
        "mixed_types_last_preserves_order",
        setup_docs=[{"_id": 1, "arr": [1, "two", True, None, {"a": 1}]}],
        query={"_id": 1},
        update={"$pop": {"arr": 1}},
        expected={"_id": 1, "arr": [1, "two", True, None]},
        msg="$pop with 1 on a mixed-type array should remove the last element and preserve order",
    ),
    UpdateTestCase(
        "nested_arrays_preserved",
        setup_docs=[{"_id": 1, "arr": [[1, 2], [3, 4], [5, 6]]}],
        query={"_id": 1},
        update={"$pop": {"arr": 1}},
        expected={"_id": 1, "arr": [[1, 2], [3, 4]]},
        msg="$pop on an array of arrays should remove the last nested array intact",
    ),
    UpdateTestCase(
        "embedded_docs_preserved",
        setup_docs=[{"_id": 1, "arr": [{"a": 1}, {"b": 2}, {"c": 3}]}],
        query={"_id": 1},
        update={"$pop": {"arr": -1}},
        expected={"_id": 1, "arr": [{"b": 2}, {"c": 3}]},
        msg="$pop on an array of documents should remove the first document intact",
    ),
    UpdateTestCase(
        "null_element_last_removed",
        setup_docs=[{"_id": 1, "arr": [1, 2, None]}],
        query={"_id": 1},
        update={"$pop": {"arr": 1}},
        expected={"_id": 1, "arr": [1, 2]},
        msg="$pop with 1 should remove a trailing null element",
    ),
    UpdateTestCase(
        "interior_nulls_preserved",
        setup_docs=[{"_id": 1, "arr": [1, None, None, 2]}],
        query={"_id": 1},
        update={"$pop": {"arr": 1}},
        expected={"_id": 1, "arr": [1, None, None]},
        msg="$pop should preserve interior null elements",
    ),
]


# Property [Upsert Behavior]: $pop with upsert inserts a document without the array field on
# no match and removes an element on match.
UPSERT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "upsert_no_match_creates_doc_without_field",
        setup_docs=None,
        query={"_id": 99},
        update={"$pop": {"arr": 1}},
        upsert=True,
        expected={"_id": 99},
        msg="$pop with upsert and no match should create a document without the array field",
    ),
    UpdateTestCase(
        "upsert_match_removes_last",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$pop": {"arr": 1}},
        upsert=True,
        expected={"_id": 1, "arr": [1, 2]},
        msg="$pop with upsert and a matching document should remove the last element",
    ),
]

# Property [Result Metadata]: $pop reports nModified only for documents whose array changed,
# so empty arrays and non-matching documents do not count as modified.
UPDATE_RESULT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "no_match",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 999},
        update={"$pop": {"arr": 1}},
        expected={"n": 0, "nModified": 0, "ok": 1.0},
        msg="$pop should report n=0, nModified=0 when no document matches",
    ),
    UpdateTestCase(
        "empty_array_not_modified",
        setup_docs=[{"_id": 1, "arr": []}],
        query={"_id": 1},
        update={"$pop": {"arr": 1}},
        expected={"n": 1, "nModified": 0, "ok": 1.0},
        msg="$pop should report nModified=0 when the matched array is empty",
    ),
    UpdateTestCase(
        "multi_partial_modification",
        setup_docs=[
            {"_id": 1, "arr": [1, 2, 3]},
            {"_id": 2, "arr": []},
            {"_id": 3, "arr": [9]},
        ],
        query={},
        update={"$pop": {"arr": 1}},
        multi=True,
        expected={"n": 3, "nModified": 2, "ok": 1.0},
        msg="$pop should modify 2 of 3 documents, skipping the empty array",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS + UPSERT_TESTS))
def test_pop_core_behavior(collection, test: UpdateTestCase):
    """Test $pop core removal and upsert document results."""
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
def test_pop_update_result(collection, test: UpdateTestCase):
    """Test $pop update command returns expected n/nModified."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    update_doc = {"q": test.query, "u": test.update}
    if test.multi:
        update_doc["multi"] = True

    result = execute_command(collection, {"update": collection.name, "updates": [update_doc]})
    assertSuccess(result, test.expected, msg=test.msg, raw_res=True)
