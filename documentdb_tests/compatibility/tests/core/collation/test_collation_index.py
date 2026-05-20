"""Tests for collation behavior with indexes."""

from __future__ import annotations

import pytest
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    DUPLICATE_KEY_ERROR,
    MISSING_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.target_collection import CustomCollection

# Property [Index Creation with Collation]: indexes can be created with a
# collation specification that determines how string values are compared
# within the index.
COLLATION_INDEX_CREATION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "create_index_with_collation",
        docs=[],
        command=lambda ctx: {
            "createIndexes": ctx.collection,
            "indexes": [
                {
                    "key": {"x": 1},
                    "name": "x_collated",
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": Eq(1.0)},
        msg="should create an index with collation specification",
    ),
    CommandTestCase(
        "create_index_with_numeric_ordering",
        docs=[],
        command=lambda ctx: {
            "createIndexes": ctx.collection,
            "indexes": [
                {
                    "key": {"x": 1},
                    "name": "x_numeric",
                    "collation": {"locale": "en", "numericOrdering": True},
                }
            ],
        },
        expected={"ok": Eq(1.0)},
        msg="should create an index with numericOrdering collation",
    ),
    CommandTestCase(
        "create_index_invalid_collation",
        docs=[],
        command=lambda ctx: {
            "createIndexes": ctx.collection,
            "indexes": [
                {
                    "key": {"x": 1},
                    "name": "x_bad",
                    "collation": {"locale": "invalid_locale_xyz"},
                }
            ],
        },
        error_code=BAD_VALUE_ERROR,
        msg="creating index with invalid locale should produce an error",
    ),
    CommandTestCase(
        "create_index_collation_missing_locale",
        docs=[],
        command=lambda ctx: {
            "createIndexes": ctx.collection,
            "indexes": [
                {
                    "key": {"x": 1},
                    "name": "x_no_locale",
                    "collation": {"strength": 2},
                }
            ],
        },
        error_code=MISSING_FIELD_ERROR,
        msg="creating index with collation missing locale should produce an error",
    ),
]

# Property [Unique Index Enforcement Under Collation]: a unique index with
# collation enforces uniqueness based on collation comparison, so values that
# are equal under the collation cannot coexist.
COLLATION_UNIQUE_INDEX_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unique_index_rejects_case_variant",
        indexes=[
            IndexModel(
                [("x", 1)],
                unique=True,
                collation={"locale": "en", "strength": 2},
                name="x_unique_ci",
            )
        ],
        docs=[{"_id": 1, "x": "apple"}],
        command=lambda ctx: {
            "insert": ctx.collection,
            "documents": [{"_id": 2, "x": "Apple"}],
        },
        error_code=DUPLICATE_KEY_ERROR,
        msg="unique index with strength 2 should reject case-variant duplicates",
    ),
    CommandTestCase(
        "unique_index_allows_different_values",
        indexes=[
            IndexModel(
                [("x", 1)],
                unique=True,
                collation={"locale": "en", "strength": 2},
                name="x_unique_ci",
            )
        ],
        docs=[{"_id": 1, "x": "apple"}],
        command=lambda ctx: {
            "insert": ctx.collection,
            "documents": [{"_id": 2, "x": "banana"}],
        },
        expected={"ok": 1.0, "n": 1},
        msg="unique index with collation should allow distinct values",
    ),
    CommandTestCase(
        "unique_index_strength3_allows_case_variants",
        indexes=[
            IndexModel(
                [("x", 1)],
                unique=True,
                collation={"locale": "en", "strength": 3},
                name="x_unique_cs",
            )
        ],
        docs=[{"_id": 1, "x": "apple"}],
        command=lambda ctx: {
            "insert": ctx.collection,
            "documents": [{"_id": 2, "x": "Apple"}],
        },
        expected={"ok": 1.0, "n": 1},
        msg="unique index with strength 3 should allow case-different values",
    ),
    CommandTestCase(
        "unique_index_accent_insensitive_rejects",
        indexes=[
            IndexModel(
                [("x", 1)],
                unique=True,
                collation={"locale": "en", "strength": 1},
                name="x_unique_ai",
            )
        ],
        docs=[{"_id": 1, "x": "cafe"}],
        command=lambda ctx: {
            "insert": ctx.collection,
            "documents": [{"_id": 2, "x": "caf\u00e9"}],
        },
        error_code=DUPLICATE_KEY_ERROR,
        msg="unique index with strength 1 should reject accent-variant duplicates",
    ),
]

# Property [Compound Index with Collation]: collation applies to all string
# fields in a compound index.
COLLATION_COMPOUND_INDEX_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "compound_unique_rejects_combined_variant",
        indexes=[
            IndexModel(
                [("x", 1), ("y", 1)],
                unique=True,
                collation={"locale": "en", "strength": 2},
                name="xy_unique_ci",
            )
        ],
        docs=[{"_id": 1, "x": "apple", "y": "red"}],
        command=lambda ctx: {
            "insert": ctx.collection,
            "documents": [{"_id": 2, "x": "Apple", "y": "RED"}],
        },
        error_code=DUPLICATE_KEY_ERROR,
        msg="compound unique index with collation should reject case-variant combination",
    ),
    CommandTestCase(
        "compound_unique_allows_different_second_field",
        indexes=[
            IndexModel(
                [("x", 1), ("y", 1)],
                unique=True,
                collation={"locale": "en", "strength": 2},
                name="xy_unique_ci",
            )
        ],
        docs=[{"_id": 1, "x": "apple", "y": "red"}],
        command=lambda ctx: {
            "insert": ctx.collection,
            "documents": [{"_id": 2, "x": "Apple", "y": "blue"}],
        },
        expected={"ok": 1.0, "n": 1},
        msg="compound unique index should allow when second field differs under collation",
    ),
]

# Property [Collection Default Collation Inherited by Indexes]: indexes created
# on a collection with a default collation inherit that collation unless they
# specify their own.
COLLATION_INDEX_INHERITANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "index_inherits_collection_collation",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[{"_id": 1, "x": "apple"}],
        indexes=[
            IndexModel([("x", 1)], unique=True, name="x_inherited"),
        ],
        command=lambda ctx: {
            "insert": ctx.collection,
            "documents": [{"_id": 2, "x": "Apple"}],
        },
        error_code=DUPLICATE_KEY_ERROR,
        msg="index on collated collection should inherit collection collation for uniqueness",
    ),
    CommandTestCase(
        "index_overrides_collection_collation",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[{"_id": 1, "x": "apple"}],
        indexes=[
            IndexModel(
                [("x", 1)],
                unique=True,
                collation={"locale": "simple"},
                name="x_simple",
            ),
        ],
        command=lambda ctx: {
            "insert": ctx.collection,
            "documents": [{"_id": 2, "x": "Apple"}],
        },
        expected={"ok": 1.0, "n": 1},
        msg="index with explicit simple collation should override collection default",
    ),
]

COLLATION_INDEX_TESTS = (
    COLLATION_INDEX_CREATION_TESTS
    + COLLATION_UNIQUE_INDEX_TESTS
    + COLLATION_COMPOUND_INDEX_TESTS
    + COLLATION_INDEX_INHERITANCE_TESTS
)

# Property [Index Selection Based on Collation Match]: a query only uses a
# collated index if the query's collation matches the index's collation;
# otherwise the index is not selected and a collection scan is used.
COLLATION_INDEX_SELECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "matching_collation_uses_index",
        indexes=[
            IndexModel(
                [("x", 1)],
                collation={"locale": "en", "strength": 2},
                name="x_ci",
            )
        ],
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": "apple"},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
        ],
        msg="find with matching collation should return correct results using index",
    ),
    CommandTestCase(
        "mismatched_collation_still_correct",
        indexes=[
            IndexModel(
                [("x", 1)],
                collation={"locale": "en", "strength": 2},
                name="x_ci",
            )
        ],
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": "apple"},
            "collation": {"locale": "en", "strength": 3},
        },
        expected=[{"_id": 1, "x": "apple"}],
        msg="find with different collation should still return correct results via scan",
    ),
    CommandTestCase(
        "no_collation_binary_comparison",
        indexes=[
            IndexModel(
                [("x", 1)],
                collation={"locale": "en", "strength": 2},
                name="x_ci",
            )
        ],
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": "apple"},
        },
        expected=[{"_id": 1, "x": "apple"}],
        msg="find without collation should use binary comparison not the index collation",
    ),
    CommandTestCase(
        "sort_with_matching_collation",
        indexes=[
            IndexModel(
                [("x", 1)],
                collation={"locale": "en", "strength": 2},
                name="x_ci",
            )
        ],
        docs=[
            {"_id": 1, "x": "banana"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "cherry"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {},
            "sort": {"x": 1},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 2, "x": "Apple"},
            {"_id": 1, "x": "banana"},
            {"_id": 3, "x": "cherry"},
        ],
        msg="find sort with matching index collation should return correct order",
    ),
]

# Property [Sparse Index with Collation]: a sparse unique index with collation
# allows multiple documents with missing indexed field while enforcing
# collation-aware uniqueness on present values.
COLLATION_SPARSE_INDEX_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "sparse_unique_allows_multiple_missing",
        indexes=[
            IndexModel(
                [("x", 1)],
                unique=True,
                sparse=True,
                collation={"locale": "en", "strength": 2},
                name="x_sparse_unique_ci",
            )
        ],
        docs=[{"_id": 1, "y": "hello"}, {"_id": 2, "y": "world"}, {"_id": 3, "x": "apple"}],
        command=lambda ctx: {
            "insert": ctx.collection,
            "documents": [{"_id": 4, "y": "another"}],
        },
        expected={"ok": 1.0, "n": 1},
        msg="sparse unique index with collation should allow multiple docs with missing field",
    ),
    CommandTestCase(
        "sparse_unique_rejects_collation_equal",
        indexes=[
            IndexModel(
                [("x", 1)],
                unique=True,
                sparse=True,
                collation={"locale": "en", "strength": 2},
                name="x_sparse_unique_ci",
            )
        ],
        docs=[{"_id": 1, "y": "no_x"}, {"_id": 2, "x": "apple"}],
        command=lambda ctx: {
            "insert": ctx.collection,
            "documents": [{"_id": 3, "x": "Apple"}],
        },
        error_code=DUPLICATE_KEY_ERROR,
        msg="sparse unique index with collation should reject case-variant duplicates",
    ),
]

# Property [Wildcard Index with Collation]: a wildcard index can be created
# with a collation specification, and queries with matching collation produce
# correct collation-aware results.
COLLATION_WILDCARD_INDEX_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wildcard_index_creation_with_collation",
        docs=[],
        command=lambda ctx: {
            "createIndexes": ctx.collection,
            "indexes": [
                {
                    "key": {"$**": 1},
                    "name": "wildcard_collated",
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": Eq(1.0)},
        msg="should create a wildcard index with collation specification",
    ),
    CommandTestCase(
        "wildcard_index_query_with_matching_collation",
        indexes=[
            IndexModel(
                [("$**", 1)],
                collation={"locale": "en", "strength": 2},
                name="wildcard_ci",
            )
        ],
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": "apple"},
            "sort": {"_id": 1},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
        ],
        msg="wildcard index with matching collation should return case-insensitive results",
    ),
]

# Property [Hashed Index with Collation]: a hashed index can be created with a
# collation specification, and queries with matching collation produce correct
# collation-aware results.
COLLATION_HASHED_INDEX_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "hashed_index_creation_with_collation",
        docs=[],
        command=lambda ctx: {
            "createIndexes": ctx.collection,
            "indexes": [
                {
                    "key": {"x": "hashed"},
                    "name": "x_hashed_collated",
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": Eq(1.0)},
        msg="should create a hashed index with collation specification",
    ),
    CommandTestCase(
        "hashed_index_query_with_matching_collation",
        indexes=[
            IndexModel(
                [("x", "hashed")],
                collation={"locale": "en", "strength": 2},
                name="x_hashed_ci",
            )
        ],
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": "apple"},
            "sort": {"_id": 1},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
        ],
        msg="hashed index with matching collation should return case-insensitive results",
    ),
]

COLLATION_INDEX_ALL_TESTS = (
    COLLATION_INDEX_TESTS
    + COLLATION_INDEX_SELECTION_TESTS
    + COLLATION_SPARSE_INDEX_TESTS
    + COLLATION_WILDCARD_INDEX_TESTS
    + COLLATION_HASHED_INDEX_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_INDEX_ALL_TESTS))
def test_collation_index(database_client, collection, test):
    """Test collation behavior with indexes."""
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
