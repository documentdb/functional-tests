"""Tests for $out stage - timeseries field/timeField/metaField type errors."""

from __future__ import annotations

from datetime import datetime

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

from documentdb_tests.compatibility.tests.core.operator.stages.out.utils.out_test_helpers import (
    OutTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    populate_collection,
)
from documentdb_tests.framework.assertions import (
    assertResult,
)
from documentdb_tests.framework.error_codes import (
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Timeseries Field Type Errors]: all timeseries sub-fields reject
# non-accepted types with a type mismatch error - timeseries accepts only
# object, timeField/metaField/granularity accept only string, and
# bucketMaxSpanSeconds/bucketRoundingSeconds accept only numeric types
# (int32, Int64, float, Decimal128).

OUT_TIMESERIES_FIELD_TYPE_ERROR_TESTS: list[OutTestCase] = [
    OutTestCase(
        "ts_field_type_int32",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": "target", "timeseries": 42}}],
        msg="$out should reject int32 as timeseries field type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_field_type_int64",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": "target", "timeseries": Int64(42)}}],
        msg="$out should reject int64 as timeseries field type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_field_type_float",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": "target", "timeseries": 3.14}}],
        msg="$out should reject float as timeseries field type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_field_type_decimal128",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": "target", "timeseries": Decimal128("99.9")}}],
        msg="$out should reject decimal128 as timeseries field type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_field_type_bool",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": "target", "timeseries": True}}],
        msg="$out should reject bool as timeseries field type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_field_type_string",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": "target", "timeseries": "invalid"}}],
        msg="$out should reject string as timeseries field type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_field_type_array_empty",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": "target", "timeseries": []}}],
        msg="$out should reject array_empty as timeseries field type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_field_type_array_with_object",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": "target", "timeseries": [{"timeField": "ts"}]}}],
        msg="$out should reject array_with_object as timeseries field type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_field_type_binary",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": "target", "timeseries": Binary(b"\x01")}}],
        msg="$out should reject binary as timeseries field type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_field_type_objectid",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": ObjectId("507f1f77bcf86cd799439011"),
                }
            }
        ],
        msg="$out should reject objectid as timeseries field type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_field_type_datetime",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": "target", "timeseries": datetime(2024, 1, 1)}}],
        msg="$out should reject datetime as timeseries field type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_field_type_regex",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": "target", "timeseries": Regex("abc")}}],
        msg="$out should reject regex as timeseries field type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_field_type_timestamp",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": "target", "timeseries": Timestamp(1, 1)}}],
        msg="$out should reject timestamp as timeseries field type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_field_type_minkey",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": "target", "timeseries": MinKey()}}],
        msg="$out should reject minkey as timeseries field type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_field_type_maxkey",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": "target", "timeseries": MaxKey()}}],
        msg="$out should reject maxkey as timeseries field type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_field_type_code",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": "target", "timeseries": Code("function() {}")}}],
        msg="$out should reject code as timeseries field type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_time_field_type_int32",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": "target", "timeseries": {"timeField": 42}}}],
        msg="$out should reject int32 as timeField type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_time_field_type_int64",
        docs=[{"_id": 1}],
        pipeline=[
            {"$out": {"db": "test", "coll": "target", "timeseries": {"timeField": Int64(42)}}}
        ],
        msg="$out should reject int64 as timeField type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_time_field_type_float",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": "target", "timeseries": {"timeField": 3.14}}}],
        msg="$out should reject float as timeField type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_time_field_type_decimal128",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": Decimal128("99.9")},
                }
            }
        ],
        msg="$out should reject decimal128 as timeField type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_time_field_type_bool",
        docs=[{"_id": 1}],
        pipeline=[{"$out": {"db": "test", "coll": "target", "timeseries": {"timeField": True}}}],
        msg="$out should reject bool as timeField type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_time_field_type_array_with_object",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": [{"timeField": "ts"}]},
                }
            }
        ],
        msg="$out should reject array_with_object as timeField type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_time_field_type_binary",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": Binary(b"\x01")},
                }
            }
        ],
        msg="$out should reject binary as timeField type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_time_field_type_objectid",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": ObjectId("507f1f77bcf86cd799439011")},
                }
            }
        ],
        msg="$out should reject objectid as timeField type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_time_field_type_datetime",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": datetime(2024, 1, 1)},
                }
            }
        ],
        msg="$out should reject datetime as timeField type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_time_field_type_regex",
        docs=[{"_id": 1}],
        pipeline=[
            {"$out": {"db": "test", "coll": "target", "timeseries": {"timeField": Regex("abc")}}}
        ],
        msg="$out should reject regex as timeField type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_time_field_type_timestamp",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": Timestamp(1, 1)},
                }
            }
        ],
        msg="$out should reject timestamp as timeField type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_time_field_type_minkey",
        docs=[{"_id": 1}],
        pipeline=[
            {"$out": {"db": "test", "coll": "target", "timeseries": {"timeField": MinKey()}}}
        ],
        msg="$out should reject minkey as timeField type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_time_field_type_maxkey",
        docs=[{"_id": 1}],
        pipeline=[
            {"$out": {"db": "test", "coll": "target", "timeseries": {"timeField": MaxKey()}}}
        ],
        msg="$out should reject maxkey as timeField type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_time_field_type_code",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": Code("function() {}")},
                }
            }
        ],
        msg="$out should reject code as timeField type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_time_field_type_object",
        docs=[{"_id": 1}],
        pipeline=[
            {"$out": {"db": "test", "coll": "target", "timeseries": {"timeField": {"x": 1}}}}
        ],
        msg="$out should reject object as timeField type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_meta_field_type_int32",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": "ts", "metaField": 42},
                }
            }
        ],
        msg="$out should reject int32 as metaField type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_meta_field_type_int64",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": "ts", "metaField": Int64(42)},
                }
            }
        ],
        msg="$out should reject int64 as metaField type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_meta_field_type_float",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": "ts", "metaField": 3.14},
                }
            }
        ],
        msg="$out should reject float as metaField type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_meta_field_type_decimal128",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": "ts", "metaField": Decimal128("99.9")},
                }
            }
        ],
        msg="$out should reject decimal128 as metaField type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_meta_field_type_bool",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": "ts", "metaField": True},
                }
            }
        ],
        msg="$out should reject bool as metaField type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_meta_field_type_array_with_object",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": "ts", "metaField": [{"timeField": "ts"}]},
                }
            }
        ],
        msg="$out should reject array_with_object as metaField type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_meta_field_type_binary",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": "ts", "metaField": Binary(b"\x01")},
                }
            }
        ],
        msg="$out should reject binary as metaField type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_meta_field_type_objectid",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {
                        "timeField": "ts",
                        "metaField": ObjectId("507f1f77bcf86cd799439011"),
                    },
                }
            }
        ],
        msg="$out should reject objectid as metaField type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_meta_field_type_datetime",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": "ts", "metaField": datetime(2024, 1, 1)},
                }
            }
        ],
        msg="$out should reject datetime as metaField type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_meta_field_type_regex",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": "ts", "metaField": Regex("abc")},
                }
            }
        ],
        msg="$out should reject regex as metaField type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_meta_field_type_timestamp",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": "ts", "metaField": Timestamp(1, 1)},
                }
            }
        ],
        msg="$out should reject timestamp as metaField type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_meta_field_type_minkey",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": "ts", "metaField": MinKey()},
                }
            }
        ],
        msg="$out should reject minkey as metaField type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_meta_field_type_maxkey",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": "ts", "metaField": MaxKey()},
                }
            }
        ],
        msg="$out should reject maxkey as metaField type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_meta_field_type_code",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": "ts", "metaField": Code("function() {}")},
                }
            }
        ],
        msg="$out should reject code as metaField type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_meta_field_type_object",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": "ts", "metaField": {"x": 1}},
                }
            }
        ],
        msg="$out should reject object as metaField type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_TIMESERIES_FIELD_TYPE_ERROR_TESTS))
def test_out_error(collection, test_case: OutTestCase):
    """Test $out rejects invalid configurations with the expected error code."""
    populate_collection(collection, test_case)
    pipeline = test_case.pipeline
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)
