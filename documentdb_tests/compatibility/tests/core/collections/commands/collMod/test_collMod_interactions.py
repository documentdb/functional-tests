"""Tests for collMod cross-option parameter interactions."""

from __future__ import annotations

import pytest
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    INDEX_NOT_FOUND_ERROR,
    INVALID_OPTIONS_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, NotExists
from documentdb_tests.framework.target_collection import (
    CappedCollection,
    ClusteredCollection,
    TimeseriesCollection,
    TimeseriesTTLCollection,
    ViewCollection,
)

# Property [Cross-Group Coexistence]: independent option groups that target the
# same collection type apply together in one command, and each group's effect is
# reflected in the result independently of the others.
COLLMOD_CROSS_GROUP_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "index_hidden_and_validator",
        indexes=[IndexModel([("a", 1)], name="a_1", hidden=False)],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "hidden": True},
            "validator": {"a": 1},
        },
        expected={"ok": Eq(1.0), "hidden_old": Eq(False), "hidden_new": Eq(True)},
        msg="collMod should apply an index hidden change together with a validator",
    ),
    CommandTestCase(
        "index_hidden_and_validation_level",
        indexes=[IndexModel([("a", 1)], name="a_1", hidden=False)],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "hidden": True},
            "validationLevel": "moderate",
        },
        expected={"ok": Eq(1.0), "hidden_old": Eq(False), "hidden_new": Eq(True)},
        msg="collMod should apply an index hidden change together with a validationLevel",
    ),
    CommandTestCase(
        "validator_and_change_stream_pre_and_post_images",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "validator": {"a": 1},
            "changeStreamPreAndPostImages": {"enabled": True},
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should apply a validator together with changeStreamPreAndPostImages",
    ),
    CommandTestCase(
        "validator_and_validation_level_and_action",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "validator": {"a": 1},
            "validationLevel": "strict",
            "validationAction": "error",
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should apply a validator together with validationLevel and validationAction",
    ),
]

# Property [Clustered Index And Top-Level expireAfterSeconds]: on a clustered
# collection, an index hidden change and a top-level expireAfterSeconds both
# apply in one command, echoing the index hidden state change.
COLLMOD_CLUSTERED_INDEX_AND_EXPIRE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "clustered_index_hidden_and_expire",
        target_collection=ClusteredCollection(),
        indexes=[IndexModel([("a", 1)], name="a_1", hidden=False)],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "hidden": True},
            "expireAfterSeconds": 100,
        },
        expected={"ok": Eq(1.0), "hidden_old": Eq(False), "hidden_new": Eq(True)},
        msg="collMod should apply an index hidden change and a top-level expireAfterSeconds "
        "on a clustered collection",
    ),
]

# Property [Validation Options Without Existing Validator]: validationLevel and
# validationAction set together on a collection that never had a validator are
# accepted, so they do not require a pre-existing validator.
COLLMOD_VALIDATION_NO_PRIOR_VALIDATOR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "validation_level_and_action_together",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "validationLevel": "moderate",
            "validationAction": "warn",
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should accept validationLevel and validationAction together with no "
        "pre-existing validator",
    ),
]

# Property [All-Null Across Groups]: when every cross-group option is null, the
# command is a no-op success that echoes no modification fields.
COLLMOD_ALL_NULL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "all_null_across_groups",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "validator": None,
            "validationLevel": None,
            "validationAction": None,
            "index": None,
            "changeStreamPreAndPostImages": None,
        },
        expected={
            "ok": Eq(1.0),
            "hidden_old": NotExists(),
            "hidden_new": NotExists(),
            "expireAfterSeconds_old": NotExists(),
            "expireAfterSeconds_new": NotExists(),
        },
        msg="collMod should treat all-null cross-group options as a no-op",
    ),
]

# Property [Time Series Cross-Group Coexistence]: a timeseries modification
# applies together with a top-level expireAfterSeconds, a comment, or a
# writeConcern on a time series collection.
COLLMOD_TIMESERIES_CROSS_GROUP_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "timeseries_and_top_level_expire",
        target_collection=TimeseriesTTLCollection(),
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "timeseries": {"granularity": "minutes"},
            "expireAfterSeconds": 100,
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should apply a timeseries modification and a top-level expireAfterSeconds "
        "on a time series collection",
    ),
    CommandTestCase(
        "timeseries_and_comment",
        target_collection=TimeseriesCollection(),
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "timeseries": {"granularity": "minutes"},
            "comment": "hello",
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should apply a timeseries modification together with a comment",
    ),
    CommandTestCase(
        "timeseries_and_write_concern",
        target_collection=TimeseriesCollection(),
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "timeseries": {"granularity": "minutes"},
            "writeConcern": {},
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should apply a timeseries modification together with a writeConcern",
    ),
]

# Property [Time Series Ignores Capped Options]: a timeseries modification
# combined with cappedSize or cappedMax on a time series collection is a silent
# no-op success, since the capped options are ignored rather than rejected.
COLLMOD_TIMESERIES_CAPPED_NOOP_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "timeseries_and_capped_size",
        target_collection=TimeseriesCollection(),
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "timeseries": {},
            "cappedSize": 100_000,
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should silently ignore cappedSize on a time series collection",
    ),
    CommandTestCase(
        "timeseries_and_capped_max",
        target_collection=TimeseriesCollection(),
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "timeseries": {},
            "cappedMax": 1000,
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should silently ignore cappedMax on a time series collection",
    ),
]

# Property [View Cross-Group Coexistence]: view options coexist in one command,
# so a null viewOn paired with a null pipeline is a no-op success and a viewOn
# value paired with a comment is accepted.
COLLMOD_VIEW_CROSS_GROUP_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "view_on_null_and_pipeline_null",
        target_collection=ViewCollection(),
        command=lambda ctx: {"collMod": ctx.collection, "viewOn": None, "pipeline": None},
        expected={"ok": Eq(1.0)},
        msg="collMod should treat a null viewOn and null pipeline as a no-op",
    ),
    CommandTestCase(
        "view_on_and_comment",
        target_collection=ViewCollection(),
        command=lambda ctx: {
            "collMod": ctx.collection,
            "viewOn": "some_source",
            "comment": "hello",
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should apply a viewOn together with a comment",
    ),
]

# Property [Capped Size And Validator Coexistence]: a cappedSize modification
# and a validator apply together in one command on a capped collection.
COLLMOD_CAPPED_SIZE_AND_VALIDATOR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "capped_size_and_validator",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "cappedSize": 100_000,
            "validator": {"a": 1},
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should apply a cappedSize and a validator together on a capped collection",
    ),
]

# Property [Validation Change Result Shape]: a successful validator,
# validationLevel, or validationAction change returns ok:1.0 and echoes no
# old/new modification fields, unlike an index hidden or expireAfterSeconds
# change which does echo them.
COLLMOD_VALIDATION_RESULT_SHAPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "result_shape_validator",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {"collMod": ctx.collection, "validator": {"a": 1}},
        expected={
            "ok": Eq(1.0),
            "validator_old": NotExists(),
            "validator_new": NotExists(),
        },
        msg="collMod should return ok:1.0 with no old/new echo for a validator change",
    ),
    CommandTestCase(
        "result_shape_validation_level",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {"collMod": ctx.collection, "validationLevel": "moderate"},
        expected={
            "ok": Eq(1.0),
            "validationLevel_old": NotExists(),
            "validationLevel_new": NotExists(),
        },
        msg="collMod should return ok:1.0 with no old/new echo for a validationLevel change",
    ),
    CommandTestCase(
        "result_shape_validation_action",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {"collMod": ctx.collection, "validationAction": "warn"},
        expected={
            "ok": Eq(1.0),
            "validationAction_old": NotExists(),
            "validationAction_new": NotExists(),
        },
        msg="collMod should return ok:1.0 with no old/new echo for a validationAction change",
    ),
]

COLLMOD_INTERACTIONS_SUCCESS_TESTS: list[CommandTestCase] = (
    COLLMOD_CROSS_GROUP_TESTS
    + COLLMOD_CLUSTERED_INDEX_AND_EXPIRE_TESTS
    + COLLMOD_VALIDATION_NO_PRIOR_VALIDATOR_TESTS
    + COLLMOD_ALL_NULL_TESTS
    + COLLMOD_TIMESERIES_CROSS_GROUP_TESTS
    + COLLMOD_TIMESERIES_CAPPED_NOOP_TESTS
    + COLLMOD_VIEW_CROSS_GROUP_TESTS
    + COLLMOD_CAPPED_SIZE_AND_VALIDATOR_TESTS
    + COLLMOD_VALIDATION_RESULT_SHAPE_TESTS
)

# Property [Unrelated Option Does Not Suppress Index Resolution]: when an index
# modification names a nonexistent index, an unrelated option group present in
# the same command does not suppress the index lookup, so the index-not-found
# error still surfaces.
COLLMOD_INDEX_RESOLUTION_NOT_SUPPRESSED_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "capped_size_and_index_missing",
        target_collection=CappedCollection(),
        indexes=[IndexModel([("a", 1)], name="a_1")],
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "cappedSize": 200_000,
            "index": {"name": "nonexistent", "hidden": True},
        },
        error_code=INDEX_NOT_FOUND_ERROR,
        msg="collMod should surface an index-not-found error when a missing index is combined "
        "with a cappedSize",
    ),
]

# Property [View Options On A Regular Collection]: a view-only option applied to
# a regular (non-view) collection is rejected rather than converting the
# collection into a view.
COLLMOD_VIEW_OPTION_ON_REGULAR_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "regular_collection_view_on",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {"collMod": ctx.collection, "viewOn": "some_source"},
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject a viewOn applied to a regular collection",
    ),
    CommandTestCase(
        "regular_collection_pipeline",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {"collMod": ctx.collection, "pipeline": []},
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject a pipeline applied to a regular collection",
    ),
]

# Property [Time Series Index Resolution]: an index modification on a time
# series collection resolves against the system.buckets namespace that backs the
# collection, so a nonexistent index produces an index-not-found error
# referencing that namespace.
COLLMOD_TIMESERIES_INDEX_RESOLUTION_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "timeseries_index_resolves_against_bucket_namespace",
        target_collection=TimeseriesCollection(),
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "nonexistent", "hidden": True},
        },
        error_code=INDEX_NOT_FOUND_ERROR,
        msg="collMod should resolve an index on a time series collection against the "
        "bucket-backing namespace, producing an index-not-found error",
    ),
]

# Property [Top-Level Unknown Field Rejection]: an unrecognized top-level command
# field is rejected, and field-name matching is case-sensitive, so a case-variant
# of a known option is rejected too.
COLLMOD_TOP_LEVEL_UNKNOWN_FIELD_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unknown_top_level_field",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {"collMod": ctx.collection, "unknownField": "hello"},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="collMod should reject an unrecognized top-level command field",
    ),
    CommandTestCase(
        "case_variant_top_level_field",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "CappedSize": 100_000},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="collMod should reject a case-variant of a known top-level field as unrecognized",
    ),
]

COLLMOD_INTERACTIONS_ERROR_TESTS: list[CommandTestCase] = (
    COLLMOD_INDEX_RESOLUTION_NOT_SUPPRESSED_ERROR_TESTS
    + COLLMOD_VIEW_OPTION_ON_REGULAR_ERROR_TESTS
    + COLLMOD_TIMESERIES_INDEX_RESOLUTION_ERROR_TESTS
    + COLLMOD_TOP_LEVEL_UNKNOWN_FIELD_ERROR_TESTS
)

COLLMOD_INTERACTIONS_TESTS: list[CommandTestCase] = (
    COLLMOD_INTERACTIONS_SUCCESS_TESTS + COLLMOD_INTERACTIONS_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COLLMOD_INTERACTIONS_TESTS))
def test_collMod_interactions(database_client, collection, test):
    """Test collMod cross-option parameter interactions."""
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
