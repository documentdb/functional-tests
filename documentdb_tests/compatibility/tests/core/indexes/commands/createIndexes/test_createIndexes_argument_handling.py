"""Tests for createIndexes command-level argument handling.

Validates the createIndexes field (collection name), indexes field,
comment field, and valid argument patterns.
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

ARGUMENT_HANDLING_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="nonexistent_collection_auto_creates",
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        msg="Should auto-create collection",
    ),
    IndexTestCase(
        id="string_comment",
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        comment="test comment",
        msg="String comment should succeed",
    ),
    IndexTestCase(
        id="object_comment",
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        comment={"key": "value"},
        msg="Object comment should succeed",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ARGUMENT_HANDLING_TESTS))
def test_createIndexes_argument_handling(collection, test):
    """Test createIndexes argument handling patterns."""
    cmd = {
        "createIndexes": collection.name,
        "indexes": list(test.indexes),
    }
    if test.comment is not None:
        cmd["comment"] = test.comment
    result = execute_command(collection, cmd)
    assertSuccessPartial(result, index_created_response(), test.msg)


def test_createIndexes_multiple_indexes(collection):
    """Test createIndexes with multiple index specs succeeds."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"a": 1}, "name": "a_1"},
                {"key": {"b": 1}, "name": "b_1"},
            ],
        },
    )
    assertSuccessPartial(
        result, index_created_response(num_indexes_after=3), "Multiple indexes should succeed"
    )


def test_createIndexes_same_key_diff_directions_in_batch(database_client):
    """Test same key but different directions in same request succeeds."""
    coll = database_client["diff_dir_batch"]
    coll.drop()
    result = execute_command(
        coll,
        {
            "createIndexes": coll.name,
            "indexes": [
                {"key": {"a": 1}, "name": "a_asc"},
                {"key": {"a": -1}, "name": "a_desc"},
            ],
        },
    )
    assertSuccessPartial(
        result,
        index_created_response(num_indexes_after=3),
        "Same key different directions should succeed",
    )
    coll.drop()


def test_createIndexes_max_64_indexes_succeeds(database_client):
    """Test creating 63 indexes (plus _id = 64 total) succeeds."""
    coll = database_client["max_idx_limit_test"]
    coll.drop()
    indexes = [{"key": {f"f{i}": 1}, "name": f"f{i}_1"} for i in range(63)]
    result = execute_command(
        coll,
        {
            "createIndexes": coll.name,
            "indexes": indexes,
        },
    )
    assertSuccessPartial(
        result, index_created_response(num_indexes_after=64), "63 indexes + _id = 64 should succeed"
    )
    coll.drop()
