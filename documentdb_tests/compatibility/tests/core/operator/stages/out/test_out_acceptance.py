"""Tests for $out stage - syntax, name acceptance, and options."""

from __future__ import annotations

from datetime import datetime
from typing import Any, cast

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.out.utils.out_test_helpers import (
    OutTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    populate_collection,
)
from documentdb_tests.framework.assertions import (
    assertResult,
    assertSuccess,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Syntax Forms]: $out accepts a string (same-database output), a
# document with db/coll (cross-database output), or a document with db/coll
# and timeseries (time series collection output), and each form writes the
# pipeline results to the specified target.
OUT_SYNTAX_FORMS_TESTS: list[OutTestCase] = [
    OutTestCase(
        "string_form_same_database",
        docs=[{"_id": 1, "value": 10}, {"_id": 2, "value": 20}],
        target_coll="syntax_string_target",
        out_spec=None,
        expected_type="collection",
        expected_options={},
        msg="$out string form should write results to a collection in the same database",
    ),
    OutTestCase(
        "document_form_db_and_coll",
        docs=[{"_id": 1, "value": 10}, {"_id": 2, "value": 20}],
        target_coll="syntax_doc_target",
        out_spec={},
        expected_type="collection",
        expected_options={},
        msg="$out document form with db and coll should write results to the specified collection",
    ),
    OutTestCase(
        "document_form_with_timeseries",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "value": 10}],
        target_coll="syntax_ts_target",
        out_spec={"timeseries": {"timeField": "ts"}},
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "granularity": "seconds",
                "bucketMaxSpanSeconds": 3_600,
            }
        },
        msg="$out document form with timeseries should create a time series collection",
    ),
]

# Property [Null as Absent]: null values for timeseries and its sub-fields
# (metaField, granularity, bucketMaxSpanSeconds, bucketRoundingSeconds) are
# treated as absent, producing the same collection as if the field were omitted.
OUT_NULL_SUCCESS_TESTS: list[OutTestCase] = [
    OutTestCase(
        "null_timeseries_regular_collection",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "value": 10}],
        target_coll="target_ts_null",
        out_spec={"timeseries": None},
        expected_type="collection",
        expected_options={},
        msg="$out should treat timeseries null as absent and create a regular collection",
    ),
    OutTestCase(
        "null_meta_field_omitted",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "value": 10}],
        target_coll="target_meta_null",
        out_spec={"timeseries": {"timeField": "ts", "metaField": None}},
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "granularity": "seconds",
                "bucketMaxSpanSeconds": 3_600,
            }
        },
        msg="$out should treat metaField null as absent and omit it from timeseries options",
    ),
    OutTestCase(
        "null_granularity_defaults_to_seconds",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "value": 10}],
        target_coll="target_gran_null",
        out_spec={"timeseries": {"timeField": "ts", "granularity": None}},
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "granularity": "seconds",
                "bucketMaxSpanSeconds": 3_600,
            }
        },
        msg="$out should treat granularity null as absent and default to 'seconds'",
    ),
    OutTestCase(
        "null_bucket_params_defaults_to_granularity",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "value": 10}],
        target_coll="target_bucket_null",
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": None,
                "bucketRoundingSeconds": None,
            }
        },
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "granularity": "seconds",
                "bucketMaxSpanSeconds": 3_600,
            }
        },
        msg=(
            "$out should treat null bucketMaxSpanSeconds and bucketRoundingSeconds"
            " as absent and default to granularity-based bucketing"
        ),
    ),
]

# Property [Collection Name Acceptance]: any non-empty string of non-null
# bytes that does not match a rejection rule is accepted as a collection name.
OUT_COLLECTION_NAME_ACCEPTANCE_TESTS: list[OutTestCase] = [
    OutTestCase(
        "control_character",
        docs=[{"_id": 1}],
        target_coll="\x01",
        expected_type="collection",
        expected_options={},
        msg="$out should accept a control character as a collection name",
    ),
    OutTestCase(
        "embedded_control_character",
        docs=[{"_id": 1}],
        target_coll="test\x1fcoll",
        expected_type="collection",
        expected_options={},
        msg="$out should accept embedded control characters in a collection name",
    ),
    OutTestCase(
        "unicode_no_break_space",
        docs=[{"_id": 1}],
        target_coll="\u00a0",
        expected_type="collection",
        expected_options={},
        msg="$out should accept Unicode no-break space as a collection name",
    ),
    OutTestCase(
        "zero_width_space",
        docs=[{"_id": 1}],
        target_coll="\u200b",
        expected_type="collection",
        expected_options={},
        msg="$out should accept zero-width space as a collection name",
    ),
    OutTestCase(
        "bom_character",
        docs=[{"_id": 1}],
        target_coll="\ufeff",
        expected_type="collection",
        expected_options={},
        msg="$out should accept BOM character as a collection name",
    ),
    OutTestCase(
        "emoji",
        docs=[{"_id": 1}],
        target_coll="\U0001f389",
        expected_type="collection",
        expected_options={},
        msg="$out should accept emoji as a collection name",
    ),
    OutTestCase(
        "cjk_characters",
        docs=[{"_id": 1}],
        target_coll="\u4e2d\u6587",
        expected_type="collection",
        expected_options={},
        msg="$out should accept CJK characters as a collection name",
    ),
    OutTestCase(
        "punctuation",
        docs=[{"_id": 1}],
        target_coll="a!@#b",
        expected_type="collection",
        expected_options={},
        msg="$out should accept punctuation in a collection name",
    ),
    OutTestCase(
        "single_character",
        docs=[{"_id": 1}],
        target_coll="a",
        expected_type="collection",
        expected_options={},
        msg="$out should accept a single-character collection name",
    ),
    OutTestCase(
        "single_digit",
        docs=[{"_id": 1}],
        target_coll="1",
        expected_type="collection",
        expected_options={},
        msg="$out should accept a single-digit collection name",
    ),
    OutTestCase(
        "digits_only",
        docs=[{"_id": 1}],
        target_coll="123",
        expected_type="collection",
        expected_options={},
        msg="$out should accept a digits-only collection name",
    ),
    OutTestCase(
        "temp_prefix",
        docs=[{"_id": 1}],
        target_coll="tmp.agg_out.",
        expected_type="collection",
        expected_options={},
        msg="$out should accept the tmp.agg_out. prefix as a regular collection name",
    ),
]

OUT_ACCEPTANCE_TESTS = (
    OUT_SYNTAX_FORMS_TESTS + OUT_NULL_SUCCESS_TESTS + OUT_COLLECTION_NAME_ACCEPTANCE_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_ACCEPTANCE_TESTS))
def test_out_acceptance(collection, test_case: OutTestCase):
    """Test $out writes results and creates the correct collection type."""
    populate_collection(collection, test_case)
    out_stage = test_case.build_out_stage(collection)
    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [out_stage], "cursor": {}},
    )
    result = execute_command(
        collection,
        {"listCollections": 1, "filter": {"name": test_case.target_coll}},
    )
    raw_doc = cast(dict, result)["cursor"]["firstBatch"][0]
    expected_info: dict[str, Any] = {
        "name": test_case.target_coll,
        "type": test_case.expected_type,
        "options": test_case.expected_options,
        "info": raw_doc["info"],
    }
    if "idIndex" in raw_doc:
        expected_info["idIndex"] = raw_doc["idIndex"]
    assertSuccess(result, [expected_info], msg=test_case.msg)


# Property [Nested Pipeline Restriction - View Source]: $out from a view
# source (not in the view definition) succeeds.
OUT_VIEW_SOURCE_SUCCESS_TESTS: list[OutTestCase] = [
    OutTestCase(
        "view_source_out",
        docs=[{"_id": 1, "value": 10}],
        target_coll="view_source_out_target",
        pipeline=[{"$out": "view_source_out_target"}],
        setup=lambda c: (
            c.database.drop_collection("good_view_for_out"),
            c.database.command(
                {
                    "create": "good_view_for_out",
                    "viewOn": c.name,
                    "pipeline": [{"$match": {"_id": 1}}],
                }
            ),
        ),
        expected=[{"_id": 1, "value": 10}],
        msg="$out from a view source should write the view's results to the target collection",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_VIEW_SOURCE_SUCCESS_TESTS))
def test_out_from_view_source_succeeds(collection, test_case: OutTestCase):
    """Test $out from a view source succeeds."""
    populate_collection(collection, test_case)
    if test_case.setup:
        test_case.setup(collection)
    db = collection.database
    execute_command(
        db["good_view_for_out"],
        {
            "aggregate": "good_view_for_out",
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    result = execute_command(
        collection,
        {"find": test_case.target_coll, "filter": {}},
    )
    assertResult(result, expected=test_case.expected, msg=test_case.msg)


# Property [Aggregation Options]: standard aggregation options (collation,
# hint, maxTimeMS, allowDiskUse, bypassDocumentValidation) are accepted
# with $out pipelines.
OUT_AGGREGATION_OPTION_SUCCESS_TESTS: list[OutTestCase] = [
    OutTestCase(
        "agg_opts_collation",
        docs=[{"_id": 1, "value": 10}],
        target_coll="agg_opts_target",
        pipeline=[{"$out": "agg_opts_target"}],
        out_spec={"collation": {"locale": "en", "strength": 2}},
        msg="$out should succeed with aggregation option collation",
    ),
    OutTestCase(
        "agg_opts_hint",
        docs=[{"_id": 1, "value": 10}],
        target_coll="agg_opts_target",
        pipeline=[{"$out": "agg_opts_target"}],
        out_spec={"hint": "_id_"},
        msg="$out should succeed with aggregation option hint",
    ),
    OutTestCase(
        "agg_opts_max_time_ms",
        docs=[{"_id": 1, "value": 10}],
        target_coll="agg_opts_target",
        pipeline=[{"$out": "agg_opts_target"}],
        out_spec={"maxTimeMS": 60_000},
        msg="$out should succeed with aggregation option maxTimeMS",
    ),
    OutTestCase(
        "agg_opts_allow_disk_use",
        docs=[{"_id": 1, "value": 10}],
        target_coll="agg_opts_target",
        pipeline=[{"$out": "agg_opts_target"}],
        out_spec={"allowDiskUse": True},
        msg="$out should succeed with aggregation option allowDiskUse",
    ),
    OutTestCase(
        "agg_opts_bypass_doc_validation",
        docs=[{"_id": 1, "value": 10}],
        target_coll="agg_opts_target",
        pipeline=[{"$out": "agg_opts_target"}],
        out_spec={"bypassDocumentValidation": True},
        msg="$out should succeed with aggregation option bypassDocumentValidation",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_AGGREGATION_OPTION_SUCCESS_TESTS))
def test_out_aggregation_options(collection, test_case: OutTestCase):
    """Test $out succeeds with standard aggregation options."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
            **test_case.out_spec,
        },
    )
    assertSuccess(
        result,
        [],
        msg=test_case.msg,
    )


# Property [Read Concern Acceptance]: non-linearizable read concerns
# (majority, local, available) are accepted with $out pipelines.
OUT_READ_CONCERN_ACCEPTANCE_TESTS: list[OutTestCase] = [
    OutTestCase(
        "rc_majority",
        docs=[{"_id": 1, "value": 10}],
        target_coll="rc_majority_target",
        pipeline=[{"$out": "rc_majority_target"}],
        out_spec={"readConcern": "majority"},
        msg="$out should succeed with readConcern level 'majority'",
    ),
    OutTestCase(
        "rc_local",
        docs=[{"_id": 1, "value": 10}],
        target_coll="rc_local_target",
        pipeline=[{"$out": "rc_local_target"}],
        out_spec={"readConcern": "local"},
        msg="$out should succeed with readConcern level 'local'",
    ),
    OutTestCase(
        "rc_available",
        docs=[{"_id": 1, "value": 10}],
        target_coll="rc_available_target",
        pipeline=[{"$out": "rc_available_target"}],
        out_spec={"readConcern": "available"},
        msg="$out should succeed with readConcern level 'available'",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_READ_CONCERN_ACCEPTANCE_TESTS))
def test_out_read_concern_acceptance(collection, test_case: OutTestCase):
    """Test $out succeeds with non-linearizable read concern levels."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
            "readConcern": {"level": test_case.out_spec["readConcern"]},
        },
    )
    assertSuccess(
        result,
        [],
        msg=test_case.msg,
    )


# Property [Schema Validation Success]: when the target collection has
# validationAction set to warn the write succeeds, and
# bypassDocumentValidation bypasses schema validation errors.
OUT_SCHEMA_VALIDATION_SUCCESS_TESTS: list[OutTestCase] = [
    OutTestCase(
        "schema_val_warn",
        docs=[{"_id": 1, "value": "not_a_number"}],
        target_coll="schema_val_warn_target",
        pipeline=[{"$out": "schema_val_warn_target"}],
        out_spec={"bypassDocumentValidation": False},
        setup=lambda c: (
            c.database.drop_collection("schema_val_warn_target"),
            c.database.command(
                {
                    "create": "schema_val_warn_target",
                    "validator": {
                        "$jsonSchema": {
                            "bsonType": "object",
                            "required": ["value"],
                            "properties": {"value": {"bsonType": "int"}},
                        }
                    },
                    "validationAction": "warn",
                }
            ),
        ),
        expected=[{"_id": 1, "value": "not_a_number"}],
        msg="$out should succeed with validationAction='warn'",
    ),
    OutTestCase(
        "schema_val_bypass",
        docs=[{"_id": 1, "value": "not_a_number"}],
        target_coll="schema_val_bypass_target",
        pipeline=[{"$out": "schema_val_bypass_target"}],
        out_spec={"bypassDocumentValidation": True},
        setup=lambda c: (
            c.database.drop_collection("schema_val_bypass_target"),
            c.database.command(
                {
                    "create": "schema_val_bypass_target",
                    "validator": {
                        "$jsonSchema": {
                            "bsonType": "object",
                            "required": ["value"],
                            "properties": {"value": {"bsonType": "int"}},
                        }
                    },
                    "validationAction": "error",
                }
            ),
        ),
        expected=[{"_id": 1, "value": "not_a_number"}],
        msg="$out should succeed with bypassDocumentValidation=True",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_SCHEMA_VALIDATION_SUCCESS_TESTS))
def test_out_schema_validation_success(collection, test_case: OutTestCase):
    """Test $out succeeds when schema validation is warn or bypassed."""
    populate_collection(collection, test_case)
    if test_case.setup:
        test_case.setup(collection)
    cmd: dict[str, Any] = {
        "aggregate": collection.name,
        "pipeline": test_case.pipeline,
        "cursor": {},
    }
    if test_case.out_spec["bypassDocumentValidation"]:
        cmd["bypassDocumentValidation"] = True
    execute_command(collection, cmd)
    result = execute_command(
        collection,
        {"find": test_case.target_coll, "filter": {}, "projection": {"_id": 1, "value": 1}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)


# Property [Index Constraint Errors - Nonexistent Target]: when a unique
# index violation occurs writing to a nonexistent target, the target
# collection is not created.
OUT_INDEX_NONEXISTENT_TARGET_NOT_CREATED_TESTS: list[OutTestCase] = [
    OutTestCase(
        "idx_nonexist_not_created",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        target_coll="idx_nonexist_target",
        pipeline=[
            {"$unset": "_id"},
            {"$addFields": {"_id": "same"}},
            {"$out": "idx_nonexist_target"},
        ],
        expected=[],
        msg="$out should not create the target collection when a unique index violation occurs",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_INDEX_NONEXISTENT_TARGET_NOT_CREATED_TESTS))
def test_out_unique_violation_nonexistent_target_not_created(collection, test_case: OutTestCase):
    """Test $out does not create the target when a unique index violation occurs."""
    populate_collection(collection, test_case)
    collection.database.drop_collection(test_case.target_coll)
    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    result = execute_command(
        collection,
        {"listCollections": 1, "filter": {"name": test_case.target_coll}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
