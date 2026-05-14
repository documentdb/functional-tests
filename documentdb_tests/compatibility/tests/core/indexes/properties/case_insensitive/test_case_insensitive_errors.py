"""Tests for case-insensitive index error scenarios.

Validates error handling for invalid collation configurations,
collation index conflicts, and unique constraint violations
with case-insensitive collation.
"""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    CANNOT_CREATE_INDEX_ERROR,
    DUPLICATE_KEY_ERROR,
    INDEX_KEY_SPECS_CONFLICT_ERROR,
    INDEX_OPTIONS_CONFLICT_ERROR,
    MISSING_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index

INVALID_CREATE_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="missing_locale",
        indexes=({"key": {"name": 1}, "name": "idx_bad", "collation": {"strength": 2}},),
        error_code=MISSING_FIELD_ERROR,
        msg="Should reject collation missing locale field",
    ),
    IndexTestCase(
        id="empty_locale",
        indexes=(
            {"key": {"name": 1}, "name": "idx_bad", "collation": {"locale": "", "strength": 2}},
        ),
        error_code=BAD_VALUE_ERROR,
        msg="Should reject collation with empty locale",
    ),
    IndexTestCase(
        id="collation_empty_object",
        indexes=({"key": {"name": 1}, "name": "idx_bad", "collation": {}},),
        error_code=BAD_VALUE_ERROR,
        msg="Should reject empty collation object",
    ),
    IndexTestCase(
        id="key_empty_object",
        indexes=({"key": {}, "name": "idx_bad", "collation": {"locale": "en", "strength": 2}},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Should reject empty key object",
    ),
    IndexTestCase(
        id="strength_zero",
        indexes=(
            {"key": {"name": 1}, "name": "idx_bad", "collation": {"locale": "en", "strength": 0}},
        ),
        error_code=BAD_VALUE_ERROR,
        msg="Should reject collation with strength 0",
    ),
    IndexTestCase(
        id="strength_negative",
        indexes=(
            {"key": {"name": 1}, "name": "idx_bad", "collation": {"locale": "en", "strength": -1}},
        ),
        error_code=BAD_VALUE_ERROR,
        msg="Should reject collation with negative strength",
    ),
    IndexTestCase(
        id="invalid_locale",
        indexes=(
            {"key": {"name": 1}, "name": "idx_bad", "collation": {"locale": "zzz", "strength": 2}},
        ),
        error_code=BAD_VALUE_ERROR,
        msg="Should reject unsupported locale",
    ),
    IndexTestCase(
        id="strength_above_max",
        indexes=(
            {"key": {"name": 1}, "name": "idx_bad", "collation": {"locale": "en", "strength": 6}},
        ),
        error_code=BAD_VALUE_ERROR,
        msg="Should reject strength greater than 5",
    ),
    IndexTestCase(
        id="strength_as_string",
        indexes=(
            {"key": {"name": 1}, "name": "idx_bad", "collation": {"locale": "en", "strength": "2"}},
        ),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject non-integer strength",
    ),
    IndexTestCase(
        id="locale_as_empty_object",
        indexes=(
            {"key": {"name": 1}, "name": "idx_bad", "collation": {"locale": {}, "strength": 2}},
        ),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject empty object as locale",
    ),
    IndexTestCase(
        id="locale_as_empty_array",
        indexes=(
            {"key": {"name": 1}, "name": "idx_bad", "collation": {"locale": [], "strength": 2}},
        ),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject empty array as locale",
    ),
    IndexTestCase(
        id="strength_as_empty_object",
        indexes=(
            {"key": {"name": 1}, "name": "idx_bad", "collation": {"locale": "en", "strength": {}}},
        ),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject empty object as strength",
    ),
    IndexTestCase(
        id="strength_as_empty_array",
        indexes=(
            {"key": {"name": 1}, "name": "idx_bad", "collation": {"locale": "en", "strength": []}},
        ),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject empty array as strength",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_CREATE_TESTS))
def test_case_insensitive_create_invalid(collection, test):
    """Test createIndex with invalid collation options fails."""
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    assertFailureCode(result, test.error_code, msg=test.msg)


CONFLICT_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="same_key_collation_different_name",
        indexes=(
            {"key": {"name": 1}, "name": "idx_ci_2", "collation": {"locale": "en", "strength": 2}},
        ),
        setup_indexes=[
            {"key": {"name": 1}, "name": "idx_ci_1", "collation": {"locale": "en", "strength": 2}}
        ],
        error_code=INDEX_OPTIONS_CONFLICT_ERROR,
        msg="Should error when same key+collation has different name",
    ),
    IndexTestCase(
        id="same_name_different_collation",
        indexes=(
            {"key": {"name": 1}, "name": "idx_ci", "collation": {"locale": "en", "strength": 1}},
        ),
        setup_indexes=[
            {"key": {"name": 1}, "name": "idx_ci", "collation": {"locale": "en", "strength": 2}}
        ],
        error_code=INDEX_KEY_SPECS_CONFLICT_ERROR,
        msg="Should error when same name has different collation",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CONFLICT_TESTS))
def test_case_insensitive_create_conflict(collection, test):
    """Test createIndex with conflicting collation options fails."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": test.setup_indexes},
    )
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    assertFailureCode(result, test.error_code, msg=test.msg)


def test_case_insensitive_unique_rejects_case_variant(collection):
    """Test unique case-insensitive index rejects case-different duplicate."""
    collection.create_index([("v", 1)], unique=True, collation={"locale": "en", "strength": 2})
    collection.insert_one({"v": "hello"})
    result = execute_command(
        collection,
        {
            "insert": collection.name,
            "documents": [{"v": "HELLO"}],
        },
    )
    assertFailureCode(
        result, DUPLICATE_KEY_ERROR, msg="Should reject case-different duplicate with strength 2"
    )


def test_case_insensitive_unique_strength_1_rejects_accented(collection):
    """Test unique index with strength 1 rejects accented variant."""
    collection.create_index([("v", 1)], unique=True, collation={"locale": "en", "strength": 1})
    collection.insert_one({"v": "cafe"})
    result = execute_command(
        collection,
        {
            "insert": collection.name,
            "documents": [{"v": "café"}],
        },
    )
    assertFailureCode(
        result, DUPLICATE_KEY_ERROR, msg="Should reject accented variant with strength 1"
    )


def test_case_insensitive_unique_multiple_case_variants_rejected(collection):
    """Test unique index rejects multiple case variants."""
    collection.create_index([("v", 1)], unique=True, collation={"locale": "en", "strength": 2})
    collection.insert_one({"v": "Test"})
    result = execute_command(
        collection,
        {
            "insert": collection.name,
            "documents": [{"v": "test"}],
        },
    )
    assertFailureCode(result, DUPLICATE_KEY_ERROR, msg="Should reject 'test' when 'Test' exists")


def test_case_insensitive_unique_compound_rejects_duplicate(collection):
    """Test unique compound case-insensitive index rejects case-variant duplicate."""
    collection.create_index(
        [("a", 1), ("b", 1)], unique=True, collation={"locale": "en", "strength": 2}
    )
    collection.insert_one({"a": "Hello", "b": "World"})
    result = execute_command(
        collection,
        {
            "insert": collection.name,
            "documents": [{"a": "hello", "b": "world"}],
        },
    )
    assertFailureCode(
        result,
        DUPLICATE_KEY_ERROR,
        msg="Should reject case-variant duplicate on compound unique index",
    )
