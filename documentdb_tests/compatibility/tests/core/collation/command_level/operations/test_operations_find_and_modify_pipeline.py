"""Tests for collation with pipeline-style updates in findAndModify."""

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

# Property [FindAndModify Pipeline Update Filter Matching]: collation affects
# which document findAndModify selects when the update expression is an
# aggregation pipeline array.
COLLATION_FAM_PIPELINE_FILTER_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "fam_pipeline_case_insensitive",
        docs=[
            {"_id": 1, "x": "apple", "v": 1},
            {"_id": 2, "x": "Apple", "v": 1},
            {"_id": 3, "x": "banana", "v": 1},
        ],
        command=lambda ctx: {
            "findAndModify": ctx.collection,
            "query": {"x": "APPLE"},
            "update": [{"$set": {"v": 2}}],
            "new": True,
            "collation": {"locale": "en", "strength": 2},
        },
        expected={"_id": 1, "x": "apple", "v": 2},
        msg="findAndModify pipeline update with strength 2 should match case-insensitively",
    ),
    CommandTestCase(
        "fam_pipeline_no_collation_binary",
        docs=[
            {"_id": 1, "x": "apple", "v": 1},
            {"_id": 2, "x": "Apple", "v": 1},
        ],
        command=lambda ctx: {
            "findAndModify": ctx.collection,
            "query": {"x": "apple"},
            "update": [{"$set": {"v": 2}}],
            "new": True,
        },
        expected={"_id": 1, "x": "apple", "v": 2},
        msg="findAndModify pipeline update without collation should use binary comparison",
    ),
    CommandTestCase(
        "fam_pipeline_accent_insensitive",
        docs=[
            {"_id": 1, "x": "cafe", "v": 1},
            {"_id": 2, "x": "caf\u00e9", "v": 1},
        ],
        command=lambda ctx: {
            "findAndModify": ctx.collection,
            "query": {"x": "caf\u00e9"},
            "update": [{"$set": {"v": 2}}],
            "new": True,
            "collation": {"locale": "en", "strength": 1},
        },
        expected={"_id": 1, "x": "cafe", "v": 2},
        msg="findAndModify pipeline update with strength 1 should match accent-insensitively",
    ),
]

# Property [FindAndModify Pipeline Update Sort with Collation]: collation
# affects the sort order used to select which document to modify when using
# pipeline-style updates.
COLLATION_FAM_PIPELINE_SORT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "fam_pipeline_sort_case_insensitive",
        docs=[
            {"_id": 1, "x": "banana", "v": 1},
            {"_id": 2, "x": "Apple", "v": 1},
            {"_id": 3, "x": "cherry", "v": 1},
        ],
        command=lambda ctx: {
            "findAndModify": ctx.collection,
            "query": {},
            "sort": {"x": 1},
            "update": [{"$set": {"v": 2}}],
            "new": True,
            "collation": {"locale": "en", "strength": 2},
        },
        expected={"_id": 2, "x": "Apple", "v": 2},
        msg="findAndModify pipeline update sort should use collation ordering",
    ),
]

# Property [FindAndModify Pipeline Update Collection Default]: when no collation
# is specified, the collection's default collation is used for filter matching
# with pipeline-style updates.
COLLATION_FAM_PIPELINE_COLLECTION_DEFAULT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "fam_pipeline_collection_default_inherited",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[
            {"_id": 1, "x": "apple", "v": 1},
            {"_id": 2, "x": "Apple", "v": 1},
        ],
        command=lambda ctx: {
            "findAndModify": ctx.collection,
            "query": {"x": "APPLE"},
            "update": [{"$set": {"v": 2}}],
            "new": True,
        },
        expected={"_id": 1, "x": "apple", "v": 2},
        msg="findAndModify pipeline update should inherit collection default collation",
    ),
    CommandTestCase(
        "fam_pipeline_collection_default_overridden",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[
            {"_id": 1, "x": "apple", "v": 1},
            {"_id": 2, "x": "Apple", "v": 1},
        ],
        command=lambda ctx: {
            "findAndModify": ctx.collection,
            "query": {"x": "APPLE"},
            "update": [{"$set": {"v": 2}}],
            "new": True,
            "collation": {"locale": "en", "strength": 3},
        },
        expected=None,
        msg="findAndModify pipeline update with strength 3 should not match case variants",
    ),
]

COLLATION_FAM_PIPELINE_TESTS = (
    COLLATION_FAM_PIPELINE_FILTER_TESTS
    + COLLATION_FAM_PIPELINE_SORT_TESTS
    + COLLATION_FAM_PIPELINE_COLLECTION_DEFAULT_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_FAM_PIPELINE_TESTS))
def test_collation_find_and_modify_pipeline(database_client, collection, test):
    """Test collation with pipeline-style updates in findAndModify."""
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
