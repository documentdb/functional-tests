"""Tests for the create command view error behavior."""

import functools
from datetime import datetime, timezone
from typing import Any

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    CHANGE_STREAM_NOT_ALLOWED_ERROR,
    FACET_PIPELINE_INVALID_STAGE_ERROR,
    GRAPH_CONTAINS_CYCLE_ERROR,
    INVALID_NAMESPACE_ERROR,
    INVALID_OPTIONS_ERROR,
    LOOKUP_SUB_PIPELINE_NOT_ALLOWED_ERROR,
    MAX_NESTED_SUB_PIPELINE_ERROR,
    OPTION_NOT_SUPPORTED_ON_VIEW_ERROR,
    PIPELINE_LENGTH_LIMIT_ERROR,
    PIPELINE_STAGE_EXTRA_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
    UNION_WITH_SUB_PIPELINE_NOT_ALLOWED_ERROR,
    UNKNOWN_PIPELINE_STAGE_ERROR,
    VIEW_DEPTH_LIMIT_ERROR,
    VIEW_PIPELINE_TOO_LARGE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import (
    ViewChainCollection,
)

# Property [View Creation (Errors) - Type and Value Validation]: invalid types
# or values for viewOn and pipeline produce type or value errors.
CREATE_VIEW_TYPE_VALUE_ERROR_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            id=f"viewon_{tid}",
            command=lambda ctx, v=val: {
                "create": f"{ctx.collection}_custom",
                "viewOn": v,
                "pipeline": [],
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"Non-string viewOn ({tid}) should fail",
        )
        for tid, val in [
            ("int", 123),
            ("int64", Int64(1)),
            ("double", 3.14),
            ("decimal128", Decimal128("1")),
            ("bool", True),
            ("array", ["src"]),
            ("document", {"a": 1}),
            ("binary", Binary(b"x")),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("regex", Regex("x")),
            ("code", Code("f()")),
            ("code_with_scope", Code("f()", {"x": 1})),
            ("timestamp", Timestamp(0, 0)),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    CommandTestCase(
        id="viewon_empty_string",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": "",
            "pipeline": [],
        },
        error_code=BAD_VALUE_ERROR,
        msg="Empty string viewOn should fail",
    ),
    *[
        CommandTestCase(
            id=f"pipeline_non_array_{tid}",
            command=lambda ctx, v=val: {
                "create": f"{ctx.collection}_custom",
                "viewOn": ctx.collection,
                "pipeline": v,
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"Non-array pipeline ({tid}) should fail",
        )
        for tid, val in [
            ("string", "bad"),
            ("int", 42),
            ("int64", Int64(1)),
            ("double", 3.14),
            ("decimal128", Decimal128("1")),
            ("bool", True),
            ("document", {"$match": {"x": 1}}),
            ("binary", Binary(b"x")),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("regex", Regex("x")),
            ("code", Code("f()")),
            ("code_with_scope", Code("f()", {"x": 1})),
            ("timestamp", Timestamp(0, 0)),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    *[
        CommandTestCase(
            id=f"pipeline_element_{tid}",
            command=lambda ctx, v=val: {
                "create": f"{ctx.collection}_custom",
                "viewOn": ctx.collection,
                "pipeline": [v],
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"Non-object pipeline element ({tid}) should fail",
        )
        for tid, val in [
            ("string", "bad"),
            ("int", 42),
            ("int64", Int64(1)),
            ("double", 3.14),
            ("decimal128", Decimal128("1")),
            ("bool", True),
            ("array", [{"$match": {"x": 1}}]),
            ("binary", Binary(b"x")),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("regex", Regex("x")),
            ("code", Code("f()")),
            ("code_with_scope", Code("f()", {"x": 1})),
            ("timestamp", Timestamp(0, 0)),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    CommandTestCase(
        id="pipeline_without_viewon",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "pipeline": [{"$match": {"x": 1}}],
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="pipeline without viewOn should fail",
    ),
]

# Property [View Creation (Errors) - Disallowed Stages]: pipeline stages not
# permitted in views produce stage-specific errors.
CREATE_VIEW_DISALLOWED_STAGE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="out_in_top_level",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$out": "dest"}],
        },
        error_code=OPTION_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="$out in top-level pipeline should fail",
    ),
    CommandTestCase(
        id="merge_in_top_level",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$merge": {"into": "dest"}}],
        },
        error_code=OPTION_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="$merge in top-level pipeline should fail",
    ),
    CommandTestCase(
        id="out_in_lookup_sub_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [
                {
                    "$lookup": {
                        "from": "other",
                        "pipeline": [{"$out": "dest"}],
                        "as": "x",
                    }
                }
            ],
        },
        error_code=LOOKUP_SUB_PIPELINE_NOT_ALLOWED_ERROR,
        msg="$out in $lookup sub-pipeline should fail",
    ),
    CommandTestCase(
        id="merge_in_lookup_sub_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [
                {
                    "$lookup": {
                        "from": "other",
                        "pipeline": [{"$merge": {"into": "dest"}}],
                        "as": "x",
                    }
                }
            ],
        },
        error_code=LOOKUP_SUB_PIPELINE_NOT_ALLOWED_ERROR,
        msg="$merge in $lookup sub-pipeline should fail",
    ),
    CommandTestCase(
        id="out_in_facet_sub_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$facet": {"a": [{"$out": "dest"}]}}],
        },
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$out in $facet sub-pipeline should fail",
    ),
    CommandTestCase(
        id="merge_in_facet_sub_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$facet": {"a": [{"$merge": {"into": "dest"}}]}}],
        },
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$merge in $facet sub-pipeline should fail",
    ),
    CommandTestCase(
        id="out_in_unionwith_sub_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [
                {
                    "$unionWith": {
                        "coll": "other",
                        "pipeline": [{"$out": "dest"}],
                    }
                }
            ],
        },
        error_code=UNION_WITH_SUB_PIPELINE_NOT_ALLOWED_ERROR,
        msg="$out in $unionWith sub-pipeline should fail",
    ),
    CommandTestCase(
        id="merge_in_unionwith_sub_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [
                {
                    "$unionWith": {
                        "coll": "other",
                        "pipeline": [{"$merge": {"into": "dest"}}],
                    }
                }
            ],
        },
        error_code=UNION_WITH_SUB_PIPELINE_NOT_ALLOWED_ERROR,
        msg="$merge in $unionWith sub-pipeline should fail",
    ),
    CommandTestCase(
        id="change_stream_stage",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$changeStream": {}}],
        },
        error_code=CHANGE_STREAM_NOT_ALLOWED_ERROR,
        msg="$changeStream in view pipeline should fail",
    ),
    CommandTestCase(
        id="current_op_stage",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$currentOp": {}}],
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="$currentOp in view pipeline should fail",
    ),
    CommandTestCase(
        id="list_sessions_stage",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$listSessions": {}}],
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="$listSessions in view pipeline should fail",
    ),
    CommandTestCase(
        id="list_local_sessions_stage",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$listLocalSessions": {}}],
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="$listLocalSessions in view pipeline should fail",
    ),
    CommandTestCase(
        id="documents_stage",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$documents": [{"x": 1}]}],
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="$documents in view pipeline should fail",
    ),
    CommandTestCase(
        id="invalid_stage_name",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$badStage": {}}],
        },
        error_code=UNKNOWN_PIPELINE_STAGE_ERROR,
        msg="Invalid stage name should fail",
    ),
    CommandTestCase(
        id="empty_object_pipeline_element",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{}],
        },
        error_code=PIPELINE_STAGE_EXTRA_FIELD_ERROR,
        msg="Empty object as pipeline element should fail",
    ),
]

# Property [View Creation (Errors) - Validation Ordering]: options that are
# "ignored" for views still undergo type and enum validation before being
# discarded; invalid values produce errors even when viewOn is present.
CREATE_VIEW_VALIDATION_ORDERING_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="invalid_validation_level_with_viewon",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [],
            "validationLevel": "bogus",
        },
        error_code=BAD_VALUE_ERROR,
        msg="Invalid validationLevel enum still validated even with viewOn",
    ),
    CommandTestCase(
        id="invalid_validation_action_with_viewon",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [],
            "validationAction": "bogus",
        },
        error_code=BAD_VALUE_ERROR,
        msg="Invalid validationAction enum still validated even with viewOn",
    ),
    CommandTestCase(
        id="invalid_storage_engine_with_viewon",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [],
            "storageEngine": {"unknownEngine": {}},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Unknown storage engine still validated even with viewOn",
    ),
]

# Property [View Creation (Errors) - Structural Limits]: views exceeding
# depth, cycle, stage count, sub-pipeline, or size limits produce errors.
CREATE_VIEW_STRUCTURAL_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="view_depth_exceeds_limit",
        target_collection=ViewChainCollection(depth=20),
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [],
        },
        error_code=VIEW_DEPTH_LIMIT_ERROR,
        msg="View at depth 21 (exceeding limit of 20) should fail",
    ),
    CommandTestCase(
        id="self_referencing_view",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": f"{ctx.collection}_custom",
            "pipeline": [],
        },
        error_code=GRAPH_CONTAINS_CYCLE_ERROR,
        msg="Self-referencing view should fail",
    ),
    CommandTestCase(
        id="viewon_with_timeseries",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [],
            "timeseries": {"timeField": "ts"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="viewOn + timeseries should fail",
    ),
    CommandTestCase(
        id="viewon_with_id_index",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [],
            "idIndex": {"key": {"_id": 1}, "name": "_id_"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="viewOn + idIndex should fail",
    ),
    CommandTestCase(
        id="more_than_1000_stages",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$match": {"x": 1}}] * 1_001,
        },
        error_code=PIPELINE_LENGTH_LIMIT_ERROR,
        msg="More than 1000 stages should fail",
    ),
    CommandTestCase(
        id="nested_sub_pipelines_exceeds_20",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": functools.reduce(
                lambda p, i: [{"$lookup": {"from": "src", "pipeline": p, "as": f"x{i}"}}],
                range(21),
                list[dict[str, Any]]([{"$match": {"x": 1}}]),
            ),
        },
        error_code=MAX_NESTED_SUB_PIPELINE_ERROR,
        msg="More than 20 nested sub-pipelines should fail",
    ),
    CommandTestCase(
        id="pipeline_bson_exceeds_16mb",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$match": {"x": "A" * 16_000_000}}],
        },
        error_code=VIEW_PIPELINE_TOO_LARGE_ERROR,
        msg="Pipeline BSON > 16MB should fail",
    ),
]

CREATE_VIEW_ERROR_TESTS: list[CommandTestCase] = (
    CREATE_VIEW_TYPE_VALUE_ERROR_TESTS
    + CREATE_VIEW_DISALLOWED_STAGE_ERROR_TESTS
    + CREATE_VIEW_VALIDATION_ORDERING_ERROR_TESTS
    + CREATE_VIEW_STRUCTURAL_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(CREATE_VIEW_ERROR_TESTS))
def test_create_view_errors(database_client, collection, test):
    """Test create command view error behavior."""
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
