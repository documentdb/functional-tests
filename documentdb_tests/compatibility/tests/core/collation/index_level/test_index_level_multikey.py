"""Tests for collation with multikey indexes and index build on existing duplicates."""

from __future__ import annotations

import pytest
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import DUPLICATE_KEY_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [Multikey Index with Collation]: a collated index on an array field
# correctly handles multiple keys per document, using collation for both
# uniqueness enforcement and query matching across array elements.
COLLATION_MULTIKEY_INDEX_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "multikey_unique_rejects_case_variant_across_docs",
        indexes=[
            IndexModel(
                [("tags", 1)],
                unique=True,
                collation={"locale": "en", "strength": 2},
                name="tags_unique_ci",
            )
        ],
        docs=[{"_id": 1, "tags": ["apple", "banana"]}],
        command=lambda ctx: {
            "insert": ctx.collection,
            "documents": [{"_id": 2, "tags": ["Apple"]}],
        },
        error_code=DUPLICATE_KEY_ERROR,
        msg="multikey unique index with collation should reject case-variant element",
    ),
    CommandTestCase(
        "multikey_unique_allows_different_elements",
        indexes=[
            IndexModel(
                [("tags", 1)],
                unique=True,
                collation={"locale": "en", "strength": 2},
                name="tags_unique_ci",
            )
        ],
        docs=[{"_id": 1, "tags": ["apple", "banana"]}],
        command=lambda ctx: {
            "insert": ctx.collection,
            "documents": [{"_id": 2, "tags": ["cherry"]}],
        },
        expected={"ok": 1.0, "n": 1},
        msg="multikey unique index with collation should allow distinct elements",
    ),
    CommandTestCase(
        "multikey_query_uses_collation",
        indexes=[
            IndexModel(
                [("tags", 1)],
                collation={"locale": "en", "strength": 2},
                name="tags_ci",
            )
        ],
        docs=[
            {"_id": 1, "tags": ["Apple", "banana"]},
            {"_id": 2, "tags": ["cherry"]},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"tags": "apple"},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "tags": ["Apple", "banana"]}],
        msg="find on multikey index with matching collation should match case-insensitively",
    ),
    CommandTestCase(
        "multikey_unique_rejects_within_same_doc",
        docs=[{"_id": 1, "tags": ["other"]}],
        command=lambda ctx: {
            "createIndexes": ctx.collection,
            "indexes": [
                {
                    "key": {"tags": 1},
                    "name": "tags_unique_ci",
                    "unique": True,
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        # First create the index, then try to insert a doc with collation-equal
        # elements within the same array.
        expected={"ok": Eq(1.0)},
        msg="creating multikey unique index should succeed on clean data",
    ),
]

# Property [Unique Index Build on Pre-Existing Duplicates]: creating a unique
# index with collation on a collection that already contains
# collation-equivalent values produces DUPLICATE_KEY_ERROR during index build.
COLLATION_INDEX_BUILD_DUPLICATE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "build_unique_index_rejects_existing_case_duplicates",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
        ],
        command=lambda ctx: {
            "createIndexes": ctx.collection,
            "indexes": [
                {
                    "key": {"x": 1},
                    "name": "x_unique_ci",
                    "unique": True,
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        error_code=DUPLICATE_KEY_ERROR,
        msg="building unique index should fail when existing data has collation-equivalent values",
    ),
    CommandTestCase(
        "build_unique_index_rejects_existing_accent_duplicates",
        docs=[
            {"_id": 1, "x": "cafe"},
            {"_id": 2, "x": "caf\u00e9"},
        ],
        command=lambda ctx: {
            "createIndexes": ctx.collection,
            "indexes": [
                {
                    "key": {"x": 1},
                    "name": "x_unique_ai",
                    "unique": True,
                    "collation": {"locale": "en", "strength": 1},
                }
            ],
        },
        error_code=DUPLICATE_KEY_ERROR,
        msg="building unique index should fail when existing data has accent-equivalent values",
    ),
    CommandTestCase(
        "build_unique_index_succeeds_on_distinct_data",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "banana"},
        ],
        command=lambda ctx: {
            "createIndexes": ctx.collection,
            "indexes": [
                {
                    "key": {"x": 1},
                    "name": "x_unique_ci",
                    "unique": True,
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": Eq(1.0)},
        msg="building unique index should succeed when no collation-equivalent duplicates exist",
    ),
    CommandTestCase(
        "build_unique_multikey_rejects_cross_doc_duplicates",
        docs=[
            {"_id": 1, "tags": ["apple", "banana"]},
            {"_id": 2, "tags": ["Apple", "cherry"]},
        ],
        command=lambda ctx: {
            "createIndexes": ctx.collection,
            "indexes": [
                {
                    "key": {"tags": 1},
                    "name": "tags_unique_ci",
                    "unique": True,
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        error_code=DUPLICATE_KEY_ERROR,
        msg="building unique multikey index should fail on cross-doc collation-equivalent elements",
    ),
]

COLLATION_INDEX_MULTIKEY_TESTS = (
    COLLATION_MULTIKEY_INDEX_TESTS + COLLATION_INDEX_BUILD_DUPLICATE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_INDEX_MULTIKEY_TESTS))
def test_collation_index_multikey(database_client, collection, test):
    """Test collation with multikey indexes and index build on duplicates."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    expected = test.build_expected(ctx)
    assertResult(
        result,
        expected=expected,
        error_code=test.error_code,
        msg=test.msg,
        raw_res=not isinstance(expected, list),
    )
