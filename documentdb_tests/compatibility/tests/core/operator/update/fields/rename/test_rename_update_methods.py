"""
Update method context tests for $rename.

Tests $rename result metadata and behavior across updateOne, updateMany, and
upsert, including no-op outcomes (missing source, empty operand, $-prefixed
source) asserted via update-result metadata.

Cross-operator behavior is covered elsewhere: same-field conflicts in
test_rename_errors.py::PATH_CONFLICT_TESTS.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

UPDATE_METHOD_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "update_one",
        setup_docs=[{"_id": 1, "old": "value"}],
        query={"_id": 1},
        update={"$rename": {"old": "new"}},
        expected={"n": 1, "nModified": 1},
        msg="$rename in updateOne should report correct metadata",
    ),
    UpdateTestCase(
        "update_many",
        setup_docs=[{"_id": 1, "old": "a"}, {"_id": 2, "old": "b"}, {"_id": 3, "old": "c"}],
        query={},
        update={"$rename": {"old": "new"}},
        multi=True,
        expected={"n": 3, "nModified": 3},
        msg="$rename in updateMany should update all matching docs",
    ),
    UpdateTestCase(
        "update_no_match",
        setup_docs=[{"_id": 1, "a": 1}],
        query={"_id": 999},
        update={"$rename": {"a": "b"}},
        expected={"n": 0, "nModified": 0},
        msg="$rename with no match should report n=0",
    ),
    UpdateTestCase(
        "update_source_missing_no_modification",
        setup_docs=[{"_id": 1, "x": 1}],
        query={"_id": 1},
        update={"$rename": {"nonexistent": "b"}},
        expected={"n": 1, "nModified": 0},
        msg="$rename on missing source should report nModified=0",
    ),
    UpdateTestCase(
        "empty_operand_no_op",
        setup_docs=[{"_id": 1, "a": 1}],
        query={"_id": 1},
        update={"$rename": {}},
        expected={"n": 1, "nModified": 0},
        msg="$rename with empty operand should match but modify nothing",
    ),
    UpdateTestCase(
        "dollar_prefixed_source_no_op",
        setup_docs=[{"_id": 1, "a": 1}],
        query={"_id": 1},
        update={"$rename": {"$a": "b"}},
        expected={"n": 1, "nModified": 0},
        msg="$rename with $-prefixed source (field absent) should match but modify nothing",
    ),
    UpdateTestCase(
        "update_many_partial_source",
        setup_docs=[{"_id": 1, "old": "a"}, {"_id": 2, "other": "b"}, {"_id": 3, "old": "c"}],
        query={},
        update={"$rename": {"old": "new"}},
        multi=True,
        expected={"n": 3, "nModified": 2},
        msg="$rename updateMany should report nModified only for docs with source field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(UPDATE_METHOD_TESTS))
def test_rename_update_methods(collection, test: UpdateTestCase):
    """Test $rename update result metadata across methods."""
    collection.insert_many(test.setup_docs)

    update_doc = {"q": test.query, "u": test.update}
    if test.multi:
        update_doc["multi"] = True

    result = execute_command(collection, {"update": collection.name, "updates": [update_doc]})
    assertSuccessPartial(result, test.expected, msg=test.msg)


UPSERT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "upsert_source_missing",
        setup_docs=None,
        query={"_id": 1},
        update={"$rename": {"a": "b"}},
        upsert=True,
        expected={"_id": 1},
        msg="$rename with upsert on missing doc should create empty doc (source absent)",
    ),
    UpdateTestCase(
        "upsert_source_from_query",
        setup_docs=None,
        query={"_id": 1, "a": 1},
        update={"$rename": {"a": "b"}},
        upsert=True,
        expected={"_id": 1, "b": 1},
        msg="$rename with upsert should rename field implied by query equality",
    ),
]


@pytest.mark.parametrize("test", pytest_params(UPSERT_TESTS))
def test_rename_upsert(collection, test: UpdateTestCase):
    """Test $rename with upsert creates expected document."""
    update_doc = {"q": test.query, "u": test.update, "upsert": True}
    execute_command(collection, {"update": collection.name, "updates": [update_doc]})

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [test.expected], msg=test.msg)
