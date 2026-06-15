"""Tests for collMod view pipeline."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    CHANGE_STREAM_NOT_ALLOWED_ERROR,
    FACET_PIPELINE_INVALID_STAGE_ERROR,
    GRAPH_CONTAINS_CYCLE_ERROR,
    INVALID_NAMESPACE_ERROR,
    LOOKUP_SUB_PIPELINE_NOT_ALLOWED_ERROR,
    OPTION_NOT_SUPPORTED_ON_VIEW_ERROR,
    PIPELINE_STAGE_EXTRA_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
    UNION_WITH_SUB_PIPELINE_NOT_ALLOWED_ERROR,
    UNKNOWN_PIPELINE_STAGE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.target_collection import ViewCollection
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
)

# Property [pipeline Success]: an array pipeline is accepted as a view
# definition, null is accepted as an omitted field, null elements are silently
# dropped, a large stage count is accepted, and a range of stages valid in a
# view definition are accepted.
COLLMOD_PIPELINE_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "empty_array",
        target_collection=ViewCollection(),
        command=lambda ctx: {"collMod": ctx.collection, "pipeline": []},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept an empty pipeline array",
    ),
    CommandTestCase(
        "single_stage",
        target_collection=ViewCollection(),
        command=lambda ctx: {"collMod": ctx.collection, "pipeline": [{"$match": {"a": 1}}]},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a pipeline with a single valid object stage",
    ),
    CommandTestCase(
        "pipeline_null",
        target_collection=ViewCollection(),
        command=lambda ctx: {"collMod": ctx.collection, "pipeline": None},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a null pipeline as an omitted field",
    ),
    CommandTestCase(
        "single_null_element",
        target_collection=ViewCollection(),
        command=lambda ctx: {"collMod": ctx.collection, "pipeline": [None]},
        expected={"ok": Eq(1.0)},
        msg="collMod should silently drop a lone null pipeline element",
    ),
    CommandTestCase(
        "stage_then_null_element",
        target_collection=ViewCollection(),
        command=lambda ctx: {
            "collMod": ctx.collection,
            "pipeline": [{"$match": {"a": 1}}, None],
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should silently drop a trailing null pipeline element while keeping the stage",
    ),
    CommandTestCase(
        "many_stages",
        target_collection=ViewCollection(),
        # The server caps a view pipeline's stage count below the standard 10_000
        # stress value, so 1000 stages is the largest count shown to be accepted.
        command=lambda ctx: {"collMod": ctx.collection, "pipeline": [{"$match": {"a": 1}}] * 1000},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a pipeline with 1000 stages",
    ),
    CommandTestCase(
        "coll_stats_stage",
        target_collection=ViewCollection(),
        command=lambda ctx: {
            "collMod": ctx.collection,
            "pipeline": [{"$collStats": {"storageStats": {}}}],
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a $collStats stage in a view definition",
    ),
    CommandTestCase(
        "index_stats_stage",
        target_collection=ViewCollection(),
        command=lambda ctx: {"collMod": ctx.collection, "pipeline": [{"$indexStats": {}}]},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept an $indexStats stage in a view definition",
    ),
    CommandTestCase(
        "sample_stage",
        target_collection=ViewCollection(),
        command=lambda ctx: {"collMod": ctx.collection, "pipeline": [{"$sample": {"size": 1}}]},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a $sample stage in a view definition",
    ),
    CommandTestCase(
        "lookup_stage",
        target_collection=ViewCollection(),
        command=lambda ctx: {
            "collMod": ctx.collection,
            "pipeline": [
                {
                    "$lookup": {
                        "from": "other",
                        "localField": "a",
                        "foreignField": "a",
                        "as": "r",
                    }
                }
            ],
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a $lookup stage in a view definition",
    ),
    CommandTestCase(
        "graph_lookup_stage",
        target_collection=ViewCollection(),
        command=lambda ctx: {
            "collMod": ctx.collection,
            "pipeline": [
                {
                    "$graphLookup": {
                        "from": "other",
                        "startWith": "$a",
                        "connectFromField": "a",
                        "connectToField": "a",
                        "as": "r",
                    }
                }
            ],
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a $graphLookup stage in a view definition",
    ),
    CommandTestCase(
        "facet_stage",
        target_collection=ViewCollection(),
        command=lambda ctx: {
            "collMod": ctx.collection,
            "pipeline": [{"$facet": {"f": [{"$match": {"a": 1}}]}}],
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a $facet stage in a view definition",
    ),
    CommandTestCase(
        "union_with_stage",
        target_collection=ViewCollection(),
        command=lambda ctx: {"collMod": ctx.collection, "pipeline": [{"$unionWith": "other"}]},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a $unionWith stage in a view definition",
    ),
]

# Property [pipeline Type Rejection]: any non-array value for pipeline produces
# a TypeMismatch error.
COLLMOD_PIPELINE_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"pipeline_type_{tid}",
        target_collection=ViewCollection(),
        command=lambda ctx, v=val: {"collMod": ctx.collection, "pipeline": v},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"collMod should reject a {tid} pipeline as a non-array",
    )
    for tid, val in [
        ("string", "x"),
        ("int32", 42),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool_true", True),
        ("bool_false", False),
        ("object", {"a": 1}),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [pipeline Element Type Rejection]: any non-object, non-null array
# element produces a TypeMismatch error.
COLLMOD_PIPELINE_ELEMENT_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "element_string",
        target_collection=ViewCollection(),
        command=lambda ctx: {"collMod": ctx.collection, "pipeline": ["x"]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="collMod should reject a non-object pipeline element",
    ),
    CommandTestCase(
        "element_null_then_string",
        target_collection=ViewCollection(),
        command=lambda ctx: {"collMod": ctx.collection, "pipeline": [None, "x"]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="collMod should reject a non-object element after a dropped null element",
    ),
]

# Property [pipeline Stage Shape Rejection]: a stage object that does not contain
# exactly one field produces a stage-shape error.
COLLMOD_PIPELINE_STAGE_SHAPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "empty_stage",
        target_collection=ViewCollection(),
        command=lambda ctx: {"collMod": ctx.collection, "pipeline": [{}]},
        error_code=PIPELINE_STAGE_EXTRA_FIELD_ERROR,
        msg="collMod should reject an empty stage object",
    ),
    CommandTestCase(
        "two_key_stage",
        target_collection=ViewCollection(),
        command=lambda ctx: {
            "collMod": ctx.collection,
            "pipeline": [{"$match": {}, "$limit": 1}],
        },
        error_code=PIPELINE_STAGE_EXTRA_FIELD_ERROR,
        msg="collMod should reject a stage object with two fields",
    ),
]

# Property [pipeline Unknown Stage Rejection]: a stage whose key is not a
# recognized pipeline stage name produces an unrecognized-stage error, including
# a key with no dollar prefix.
COLLMOD_PIPELINE_UNKNOWN_STAGE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unknown_stage",
        target_collection=ViewCollection(),
        command=lambda ctx: {"collMod": ctx.collection, "pipeline": [{"$nope": {}}]},
        error_code=UNKNOWN_PIPELINE_STAGE_ERROR,
        msg="collMod should reject an unknown pipeline stage name",
    ),
    CommandTestCase(
        "dollarless_stage",
        target_collection=ViewCollection(),
        command=lambda ctx: {"collMod": ctx.collection, "pipeline": [{"match": {}}]},
        error_code=UNKNOWN_PIPELINE_STAGE_ERROR,
        msg="collMod should reject a pipeline stage key with no dollar prefix",
    ),
]

# Property [pipeline Prohibited Output Stage Rejection]: a $out or $merge stage
# is prohibited in a view definition, with the error code determined by its
# nesting location.
COLLMOD_PIPELINE_OUTPUT_STAGE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "out_top_level",
        target_collection=ViewCollection(),
        command=lambda ctx: {"collMod": ctx.collection, "pipeline": [{"$out": "dest"}]},
        error_code=OPTION_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="collMod should reject a top-level $out stage in a view definition",
    ),
    CommandTestCase(
        "merge_top_level",
        target_collection=ViewCollection(),
        command=lambda ctx: {"collMod": ctx.collection, "pipeline": [{"$merge": "dest"}]},
        error_code=OPTION_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="collMod should reject a top-level $merge stage in a view definition",
    ),
    CommandTestCase(
        "out_in_lookup",
        target_collection=ViewCollection(),
        command=lambda ctx: {
            "collMod": ctx.collection,
            "pipeline": [{"$lookup": {"from": "other", "as": "r", "pipeline": [{"$out": "dest"}]}}],
        },
        error_code=LOOKUP_SUB_PIPELINE_NOT_ALLOWED_ERROR,
        msg="collMod should reject a $out stage inside a $lookup sub-pipeline",
    ),
    CommandTestCase(
        "out_in_facet",
        target_collection=ViewCollection(),
        command=lambda ctx: {
            "collMod": ctx.collection,
            "pipeline": [{"$facet": {"f": [{"$out": "dest"}]}}],
        },
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="collMod should reject a $out stage inside a $facet",
    ),
    CommandTestCase(
        "out_in_union_with",
        target_collection=ViewCollection(),
        command=lambda ctx: {
            "collMod": ctx.collection,
            "pipeline": [{"$unionWith": {"coll": "other", "pipeline": [{"$out": "dest"}]}}],
        },
        error_code=UNION_WITH_SUB_PIPELINE_NOT_ALLOWED_ERROR,
        msg="collMod should reject a $out stage inside a $unionWith sub-pipeline",
    ),
]

# Property [pipeline View-Incompatible Stage Rejection]: a $changeStream stage is
# rejected as an option not supported on a view, and $documents, $currentOp, and
# $listSessions stages are rejected as invalid namespaces in a view definition.
COLLMOD_PIPELINE_VIEW_INCOMPATIBLE_STAGE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "change_stream_stage",
        target_collection=ViewCollection(),
        command=lambda ctx: {"collMod": ctx.collection, "pipeline": [{"$changeStream": {}}]},
        error_code=OPTION_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="collMod should reject a $changeStream stage in a view definition",
        marks=(pytest.mark.replica_set,),
    ),
    CommandTestCase(
        "change_stream_stage_unavailable",
        target_collection=ViewCollection(),
        command=lambda ctx: {"collMod": ctx.collection, "pipeline": [{"$changeStream": {}}]},
        error_code=CHANGE_STREAM_NOT_ALLOWED_ERROR,
        msg="collMod should reject a $changeStream stage where change streams are unavailable",
    ),
    CommandTestCase(
        "documents_stage",
        target_collection=ViewCollection(),
        command=lambda ctx: {"collMod": ctx.collection, "pipeline": [{"$documents": []}]},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="collMod should reject a $documents stage in a view definition",
    ),
    CommandTestCase(
        "current_op_stage",
        target_collection=ViewCollection(),
        command=lambda ctx: {"collMod": ctx.collection, "pipeline": [{"$currentOp": {}}]},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="collMod should reject a $currentOp stage in a view definition",
    ),
    CommandTestCase(
        "list_sessions_stage",
        target_collection=ViewCollection(),
        command=lambda ctx: {"collMod": ctx.collection, "pipeline": [{"$listSessions": {}}]},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="collMod should reject a $listSessions stage in a view definition",
    ),
]

# Property [pipeline Self Reference Rejection]: a $lookup or $unionWith stage
# that references the view's own name produces a GraphContainsCycle error.
COLLMOD_PIPELINE_CYCLE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "lookup_self_reference",
        target_collection=ViewCollection(),
        command=lambda ctx: {
            "collMod": ctx.collection,
            "pipeline": [
                {
                    "$lookup": {
                        "from": ctx.collection,
                        "localField": "a",
                        "foreignField": "a",
                        "as": "r",
                    }
                }
            ],
        },
        error_code=GRAPH_CONTAINS_CYCLE_ERROR,
        msg="collMod should reject a $lookup self-reference as a cycle",
    ),
    CommandTestCase(
        "union_with_self_reference",
        target_collection=ViewCollection(),
        command=lambda ctx: {
            "collMod": ctx.collection,
            "pipeline": [{"$unionWith": ctx.collection}],
        },
        error_code=GRAPH_CONTAINS_CYCLE_ERROR,
        msg="collMod should reject a $unionWith self-reference as a cycle",
    ),
]

COLLMOD_PIPELINE_TESTS: list[CommandTestCase] = (
    COLLMOD_PIPELINE_SUCCESS_TESTS
    + COLLMOD_PIPELINE_TYPE_ERROR_TESTS
    + COLLMOD_PIPELINE_ELEMENT_TYPE_ERROR_TESTS
    + COLLMOD_PIPELINE_STAGE_SHAPE_ERROR_TESTS
    + COLLMOD_PIPELINE_UNKNOWN_STAGE_ERROR_TESTS
    + COLLMOD_PIPELINE_OUTPUT_STAGE_ERROR_TESTS
    + COLLMOD_PIPELINE_VIEW_INCOMPATIBLE_STAGE_ERROR_TESTS
    + COLLMOD_PIPELINE_CYCLE_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COLLMOD_PIPELINE_TESTS))
def test_collMod_pipeline(database_client, collection, test):
    """Test collMod view pipeline acceptance and rejection."""
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
