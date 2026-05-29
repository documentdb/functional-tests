"""Tests for text index creation error cases.

Validates invalid key specifier, missing text index requirement,
and multiple text indexes on the same collection.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    CANNOT_CREATE_INDEX_ERROR,
    INDEX_NOT_FOUND_ERROR,
    INDEX_OPTIONS_CONFLICT_ERROR,
)
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.text_search


def test_text_invalid_string_key_specifier_fails(collection):
    """Test index creation with invalid string key specifier fails."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"content": "invalid"}, "name": "idx"}],
        },
    )
    assertFailureCode(
        result, CANNOT_CREATE_INDEX_ERROR, msg="Invalid string key specifier should fail"
    )


def test_text_without_index_fails(collection):
    """Test $text query without text index fails."""
    collection.insert_one({"_id": 1, "content": "hello"})
    result = execute_command(
        collection, {"find": collection.name, "filter": {"$text": {"$search": "hello"}}}
    )
    assertFailureCode(result, INDEX_NOT_FOUND_ERROR, msg="$text without text index should fail")


def test_text_two_indexes_fails(collection):
    """Test creating two text indexes on same collection fails."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"a": "text"}, "name": "a_text"}]},
    )
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"b": "text"}, "name": "b_text"}]},
    )
    assertFailureCode(result, INDEX_OPTIONS_CONFLICT_ERROR, msg="Two text indexes should fail")
