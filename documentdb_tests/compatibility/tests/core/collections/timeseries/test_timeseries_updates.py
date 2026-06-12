"""Tests for timeseries collection update restrictions."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccess
from documentdb_tests.framework.error_codes import INVALID_OPTIONS_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.target_collection import TimeseriesCollection

# Property [Non-Multi Update Rejected]: single-document updates (multi:false)
# are not allowed on timeseries collections.
NON_MULTI_REJECTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "non_multi_update_rejected",
        target_collection=TimeseriesCollection(
            timeseries_options={"timeField": "time", "metaField": "meta"}
        ),
        docs=[
            {"time": datetime(2024, 1, 1, tzinfo=timezone.utc), "meta": "s1", "v": 1},
            {"time": datetime(2024, 1, 2, tzinfo=timezone.utc), "meta": "s1", "v": 2},
            {"time": datetime(2024, 1, 3, tzinfo=timezone.utc), "meta": "s2", "v": 3},
        ],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [{"q": {"v": 1}, "u": {"$set": {"meta": "x"}}, "multi": False}],
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Should reject non-multi update",
    ),
]

# Property [Multi Update MetaField Succeeds]: multi-update on the metaField
# and its subfields is allowed.
METAFIELD_UPDATE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "multi_update_metafield_succeeds",
        target_collection=TimeseriesCollection(
            timeseries_options={"timeField": "time", "metaField": "meta"}
        ),
        docs=[
            {"time": datetime(2024, 1, 1, tzinfo=timezone.utc), "meta": "s1", "v": 1},
            {"time": datetime(2024, 1, 2, tzinfo=timezone.utc), "meta": "s1", "v": 2},
            {"time": datetime(2024, 1, 3, tzinfo=timezone.utc), "meta": "s2", "v": 3},
        ],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [{"q": {"meta": "s1"}, "u": {"$set": {"meta": "s3"}}, "multi": True}],
        },
        expected={"n": 2, "nModified": 2, "ok": 1.0},
        msg="Should update metaField",
    ),
    CommandTestCase(
        "multi_update_metafield_subfield_succeeds",
        target_collection=TimeseriesCollection(
            timeseries_options={"timeField": "time", "metaField": "meta"}
        ),
        docs=[
            {
                "time": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "meta": {"sensor": "a", "loc": "x"},
                "v": 1,
            }
        ],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [{"q": {}, "u": {"$set": {"meta.sensor": "b"}}, "multi": True}],
        },
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="Should update metaField subfield",
    ),
    CommandTestCase(
        "unset_metafield_succeeds",
        target_collection=TimeseriesCollection(
            timeseries_options={"timeField": "time", "metaField": "meta"}
        ),
        docs=[
            {"time": datetime(2024, 1, 1, tzinfo=timezone.utc), "meta": "s1", "v": 1},
            {"time": datetime(2024, 1, 2, tzinfo=timezone.utc), "meta": "s1", "v": 2},
            {"time": datetime(2024, 1, 3, tzinfo=timezone.utc), "meta": "s2", "v": 3},
        ],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [{"q": {"meta": "s1"}, "u": {"$unset": {"meta": ""}}, "multi": True}],
        },
        expected={"n": 2, "nModified": 2, "ok": 1.0},
        msg="Should unset metaField",
    ),
]

# Property [Multi Update Non-MetaField Rejected]: multi-update on measurement
# fields, timeField, or mixed fields is rejected.
NON_METAFIELD_REJECTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "multi_update_measurement_rejected",
        target_collection=TimeseriesCollection(
            timeseries_options={"timeField": "time", "metaField": "meta"}
        ),
        docs=[
            {"time": datetime(2024, 1, 1, tzinfo=timezone.utc), "meta": "s1", "v": 1},
            {"time": datetime(2024, 1, 2, tzinfo=timezone.utc), "meta": "s1", "v": 2},
            {"time": datetime(2024, 1, 3, tzinfo=timezone.utc), "meta": "s2", "v": 3},
        ],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [{"q": {}, "u": {"$set": {"v": 99}}, "multi": True}],
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Should reject update on measurement field",
    ),
    CommandTestCase(
        "multi_update_timefield_rejected",
        target_collection=TimeseriesCollection(
            timeseries_options={"timeField": "time", "metaField": "meta"}
        ),
        docs=[
            {"time": datetime(2024, 1, 1, tzinfo=timezone.utc), "meta": "s1", "v": 1},
            {"time": datetime(2024, 1, 2, tzinfo=timezone.utc), "meta": "s1", "v": 2},
            {"time": datetime(2024, 1, 3, tzinfo=timezone.utc), "meta": "s2", "v": 3},
        ],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {},
                    "u": {"$set": {"time": datetime(2025, 1, 1, tzinfo=timezone.utc)}},
                    "multi": True,
                }
            ],
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Should reject update on timeField",
    ),
    CommandTestCase(
        "multi_update_mixed_fields_rejected",
        target_collection=TimeseriesCollection(
            timeseries_options={"timeField": "time", "metaField": "meta"}
        ),
        docs=[
            {"time": datetime(2024, 1, 1, tzinfo=timezone.utc), "meta": "s1", "v": 1},
            {"time": datetime(2024, 1, 2, tzinfo=timezone.utc), "meta": "s1", "v": 2},
            {"time": datetime(2024, 1, 3, tzinfo=timezone.utc), "meta": "s2", "v": 3},
        ],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [{"q": {}, "u": {"$set": {"meta": "x", "v": 99}}, "multi": True}],
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Should reject update on mixed fields",
    ),
    CommandTestCase(
        "rename_metafield_rejected",
        target_collection=TimeseriesCollection(
            timeseries_options={"timeField": "time", "metaField": "meta"}
        ),
        docs=[
            {"time": datetime(2024, 1, 1, tzinfo=timezone.utc), "meta": "s1", "v": 1},
            {"time": datetime(2024, 1, 2, tzinfo=timezone.utc), "meta": "s1", "v": 2},
            {"time": datetime(2024, 1, 3, tzinfo=timezone.utc), "meta": "s2", "v": 3},
        ],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [{"q": {}, "u": {"$rename": {"meta": "metadata"}}, "multi": True}],
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Should reject $rename on metaField",
    ),
]

# Property [Pipeline Update Rejected]: pipeline-style updates are not allowed
# on timeseries collections.
PIPELINE_REJECTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "pipeline_update_rejected",
        target_collection=TimeseriesCollection(
            timeseries_options={"timeField": "time", "metaField": "meta"}
        ),
        docs=[
            {"time": datetime(2024, 1, 1, tzinfo=timezone.utc), "meta": "s1", "v": 1},
            {"time": datetime(2024, 1, 2, tzinfo=timezone.utc), "meta": "s1", "v": 2},
            {"time": datetime(2024, 1, 3, tzinfo=timezone.utc), "meta": "s2", "v": 3},
        ],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [{"q": {}, "u": [{"$set": {"meta": "x"}}], "multi": True}],
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Should reject pipeline-style update",
    ),
]

# Property [Upsert Rejected]: upserts are not allowed on timeseries collections.
UPSERT_REJECTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "upsert_rejected",
        target_collection=TimeseriesCollection(
            timeseries_options={"timeField": "time", "metaField": "meta"}
        ),
        docs=[
            {"time": datetime(2024, 1, 1, tzinfo=timezone.utc), "meta": "s1", "v": 1},
            {"time": datetime(2024, 1, 2, tzinfo=timezone.utc), "meta": "s1", "v": 2},
            {"time": datetime(2024, 1, 3, tzinfo=timezone.utc), "meta": "s2", "v": 3},
        ],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"meta": "new"},
                    "u": {"$set": {"meta": "new"}},
                    "upsert": True,
                    "multi": True,
                }
            ],
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Should reject upsert on timeseries",
    ),
]

# Property [findAndModify Restrictions]: findAndModify with update is rejected,
# but findAndModify with remove succeeds.
FIND_AND_MODIFY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "find_and_modify_update_rejected",
        target_collection=TimeseriesCollection(
            timeseries_options={"timeField": "time", "metaField": "meta"}
        ),
        docs=[
            {"time": datetime(2024, 1, 1, tzinfo=timezone.utc), "meta": "s1", "v": 1},
            {"time": datetime(2024, 1, 2, tzinfo=timezone.utc), "meta": "s1", "v": 2},
            {"time": datetime(2024, 1, 3, tzinfo=timezone.utc), "meta": "s2", "v": 3},
        ],
        command=lambda ctx: {
            "findAndModify": ctx.collection,
            "query": {"v": 1},
            "update": {"$set": {"meta": "x"}},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Should reject findAndModify update",
    ),
    CommandTestCase(
        "find_and_modify_remove_succeeds",
        target_collection=TimeseriesCollection(
            timeseries_options={"timeField": "time", "metaField": "meta"}
        ),
        docs=[
            {"time": datetime(2024, 1, 1, tzinfo=timezone.utc), "meta": "s1", "v": 1},
        ],
        command=lambda ctx: {
            "findAndModify": ctx.collection,
            "query": {"v": 1},
            "remove": True,
        },
        expected={"ok": Eq(1.0)},
        msg="Should allow findAndModify remove on timeseries",
    ),
]

TIMESERIES_UPDATE_TESTS = (
    NON_MULTI_REJECTED_TESTS
    + METAFIELD_UPDATE_TESTS
    + NON_METAFIELD_REJECTED_TESTS
    + PIPELINE_REJECTED_TESTS
    + UPSERT_REJECTED_TESTS
    + FIND_AND_MODIFY_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(TIMESERIES_UPDATE_TESTS))
def test_timeseries_update_cases(database_client, collection, test):
    """Test timeseries update restriction cases."""
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


# Property [$inc MetaField Succeeds]: $inc on a numeric metaField is allowed.
@pytest.mark.collection_mgmt
def test_timeseries_inc_metafield(database_client, collection):
    """Test that $inc on numeric metaField succeeds."""
    coll = TimeseriesCollection(
        timeseries_options={"timeField": "time", "metaField": "meta"}
    ).resolve(database_client, collection)
    coll.insert_one({"time": datetime(2024, 1, 1, tzinfo=timezone.utc), "meta": 5, "v": 1})
    execute_command(
        coll,
        {"update": coll.name, "updates": [{"q": {}, "u": {"$inc": {"meta": 1}}, "multi": True}]},
    )
    result = execute_command(coll, {"find": coll.name, "projection": {"_id": 0, "meta": 1}})
    assertSuccess(result, [{"meta": 6}], msg="Should $inc metaField")
