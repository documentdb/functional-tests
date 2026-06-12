"""Tests for collation effects on field update operators ($min, $max, $push+$sort)."""

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

COLLATION_UPDATE_FIELD_OPS_TESTS = (
    COLLATION_UPDATE_MIN_TESTS + COLLATION_UPDATE_MAX_TESTS + COLLATION_PUSH_SORT_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_UPDATE_FIELD_OPS_TESTS))
def test_collation_update_field_ops(database_client, collection, test):
    """Test collation behavior in $min, $max, and $push+$sort update operators."""
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
