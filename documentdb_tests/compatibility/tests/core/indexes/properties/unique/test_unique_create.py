"""Tests for unique index creation — success cases.

Validates createIndex with unique option for direction variants,
implicit collection creation, coexistence with non-unique indexes
on the same key, and idempotent re-creation.
"""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
    index_created_response,
)
from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index


UNIQUE_CREATE_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="ascending",
        indexes=({"key": {"a": 1}, "name": "idx_asc_unique", "unique": True},),
        msg="Should create unique index on ascending field",
    ),
    IndexTestCase(
        id="descending",
        indexes=({"key": {"a": -1}, "name": "idx_desc_unique", "unique": True},),
        msg="Should create unique index on descending field",
    ),
    IndexTestCase(
        id="on_nonexistent_collection",
        indexes=({"key": {"a": 1}, "name": "idx_unique", "unique": True},),
        expected={"ok": 1.0, "createdCollectionAutomatically": True, "numIndexesAfter": 2},
        msg="Should implicitly create collection when it doesn't exist",
    ),
    IndexTestCase(
        id="separate_from_basic",
        indexes=({"key": {"a": 1}, "name": "idx_unique", "unique": True},),
        setup_indexes=[{"key": {"a": 1}, "name": "idx_basic"}],
        expected=index_created_response(num_indexes_before=2, num_indexes_after=3),
        msg="Should create unique index alongside basic index on same key",
    ),
    IndexTestCase(
        id="duplicate_identical_noop",
        indexes=({"key": {"a": 1}, "name": "idx_unique", "unique": True},),
        setup_indexes=[{"key": {"a": 1}, "name": "idx_unique", "unique": True}],
        expected=index_created_response(num_indexes_before=2, num_indexes_after=2),
        msg="Creating identical unique index should be a no-op",
    ),
]


@pytest.mark.parametrize("test", pytest_params(UNIQUE_CREATE_TESTS))
def test_unique_create(collection, test):
    """Test createIndex with unique option succeeds."""
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
