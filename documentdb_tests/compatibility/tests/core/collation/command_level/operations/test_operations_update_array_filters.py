"""Tests for collation effects on arrayFilters and positional update operators."""

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

# Property [ArrayFilters with Collation]: arrayFilters conditions use collation
# for string comparisons, enabling case-insensitive and accent-insensitive
# matching when selecting which array elements to update.
COLLATION_ARRAY_FILTERS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "arrayfilter_eq_case_insensitive",
        docs=[{"_id": 1, "items": [{"name": "Apple", "v": 1}, {"name": "banana", "v": 2}]}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$set": {"items.$[elem].v": 99}},
                    "arrayFilters": [{"elem.name": "apple"}],
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="arrayFilters with strength 2 should match case-insensitively",
    ),
    CommandTestCase(
        "arrayfilter_no_collation_binary",
        docs=[{"_id": 1, "items": [{"name": "Apple", "v": 1}, {"name": "apple", "v": 2}]}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$set": {"items.$[elem].v": 99}},
                    "arrayFilters": [{"elem.name": "apple"}],
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="arrayFilters without collation should use binary comparison",
    ),
    CommandTestCase(
        "arrayfilter_comparison_case_insensitive",
        docs=[{"_id": 1, "items": [{"name": "Apple", "v": 1}, {"name": "cherry", "v": 2}]}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$set": {"items.$[elem].v": 99}},
                    "arrayFilters": [{"elem.name": {"$gt": "banana"}}],
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="arrayFilters $gt with collation should compare case-insensitively",
    ),
    CommandTestCase(
        "arrayfilter_in_case_insensitive",
        docs=[
            {
                "_id": 1,
                "items": [
                    {"name": "Apple", "v": 1},
                    {"name": "BANANA", "v": 2},
                    {"name": "cherry", "v": 3},
                ],
            }
        ],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$set": {"items.$[elem].v": 99}},
                    "arrayFilters": [{"elem.name": {"$in": ["apple", "banana"]}}],
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="arrayFilters $in with collation should match case-insensitively",
    ),
    CommandTestCase(
        "arrayfilter_collection_default_collation",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[{"_id": 1, "items": [{"name": "Apple", "v": 1}, {"name": "banana", "v": 2}]}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$set": {"items.$[elem].v": 99}},
                    "arrayFilters": [{"elem.name": "apple"}],
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="arrayFilters should inherit collection default collation",
    ),
]

# Property [Positional $ Update with Collation]: the positional $ operator in
# an update targets the first array element matched by the query filter under
# the active collation.
COLLATION_POSITIONAL_UPDATE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "positional_update_case_insensitive",
        docs=[{"_id": 1, "tags": ["Apple", "banana", "cherry"]}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"_id": 1, "tags": "apple"},
                    "u": {"$set": {"tags.$": "REPLACED"}},
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="positional $ should target element matched under collation",
    ),
    CommandTestCase(
        "positional_update_no_collation_binary",
        docs=[{"_id": 1, "tags": ["Apple", "apple", "banana"]}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"_id": 1, "tags": "apple"},
                    "u": {"$set": {"tags.$": "REPLACED"}},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="positional $ without collation should use binary match",
    ),
]

COLLATION_UPDATE_ARRAY_FILTERS_TESTS = (
    COLLATION_ARRAY_FILTERS_TESTS + COLLATION_POSITIONAL_UPDATE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_UPDATE_ARRAY_FILTERS_TESTS))
def test_collation_update_array_filters(database_client, collection, test):
    """Test collation behavior in arrayFilters and positional update operators."""
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
