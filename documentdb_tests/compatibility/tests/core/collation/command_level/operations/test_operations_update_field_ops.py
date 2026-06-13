"""Tests for collation effects on field update operators ($min, $max, $push+$sort, $rename)."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import CustomCollection

# Property [Update $min with Collation]: the $min update operator uses collation
# for string comparison, only replacing the field value if the new value is less
# than the current value under the active collation.
COLLATION_UPDATE_MIN_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "min_replaces_when_less_case_insensitive",
        docs=[{"_id": 1, "x": "Banana"}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$min": {"x": "apple"}},
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="$min with collation should replace when new value sorts earlier",
    ),
    CommandTestCase(
        "min_no_replace_when_greater_case_insensitive",
        docs=[{"_id": 1, "x": "Apple"}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$min": {"x": "banana"}},
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 0},
        msg="$min with collation should not replace when new value sorts later",
    ),
    CommandTestCase(
        "min_no_collation_binary",
        docs=[{"_id": 1, "x": "banana"}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$min": {"x": "Apple"}},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="$min without collation should use binary comparison (uppercase < lowercase)",
    ),
]

# Property [Update $max with Collation]: the $max update operator uses collation
# for string comparison, only replacing the field value if the new value is
# greater than the current value under the active collation.
COLLATION_UPDATE_MAX_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "max_replaces_when_greater_case_insensitive",
        docs=[{"_id": 1, "x": "Apple"}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$max": {"x": "banana"}},
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="$max with collation should replace when new value sorts later",
    ),
    CommandTestCase(
        "max_no_replace_when_less_case_insensitive",
        docs=[{"_id": 1, "x": "Banana"}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$max": {"x": "apple"}},
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 0},
        msg="$max with collation should not replace when new value sorts earlier",
    ),
    CommandTestCase(
        "max_collection_default_collation",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[{"_id": 1, "x": "Apple"}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$max": {"x": "banana"}},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="$max should inherit collection default collation",
    ),
]

# Property [Push with Sort and Collation]: $push with the $sort modifier uses
# collation for string ordering when sorting array elements.
COLLATION_PUSH_SORT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "push_sort_case_insensitive",
        docs=[{"_id": 1, "items": ["banana", "Apple"]}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$push": {"items": {"$each": ["cherry"], "$sort": 1}}},
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="$push with $sort should use collation for string ordering",
    ),
    CommandTestCase(
        "push_sort_no_collation_binary",
        docs=[{"_id": 1, "items": ["banana", "Apple"]}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$push": {"items": {"$each": ["cherry"], "$sort": 1}}},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="$push with $sort without collation should use binary ordering",
    ),
    CommandTestCase(
        "push_sort_nested_field_case_insensitive",
        docs=[{"_id": 1, "items": [{"name": "banana", "v": 1}, {"name": "Apple", "v": 2}]}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {
                        "$push": {
                            "items": {"$each": [{"name": "cherry", "v": 3}], "$sort": {"name": 1}}
                        }
                    },
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="$push with $sort on nested field should use collation",
    ),
]


# Property [Rename Filter with Collation]: collation on the update statement
# affects which documents are matched by the query filter for $rename.
COLLATION_RENAME_FILTER_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "rename_case_insensitive_filter",
        docs=[
            {"_id": 1, "name": "apple", "old_field": "v1"},
            {"_id": 2, "name": "Apple", "old_field": "v2"},
            {"_id": 3, "name": "banana", "old_field": "v3"},
        ],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"name": "apple"},
                    "u": {"$rename": {"old_field": "new_field"}},
                    "multi": True,
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": 1.0, "n": 2, "nModified": 2},
        msg="$rename with collation should match filter case-insensitively",
    ),
    CommandTestCase(
        "rename_accent_insensitive_filter",
        docs=[
            {"_id": 1, "name": "cafe", "src": 1},
            {"_id": 2, "name": "café", "src": 2},
            {"_id": 3, "name": "other", "src": 3},
        ],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"name": "cafe"},
                    "u": {"$rename": {"src": "dst"}},
                    "multi": True,
                    "collation": {"locale": "en", "strength": 1},
                }
            ],
        },
        expected={"ok": 1.0, "n": 2, "nModified": 2},
        msg="$rename with strength 1 should match accent variants in filter",
    ),
]

# Property [Rename with Collection Default Collation]: $rename inherits
# collection-level collation for filter matching when no explicit collation
# is specified on the update statement.
COLLATION_RENAME_COLLECTION_DEFAULT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "rename_inherits_collection_collation",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[
            {"_id": 1, "name": "apple", "a": 1},
            {"_id": 2, "name": "Apple", "a": 2},
        ],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"name": "apple"},
                    "u": {"$rename": {"a": "b"}},
                    "multi": True,
                }
            ],
        },
        expected={"ok": 1.0, "n": 2, "nModified": 2},
        msg="$rename should inherit collection default collation for filter",
    ),
    CommandTestCase(
        "rename_explicit_overrides_collection_collation",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[
            {"_id": 1, "name": "apple", "a": 1},
            {"_id": 2, "name": "Apple", "a": 2},
        ],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"name": "apple"},
                    "u": {"$rename": {"a": "b"}},
                    "multi": True,
                    "collation": {"locale": "en", "strength": 3},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="$rename explicit collation should override collection default",
    ),
]

COLLATION_UPDATE_FIELD_OPS_TESTS = (
    COLLATION_UPDATE_MIN_TESTS
    + COLLATION_UPDATE_MAX_TESTS
    + COLLATION_PUSH_SORT_TESTS
    + COLLATION_RENAME_FILTER_TESTS
    + COLLATION_RENAME_COLLECTION_DEFAULT_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_UPDATE_FIELD_OPS_TESTS))
def test_collation_update_field_ops(database_client, collection, test):
    """Test collation behavior in $min, $max, $push+$sort, and $rename update operators."""
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
