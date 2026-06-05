"""Tests for text index creation error cases.

Validates invalid key specifier, missing text index requirement, multiple
text indexes on the same collection, non-simple collation, invalid
textIndexVersion, non-adjacent text keys, and text combined with geospatial.
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


def test_text_on_non_simple_collation_fails(database_client, collection):
    """Test text index on a collection with non-simple collation fails.

    Text indexes do not support collation; the collection's non-simple
    collation is inherited unless overridden with locale 'simple'.
    """
    database_client.create_collection(collection.name, collation={"locale": "en"})
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"a": "text"}, "name": "a_text"}]},
    )
    assertFailureCode(
        result, CANNOT_CREATE_INDEX_ERROR, msg="Text index on non-simple collation should fail"
    )


def test_text_index_version_zero_fails(collection):
    """Test textIndexVersion 0 fails (only versions 1, 2, 3 are valid)."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": "text"}, "name": "a_text_v0", "textIndexVersion": 0}],
        },
    )
    assertFailureCode(result, CANNOT_CREATE_INDEX_ERROR, msg="textIndexVersion 0 should fail")


def test_text_index_version_four_fails(collection):
    """Test textIndexVersion 4 fails (only versions 1, 2, 3 are valid)."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": "text"}, "name": "a_text_v4", "textIndexVersion": 4}],
        },
    )
    assertFailureCode(result, CANNOT_CREATE_INDEX_ERROR, msg="textIndexVersion 4 should fail")


def test_text_non_adjacent_text_keys_fails(collection):
    """Test compound index with non-adjacent text keys fails (text keys must be adjacent)."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": "text", "b": 1, "c": "text"}, "name": "a_text_b_c_text"}],
        },
    )
    assertFailureCode(result, CANNOT_CREATE_INDEX_ERROR, msg="Non-adjacent text keys should fail")


def test_text_with_geospatial_key_fails(collection):
    """Test compound index combining text and 2dsphere keys fails."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"content": "text", "loc": "2dsphere"}, "name": "content_loc"}],
        },
    )
    assertFailureCode(
        result, CANNOT_CREATE_INDEX_ERROR, msg="Text combined with 2dsphere should fail"
    )
