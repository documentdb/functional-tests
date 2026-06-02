"""Tests for timeseries collection collMod, default indexes, and drop behaviors."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertResult,
)
from documentdb_tests.framework.error_codes import (
    INVALID_OPTIONS_ERROR,
    NAMESPACE_NOT_FOUND_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Contains, Len
from documentdb_tests.framework.target_collection import TimeseriesCollection

# Property [collMod Granularity]: granularity can be upgraded but not downgraded.
COLLMOD_GRANULARITY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "granularity_upgrade_seconds_to_minutes",
        target_collection=TimeseriesCollection(
            timeseries_options={"timeField": "time", "metaField": "meta", "granularity": "seconds"}
        ),
        command=lambda ctx: {
            "collMod": ctx.collection,
            "timeseries": {"granularity": "minutes"},
        },
        expected={"ok": 1.0},
        msg="Should upgrade granularity seconds to minutes",
    ),
    CommandTestCase(
        "granularity_upgrade_minutes_to_hours",
        target_collection=TimeseriesCollection(
            timeseries_options={"timeField": "time", "metaField": "meta", "granularity": "minutes"}
        ),
        command=lambda ctx: {
            "collMod": ctx.collection,
            "timeseries": {"granularity": "hours"},
        },
        expected={"ok": 1.0},
        msg="Should upgrade granularity minutes to hours",
    ),
    CommandTestCase(
        "granularity_downgrade_rejected",
        target_collection=TimeseriesCollection(
            timeseries_options={"timeField": "time", "metaField": "meta", "granularity": "minutes"}
        ),
        command=lambda ctx: {
            "collMod": ctx.collection,
            "timeseries": {"granularity": "seconds"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Should reject granularity downgrade",
    ),
]

# Property [collMod Field Immutability]: timeField and metaField cannot be
# changed via collMod.
COLLMOD_FIELD_IMMUTABILITY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "timefield_immutable",
        target_collection=TimeseriesCollection(
            timeseries_options={"timeField": "time", "metaField": "meta", "granularity": "seconds"}
        ),
        command=lambda ctx: {
            "collMod": ctx.collection,
            "timeseries": {"timeField": "newtime"},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Should reject changing timeField via collMod",
    ),
    CommandTestCase(
        "metafield_immutable",
        target_collection=TimeseriesCollection(
            timeseries_options={"timeField": "time", "metaField": "meta", "granularity": "seconds"}
        ),
        command=lambda ctx: {
            "collMod": ctx.collection,
            "timeseries": {"metaField": "newmeta"},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Should reject changing metaField via collMod",
    ),
]

# Property [collMod Option Restrictions]: validator, validationLevel, and
# negative expireAfterSeconds are rejected on timeseries collections.
COLLMOD_OPTION_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "validator_rejected",
        target_collection=TimeseriesCollection(
            timeseries_options={"timeField": "time", "metaField": "meta"}
        ),
        command=lambda ctx: {
            "collMod": ctx.collection,
            "validator": {"$jsonSchema": {"bsonType": "object"}},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Should reject setting validator on timeseries",
    ),
    CommandTestCase(
        "validation_level_rejected",
        target_collection=TimeseriesCollection(
            timeseries_options={"timeField": "time", "metaField": "meta"}
        ),
        command=lambda ctx: {
            "collMod": ctx.collection,
            "validationLevel": "moderate",
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Should reject setting validationLevel on timeseries",
    ),
    CommandTestCase(
        "negative_ttl_rejected",
        target_collection=TimeseriesCollection(
            timeseries_options={"timeField": "time", "metaField": "meta"}
        ),
        command=lambda ctx: {
            "collMod": ctx.collection,
            "expireAfterSeconds": -1,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Should reject negative expireAfterSeconds via collMod",
    ),
]

# Property [collMod Bucket Span]: bucketMaxSpanSeconds can be increased but
# not decreased.
COLLMOD_BUCKET_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "bucket_span_increase",
        target_collection=TimeseriesCollection(
            timeseries_options={
                "timeField": "time",
                "metaField": "meta",
                "bucketMaxSpanSeconds": 300,
                "bucketRoundingSeconds": 300,
            },
        ),
        command=lambda ctx: {
            "collMod": ctx.collection,
            "timeseries": {"bucketMaxSpanSeconds": 600, "bucketRoundingSeconds": 600},
        },
        expected={"ok": 1.0},
        msg="Should increase bucket span",
    ),
    CommandTestCase(
        "bucket_span_decrease_rejected",
        target_collection=TimeseriesCollection(
            timeseries_options={
                "timeField": "time",
                "metaField": "meta",
                "bucketMaxSpanSeconds": 600,
                "bucketRoundingSeconds": 600,
            },
        ),
        command=lambda ctx: {
            "collMod": ctx.collection,
            "timeseries": {"bucketMaxSpanSeconds": 300, "bucketRoundingSeconds": 300},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Should reject bucket span decrease",
    ),
]

# Property [collMod expireAfterSeconds]: TTL can be modified and removed via
# collMod.
COLLMOD_TTL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "expire_modify",
        target_collection=TimeseriesCollection(
            timeseries_options={"timeField": "time", "metaField": "meta"},
            create_options={"expireAfterSeconds": 3600},
        ),
        command=lambda ctx: {
            "collMod": ctx.collection,
            "expireAfterSeconds": 7200,
        },
        expected={"ok": 1.0},
        msg="Should modify expireAfterSeconds",
    ),
    CommandTestCase(
        "expire_remove_off",
        target_collection=TimeseriesCollection(
            timeseries_options={"timeField": "time", "metaField": "meta"},
            create_options={"expireAfterSeconds": 3600},
        ),
        command=lambda ctx: {
            "collMod": ctx.collection,
            "expireAfterSeconds": "off",
        },
        expected={"ok": 1.0},
        msg="Should remove expireAfterSeconds with 'off'",
    ),
]

# Property [Default Indexes]: timeseries with metaField gets a default
# {meta: 1, time: 1} index; without metaField there are no default indexes.
DEFAULT_INDEX_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "default_index_with_meta",
        target_collection=TimeseriesCollection(
            timeseries_options={"timeField": "time", "metaField": "meta"}
        ),
        command=lambda ctx: {"listIndexes": ctx.collection},
        expected={"cursor.firstBatch": Contains("name", "meta_1_time_1")},
        msg="Should have default meta_1_time_1 index",
    ),
    CommandTestCase(
        "no_default_index_without_meta",
        target_collection=TimeseriesCollection(timeseries_options={"timeField": "time"}),
        command=lambda ctx: {"listIndexes": ctx.collection},
        expected={"cursor.firstBatch": Len(0)},
        msg="Should have no default indexes without metaField",
    ),
]

TIMESERIES_OPERATIONS_TESTS = (
    COLLMOD_GRANULARITY_TESTS
    + COLLMOD_FIELD_IMMUTABILITY_TESTS
    + COLLMOD_OPTION_REJECTION_TESTS
    + COLLMOD_BUCKET_TESTS
    + COLLMOD_TTL_TESTS
    + DEFAULT_INDEX_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(TIMESERIES_OPERATIONS_TESTS))
def test_timeseries_operations(database_client, collection, test):
    """Test timeseries collMod and default index cases."""
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


# Property [Drop Removes Buckets]: dropping a timeseries collection also drops
# the system.buckets companion.
@pytest.mark.collection_mgmt
def test_timeseries_drop_removes_buckets(database_client, collection):
    """Test that dropping timeseries removes system.buckets companion."""
    db = database_client
    name = f"{collection.name}_ts_drop"
    db.command("create", name, timeseries={"timeField": "time", "metaField": "meta"})
    bucket_name = f"system.buckets.{name}"

    db.drop_collection(name)

    result = execute_command(
        db[bucket_name],
        {"listIndexes": bucket_name},
    )
    assertFailureCode(
        result, NAMESPACE_NOT_FOUND_ERROR, msg="system.buckets should not exist after drop"
    )
