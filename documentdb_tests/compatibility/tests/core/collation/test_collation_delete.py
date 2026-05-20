"""Tests for collation behavior in the delete command."""

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

# Property [Delete Filter Matching]: collation affects which documents the
# delete filter selects, enabling case-insensitive and accent-insensitive
# matching for the query portion of the delete.
COLLATION_DELETE_FILTER_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "deleteone_case_insensitive",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [
                {"q": {"x": "apple"}, "limit": 1, "collation": {"locale": "en", "strength": 2}}
            ],
        },
        expected={"ok": 1.0, "n": 1},
        msg="deleteOne with strength 2 should match first case-insensitive document",
    ),
    CommandTestCase(
        "deletemany_case_insensitive",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "APPLE"},
            {"_id": 4, "x": "banana"},
        ],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [
                {"q": {"x": "apple"}, "limit": 0, "collation": {"locale": "en", "strength": 2}}
            ],
        },
        expected={"ok": 1.0, "n": 3},
        msg="deleteMany with strength 2 should match all case variants",
    ),
    CommandTestCase(
        "delete_accent_insensitive",
        docs=[
            {"_id": 1, "x": "cafe"},
            {"_id": 2, "x": "caf\u00e9"},
            {"_id": 3, "x": "other"},
        ],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [
                {"q": {"x": "cafe"}, "limit": 0, "collation": {"locale": "en", "strength": 1}}
            ],
        },
        expected={"ok": 1.0, "n": 2},
        msg="delete with strength 1 should match accent variants",
    ),
    CommandTestCase(
        "delete_no_collation_binary",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "APPLE"},
        ],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"x": "apple"}, "limit": 0}],
        },
        expected={"ok": 1.0, "n": 1},
        msg="delete without collation should use binary comparison",
    ),
    CommandTestCase(
        "delete_gt_filter",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
            {"_id": 4, "x": "Banana"},
        ],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [
                {
                    "q": {"x": {"$gt": "apple"}},
                    "limit": 0,
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": 1.0, "n": 2},
        msg="delete $gt with strength 2 should compare case-insensitively",
    ),
    CommandTestCase(
        "delete_in_operator",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
            {"_id": 4, "x": "cherry"},
        ],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [
                {
                    "q": {"x": {"$in": ["apple", "cherry"]}},
                    "limit": 0,
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": 1.0, "n": 3},
        msg="delete $in with strength 2 should match case variants",
    ),
]

# Property [Delete Collation Validation]: the delete command validates the
# collation document in each delete statement.
COLLATION_DELETE_VALIDATION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "validation_non_object_collation",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"x": "a"}, "limit": 0, "collation": "en"}],
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="delete with non-object collation should produce an error",
    ),
    CommandTestCase(
        "validation_missing_locale",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"x": "a"}, "limit": 0, "collation": {"strength": 2}}],
        },
        error_code=MISSING_FIELD_ERROR,
        msg="delete with collation missing locale should produce an error",
    ),
    CommandTestCase(
        "validation_invalid_locale",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [
                {"q": {"x": "a"}, "limit": 0, "collation": {"locale": "invalid_locale_xyz"}}
            ],
        },
        error_code=BAD_VALUE_ERROR,
        msg="delete with invalid locale string should produce an error",
    ),
]

# Property [Delete Collection Default Collation]: when no collation is specified
# on the delete statement, the collection's default collation is used for
# filter matching.
COLLATION_DELETE_COLLECTION_DEFAULT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collection_default_inherited",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"x": "apple"}, "limit": 0}],
        },
        expected={"ok": 1.0, "n": 2},
        msg="delete should inherit collection default collation",
    ),
    CommandTestCase(
        "collection_default_overridden",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [
                {
                    "q": {"x": "apple"},
                    "limit": 0,
                    "collation": {"locale": "en", "strength": 3},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1},
        msg="delete with explicit collation should override collection default",
    ),
]

COLLATION_DELETE_TESTS = (
    COLLATION_DELETE_FILTER_TESTS
    + COLLATION_DELETE_VALIDATION_TESTS
    + COLLATION_DELETE_COLLECTION_DEFAULT_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_DELETE_TESTS))
def test_collation_delete(database_client, collection, test):
    """Test collation behavior in the delete command."""
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
