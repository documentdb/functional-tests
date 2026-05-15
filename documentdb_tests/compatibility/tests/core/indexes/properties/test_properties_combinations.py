"""Tests for index property combinations.

Validates that indexes work correctly with combined properties:
TTL with sparse/partial/unique/collation, sparse with unique/collation,
and collation with background options.
"""

from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
    index_created_response,
)
from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertSuccess,
    assertSuccessPartial,
)
from documentdb_tests.framework.error_codes import DUPLICATE_KEY_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index

PROPERTY_COMBINATION_CREATE_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="ttl_with_sparse",
        indexes=(
            {
                "key": {"dateField": 1},
                "name": "ttl_sparse",
                "expireAfterSeconds": 3600,
                "sparse": True,
            },
        ),
        msg="Should allow TTL + sparse",
    ),
    IndexTestCase(
        id="ttl_with_partial_filter",
        indexes=(
            {
                "key": {"dateField": 1},
                "name": "ttl_partial",
                "expireAfterSeconds": 3600,
                "partialFilterExpression": {"status": "active"},
            },
        ),
        msg="Should allow TTL + partialFilterExpression",
    ),
    IndexTestCase(
        id="ttl_with_unique",
        indexes=(
            {
                "key": {"dateField": 1},
                "name": "ttl_unique",
                "expireAfterSeconds": 3600,
                "unique": True,
            },
        ),
        msg="Should allow TTL + unique",
    ),
    IndexTestCase(
        id="ttl_with_collation",
        indexes=(
            {
                "key": {"dateField": 1},
                "name": "ttl_collation",
                "expireAfterSeconds": 3600,
                "collation": {"locale": "en"},
            },
        ),
        msg="Should allow TTL + collation",
    ),
    IndexTestCase(
        id="ttl_with_sparse_and_unique",
        indexes=(
            {
                "key": {"dateField": 1},
                "name": "ttl_sparse_unique",
                "expireAfterSeconds": 3600,
                "sparse": True,
                "unique": True,
            },
        ),
        msg="Should allow TTL + sparse + unique",
    ),
    IndexTestCase(
        id="sparse_with_partial_filter",
        indexes=(
            {
                "key": {"status": 1},
                "name": "idx_sparse_partial",
                "sparse": True,
                "partialFilterExpression": {"status": {"$exists": True}},
            },
        ),
        msg="Should allow sparse + partialFilterExpression",
    ),
    IndexTestCase(
        id="sparse_with_collation",
        indexes=(
            {
                "key": {"name": 1},
                "name": "idx_ci_sparse",
                "sparse": True,
                "collation": {"locale": "en", "strength": 2},
            },
        ),
        msg="Should create sparse index with collation",
    ),
    IndexTestCase(
        id="background_with_collation",
        indexes=(
            {
                "key": {"name": 1},
                "name": "idx_ci_bg",
                "background": True,
                "collation": {"locale": "en", "strength": 2},
            },
        ),
        msg="Should create index with background option and collation",
    ),
    IndexTestCase(
        id="sparse_separate_from_unique",
        indexes=({"key": {"a": 1}, "name": "idx_sparse", "sparse": True},),
        setup_indexes=[{"key": {"a": 1}, "name": "idx_unique", "unique": True}],
        expected=index_created_response(num_indexes_before=2, num_indexes_after=3),
        msg="Sparse index should be separate from unique index on same key",
    ),
    IndexTestCase(
        id="unique_sparse_separate_from_sparse",
        indexes=({"key": {"a": 1}, "name": "idx_unique_sparse", "sparse": True, "unique": True},),
        setup_indexes=[{"key": {"a": 1}, "name": "idx_sparse", "sparse": True}],
        expected=index_created_response(num_indexes_before=2, num_indexes_after=3),
        msg="Unique+sparse should be separate from sparse-only on same key",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PROPERTY_COMBINATION_CREATE_TESTS))
def test_property_combination_create(collection, test):
    """Test that indexes can be created with combined properties."""
    if hasattr(test, "setup_indexes") and test.setup_indexes:
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


SPARSE_TTL_COUNT_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="ttl_combination",
        indexes=(
            {
                "key": {"expires": 1},
                "name": "idx_sparse_ttl",
                "sparse": True,
                "expireAfterSeconds": 3600,
            },
        ),
        doc=(
            {"_id": 1, "expires": datetime(2099, 1, 1, tzinfo=timezone.utc)},
            {"_id": 2},
        ),
        expected={"n": 1, "ok": 1.0},
        command_options={"query": {}, "hint": {"expires": 1}},
        msg="Sparse + TTL index — documents without TTL field not indexed",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SPARSE_TTL_COUNT_TESTS))
def test_sparse_ttl_count(collection, test):
    """Test sparse + TTL index behavior via count with hint."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    if test.doc:
        collection.insert_many(list(test.doc))
    result = execute_command(
        collection,
        {"count": collection.name, **test.command_options},
    )
    assertSuccess(result, test.expected, raw_res=True)


SPARSE_UNIQUE_SUCCESS_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="unique_allows_multiple_missing",
        indexes=({"key": {"a": 1}, "name": "idx_sparse_unique", "sparse": True, "unique": True},),
        doc=({"_id": 1},),
        expected={"n": 1, "ok": 1.0},
        command_options={"documents": [{"_id": 2}]},
        msg="Sparse + unique allows multiple documents missing the indexed field",
    ),
    IndexTestCase(
        id="unique_allows_one_null",
        indexes=({"key": {"a": 1}, "name": "idx_sparse_unique", "sparse": True, "unique": True},),
        doc=({"_id": 1, "a": 5},),
        expected={"n": 1, "ok": 1.0},
        command_options={"documents": [{"_id": 2, "a": None}]},
        msg="Sparse + unique allows first document with null value",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SPARSE_UNIQUE_SUCCESS_TESTS))
def test_sparse_unique_success(collection, test):
    """Test sparse + unique allows valid inserts."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    if test.doc:
        collection.insert_many(list(test.doc))
    result = execute_command(
        collection,
        {"insert": collection.name, **test.command_options},
    )
    assertSuccess(result, test.expected, raw_res=True)


SPARSE_UNIQUE_FAILURE_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="unique_rejects_second_null",
        indexes=({"key": {"a": 1}, "name": "idx_sparse_unique", "sparse": True, "unique": True},),
        doc=({"_id": 1, "a": None},),
        error_code=DUPLICATE_KEY_ERROR,
        command_options={"documents": [{"_id": 2, "a": None}]},
        msg="Sparse + unique rejects second document with null value",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SPARSE_UNIQUE_FAILURE_TESTS))
def test_sparse_unique_failure(collection, test):
    """Test sparse + unique rejects invalid inserts."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    if test.doc:
        collection.insert_many(list(test.doc))
    result = execute_command(
        collection,
        {"insert": collection.name, **test.command_options},
    )
    assertFailureCode(result, test.error_code, test.msg)
