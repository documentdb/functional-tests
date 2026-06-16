"""Tests for collation behavior in the update command."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
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

# Property [Update Filter Matching]: collation affects which documents the
# update filter selects, enabling case-insensitive and accent-insensitive
# matching for the query portion of the update.
COLLATION_UPDATE_FILTER_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "updateone_case_insensitive",
        docs=[
            {"_id": 1, "x": "apple", "v": 1},
            {"_id": 2, "x": "Apple", "v": 1},
            {"_id": 3, "x": "banana", "v": 1},
        ],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"x": "apple"},
                    "u": {"$set": {"v": 2}},
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="updateOne with strength 2 should match first case-insensitive document",
    ),
    CommandTestCase(
        "updatemany_case_insensitive",
        docs=[
            {"_id": 1, "x": "apple", "v": 1},
            {"_id": 2, "x": "Apple", "v": 1},
            {"_id": 3, "x": "APPLE", "v": 1},
            {"_id": 4, "x": "banana", "v": 1},
        ],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"x": "apple"},
                    "u": {"$set": {"v": 2}},
                    "multi": True,
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": 1.0, "n": 3, "nModified": 3},
        msg="updateMany with strength 2 should match all case variants",
    ),
    CommandTestCase(
        "update_accent_insensitive",
        docs=[
            {"_id": 1, "x": "cafe", "v": 1},
            {"_id": 2, "x": "caf\u00e9", "v": 1},
            {"_id": 3, "x": "other", "v": 1},
        ],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"x": "cafe"},
                    "u": {"$set": {"v": 2}},
                    "multi": True,
                    "collation": {"locale": "en", "strength": 1},
                }
            ],
        },
        expected={"ok": 1.0, "n": 2, "nModified": 2},
        msg="update with strength 1 should match accent variants",
    ),
    CommandTestCase(
        "update_no_collation_binary",
        docs=[
            {"_id": 1, "x": "apple", "v": 1},
            {"_id": 2, "x": "Apple", "v": 1},
        ],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [{"q": {"x": "apple"}, "u": {"$set": {"v": 2}}, "multi": True}],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="update without collation should use binary comparison",
    ),
    CommandTestCase(
        "update_gt_filter",
        docs=[
            {"_id": 1, "x": "apple", "v": 1},
            {"_id": 2, "x": "Apple", "v": 1},
            {"_id": 3, "x": "banana", "v": 1},
            {"_id": 4, "x": "Banana", "v": 1},
        ],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"x": {"$gt": "apple"}},
                    "u": {"$set": {"v": 2}},
                    "multi": True,
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": 1.0, "n": 2, "nModified": 2},
        msg="update $gt with strength 2 should compare case-insensitively",
    ),
]

# Property [Update Upsert with Collation]: collation affects the filter
# matching for upsert operations - if no document matches under the collation,
# a new document is inserted.
COLLATION_UPDATE_UPSERT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "upsert_match_found_case_insensitive",
        docs=[
            {"_id": 1, "x": "Apple", "v": 1},
        ],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"x": "apple"},
                    "u": {"$set": {"v": 2}},
                    "upsert": True,
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="upsert with collation should find existing case-variant and update it",
    ),
    CommandTestCase(
        "upsert_no_match_inserts",
        docs=[
            {"_id": 1, "x": "banana", "v": 1},
        ],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"_id": 99, "x": "apple"},
                    "u": {"$set": {"v": 2}},
                    "upsert": True,
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 0, "upserted": [{"index": 0, "_id": 99}]},
        msg="upsert with collation should insert when no match found",
    ),
]

# Property [Update Collation Validation]: the update command validates the
# collation document in each update statement.
COLLATION_UPDATE_VALIDATION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "validation_non_object_collation",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [{"q": {"x": "a"}, "u": {"$set": {"v": 1}}, "collation": "en"}],
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="update with non-object collation should produce an error",
    ),
    CommandTestCase(
        "validation_missing_locale",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [{"q": {"x": "a"}, "u": {"$set": {"v": 1}}, "collation": {"strength": 2}}],
        },
        error_code=MISSING_FIELD_ERROR,
        msg="update with collation missing locale should produce an error",
    ),
    CommandTestCase(
        "validation_invalid_locale",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"x": "a"},
                    "u": {"$set": {"v": 1}},
                    "collation": {"locale": "invalid_locale_xyz"},
                }
            ],
        },
        error_code=BAD_VALUE_ERROR,
        msg="update with invalid locale string should produce an error",
    ),
]

# Property [Update Collection Default Collation]: when no collation is specified
# on the update statement, the collection's default collation is used for
# filter matching.
COLLATION_UPDATE_COLLECTION_DEFAULT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collection_default_inherited",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[
            {"_id": 1, "x": "apple", "v": 1},
            {"_id": 2, "x": "Apple", "v": 1},
            {"_id": 3, "x": "banana", "v": 1},
        ],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [{"q": {"x": "apple"}, "u": {"$set": {"v": 2}}, "multi": True}],
        },
        expected={"ok": 1.0, "n": 2, "nModified": 2},
        msg="update should inherit collection default collation",
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
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"x": "apple"},
                    "u": {"$set": {"v": 2}},
                    "multi": True,
                    "collation": {"locale": "en", "strength": 3},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="update with explicit collation should override collection default",
    ),
]

COLLATION_UPDATE_TESTS = (
    COLLATION_UPDATE_FILTER_TESTS
    + COLLATION_UPDATE_UPSERT_TESTS
    + COLLATION_UPDATE_VALIDATION_TESTS
    + COLLATION_UPDATE_COLLECTION_DEFAULT_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_UPDATE_TESTS))
def test_collation_update(database_client, collection, test):
    """Test collation behavior in the update command."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
