"""Tests for collation behavior in the findAndModify command."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    MISSING_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import CustomCollection

# Property [FindAndModify Filter Matching]: collation affects which document
# the findAndModify filter selects, enabling case-insensitive and
# accent-insensitive matching.
COLLATION_FAM_FILTER_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "update_case_insensitive_match",
        docs=[
            {"_id": 1, "x": "apple", "v": 1},
            {"_id": 2, "x": "Apple", "v": 1},
            {"_id": 3, "x": "banana", "v": 1},
        ],
        command=lambda ctx: {
            "findAndModify": ctx.collection,
            "query": {"x": "apple"},
            "update": {"$set": {"v": 2}},
            "new": True,
            "collation": {"locale": "en", "strength": 2},
        },
        expected={"_id": 1, "x": "apple", "v": 2},
        msg="findAndModify with strength 2 should match case-insensitively",
    ),
    CommandTestCase(
        "update_accent_insensitive_match",
        docs=[
            {"_id": 1, "x": "caf\u00e9", "v": 1},
            {"_id": 2, "x": "other", "v": 1},
        ],
        command=lambda ctx: {
            "findAndModify": ctx.collection,
            "query": {"x": "cafe"},
            "update": {"$set": {"v": 2}},
            "new": True,
            "collation": {"locale": "en", "strength": 1},
        },
        expected={"_id": 1, "x": "caf\u00e9", "v": 2},
        msg="findAndModify with strength 1 should match accent-insensitively",
    ),
    CommandTestCase(
        "update_no_collation_binary",
        docs=[
            {"_id": 1, "x": "apple", "v": 1},
            {"_id": 2, "x": "Apple", "v": 1},
        ],
        command=lambda ctx: {
            "findAndModify": ctx.collection,
            "query": {"x": "Apple"},
            "update": {"$set": {"v": 2}},
            "new": True,
        },
        expected={"_id": 2, "x": "Apple", "v": 2},
        msg="findAndModify without collation should use binary comparison",
    ),
    CommandTestCase(
        "remove_case_insensitive",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "findAndModify": ctx.collection,
            "query": {"x": "apple"},
            "remove": True,
            "collation": {"locale": "en", "strength": 2},
        },
        expected={"_id": 1, "x": "apple"},
        msg="findAndModify remove with collation should match case-insensitively",
    ),
]

# Property [FindAndModify Sort with Collation]: collation affects the sort
# order used to select which document to modify when multiple documents
# match the filter.
COLLATION_FAM_SORT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "sort_ascending_with_collation",
        docs=[
            {"_id": 1, "x": "banana", "v": 1},
            {"_id": 2, "x": "Apple", "v": 1},
            {"_id": 3, "x": "cherry", "v": 1},
        ],
        command=lambda ctx: {
            "findAndModify": ctx.collection,
            "query": {},
            "sort": {"x": 1},
            "update": {"$set": {"v": 2}},
            "new": True,
            "collation": {"locale": "en", "strength": 2},
        },
        expected={"_id": 2, "x": "Apple", "v": 2},
        msg="findAndModify sort should use collation ordering to pick first document",
    ),
    CommandTestCase(
        "sort_numeric_ordering",
        docs=[
            {"_id": 1, "x": "file10", "v": 1},
            {"_id": 2, "x": "file2", "v": 1},
            {"_id": 3, "x": "file1", "v": 1},
        ],
        command=lambda ctx: {
            "findAndModify": ctx.collection,
            "query": {},
            "sort": {"x": 1},
            "update": {"$set": {"v": 2}},
            "new": True,
            "collation": {"locale": "en", "numericOrdering": True},
        },
        expected={"_id": 3, "x": "file1", "v": 2},
        msg="findAndModify sort with numericOrdering should pick numerically first",
    ),
    CommandTestCase(
        "sort_descending_with_collation",
        docs=[
            {"_id": 1, "x": "apple", "v": 1},
            {"_id": 2, "x": "banana", "v": 1},
            {"_id": 3, "x": "cherry", "v": 1},
        ],
        command=lambda ctx: {
            "findAndModify": ctx.collection,
            "query": {},
            "sort": {"x": -1},
            "update": {"$set": {"v": 2}},
            "new": True,
            "collation": {"locale": "en", "strength": 2},
        },
        expected={"_id": 3, "x": "cherry", "v": 2},
        msg="findAndModify sort descending with collation should pick last in collation order",
    ),
]

# Property [FindAndModify Upsert with Collation]: collation affects the filter
# matching for upsert operations in findAndModify.
COLLATION_FAM_UPSERT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "upsert_match_found_case_insensitive",
        docs=[
            {"_id": 1, "x": "Apple", "v": 1},
        ],
        command=lambda ctx: {
            "findAndModify": ctx.collection,
            "query": {"x": "apple"},
            "update": {"$set": {"v": 2}},
            "upsert": True,
            "new": True,
            "collation": {"locale": "en", "strength": 2},
        },
        expected={"_id": 1, "x": "Apple", "v": 2},
        msg="findAndModify upsert with collation should find existing case-variant",
    ),
    CommandTestCase(
        "upsert_no_match_inserts",
        docs=[
            {"_id": 1, "x": "banana", "v": 1},
        ],
        command=lambda ctx: {
            "findAndModify": ctx.collection,
            "query": {"_id": 99, "x": "apple"},
            "update": {"$set": {"v": 2}},
            "upsert": True,
            "new": True,
            "collation": {"locale": "en", "strength": 2},
        },
        expected={"_id": 99, "x": "apple", "v": 2},
        msg="findAndModify upsert with collation should insert when no match found",
    ),
]

# Property [FindAndModify Collation Validation]: the findAndModify command
# validates the collation document.
COLLATION_FAM_VALIDATION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "validation_non_object_collation",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "findAndModify": ctx.collection,
            "query": {"x": "a"},
            "update": {"$set": {"v": 1}},
            "collation": "en",
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="findAndModify with non-object collation should produce an error",
    ),
    CommandTestCase(
        "validation_missing_locale",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "findAndModify": ctx.collection,
            "query": {"x": "a"},
            "update": {"$set": {"v": 1}},
            "collation": {"strength": 2},
        },
        error_code=MISSING_FIELD_ERROR,
        msg="findAndModify with collation missing locale should produce an error",
    ),
    CommandTestCase(
        "validation_invalid_locale",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "findAndModify": ctx.collection,
            "query": {"x": "a"},
            "update": {"$set": {"v": 1}},
            "collation": {"locale": "invalid_locale_xyz"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="findAndModify with invalid locale string should produce an error",
    ),
]

# Property [FindAndModify Collection Default Collation]: when no collation is
# specified on the findAndModify command, the collection's default collation
# is used for filter matching and sort.
COLLATION_FAM_COLLECTION_DEFAULT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collection_default_inherited",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[
            {"_id": 1, "x": "apple", "v": 1},
            {"_id": 2, "x": "Apple", "v": 1},
            {"_id": 3, "x": "banana", "v": 1},
        ],
        command=lambda ctx: {
            "findAndModify": ctx.collection,
            "query": {"x": "apple"},
            "update": {"$set": {"v": 2}},
            "new": True,
        },
        expected={"_id": 1, "x": "apple", "v": 2},
        msg="findAndModify should inherit collection default collation",
    ),
    CommandTestCase(
        "collection_default_overridden",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[
            {"_id": 1, "x": "apple", "v": 1},
            {"_id": 2, "x": "Apple", "v": 1},
            {"_id": 3, "x": "banana", "v": 1},
        ],
        command=lambda ctx: {
            "findAndModify": ctx.collection,
            "query": {"x": "apple"},
            "update": {"$set": {"v": 2}},
            "new": True,
            "collation": {"locale": "en", "strength": 3},
        },
        expected={"_id": 1, "x": "apple", "v": 2},
        msg="findAndModify with explicit collation should override collection default",
    ),
]

# Property [FindAndModify Return Old Document]: when new is false or omitted,
# findAndModify returns the document as it was before the update, but collation
# still affects which document is selected.
COLLATION_FAM_RETURN_OLD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "return_old_case_insensitive",
        docs=[
            {"_id": 1, "x": "apple", "v": 1},
            {"_id": 2, "x": "Apple", "v": 1},
        ],
        command=lambda ctx: {
            "findAndModify": ctx.collection,
            "query": {"x": "APPLE"},
            "update": {"$set": {"v": 2}},
            "collation": {"locale": "en", "strength": 2},
        },
        expected={"_id": 1, "x": "apple", "v": 1},
        msg="findAndModify returning old doc should still use collation for selection",
    ),
]

COLLATION_FAM_TESTS = (
    COLLATION_FAM_FILTER_TESTS
    + COLLATION_FAM_SORT_TESTS
    + COLLATION_FAM_UPSERT_TESTS
    + COLLATION_FAM_VALIDATION_TESTS
    + COLLATION_FAM_COLLECTION_DEFAULT_TESTS
    + COLLATION_FAM_RETURN_OLD_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_FAM_TESTS))
def test_collation_find_and_modify(database_client, collection, test):
    """Test collation behavior in the findAndModify command."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    if not isinstance(result, Exception):
        result = {"cursor": {"firstBatch": [result.get("value")]}}
    assertResult(
        result,
        expected=[test.build_expected(ctx)],
        error_code=test.error_code,
        msg=test.msg,
    )
