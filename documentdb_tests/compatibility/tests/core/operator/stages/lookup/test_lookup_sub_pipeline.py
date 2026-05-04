"""Tests for $lookup sub-pipeline constraints."""

from __future__ import annotations

from typing import Any

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.lookup.utils.lookup_common import (
    FOREIGN,
    LookupTestCase,
    build_lookup_command,
    setup_lookup,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccess
from documentdb_tests.framework.error_codes import (
    CHANGE_STREAM_NOT_ALLOWED_ERROR,
    FACET_PIPELINE_INVALID_STAGE_ERROR,
    FAILED_TO_PARSE_ERROR,
    INVALID_NAMESPACE_ERROR,
    LOOKUP_SUB_PIPELINE_NOT_ALLOWED_ERROR,
    MATCH_TEXT_NOT_FIRST_STAGE_ERROR,
    MAX_NESTED_SUB_PIPELINE_ERROR,
    NOT_FIRST_STAGE_ERROR,
    PIPELINE_LENGTH_LIMIT_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Restricted Stages in Sub-Pipeline]: certain stages are
# rejected inside a $lookup sub-pipeline.
LOOKUP_RESTRICTED_STAGES_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "out_in_sub_pipeline",
        docs=[{"_id": 1}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "pipeline": [{"$out": "dest"}],
                    "as": "joined",
                }
            }
        ],
        error_code=LOOKUP_SUB_PIPELINE_NOT_ALLOWED_ERROR,
        msg="$lookup should reject $out in the sub-pipeline",
    ),
    LookupTestCase(
        "merge_in_sub_pipeline",
        docs=[{"_id": 1}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "pipeline": [{"$merge": {"into": "dest"}}],
                    "as": "joined",
                }
            }
        ],
        error_code=LOOKUP_SUB_PIPELINE_NOT_ALLOWED_ERROR,
        msg="$lookup should reject $merge in the sub-pipeline",
    ),
    LookupTestCase(
        "change_stream_in_sub_pipeline",
        docs=[{"_id": 1}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "pipeline": [{"$changeStream": {}}],
                    "as": "joined",
                }
            }
        ],
        error_code=CHANGE_STREAM_NOT_ALLOWED_ERROR,
        msg="$lookup should reject $changeStream in the sub-pipeline",
    ),
    LookupTestCase(
        "current_op_in_sub_pipeline",
        docs=[{"_id": 1}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "pipeline": [{"$currentOp": {}}],
                    "as": "joined",
                }
            }
        ],
        error_code=INVALID_NAMESPACE_ERROR,
        msg="$lookup should reject $currentOp in the sub-pipeline",
    ),
    LookupTestCase(
        "list_sessions_in_sub_pipeline",
        docs=[{"_id": 1}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "pipeline": [{"$listSessions": {}}],
                    "as": "joined",
                }
            }
        ],
        error_code=INVALID_NAMESPACE_ERROR,
        msg="$lookup should reject $listSessions in the sub-pipeline",
    ),
    LookupTestCase(
        "list_local_sessions_in_sub_pipeline",
        docs=[{"_id": 1}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "pipeline": [{"$listLocalSessions": {}}],
                    "as": "joined",
                }
            }
        ],
        error_code=INVALID_NAMESPACE_ERROR,
        msg="$lookup should reject $listLocalSessions in the sub-pipeline",
    ),
    LookupTestCase(
        "out_transitive_in_nested_lookup",
        docs=[{"_id": 1}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "pipeline": [
                        {
                            "$lookup": {
                                "from": FOREIGN,
                                "pipeline": [{"$out": "dest"}],
                                "as": "inner",
                            }
                        }
                    ],
                    "as": "joined",
                }
            }
        ],
        error_code=LOOKUP_SUB_PIPELINE_NOT_ALLOWED_ERROR,
        msg="$lookup should reject $out transitively in nested sub-pipelines",
    ),
    LookupTestCase(
        "merge_transitive_in_nested_lookup",
        docs=[{"_id": 1}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "pipeline": [
                        {
                            "$lookup": {
                                "from": FOREIGN,
                                "pipeline": [{"$merge": {"into": "dest"}}],
                                "as": "inner",
                            }
                        }
                    ],
                    "as": "joined",
                }
            }
        ],
        error_code=LOOKUP_SUB_PIPELINE_NOT_ALLOWED_ERROR,
        msg="$lookup should reject $merge transitively in nested sub-pipelines",
    ),
    LookupTestCase(
        "out_in_facet_within_sub_pipeline",
        docs=[{"_id": 1}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "pipeline": [{"$facet": {"branch": [{"$out": "dest"}]}}],
                    "as": "joined",
                }
            }
        ],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$lookup should reject $out in $facet within the sub-pipeline",
    ),
]

# Property [pipeline Parameter Validation Errors]: invalid pipeline
# values produce type mismatch or parse errors.
LOOKUP_PIPELINE_VALIDATION_ERROR_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "pipeline_int_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "pipeline": 123,
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-array pipeline (int)",
    ),
    LookupTestCase(
        "pipeline_string_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "pipeline": "abc",
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-array pipeline (string)",
    ),
    LookupTestCase(
        "pipeline_bool_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "pipeline": True,
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-array pipeline (bool)",
    ),
    LookupTestCase(
        "pipeline_null_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "pipeline": None,
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject pipeline: null",
    ),
    LookupTestCase(
        "pipeline_non_object_element_produces_type_error",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "pipeline": [123],
                    "as": "j",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup should reject non-object array elements in pipeline",
    ),
    LookupTestCase(
        "text_as_non_first_stage_in_sub_pipeline",
        docs=[{"_id": 1}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "pipeline": [
                        {"$match": {}},
                        {"$match": {"$text": {"$search": "hello"}}},
                    ],
                    "as": "j",
                }
            }
        ],
        error_code=MATCH_TEXT_NOT_FIRST_STAGE_ERROR,
        msg="$lookup should reject $text as a non-first stage in the sub-pipeline",
    ),
    LookupTestCase(
        "documents_not_first_stage_without_from",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "pipeline": [
                        {"$match": {}},
                        {"$documents": [{"x": 1}]},
                    ],
                    "as": "j",
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg=(
            "$lookup should reject $documents not as the first stage"
            " in the sub-pipeline when from is omitted"
        ),
    ),
    LookupTestCase(
        "documents_not_first_stage_with_from",
        docs=[{"_id": 1}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "pipeline": [
                        {"$match": {}},
                        {"$documents": [{"x": 1}]},
                    ],
                    "as": "j",
                }
            }
        ],
        error_code=NOT_FIRST_STAGE_ERROR,
        msg=(
            "$lookup should reject $documents not as the first stage"
            " in the sub-pipeline when from is specified"
        ),
    ),
    LookupTestCase(
        "two_documents_stages_in_sub_pipeline",
        docs=[{"_id": 1}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "pipeline": [
                        {"$documents": [{"x": 1}]},
                        {"$documents": [{"y": 2}]},
                    ],
                    "as": "j",
                }
            }
        ],
        error_code=NOT_FIRST_STAGE_ERROR,
        msg="$lookup should reject two $documents stages in the sub-pipeline",
    ),
]

LOOKUP_SUB_PIPELINE_ERROR_TESTS: list[LookupTestCase] = (
    LOOKUP_RESTRICTED_STAGES_TESTS + LOOKUP_PIPELINE_VALIDATION_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LOOKUP_SUB_PIPELINE_ERROR_TESTS))
def test_lookup_sub_pipeline_errors(collection, test_case: LookupTestCase):
    """Test $lookup sub-pipeline constraint errors."""
    with setup_lookup(collection, test_case) as foreign_name:
        command = build_lookup_command(collection, test_case, foreign_name)
        result = execute_command(collection, command)
        assertResult(
            result,
            expected=test_case.expected,
            error_code=test_case.error_code,
            msg=test_case.msg,
        )


# Property [$text in Sub-Pipeline]: $text is accepted as the first stage
# in the sub-pipeline, performing a text search against the foreign
# collection's text index.
@pytest.mark.aggregate
def test_lookup_text_in_sub_pipeline(collection):
    """Test $text as the first stage in a $lookup sub-pipeline."""
    foreign_name = f"{collection.name}_foreign"
    db = collection.database
    db.create_collection(collection.name)
    collection.insert_many([{"_id": 1, "val": "a"}])
    db.drop_collection(foreign_name)
    db.create_collection(foreign_name)
    db[foreign_name].insert_many(
        [
            {"_id": 1, "content": "hello world"},
            {"_id": 2, "content": "goodbye world"},
            {"_id": 3, "content": "hello there"},
        ]
    )
    db[foreign_name].create_index([("content", "text")])
    try:
        result = execute_command(
            collection,
            {
                "aggregate": collection.name,
                "pipeline": [
                    {
                        "$lookup": {
                            "from": foreign_name,
                            "pipeline": [
                                {"$match": {"$text": {"$search": "hello"}}},
                                {"$sort": {"_id": 1}},
                            ],
                            "as": "joined",
                        }
                    }
                ],
                "cursor": {},
            },
        )
        assertSuccess(
            result,
            expected=[
                {
                    "_id": 1,
                    "val": "a",
                    "joined": [
                        {"_id": 1, "content": "hello world"},
                        {"_id": 3, "content": "hello there"},
                    ],
                },
            ],
            msg=(
                "$lookup should accept $text as the first stage in the"
                " sub-pipeline and return matching documents"
            ),
        )
    finally:
        db.drop_collection(foreign_name)


# Property [Sub-Pipeline Nesting and Size Limits]: nested $lookup
# sub-pipelines and stage counts are bounded by server limits.
@pytest.mark.aggregate
def test_lookup_nested_20_levels(collection):
    """Test $lookup nested sub-pipelines up to 20 levels deep."""
    foreign_name = f"{collection.name}_foreign"
    db = collection.database
    db.create_collection(collection.name)
    collection.insert_one({"_id": 1})
    db.drop_collection(foreign_name)
    db.create_collection(foreign_name)
    db[foreign_name].insert_one({"_id": 1})
    try:
        # Build 20 levels of nested $lookup
        pipeline_inner: list[dict[str, Any]] = []
        for depth in range(1, 21):
            pipeline_inner = [
                {
                    "$lookup": {
                        "from": foreign_name,
                        "pipeline": pipeline_inner,
                        "as": f"level_{depth}",
                    }
                }
            ]
        # Add a $project that extracts the innermost level to verify
        # the full nesting chain is present.
        pipeline_inner.append(
            {
                "$project": {
                    "depth": {
                        "$size": "$level_20.level_19.level_18.level_17"
                        ".level_16.level_15.level_14.level_13"
                        ".level_12.level_11.level_10.level_9"
                        ".level_8.level_7.level_6.level_5"
                        ".level_4.level_3.level_2.level_1"
                    }
                }
            }
        )
        result = execute_command(
            collection,
            {
                "aggregate": collection.name,
                "pipeline": pipeline_inner,
                "cursor": {},
            },
        )
        assertSuccess(
            result,
            expected=[{"_id": 1, "depth": 1}],
            msg="$lookup should allow nested sub-pipelines up to 20 levels deep",
        )
    finally:
        db.drop_collection(foreign_name)


@pytest.mark.aggregate
def test_lookup_sub_pipeline_1000_stages(collection):
    """Test $lookup sub-pipeline with 1000 stages."""
    foreign_name = f"{collection.name}_foreign"
    db = collection.database
    db.create_collection(collection.name)
    collection.insert_one({"_id": 1})
    db.drop_collection(foreign_name)
    db.create_collection(foreign_name)
    db[foreign_name].insert_one({"_id": 1, "val": 0})
    try:
        stages: list[dict[str, Any]] = [
            {"$addFields": {"val": {"$add": ["$val", 1]}}} for _ in range(1_000)
        ]
        result = execute_command(
            collection,
            {
                "aggregate": collection.name,
                "pipeline": [
                    {
                        "$lookup": {
                            "from": foreign_name,
                            "pipeline": stages,
                            "as": "joined",
                        }
                    },
                    {"$project": {"val": {"$arrayElemAt": ["$joined.val", 0]}}},
                ],
                "cursor": {},
            },
        )
        assertSuccess(
            result,
            expected=[{"_id": 1, "val": 1_000}],
            msg="$lookup sub-pipeline should accept up to 1000 stages",
        )
    finally:
        db.drop_collection(foreign_name)


# Property [Sub-Pipeline Nesting and Size Limit Errors]: exceeding the
# maximum nesting depth or sub-pipeline length produces an error.
@pytest.mark.aggregate
def test_lookup_nested_21_levels_error(collection):
    """Test $lookup rejects 21 levels of nested sub-pipelines."""
    foreign_name = f"{collection.name}_foreign"
    db = collection.database
    db.create_collection(collection.name)
    collection.insert_one({"_id": 1})
    db.drop_collection(foreign_name)
    db.create_collection(foreign_name)
    db[foreign_name].insert_one({"_id": 1})
    try:
        pipeline_inner: list[dict[str, Any]] = []
        for depth in range(1, 22):
            pipeline_inner = [
                {
                    "$lookup": {
                        "from": foreign_name,
                        "pipeline": pipeline_inner,
                        "as": f"level_{depth}",
                    }
                }
            ]
        result = execute_command(
            collection,
            {
                "aggregate": collection.name,
                "pipeline": pipeline_inner,
                "cursor": {},
            },
        )
        assertResult(
            result,
            error_code=MAX_NESTED_SUB_PIPELINE_ERROR,
            msg="$lookup should reject 21 levels of nested sub-pipelines",
        )
    finally:
        db.drop_collection(foreign_name)


@pytest.mark.aggregate
def test_lookup_sub_pipeline_1001_stages_error(collection):
    """Test $lookup rejects a sub-pipeline with 1001 stages."""
    foreign_name = f"{collection.name}_foreign"
    db = collection.database
    db.create_collection(collection.name)
    collection.insert_one({"_id": 1})
    db.drop_collection(foreign_name)
    db.create_collection(foreign_name)
    db[foreign_name].insert_one({"_id": 1, "val": 0})
    try:
        stages: list[dict[str, Any]] = [
            {"$addFields": {"val": {"$add": ["$val", 1]}}} for _ in range(1_001)
        ]
        result = execute_command(
            collection,
            {
                "aggregate": collection.name,
                "pipeline": [
                    {
                        "$lookup": {
                            "from": foreign_name,
                            "pipeline": stages,
                            "as": "joined",
                        }
                    },
                ],
                "cursor": {},
            },
        )
        assertResult(
            result,
            error_code=PIPELINE_LENGTH_LIMIT_ERROR,
            msg="$lookup should reject a sub-pipeline with 1001 stages",
        )
    finally:
        db.drop_collection(foreign_name)
