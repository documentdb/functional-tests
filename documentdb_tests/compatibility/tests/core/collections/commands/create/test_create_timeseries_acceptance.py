"""Tests for the create command timeseries acceptance behavior."""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Timeseries TimeField Acceptance]: timeField accepts any string;
# null timeseries creates a regular collection.
CREATE_TIMESERIES_TIMEFIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="basic_timeseries",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
        },
        expected={"ok": 1.0},
        msg="Basic timeseries creation should succeed",
    ),
    CommandTestCase(
        id="timefield_empty_string",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": ""},
        },
        expected={"ok": 1.0},
        msg="Empty string timeField should succeed",
    ),
    CommandTestCase(
        id="timefield_dollar_prefix",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "$price"},
        },
        expected={"ok": 1.0},
        msg="Dollar-prefix timeField should succeed",
    ),
    CommandTestCase(
        id="timefield_spaces",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "time field"},
        },
        expected={"ok": 1.0},
        msg="Spaces in timeField should succeed",
    ),
    CommandTestCase(
        id="timefield_unicode",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "\u6d4b\u8bd5"},
        },
        expected={"ok": 1.0},
        msg="Unicode timeField should succeed",
    ),
    CommandTestCase(
        id="timefield_underscore_id",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "_id"},
        },
        expected={"ok": 1.0},
        msg="_id as timeField should succeed",
    ),
    CommandTestCase(
        id="timefield_long_string",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "x" * 10_000},
        },
        expected={"ok": 1.0},
        msg="10K+ char timeField should succeed",
    ),
]

# Property [Timeseries MetaField Acceptance]: metaField accepts any string
# including empty; null creates a regular collection.
CREATE_TIMESERIES_METAFIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="metafield_null_treated_as_omitted",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts", "metaField": None},
        },
        expected={"ok": 1.0},
        msg="null metaField is treated as omitted",
    ),
    CommandTestCase(
        id="metafield_empty_string",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts", "metaField": ""},
        },
        expected={"ok": 1.0},
        msg="Empty string metaField should succeed",
    ),
    CommandTestCase(
        id="metafield_valid",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts", "metaField": "meta"},
        },
        expected={"ok": 1.0},
        msg="Valid metaField should succeed",
    ),
]

# Property [Timeseries Granularity Acceptance]: granularity accepts "seconds",
# "minutes", and "hours"; null uses the default.
CREATE_TIMESERIES_GRANULARITY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="granularity_seconds",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts", "granularity": "seconds"},
        },
        expected={"ok": 1.0},
        msg="granularity 'seconds' should succeed",
    ),
    CommandTestCase(
        id="granularity_minutes",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts", "granularity": "minutes"},
        },
        expected={"ok": 1.0},
        msg="granularity 'minutes' should succeed",
    ),
    CommandTestCase(
        id="granularity_hours",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts", "granularity": "hours"},
        },
        expected={"ok": 1.0},
        msg="granularity 'hours' should succeed",
    ),
    CommandTestCase(
        id="granularity_null_uses_default",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts", "granularity": None},
        },
        expected={"ok": 1.0},
        msg="null granularity uses default",
    ),
]

# Property [Timeseries Bucket Field Acceptance]: bucketMaxSpanSeconds and
# bucketRoundingSeconds accept numeric types with coercion in [1, 31536000].
CREATE_TIMESERIES_BUCKET_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="bucket_fields_int32",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": 300,
                "bucketRoundingSeconds": 300,
            },
        },
        expected={"ok": 1.0},
        msg="Bucket fields with int32 should succeed",
    ),
    CommandTestCase(
        id="bucket_fields_int64",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": Int64(300),
                "bucketRoundingSeconds": Int64(300),
            },
        },
        expected={"ok": 1.0},
        msg="Bucket fields with Int64 should succeed",
    ),
    CommandTestCase(
        id="bucket_fields_double",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": 300.0,
                "bucketRoundingSeconds": 300.0,
            },
        },
        expected={"ok": 1.0},
        msg="Bucket fields with double should succeed",
    ),
    CommandTestCase(
        id="bucket_fields_decimal128",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": Decimal128("300"),
                "bucketRoundingSeconds": Decimal128("300"),
            },
        },
        expected={"ok": 1.0},
        msg="Bucket fields with Decimal128 should succeed",
    ),
    CommandTestCase(
        id="bucket_double_truncation_cross_type",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": 3.9,
                "bucketRoundingSeconds": 3,
            },
        },
        expected={"ok": 1.0},
        msg="Double 3.9 truncates to 3, matches int 3",
    ),
    CommandTestCase(
        id="bucket_decimal128_bankers_rounding_cross_type",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": Decimal128("3.5"),
                "bucketRoundingSeconds": 4,
            },
        },
        expected={"ok": 1.0},
        msg="Decimal128('3.5') banker's rounds to 4, matches int 4",
    ),
    CommandTestCase(
        id="bucket_range_minimum",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": 1,
                "bucketRoundingSeconds": 1,
            },
        },
        expected={"ok": 1.0},
        msg="Bucket minimum value 1 should succeed",
    ),
    CommandTestCase(
        id="bucket_range_maximum",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": 31_536_000,
                "bucketRoundingSeconds": 31_536_000,
            },
        },
        expected={"ok": 1.0},
        msg="Bucket maximum value 31536000 should succeed",
    ),
    CommandTestCase(
        id="granularity_seconds_with_matching_bucket",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {
                "timeField": "ts",
                "granularity": "seconds",
                "bucketMaxSpanSeconds": 3600,
            },
        },
        expected={"ok": 1.0},
        msg="granularity 'seconds' + matching bucketMaxSpanSeconds 3600 should succeed",
    ),
    CommandTestCase(
        id="granularity_minutes_with_matching_bucket",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {
                "timeField": "ts",
                "granularity": "minutes",
                "bucketMaxSpanSeconds": 86_400,
            },
        },
        expected={"ok": 1.0},
        msg="granularity 'minutes' + matching bucketMaxSpanSeconds 86400 should succeed",
    ),
    CommandTestCase(
        id="granularity_hours_with_matching_bucket",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {
                "timeField": "ts",
                "granularity": "hours",
                "bucketMaxSpanSeconds": 2_592_000,
            },
        },
        expected={"ok": 1.0},
        msg="granularity 'hours' + matching bucketMaxSpanSeconds 2592000 should succeed",
    ),
]

# Property [Timeseries Compatibility]: timeseries is compatible with collation,
# storageEngine, indexOptionDefaults, writeConcern, expireAfterSeconds, and
# comment; null timeseries creates a regular collection.
CREATE_TIMESERIES_COMPATIBILITY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="compatible_with_collation",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "collation": {"locale": "en"},
        },
        expected={"ok": 1.0},
        msg="Timeseries with collation should succeed",
    ),
    CommandTestCase(
        id="compatible_with_storage_engine",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "storageEngine": {"wiredTiger": {"configString": ""}},
        },
        expected={"ok": 1.0},
        msg="Timeseries with storageEngine should succeed",
    ),
    CommandTestCase(
        id="compatible_with_index_option_defaults",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "indexOptionDefaults": {"storageEngine": {"wiredTiger": {"configString": ""}}},
        },
        expected={"ok": 1.0},
        msg="Timeseries with indexOptionDefaults should succeed",
    ),
    CommandTestCase(
        id="compatible_with_write_concern",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "writeConcern": {"w": 1},
        },
        expected={"ok": 1.0},
        msg="Timeseries with writeConcern should succeed",
    ),
    CommandTestCase(
        id="compatible_with_expire_after_seconds",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "expireAfterSeconds": 7200,
        },
        expected={"ok": 1.0},
        msg="Timeseries with expireAfterSeconds should succeed",
    ),
    CommandTestCase(
        id="compatible_with_comment",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "comment": "hello",
        },
        expected={"ok": 1.0},
        msg="Timeseries with comment should succeed",
    ),
    CommandTestCase(
        id="null_timeseries_creates_regular_collection",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": None,
        },
        expected={"ok": 1.0},
        msg="Null timeseries field creates a regular collection",
    ),
]

CREATE_TIMESERIES_SUCCESS_TESTS: list[CommandTestCase] = (
    CREATE_TIMESERIES_TIMEFIELD_TESTS
    + CREATE_TIMESERIES_METAFIELD_TESTS
    + CREATE_TIMESERIES_GRANULARITY_TESTS
    + CREATE_TIMESERIES_BUCKET_TESTS
    + CREATE_TIMESERIES_COMPATIBILITY_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(CREATE_TIMESERIES_SUCCESS_TESTS))
def test_create_timeseries_acceptance(database_client, collection, test):
    """Test create command timeseries acceptance behavior."""
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
