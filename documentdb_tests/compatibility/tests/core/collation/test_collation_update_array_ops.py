"""Tests for collation effects on array update operators ($pull, $pullAll, $addToSet)."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import CustomCollection

# Property [Pull with Collation]: $pull uses collation to determine which array
# elements match the removal condition, enabling case-insensitive and
# accent-insensitive element removal.
COLLATION_PULL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "pull_case_insensitive",
        docs=[{"_id": 1, "tags": ["Apple", "BANANA", "cherry"]}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$pull": {"tags": "apple"}},
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="$pull with strength 2 should remove case-variant element",
    ),
    CommandTestCase(
        "pull_accent_insensitive",
        docs=[{"_id": 1, "tags": ["cafe", "caf\u00e9", "tea"]}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$pull": {"tags": "cafe"}},
                    "collation": {"locale": "en", "strength": 1},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="$pull with strength 1 should remove accent-variant elements",
    ),
    CommandTestCase(
        "pull_no_collation_binary",
        docs=[{"_id": 1, "tags": ["Apple", "apple", "banana"]}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$pull": {"tags": "apple"}},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="$pull without collation should use binary comparison",
    ),
    CommandTestCase(
        "pull_condition_case_insensitive",
        docs=[{"_id": 1, "tags": ["Apple", "banana", "Cherry"]}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$pull": {"tags": {"$gte": "banana"}}},
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="$pull with comparison condition should use collation",
    ),
    CommandTestCase(
        "pull_collection_default_collation",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[{"_id": 1, "tags": ["Apple", "banana"]}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$pull": {"tags": "apple"}},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="$pull should inherit collection default collation",
    ),
]

# Property [PullAll with Collation]: $pullAll uses collation to compare each
# value in the removal list against array elements.
COLLATION_PULLALL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "pullall_case_insensitive",
        docs=[{"_id": 1, "tags": ["Apple", "BANANA", "cherry"]}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$pullAll": {"tags": ["apple", "banana"]}},
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="$pullAll with strength 2 should remove case-variant elements",
    ),
    CommandTestCase(
        "pullall_no_collation_binary",
        docs=[{"_id": 1, "tags": ["Apple", "apple", "banana"]}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$pullAll": {"tags": ["apple"]}},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="$pullAll without collation should use binary comparison",
    ),
]

# Property [AddToSet with Collation]: $addToSet uses collation to determine
# whether a value already exists in the array, preventing collation-equal
# duplicates.
COLLATION_ADDTOSET_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "addtoset_duplicate_case_insensitive",
        docs=[{"_id": 1, "tags": ["Apple"]}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$addToSet": {"tags": "apple"}},
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 0},
        msg="$addToSet with strength 2 should not add case-variant duplicate",
    ),
    CommandTestCase(
        "addtoset_new_value_case_insensitive",
        docs=[{"_id": 1, "tags": ["Apple"]}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$addToSet": {"tags": "banana"}},
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="$addToSet with collation should add genuinely new value",
    ),
    CommandTestCase(
        "addtoset_no_collation_allows_case_variant",
        docs=[{"_id": 1, "tags": ["Apple"]}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$addToSet": {"tags": "apple"}},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="$addToSet without collation should treat case variants as distinct",
    ),
    CommandTestCase(
        "addtoset_collection_default_collation",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[{"_id": 1, "tags": ["Apple"]}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$addToSet": {"tags": "apple"}},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 0},
        msg="$addToSet should inherit collection default collation for dedup",
    ),
]

COLLATION_UPDATE_ARRAY_OPS_TESTS = (
    COLLATION_PULL_TESTS + COLLATION_PULLALL_TESTS + COLLATION_ADDTOSET_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_UPDATE_ARRAY_OPS_TESTS))
def test_collation_update_array_ops(database_client, collection, test):
    """Test collation behavior in array update operators."""
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
