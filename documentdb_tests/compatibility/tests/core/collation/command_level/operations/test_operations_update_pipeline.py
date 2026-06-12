"""Tests for collation with pipeline-style updates."""

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

# Property [Pipeline Update Filter Matching]: collation affects which documents
# the filter selects when the update expression is an aggregation pipeline array,
# the same as for traditional update operators.
COLLATION_PIPELINE_UPDATE_FILTER_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "pipeline_updateone_case_insensitive",
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
                    "u": [{"$set": {"v": 2}}],
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="pipeline updateOne with strength 2 should match case-insensitively",
    ),
    CommandTestCase(
        "pipeline_updatemany_case_insensitive",
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
                    "u": [{"$set": {"v": 2}}],
                    "multi": True,
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": 1.0, "n": 3, "nModified": 3},
        msg="pipeline updateMany with strength 2 should match all case variants",
    ),
    CommandTestCase(
        "pipeline_update_no_collation_binary",
        docs=[
            {"_id": 1, "x": "apple", "v": 1},
            {"_id": 2, "x": "Apple", "v": 1},
        ],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"x": "apple"},
                    "u": [{"$set": {"v": 2}}],
                    "multi": True,
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="pipeline update without collation should use binary comparison",
    ),
    CommandTestCase(
        "pipeline_update_accent_insensitive",
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
                    "u": [{"$set": {"v": 2}}],
                    "multi": True,
                    "collation": {"locale": "en", "strength": 1},
                }
            ],
        },
        expected={"ok": 1.0, "n": 2, "nModified": 2},
        msg="pipeline update with strength 1 should match accent variants",
    ),
]

# Property [Pipeline Update Collection Default Collation]: when no collation is
# specified on a pipeline-style update, the collection's default collation is
# used for filter matching.
COLLATION_PIPELINE_UPDATE_COLLECTION_DEFAULT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "pipeline_collection_default_inherited",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[
            {"_id": 1, "x": "apple", "v": 1},
            {"_id": 2, "x": "Apple", "v": 1},
            {"_id": 3, "x": "banana", "v": 1},
        ],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [{"q": {"x": "apple"}, "u": [{"$set": {"v": 2}}], "multi": True}],
        },
        expected={"ok": 1.0, "n": 2, "nModified": 2},
        msg="pipeline update should inherit collection default collation",
    ),
    CommandTestCase(
        "pipeline_collection_default_overridden",
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
                    "u": [{"$set": {"v": 2}}],
                    "multi": True,
                    "collation": {"locale": "en", "strength": 3},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="pipeline update with explicit collation should override collection default",
    ),
]

# Property [Pipeline Update Upsert with Collation]: collation affects the
# filter matching for upsert operations using pipeline-style updates.
COLLATION_PIPELINE_UPDATE_UPSERT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "pipeline_upsert_match_found",
        docs=[{"_id": 1, "x": "Apple", "v": 1}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"x": "apple"},
                    "u": [{"$set": {"v": 2}}],
                    "upsert": True,
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="pipeline upsert with collation should find existing case-variant and update it",
    ),
    CommandTestCase(
        "pipeline_upsert_no_match_inserts",
        docs=[{"_id": 1, "x": "banana", "v": 1}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"_id": 99, "x": "apple"},
                    "u": [{"$set": {"v": 2}}],
                    "upsert": True,
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 0, "upserted": [{"index": 0, "_id": 99}]},
        msg="pipeline upsert with collation should insert when no match found",
    ),
]

COLLATION_PIPELINE_UPDATE_TESTS = (
    COLLATION_PIPELINE_UPDATE_FILTER_TESTS
    + COLLATION_PIPELINE_UPDATE_COLLECTION_DEFAULT_TESTS
    + COLLATION_PIPELINE_UPDATE_UPSERT_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_PIPELINE_UPDATE_TESTS))
def test_collation_update_pipeline(database_client, collection, test):
    """Test collation with pipeline-style updates."""
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
