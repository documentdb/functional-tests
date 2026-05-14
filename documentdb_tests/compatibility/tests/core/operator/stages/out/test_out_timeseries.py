"""Tests for $out stage - timeseries collection creation and options."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, cast

import pytest
from bson import Decimal128, Int64

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
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_TWO_AND_HALF,
)

# Property [Timeseries Collection Creation]: $out creates a new time
# series collection when valid timeseries options are provided and the
# target does not exist, including edge cases where metaField is "_id" or
# matches timeField.
OUT_TIMESERIES_CREATION_TESTS: list[OutTestCase] = [
    OutTestCase(
        "ts_meta_field_is_id",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "value": 10}],
        target_coll="ts_creation_meta_id",
        out_spec={"timeseries": {"timeField": "ts", "metaField": "_id"}},
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "metaField": "_id",
                "granularity": "seconds",
                "bucketMaxSpanSeconds": 3_600,
            }
        },
        msg='$out should accept metaField set to "_id" without error',
    ),
    OutTestCase(
        "ts_meta_field_same_as_time_field",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "value": 10}],
        target_coll="ts_creation_meta_same",
        out_spec={"timeseries": {"timeField": "ts", "metaField": "ts"}},
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "metaField": "ts",
                "granularity": "seconds",
                "bucketMaxSpanSeconds": 3_600,
            }
        },
        msg="$out should accept metaField set to the same value as timeField without error",
    ),
]

# Property [Bucket Param Type Acceptance]: bucketMaxSpanSeconds and
# bucketRoundingSeconds accept int32, Int64, float, and Decimal128, and the
# equality check between them is type-insensitive.
OUT_BUCKET_PARAM_TYPE_ACCEPTANCE_TESTS: list[OutTestCase] = [
    OutTestCase(
        "bucket_int32",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="bucket_int32",
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": 100,
                "bucketRoundingSeconds": 100,
            }
        },
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "bucketRoundingSeconds": 100,
                "bucketMaxSpanSeconds": 100,
            }
        },
        msg="$out should accept int32 for bucket parameters",
    ),
    OutTestCase(
        "bucket_int64",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="bucket_int64",
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": Int64(100),
                "bucketRoundingSeconds": Int64(100),
            }
        },
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "bucketRoundingSeconds": 100,
                "bucketMaxSpanSeconds": 100,
            }
        },
        msg="$out should accept Int64 for bucket parameters",
    ),
    OutTestCase(
        "bucket_float",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="bucket_float",
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": 100.0,
                "bucketRoundingSeconds": 100.0,
            }
        },
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "bucketRoundingSeconds": 100,
                "bucketMaxSpanSeconds": 100,
            }
        },
        msg="$out should accept float for bucket parameters",
    ),
    OutTestCase(
        "bucket_decimal128",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="bucket_decimal128",
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": Decimal128("100"),
                "bucketRoundingSeconds": Decimal128("100"),
            }
        },
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "bucketRoundingSeconds": 100,
                "bucketMaxSpanSeconds": 100,
            }
        },
        msg="$out should accept Decimal128 for bucket parameters",
    ),
    OutTestCase(
        "bucket_cross_int32_int64",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="bucket_cross_i32_i64",
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": 100,
                "bucketRoundingSeconds": Int64(100),
            }
        },
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "bucketRoundingSeconds": 100,
                "bucketMaxSpanSeconds": 100,
            }
        },
        msg="$out should accept cross-type int32/Int64 bucket parameters",
    ),
    OutTestCase(
        "bucket_cross_float_decimal128",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="bucket_cross_f_d128",
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": 100.0,
                "bucketRoundingSeconds": Decimal128("100"),
            }
        },
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "bucketRoundingSeconds": 100,
                "bucketMaxSpanSeconds": 100,
            }
        },
        msg="$out should accept cross-type float/Decimal128 bucket parameters",
    ),
    OutTestCase(
        "bucket_float_truncation_success",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="bucket_float_trunc",
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": 1.5,
                "bucketRoundingSeconds": 1.5,
            }
        },
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "bucketRoundingSeconds": 1,
                "bucketMaxSpanSeconds": 1,
            }
        },
        msg="$out should truncate float 1.5 to int32 1 for bucket parameters",
    ),
    OutTestCase(
        "bucket_decimal128_bankers_rounding",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="bucket_dec_bankers",
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": DECIMAL128_ONE_AND_HALF,
                "bucketRoundingSeconds": DECIMAL128_ONE_AND_HALF,
            }
        },
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "bucketRoundingSeconds": 2,
                "bucketMaxSpanSeconds": 2,
            }
        },
        msg="$out should round Decimal128 1.5 to 2 (banker's rounding) for bucket parameters",
    ),
    OutTestCase(
        "bucket_decimal128_bankers_round_down",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="bucket_dec_bank_dn",
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": DECIMAL128_TWO_AND_HALF,
                "bucketRoundingSeconds": DECIMAL128_TWO_AND_HALF,
            }
        },
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "bucketRoundingSeconds": 2,
                "bucketMaxSpanSeconds": 2,
            }
        },
        msg="$out should round Decimal128 2.5 to 2 (banker's rounding) for bucket parameters",
    ),
    OutTestCase(
        "bucket_cross_coerced_equality",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="bucket_cross_coerce",
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": 2,
                "bucketRoundingSeconds": DECIMAL128_ONE_AND_HALF,
            }
        },
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "bucketRoundingSeconds": 2,
                "bucketMaxSpanSeconds": 2,
            }
        },
        msg=(
            "$out should accept cross-type bucket params when coerced values are"
            " equal (int32 2 and Decimal128 1.5 -> 2)"
        ),
    ),
    OutTestCase(
        "bucket_range_min",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="bucket_range_min",
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": 1,
                "bucketRoundingSeconds": 1,
            }
        },
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "bucketRoundingSeconds": 1,
                "bucketMaxSpanSeconds": 1,
            }
        },
        msg="$out should accept bucket parameters at the minimum valid value (1)",
    ),
    OutTestCase(
        "bucket_range_max",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="bucket_range_max",
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": 31_536_000,
                "bucketRoundingSeconds": 31_536_000,
            }
        },
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "bucketRoundingSeconds": 31_536_000,
                "bucketMaxSpanSeconds": 31_536_000,
            }
        },
        msg="$out should accept bucket parameters at the maximum valid value (31536000)",
    ),
]

# Property [Timeseries Granularity]: valid granularity values ("seconds",
# "minutes", "hours") are accepted and each produces the corresponding
# bucketMaxSpanSeconds default.
OUT_TIMESERIES_GRANULARITY_TESTS: list[OutTestCase] = [
    OutTestCase(
        "granularity_seconds",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="ts_gran_seconds",
        out_spec={"timeseries": {"timeField": "ts", "granularity": "seconds"}},
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "granularity": "seconds",
                "bucketMaxSpanSeconds": 3_600,
            }
        },
        msg="$out should accept granularity 'seconds'",
    ),
    OutTestCase(
        "granularity_minutes",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="ts_gran_minutes",
        out_spec={"timeseries": {"timeField": "ts", "granularity": "minutes"}},
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "granularity": "minutes",
                "bucketMaxSpanSeconds": 86_400,
            }
        },
        msg="$out should accept granularity 'minutes'",
    ),
    OutTestCase(
        "granularity_hours",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="ts_gran_hours",
        out_spec={"timeseries": {"timeField": "ts", "granularity": "hours"}},
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "granularity": "hours",
                "bucketMaxSpanSeconds": 2_592_000,
            }
        },
        msg="$out should accept granularity 'hours'",
    ),
]

OUT_TIMESERIES_TESTS = (
    OUT_TIMESERIES_CREATION_TESTS
    + OUT_BUCKET_PARAM_TYPE_ACCEPTANCE_TESTS
    + OUT_TIMESERIES_GRANULARITY_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_TIMESERIES_TESTS))
def test_out_timeseries(collection, test_case: OutTestCase):
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


# Property [Timeseries Cross-Database]: $out creates a time series collection
# in a different database when timeseries options are specified with a
# cross-database target.
OUT_TIMESERIES_CROSS_DB_TESTS: list[OutTestCase] = [
    OutTestCase(
        "ts_cross_db",
        docs=[{"_id": 1, "ts": datetime(2024, 7, 1), "value": 70}],
        target_coll="ts_cross_target",
        target_db="out_ts_cross_db_target",
        pipeline=[
            {
                "$out": {
                    "db": "out_ts_cross_db_target",
                    "coll": "ts_cross_target",
                    "timeseries": {"timeField": "ts"},
                }
            }
        ],
        expected=[{"ts": datetime(2024, 7, 1, tzinfo=timezone.utc), "value": 70}],
        msg="$out should create a time series collection in a different database",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_TIMESERIES_CROSS_DB_TESTS))
def test_out_timeseries_cross_db(collection, test_case: OutTestCase):
    """Test $out creates a time series collection in a different database."""
    populate_collection(collection, test_case)
    client = collection.database.client
    client.drop_database(test_case.target_db)
    try:
        execute_command(
            collection,
            {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
        )
        result = execute_command(
            client[test_case.target_db][test_case.target_coll],
            {
                "find": test_case.target_coll,
                "filter": {},
                "projection": {"_id": 0},
            },
        )
        assertResult(result, expected=test_case.expected, msg=test_case.msg)
    finally:
        client.drop_database(test_case.target_db)


# Property [Timeseries DateTime Acceptance]: all datetime boundary values
# are accepted as timeField values when writing to a timeseries collection
# via $out, including Unix epoch, pre-epoch, far future, minimum datetime,
# and millisecond precision.
OUT_TIMESERIES_DATETIME_ACCEPTANCE_TESTS: list[OutTestCase] = [
    OutTestCase(
        "ts_datetime_epoch",
        docs=[{"_id": 1, "ts": datetime(1970, 1, 1), "v": 1}],
        target_coll="ts_dt_epoch",
        out_spec={"timeseries": {"timeField": "ts"}},
        expected=[{"ts": datetime(1970, 1, 1, tzinfo=timezone.utc), "v": 1}],
        msg="$out timeseries should accept Unix epoch as timeField value",
    ),
    OutTestCase(
        "ts_datetime_pre_epoch",
        docs=[{"_id": 1, "ts": datetime(1960, 6, 15), "v": 2}],
        target_coll="ts_dt_pre_epoch",
        out_spec={"timeseries": {"timeField": "ts"}},
        expected=[{"ts": datetime(1960, 6, 15, tzinfo=timezone.utc), "v": 2}],
        msg="$out timeseries should accept pre-epoch dates as timeField value",
    ),
    OutTestCase(
        "ts_datetime_far_future",
        docs=[{"_id": 1, "ts": datetime(9999, 12, 31, 23, 59, 59), "v": 3}],
        target_coll="ts_dt_far_future",
        out_spec={"timeseries": {"timeField": "ts"}},
        expected=[{"ts": datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc), "v": 3}],
        msg="$out timeseries should accept far future dates as timeField value",
    ),
    OutTestCase(
        "ts_datetime_minimum",
        docs=[{"_id": 1, "ts": datetime(1, 1, 1), "v": 4}],
        target_coll="ts_dt_minimum",
        out_spec={"timeseries": {"timeField": "ts"}},
        expected=[{"ts": datetime(1, 1, 1, tzinfo=timezone.utc), "v": 4}],
        msg="$out timeseries should accept minimum datetime (0001-01-01) as timeField value",
    ),
    OutTestCase(
        "ts_datetime_millisecond_precision",
        docs=[{"_id": 1, "ts": datetime(2024, 6, 15, 12, 30, 45, 123_000), "v": 5}],
        target_coll="ts_dt_millis",
        out_spec={"timeseries": {"timeField": "ts"}},
        expected=[{"ts": datetime(2024, 6, 15, 12, 30, 45, 123_000, tzinfo=timezone.utc), "v": 5}],
        msg="$out timeseries should accept datetimes with millisecond precision as timeField value",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_TIMESERIES_DATETIME_ACCEPTANCE_TESTS))
def test_out_timeseries_datetime_acceptance(collection, test_case: OutTestCase):
    """Test $out timeseries accepts datetime boundary values as timeField."""
    populate_collection(collection, test_case)
    out_stage = test_case.build_out_stage(collection)
    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [out_stage], "cursor": {}},
    )
    result = execute_command(
        collection,
        {
            "find": test_case.target_coll,
            "filter": {},
            "projection": {"_id": 0, "ts": 1, "v": 1},
        },
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)


# Property [Timeseries Existing Collection]: writing to an existing time
# series collection succeeds both with matching timeseries options and
# without specifying timeseries options (string and document form).
OUT_TIMESERIES_EXISTING_TESTS: list[OutTestCase] = [
    OutTestCase(
        "ts_existing_matching_options",
        docs=[{"_id": 1, "ts": datetime(2024, 6, 1), "value": 60}],
        target_coll="ts_existing_target",
        out_spec={"timeseries": {"timeField": "ts"}},
        setup=lambda c: (
            c.database.drop_collection("ts_existing_target"),
            c.database.command({"create": "ts_existing_target", "timeseries": {"timeField": "ts"}}),
        ),
        expected=[{"ts": datetime(2024, 6, 1, tzinfo=timezone.utc), "value": 60}],
        msg=(
            "$out should write to an existing time series collection with"
            " matching timeseries options"
        ),
    ),
    OutTestCase(
        "ts_existing_string_form",
        docs=[{"_id": 1, "ts": datetime(2024, 6, 1), "value": 60}],
        target_coll="ts_existing_target",
        setup=lambda c: (
            c.database.drop_collection("ts_existing_target"),
            c.database.command({"create": "ts_existing_target", "timeseries": {"timeField": "ts"}}),
        ),
        expected=[{"ts": datetime(2024, 6, 1, tzinfo=timezone.utc), "value": 60}],
        msg=(
            "$out should write to an existing time series collection using"
            " string form without timeseries options"
        ),
    ),
    OutTestCase(
        "ts_existing_document_form",
        docs=[{"_id": 1, "ts": datetime(2024, 6, 1), "value": 60}],
        target_coll="ts_existing_target",
        out_spec={},
        setup=lambda c: (
            c.database.drop_collection("ts_existing_target"),
            c.database.command({"create": "ts_existing_target", "timeseries": {"timeField": "ts"}}),
        ),
        expected=[{"ts": datetime(2024, 6, 1, tzinfo=timezone.utc), "value": 60}],
        msg=(
            "$out should write to an existing time series collection using"
            " document form without timeseries options"
        ),
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_TIMESERIES_EXISTING_TESTS))
def test_out_timeseries_existing(collection, test_case: OutTestCase):
    """Test $out writes to an existing time series collection."""
    populate_collection(collection, test_case)
    if test_case.setup:
        test_case.setup(collection)
    out_stage = test_case.build_out_stage(collection)
    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [out_stage], "cursor": {}},
    )
    result = execute_command(
        collection,
        {
            "find": test_case.target_coll,
            "filter": {},
            "projection": {"_id": 0, "ts": 1, "value": 1},
        },
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
