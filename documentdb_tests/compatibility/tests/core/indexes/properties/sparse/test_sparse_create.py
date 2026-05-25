"""Tests for sparse index creation — key types, noop, signature behavior, and error cases."""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
    index_created_response,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.error_codes import (
    COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
    INDEX_KEY_SPECS_CONFLICT_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index


SPARSE_CREATE_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="single_field",
        indexes=({"key": {"x": 1}, "name": "idx_single_sparse", "sparse": True},),
        msg="Should create sparse index on single field",
    ),
    IndexTestCase(
        id="compound",
        indexes=({"key": {"a": 1, "b": -1}, "name": "idx_compound_sparse", "sparse": True},),
        msg="Should create sparse index on compound fields",
    ),
    IndexTestCase(
        id="descending",
        indexes=({"key": {"a": -1}, "name": "idx_desc_sparse", "sparse": True},),
        msg="Should create sparse index on descending field",
    ),
    IndexTestCase(
        id="hashed",
        indexes=({"key": {"a": "hashed"}, "name": "idx_hashed_sparse", "sparse": True},),
        msg="Should create sparse index on hashed field",
    ),
    IndexTestCase(
        id="on_nonexistent_collection",
        indexes=({"key": {"a": 1}, "name": "idx_sparse", "sparse": True},),
        expected={"ok": 1.0, "createdCollectionAutomatically": True, "numIndexesAfter": 2},
        msg="Should implicitly create collection",
    ),
    IndexTestCase(
        id="duplicate_identical_noop",
        indexes=({"key": {"a": 1}, "name": "idx_sparse", "sparse": True},),
        setup_indexes=[{"key": {"a": 1}, "name": "idx_sparse", "sparse": True}],
        expected=index_created_response(num_indexes_before=2, num_indexes_after=2),
        msg="Creating identical sparse index should be a no-op",
    ),
    IndexTestCase(
        id="sparse_separate_from_basic",
        indexes=({"key": {"a": 1}, "name": "idx_sparse", "sparse": True},),
        setup_indexes=[{"key": {"a": 1}, "name": "idx_basic"}],
        expected=index_created_response(num_indexes_before=2, num_indexes_after=3),
        msg="Sparse index on same key should be a separate index",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SPARSE_CREATE_TESTS))
def test_sparse_create(collection, test):
    """Test createIndex with valid sparse option values succeeds."""
    if test.doc:
        collection.insert_many(list(test.doc))
    if test.setup_indexes:
        execute_command(
            collection,
            {"createIndexes": collection.name, "indexes": test.setup_indexes},
        )
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    expected = test.expected if test.expected is not None else index_created_response()
    assertSuccessPartial(result, expected, msg=test.msg)


def test_sparse_create_on_capped_collection(database_client):
    """Test createIndex with sparse on capped collection succeeds."""
    db = database_client
    db.create_collection("test_capped", capped=True, size=4096)
    coll = db["test_capped"]
    result = execute_command(
        coll,
        {
            "createIndexes": coll.name,
            "indexes": [{"key": {"a": 1}, "name": "idx_sparse", "sparse": True}],
        },
    )
    assertSuccessPartial(result, {"ok": 1.0, "numIndexesAfter": 2})


def test_sparse_create_on_view_error(database_client):
    """Test createIndex with sparse on view returns error."""
    db = database_client
    db.create_collection("base_coll")
    db.command({"create": "test_view", "viewOn": "base_coll", "pipeline": []})
    coll = db["test_view"]
    result = execute_command(
        coll,
        {
            "createIndexes": coll.name,
            "indexes": [{"key": {"a": 1}, "name": "idx_sparse", "sparse": True}],
        },
    )
    assertFailureCode(result, COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR)


def test_sparse_create_name_conflict_error(collection):
    """Test createIndex with same name but different sparse value returns error."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "idx_a", "sparse": False}],
        },
    )
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "idx_a", "sparse": True}],
        },
    )
    assertFailureCode(result, INDEX_KEY_SPECS_CONFLICT_ERROR)
