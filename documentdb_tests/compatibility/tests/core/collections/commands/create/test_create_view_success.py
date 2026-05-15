"""Tests for the create command view success behavior."""

import functools
from typing import Any

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import (
    TimeseriesCollection,
    ViewChainCollection,
    ViewCollection,
)

# Property [View Creation]: viewOn with a pipeline creates a view
# successfully under valid configurations.
CREATE_VIEW_BASIC_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="viewon_null_treated_as_omitted",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": None,
        },
        expected={"ok": 1.0},
        msg="viewOn:null is treated as omitted, creates regular collection",
    ),
    CommandTestCase(
        id="viewon_with_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$match": {"x": 1}}],
        },
        expected={"ok": 1.0},
        msg="viewOn + pipeline should create a view",
    ),
    CommandTestCase(
        id="viewon_without_pipeline_key",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
        },
        expected={"ok": 1.0},
        msg="viewOn without pipeline key should create view with empty pipeline",
    ),
    CommandTestCase(
        id="pipeline_null_with_viewon",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": None,
        },
        expected={"ok": 1.0},
        msg="pipeline:null with viewOn should create view with empty pipeline",
    ),
    CommandTestCase(
        id="null_elements_in_pipeline_stripped",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [None, {"$match": {"x": 1}}, None],
        },
        expected={"ok": 1.0},
        msg="Null elements in pipeline array should be silently stripped",
    ),
    CommandTestCase(
        id="view_on_nonexistent_source",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": "nonexistent_source",
            "pipeline": [],
        },
        expected={"ok": 1.0},
        msg="View on non-existent source collection should succeed",
    ),
    CommandTestCase(
        id="view_on_timeseries",
        target_collection=TimeseriesCollection(),
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [],
        },
        expected={"ok": 1.0},
        msg="View on timeseries collection should succeed",
    ),
    CommandTestCase(
        id="view_on_view",
        target_collection=ViewCollection(),
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [],
        },
        expected={"ok": 1.0},
        msg="View on view should succeed",
    ),
    CommandTestCase(
        id="locale_simple_matches_no_collation_for_view_on_view",
        target_collection=ViewCollection(),
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [],
            "collation": {"locale": "simple"},
        },
        expected={"ok": 1.0},
        msg="locale:'simple' collation = no collation for view-on-view matching",
    ),
]

# Property [View Incompatible Options Ignored]: capped, size, max, validator,
# validationLevel, validationAction, storageEngine, and indexOptionDefaults are
# silently ignored when viewOn is present.
CREATE_VIEW_IGNORED_OPTIONS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="capped_size_max_ignored_with_viewon",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [],
            "capped": True,
            "size": 4096,
            "max": 100,
        },
        expected={"ok": 1.0},
        msg="capped/size/max silently ignored when viewOn present",
    ),
    CommandTestCase(
        id="validator_ignored_with_viewon",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [],
            "validator": {"x": {"$exists": True}},
        },
        expected={"ok": 1.0},
        msg="validator silently ignored when viewOn present",
    ),
    CommandTestCase(
        id="validation_level_ignored_with_viewon",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [],
            "validationLevel": "strict",
        },
        expected={"ok": 1.0},
        msg="validationLevel silently ignored when viewOn present",
    ),
    CommandTestCase(
        id="validation_action_ignored_with_viewon",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [],
            "validationAction": "error",
        },
        expected={"ok": 1.0},
        msg="validationAction silently ignored when viewOn present",
    ),
    CommandTestCase(
        id="storage_engine_ignored_with_viewon",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [],
            "storageEngine": {"wiredTiger": {"configString": ""}},
        },
        expected={"ok": 1.0},
        msg="storageEngine silently ignored when viewOn present",
    ),
    CommandTestCase(
        id="index_option_defaults_ignored_with_viewon",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [],
            "indexOptionDefaults": {"storageEngine": {"wiredTiger": {"configString": ""}}},
        },
        expected={"ok": 1.0},
        msg="indexOptionDefaults silently ignored when viewOn present",
    ),
]

# Property [View Pipeline Limits and Allowed Stages]: pipelines up to the
# stage limit are accepted with permitted stage types.
CREATE_VIEW_PIPELINE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="pipeline_1000_stages",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$match": {"x": 1}}] * 1_000,
        },
        expected={"ok": 1.0},
        msg="Up to 1000 pipeline stages should be accepted",
    ),
    CommandTestCase(
        id="pipeline_1000_nulls_plus_1_valid",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [None] * 1_000 + [{"$match": {"x": 1}}],
        },
        expected={"ok": 1.0},
        msg="1000 nulls + 1 valid stage = 1 stored stage",
    ),
    CommandTestCase(
        id="collstats_stage_in_view_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$collStats": {"count": {}}}],
        },
        expected={"ok": 1.0},
        msg="$collStats stage allowed in view pipelines",
    ),
    CommandTestCase(
        id="indexstats_stage_in_view_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$indexStats": {}}],
        },
        expected={"ok": 1.0},
        msg="$indexStats stage allowed in view pipelines",
    ),
    CommandTestCase(
        id="plancachestats_stage_in_view_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$planCacheStats": {}}],
        },
        expected={"ok": 1.0},
        msg="$planCacheStats stage allowed in view pipelines",
    ),
    CommandTestCase(
        id="match_stage_in_view_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$match": {"x": 1}}],
        },
        expected={"ok": 1.0},
        msg="$match stage allowed in view pipelines",
    ),
    CommandTestCase(
        id="project_stage_in_view_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$project": {"x": 1}}],
        },
        expected={"ok": 1.0},
        msg="$project stage allowed in view pipelines",
    ),
    CommandTestCase(
        id="addfields_stage_in_view_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$addFields": {"z": 1}}],
        },
        expected={"ok": 1.0},
        msg="$addFields stage allowed in view pipelines",
    ),
    CommandTestCase(
        id="set_stage_in_view_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$set": {"z": 1}}],
        },
        expected={"ok": 1.0},
        msg="$set stage allowed in view pipelines",
    ),
    CommandTestCase(
        id="unset_stage_in_view_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$unset": "x"}],
        },
        expected={"ok": 1.0},
        msg="$unset stage allowed in view pipelines",
    ),
    CommandTestCase(
        id="group_stage_in_view_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$group": {"_id": "$x"}}],
        },
        expected={"ok": 1.0},
        msg="$group stage allowed in view pipelines",
    ),
    CommandTestCase(
        id="sort_stage_in_view_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
        },
        expected={"ok": 1.0},
        msg="$sort stage allowed in view pipelines",
    ),
    CommandTestCase(
        id="limit_stage_in_view_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$limit": 10}],
        },
        expected={"ok": 1.0},
        msg="$limit stage allowed in view pipelines",
    ),
    CommandTestCase(
        id="skip_stage_in_view_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$skip": 1}],
        },
        expected={"ok": 1.0},
        msg="$skip stage allowed in view pipelines",
    ),
    CommandTestCase(
        id="count_stage_in_view_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$count": "total"}],
        },
        expected={"ok": 1.0},
        msg="$count stage allowed in view pipelines",
    ),
    CommandTestCase(
        id="unwind_stage_in_view_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$unwind": "$x"}],
        },
        expected={"ok": 1.0},
        msg="$unwind stage allowed in view pipelines",
    ),
    CommandTestCase(
        id="lookup_stage_in_view_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [
                {
                    "$lookup": {
                        "from": ctx.collection,
                        "localField": "x",
                        "foreignField": "x",
                        "as": "joined",
                    }
                }
            ],
        },
        expected={"ok": 1.0},
        msg="$lookup stage allowed in view pipelines",
    ),
    CommandTestCase(
        id="graphlookup_stage_in_view_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [
                {
                    "$graphLookup": {
                        "from": ctx.collection,
                        "startWith": "$x",
                        "connectFromField": "x",
                        "connectToField": "y",
                        "as": "graph",
                    }
                }
            ],
        },
        expected={"ok": 1.0},
        msg="$graphLookup stage allowed in view pipelines",
    ),
    CommandTestCase(
        id="replaceroot_stage_in_view_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$replaceRoot": {"newRoot": {"a": "$x"}}}],
        },
        expected={"ok": 1.0},
        msg="$replaceRoot stage allowed in view pipelines",
    ),
    CommandTestCase(
        id="replacewith_stage_in_view_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$replaceWith": {"a": "$x"}}],
        },
        expected={"ok": 1.0},
        msg="$replaceWith stage allowed in view pipelines",
    ),
    CommandTestCase(
        id="bucket_stage_in_view_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$bucket": {"groupBy": "$x", "boundaries": [0, 5, 10]}}],
        },
        expected={"ok": 1.0},
        msg="$bucket stage allowed in view pipelines",
    ),
    CommandTestCase(
        id="bucketauto_stage_in_view_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$bucketAuto": {"groupBy": "$x", "buckets": 2}}],
        },
        expected={"ok": 1.0},
        msg="$bucketAuto stage allowed in view pipelines",
    ),
    CommandTestCase(
        id="sortbycount_stage_in_view_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$sortByCount": "$x"}],
        },
        expected={"ok": 1.0},
        msg="$sortByCount stage allowed in view pipelines",
    ),
    CommandTestCase(
        id="facet_stage_in_view_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$facet": {"a": [{"$match": {"x": 1}}]}}],
        },
        expected={"ok": 1.0},
        msg="$facet stage allowed in view pipelines",
    ),
    CommandTestCase(
        id="redact_stage_in_view_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$redact": "$$KEEP"}],
        },
        expected={"ok": 1.0},
        msg="$redact stage allowed in view pipelines",
    ),
    CommandTestCase(
        id="sample_stage_in_view_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$sample": {"size": 1}}],
        },
        expected={"ok": 1.0},
        msg="$sample stage allowed in view pipelines",
    ),
    CommandTestCase(
        id="geonear_stage_in_view_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [
                {
                    "$geoNear": {
                        "near": {"type": "Point", "coordinates": [0, 0]},
                        "distanceField": "dist",
                    }
                }
            ],
        },
        expected={"ok": 1.0},
        msg="$geoNear stage allowed in view pipelines",
    ),
    CommandTestCase(
        id="unionwith_stage_in_view_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$unionWith": {"coll": ctx.collection}}],
        },
        expected={"ok": 1.0},
        msg="$unionWith stage allowed in view pipelines",
    ),
    CommandTestCase(
        id="densify_stage_in_view_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$densify": {"field": "x", "range": {"step": 1, "bounds": "full"}}}],
        },
        expected={"ok": 1.0},
        msg="$densify stage allowed in view pipelines",
    ),
    CommandTestCase(
        id="fill_stage_in_view_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$fill": {"output": {"x": {"method": "locf"}}}}],
        },
        expected={"ok": 1.0},
        msg="$fill stage allowed in view pipelines",
    ),
    CommandTestCase(
        id="setwindowfields_stage_in_view_pipeline",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "sortBy": {"x": 1},
                        "output": {"rank": {"$rank": {}}},
                    }
                }
            ],
        },
        expected={"ok": 1.0},
        msg="$setWindowFields stage allowed in view pipelines",
    ),
    CommandTestCase(
        id="viewon_dotted_name_is_literal",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": "other.coll",
            "pipeline": [],
        },
        expected={"ok": 1.0},
        msg="viewOn with dot is treated as literal collection name, not a namespace",
    ),
    CommandTestCase(
        id="nested_sub_pipelines_at_20",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": functools.reduce(
                lambda p, i: [{"$lookup": {"from": "src", "pipeline": p, "as": f"x{i}"}}],
                range(20),
                list[dict[str, Any]]([{"$match": {"x": 1}}]),
            ),
        },
        expected={"ok": 1.0},
        msg="Exactly 20 nested sub-pipelines should succeed at boundary",
    ),
    CommandTestCase(
        id="pipeline_bson_at_limit",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [{"$match": {"x": "A" * 15_999_974}}],
        },
        expected={"ok": 1.0},
        msg="Pipeline at exactly 16,000,000 byte BSON limit should succeed",
    ),
    CommandTestCase(
        id="view_depth_at_limit",
        target_collection=ViewChainCollection(depth=19),
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [],
        },
        expected={"ok": 1.0},
        msg="View at depth 20 (the limit) should succeed",
    ),
]

CREATE_VIEW_SUCCESS_TESTS: list[CommandTestCase] = (
    CREATE_VIEW_BASIC_TESTS + CREATE_VIEW_IGNORED_OPTIONS_TESTS + CREATE_VIEW_PIPELINE_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(CREATE_VIEW_SUCCESS_TESTS))
def test_create_view_success(database_client, collection, test):
    """Test create command view success behavior."""
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
