"""Tests for collation behavior with merge and out stages."""

from __future__ import annotations

import pytest
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    DUPLICATE_KEY_ERROR,
    IMMUTABLE_FIELD_ERROR,
    MERGE_NO_MATCHING_UNIQUE_INDEX_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import SiblingCollection

# Property [Merge ID Immutable Field Error]: $merge on _id with collection
# default collation produces IMMUTABLE_FIELD_ERROR when _id values differ in
# case because the collation-aware _id index matches but the update would modify
# the immutable _id field.
COLLATION_MERGE_ID_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "merge_id_case_mismatch_immutable_error",
        docs=[{"_id": "Apple", "val": "updated"}],
        siblings=[
            SiblingCollection(
                suffix="_target",
                collation={"locale": "en", "strength": 1},
                docs=[{"_id": "apple", "val": "original"}],
            ),
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$merge": {
                        "into": ctx.collection + "_target",
                        "on": "_id",
                        "whenMatched": "merge",
                        "whenNotMatched": "insert",
                    }
                },
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        error_code=IMMUTABLE_FIELD_ERROR,
        msg="$merge on _id with case mismatch should error on immutable field",
    ),
]

# Property [Merge Index Collation Mismatch]: $merge on a non-_id field requires
# a matching unique index collation, and a command collation that conflicts with
# the target collection's default collation on its indexes produces
# MERGE_NO_MATCHING_UNIQUE_INDEX_ERROR.
COLLATION_MERGE_INDEX_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "merge_non_id_mismatched_index_collation",
        docs=[{"_id": 2, "key": "Apple", "val": "updated"}],
        siblings=[
            SiblingCollection(
                suffix="_target",
                docs=[{"_id": 1, "key": "apple", "val": "original"}],
                indexes=[IndexModel("key", unique=True, collation={"locale": "fr", "strength": 2})],
            ),
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$project": {"_id": 0, "key": 1, "val": 1}},
                {
                    "$merge": {
                        "into": ctx.collection + "_target",
                        "on": "key",
                        "whenMatched": "merge",
                        "whenNotMatched": "insert",
                    }
                },
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        error_code=MERGE_NO_MATCHING_UNIQUE_INDEX_ERROR,
        msg="$merge with mismatched index collation should error",
    ),
    CommandTestCase(
        "merge_command_collation_conflicts_with_collection_default",
        docs=[{"_id": 2, "key": "Apple", "val": "updated"}],
        siblings=[
            SiblingCollection(
                suffix="_target",
                collation={"locale": "fr", "strength": 2},
                docs=[{"_id": 1, "key": "apple", "val": "original"}],
                indexes=[IndexModel("key", unique=True)],
            ),
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$project": {"_id": 0, "key": 1, "val": 1}},
                {
                    "$merge": {
                        "into": ctx.collection + "_target",
                        "on": "key",
                        "whenMatched": "merge",
                        "whenNotMatched": "insert",
                    }
                },
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        error_code=MERGE_NO_MATCHING_UNIQUE_INDEX_ERROR,
        msg="$merge with command collation conflicting with target default should error",
    ),
]

# Property [Out Stage Collation Acceptance]: $out with a valid collation is
# accepted and stages before $out (e.g., $match, $sort) respect collation
# normally.
COLLATION_OUT_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "out_match_case_insensitive",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "apple"}}, {"$out": ctx.collection + "_out"}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[],
        msg="$out should accept valid collation and $match before it should respect collation",
    ),
    CommandTestCase(
        "out_sort_case_insensitive",
        docs=[
            {"_id": 1, "x": "cherry"},
            {"_id": 2, "x": "Banana"},
            {"_id": 3, "x": "apple"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$sort": {"x": 1}},
                {"$limit": 1},
                {"$out": ctx.collection + "_out"},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[],
        msg="$out should accept valid collation and $sort before it should respect collation",
    ),
]

# Property [Out Stage Collation Validation]: $out with an invalid collation
# still produces validation errors because collation is validated regardless of
# $out presence.
COLLATION_OUT_VALIDATION_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "out_invalid_collation_type",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$out": ctx.collection + "_out"}],
            "cursor": {},
            "collation": {"locale": "invalid_xyz"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="$out with invalid locale should still produce validation error",
    ),
]

# Property [Merge Successful Collation-Aware Matching]: $merge with a
# collation-aware unique index correctly matches documents whose keys are
# collation-equal, enabling merge, replace, keepExisting, fail, and pipeline
# whenMatched behaviors.
COLLATION_MERGE_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "merge_whenmatched_merge_case_insensitive",
        docs=[{"_id": 2, "key": "Apple", "val": "updated"}],
        siblings=[
            SiblingCollection(
                suffix="_target",
                collation={"locale": "en", "strength": 1},
                docs=[{"_id": 1, "key": "apple", "val": "original"}],
                indexes=[IndexModel("key", unique=True)],
            ),
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$project": {"_id": 0, "key": 1, "val": 1}},
                {
                    "$merge": {
                        "into": ctx.collection + "_target",
                        "on": "key",
                        "whenMatched": "merge",
                        "whenNotMatched": "insert",
                    }
                },
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[],
        msg="$merge whenMatched merge should match collation-equal keys",
    ),
    CommandTestCase(
        "merge_whenmatched_replace_case_insensitive",
        docs=[{"_id": 2, "key": "Apple", "val": "replaced"}],
        siblings=[
            SiblingCollection(
                suffix="_target",
                collation={"locale": "en", "strength": 1},
                docs=[{"_id": 1, "key": "apple", "val": "original", "extra": "gone"}],
                indexes=[IndexModel("key", unique=True)],
            ),
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$project": {"_id": 0, "key": 1, "val": 1}},
                {
                    "$merge": {
                        "into": ctx.collection + "_target",
                        "on": "key",
                        "whenMatched": "replace",
                        "whenNotMatched": "insert",
                    }
                },
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[],
        msg="$merge whenMatched replace should replace the matched document entirely",
    ),
    CommandTestCase(
        "merge_whenmatched_keepexisting_case_insensitive",
        docs=[{"_id": 2, "key": "Apple", "val": "new"}],
        siblings=[
            SiblingCollection(
                suffix="_target",
                collation={"locale": "en", "strength": 1},
                docs=[{"_id": 1, "key": "apple", "val": "original"}],
                indexes=[IndexModel("key", unique=True)],
            ),
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$project": {"_id": 0, "key": 1, "val": 1}},
                {
                    "$merge": {
                        "into": ctx.collection + "_target",
                        "on": "key",
                        "whenMatched": "keepExisting",
                        "whenNotMatched": "insert",
                    }
                },
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[],
        msg="$merge whenMatched keepExisting should not modify the existing document",
    ),
    CommandTestCase(
        "merge_whenmatched_fail_case_insensitive",
        docs=[{"_id": 2, "key": "Apple", "val": "new"}],
        siblings=[
            SiblingCollection(
                suffix="_target",
                collation={"locale": "en", "strength": 1},
                docs=[{"_id": 1, "key": "apple", "val": "original"}],
                indexes=[IndexModel("key", unique=True)],
            ),
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$project": {"_id": 0, "key": 1, "val": 1}},
                {
                    "$merge": {
                        "into": ctx.collection + "_target",
                        "on": "key",
                        "whenMatched": "fail",
                        "whenNotMatched": "insert",
                    }
                },
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        error_code=DUPLICATE_KEY_ERROR,
        msg="$merge whenMatched fail should error when collation-equal key exists",
    ),
    CommandTestCase(
        "merge_whenmatched_pipeline_case_insensitive",
        docs=[{"_id": 2, "key": "Apple", "val": "new", "count": 5}],
        siblings=[
            SiblingCollection(
                suffix="_target",
                collation={"locale": "en", "strength": 1},
                docs=[{"_id": 1, "key": "apple", "val": "original", "count": 1}],
                indexes=[IndexModel("key", unique=True)],
            ),
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$project": {"_id": 0, "key": 1, "val": 1, "count": 1}},
                {
                    "$merge": {
                        "into": ctx.collection + "_target",
                        "on": "key",
                        "whenMatched": [{"$set": {"count": {"$add": ["$count", "$$new.count"]}}}],
                        "whenNotMatched": "insert",
                    }
                },
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[],
        msg="$merge whenMatched pipeline should execute against collation-matched document",
    ),
    CommandTestCase(
        "merge_whennotmatched_discard",
        docs=[
            {"_id": 2, "key": "Apple", "val": "updated"},
            {"_id": 3, "key": "banana", "val": "new"},
        ],
        siblings=[
            SiblingCollection(
                suffix="_target",
                collation={"locale": "en", "strength": 1},
                docs=[{"_id": 1, "key": "apple", "val": "original"}],
                indexes=[IndexModel("key", unique=True)],
            ),
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$project": {"_id": 0, "key": 1, "val": 1}},
                {
                    "$merge": {
                        "into": ctx.collection + "_target",
                        "on": "key",
                        "whenMatched": "merge",
                        "whenNotMatched": "discard",
                    }
                },
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[],
        msg="$merge whenNotMatched discard should not insert non-matching documents",
    ),
]

COLLATION_AGGREGATE_MERGE_OUT_TESTS: list[CommandTestCase] = (
    COLLATION_MERGE_ID_ERROR_TESTS
    + COLLATION_MERGE_INDEX_ERROR_TESTS
    + COLLATION_MERGE_SUCCESS_TESTS
    + COLLATION_OUT_ACCEPTANCE_TESTS
    + COLLATION_OUT_VALIDATION_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_AGGREGATE_MERGE_OUT_TESTS))
def test_collation_aggregate_merge_out(database_client, collection, test):
    """Test collation effects on $merge and $out stages."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
