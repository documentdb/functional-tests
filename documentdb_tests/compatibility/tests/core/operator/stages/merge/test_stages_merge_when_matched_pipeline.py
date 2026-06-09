"""Tests for $merge whenMatched pipeline behavior and validation."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.operator.stages.merge.utils.merge_common import (
    TARGET,
    MergeTestCase,
)
from documentdb_tests.framework.assertions import (
    assertResult,
    assertSuccess,
)
from documentdb_tests.framework.error_codes import (
    INVALID_OPTIONS_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import (
    execute_command,
)
from documentdb_tests.framework.parametrize import (
    pytest_params,
)
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
)

# Property [whenMatched Pipeline Validation - Non-Object Elements]: non-object
# array elements in the whenMatched pipeline produce TYPE_MISMATCH_ERROR at
# parse time.
MERGE_WHEN_MATCHED_PIPELINE_NON_OBJECT_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        f"pipeline_val_{tid}_element",
        docs=[],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": [val]}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"$merge should reject a {tid} element in the whenMatched pipeline",
    )
    for tid, val in [
        ("string", "not_an_object"),
        ("int32", 123),
        ("int64", Int64(123)),
        ("double", 1.5),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("null", None),
        ("bool", True),
        ("array", [{"$set": {"x": 1}}]),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02")),
        ("regex", Regex("abc")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [whenMatched Pipeline Behavior]: whenMatched accepts a pipeline
# array that transforms the target document using $$new for the source and
# $field/$$ROOT/$$CURRENT for the target; an empty pipeline is a no-op.
MERGE_WHEN_MATCHED_PIPELINE_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "pipeline_empty_noop",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": []}}],
        expected=[{"_id": 1, "x": 99}],
        msg="$merge empty whenMatched pipeline should leave target unchanged",
    ),
    MergeTestCase(
        "pipeline_field_ref_targets_existing",
        target_docs=[{"_id": 1, "x": 99, "y": 50}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {"$merge": {"into": TARGET, "whenMatched": [{"$set": {"got_x": "$x", "got_y": "$y"}}]}}
        ],
        expected=[{"_id": 1, "x": 99, "y": 50, "got_x": 99, "got_y": 50}],
        msg="$merge pipeline $field references should resolve against the target document",
    ),
    MergeTestCase(
        "pipeline_root_refers_to_target",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": [{"$set": {"root": "$$ROOT"}}]}}],
        expected=[{"_id": 1, "x": 99, "root": {"_id": 1, "x": 99}}],
        msg="$merge pipeline $$ROOT should refer to the existing target document",
    ),
    MergeTestCase(
        "pipeline_current_refers_to_target",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": [{"$set": {"cur": "$$CURRENT"}}]}}],
        expected=[{"_id": 1, "x": 99, "cur": {"_id": 1, "x": 99}}],
        msg="$merge pipeline $$CURRENT should refer to the existing target document",
    ),
    MergeTestCase(
        "pipeline_new_refers_to_source",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"from_a": "$$new.a", "from_b": "$$new.b"}}],
                }
            }
        ],
        expected=[{"_id": 1, "x": 99, "from_a": 10, "from_b": 20}],
        msg="$merge pipeline $$new should refer to the source document",
    ),
    MergeTestCase(
        "pipeline_new_available_with_let",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"from_new": "$$new.a", "from_var": "$$myvar"}}],
                    "let": {"myvar": "$a"},
                }
            }
        ],
        expected=[{"_id": 1, "x": 99, "from_new": 10, "from_var": 10}],
        msg="$merge pipeline $$new should be available even when let is specified",
    ),
    MergeTestCase(
        "pipeline_new_dotted_path",
        target_docs=[{"_id": 1, "y": 1}],
        docs=[{"_id": 1, "nested": {"x": 42}}],
        pipeline=[
            {"$merge": {"into": TARGET, "whenMatched": [{"$set": {"got": "$$new.nested.x"}}]}}
        ],
        expected=[{"_id": 1, "y": 1, "got": 42}],
        msg="$merge pipeline dotted paths on $$new should access nested fields",
    ),
    MergeTestCase(
        "pipeline_new_missing_subfield_omitted",
        target_docs=[{"_id": 1, "y": 1}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {"$merge": {"into": TARGET, "whenMatched": [{"$set": {"got": "$$new.nonexistent"}}]}}
        ],
        expected=[{"_id": 1, "y": 1}],
        msg="$merge pipeline missing subfield on $$new should be silently omitted",
    ),
    MergeTestCase(
        "pipeline_replace_with_new",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": [{"$replaceWith": "$$new"}]}}],
        expected=[{"_id": 1, "a": 10, "b": 20}],
        msg="$merge $replaceWith $$new should replace target with source preserving _id",
    ),
    MergeTestCase(
        "pipeline_replace_with_no_id_preserves_target_id",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$replaceWith": {"$arrayToObject": [[{"k": "z", "v": 1}]]}}],
                }
            }
        ],
        expected=[{"_id": 1, "z": 1}],
        msg="$merge $replaceWith producing doc without _id should preserve target _id",
    ),
    MergeTestCase(
        "pipeline_replace_with_same_id_succeeds",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {"$merge": {"into": TARGET, "whenMatched": [{"$replaceWith": {"_id": 1, "z": 42}}]}}
        ],
        expected=[{"_id": 1, "z": 42}],
        msg="$merge $replaceWith with same _id as target should succeed",
    ),
    MergeTestCase(
        "pipeline_addfields_stage",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {"$merge": {"into": TARGET, "whenMatched": [{"$addFields": {"added": "$$new.a"}}]}}
        ],
        expected=[{"_id": 1, "x": 99, "added": 10}],
        msg="$merge pipeline should accept $addFields stage",
    ),
    MergeTestCase(
        "pipeline_project_stage",
        target_docs=[{"_id": 1, "x": 99, "y": 50}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": [{"$project": {"x": 1}}]}}],
        expected=[{"_id": 1, "x": 99}],
        msg="$merge pipeline should accept $project stage",
    ),
    MergeTestCase(
        "pipeline_unset_stage",
        target_docs=[{"_id": 1, "x": 99, "y": 50}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": [{"$unset": "y"}]}}],
        expected=[{"_id": 1, "x": 99}],
        msg="$merge pipeline should accept $unset stage",
    ),
    MergeTestCase(
        "pipeline_replace_root_stage",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {"$merge": {"into": TARGET, "whenMatched": [{"$replaceRoot": {"newRoot": "$$new"}}]}}
        ],
        expected=[{"_id": 1, "a": 10}],
        msg="$merge pipeline should accept $replaceRoot stage",
    ),
    MergeTestCase(
        "pipeline_fill_stage",
        target_docs=[{"_id": 1, "x": 99, "y": None}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$fill": {"output": {"y": {"value": 42}}}}],
                }
            }
        ],
        expected=[{"_id": 1, "x": 99, "y": 42}],
        msg="$merge pipeline should accept $fill stage",
    ),
]

# Property [whenMatched Pipeline Invalid Stage Error]: invalid stages in the
# whenMatched pipeline produce an error at execution time, not at parse time.
MERGE_PIPELINE_INVALID_STAGE_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "pipeline_invalid_match_stage",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": [{"$match": {"a": 1}}]}}],
        error_code=INVALID_OPTIONS_ERROR,
        msg="$merge pipeline should reject $match at execution time",
    ),
    MergeTestCase(
        "pipeline_invalid_group_stage",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": [{"$group": {"_id": None}}]}}],
        error_code=INVALID_OPTIONS_ERROR,
        msg="$merge pipeline should reject $group at execution time",
    ),
    MergeTestCase(
        "pipeline_invalid_sort_stage",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": [{"$sort": {"a": 1}}]}}],
        error_code=INVALID_OPTIONS_ERROR,
        msg="$merge pipeline should reject $sort at execution time",
    ),
]

# Property [whenMatched Pipeline Modifies Non-_id on Field]: non-_id on
# fields can be modified by the whenMatched pipeline.
MERGE_PIPELINE_MODIFIES_ON_FIELD_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "pipeline_modifies_on_field",
        target_docs=[{"_id": 1, "key": "abc", "x": 99}],
        target_indexes=[IndexModel([("key", 1)], unique=True)],
        docs=[{"_id": 1, "key": "abc", "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "on": "key",
                    "whenMatched": [{"$set": {"key": "modified"}}],
                }
            }
        ],
        expected=[{"_id": 1, "key": "modified", "x": 99}],
        msg="$merge pipeline should be able to modify non-_id on fields",
    ),
]

# Property [whenMatched Pipeline Many Stages]: at least 500 stages are
# accepted in the whenMatched pipeline.
MERGE_PIPELINE_MANY_STAGES_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "pipeline_many_stages",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"counter": i}} for i in range(500)],
                }
            }
        ],
        expected=[{"_id": 1, "x": 99, "counter": 499}],
        msg="$merge should accept at least 500 stages in the whenMatched pipeline",
    ),
]

MERGE_WHEN_MATCHED_PIPELINE_CASES = (
    MERGE_WHEN_MATCHED_PIPELINE_TESTS
    + MERGE_PIPELINE_INVALID_STAGE_TESTS
    + MERGE_WHEN_MATCHED_PIPELINE_NON_OBJECT_TESTS
    + MERGE_PIPELINE_MODIFIES_ON_FIELD_TESTS
    + MERGE_PIPELINE_MANY_STAGES_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(MERGE_WHEN_MATCHED_PIPELINE_CASES))
def test_stages_merge_when_matched_pipeline(collection, test_case: MergeTestCase):
    """Test $merge whenMatched pipeline behavior and validation."""
    target = test_case.prepare(collection)
    result = execute_command(collection, test_case.build_command(collection, target))
    if test_case.error_code is None:
        result = execute_command(collection, {"find": target, "filter": {}, "sort": {"_id": 1}})
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )


# Property [whenMatched Pipeline Invalid Stage Not Parse Time]: invalid
# stages in the whenMatched pipeline are not detected at parse time; an
# empty source produces no error.
@pytest.mark.aggregate
def test_stages_merge_pipeline_invalid_stage_not_parse_time(collection):
    """Test $merge pipeline does not detect invalid stages at parse time."""
    db = collection.database
    target = f"{collection.name}_invalid_no_parse"

    # Empty source: no documents enter the $merge stage.
    db.drop_collection(collection.name)
    db.create_collection(collection.name)
    db.drop_collection(target)
    db[target].insert_many([{"_id": 1, "x": 99}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$merge": {"into": target, "whenMatched": [{"$match": {"a": 1}}]}}],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [],
        msg="$merge pipeline should not detect invalid stages at parse time with empty source",
    )
