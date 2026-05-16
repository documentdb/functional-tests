"""Tests for $out stage - timeseries granularity/bucket type errors."""

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

# Continuation of timeseries field type errors: granularity, bucketMaxSpanSeconds,
# bucketRoundingSeconds type errors.
OUT_TIMESERIES_BUCKET_TYPE_ERROR_TESTS: list[OutTestCase] = [
    OutTestCase(
        "ts_granularity_type_int32",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": "ts", "granularity": 42},
                }
            }
        ],
        msg="$out should reject int32 as granularity type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_granularity_type_int64",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": "ts", "granularity": Int64(42)},
                }
            }
        ],
        msg="$out should reject int64 as granularity type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_granularity_type_float",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": "ts", "granularity": 3.14},
                }
            }
        ],
        msg="$out should reject float as granularity type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_granularity_type_decimal128",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": "ts", "granularity": Decimal128("99.9")},
                }
            }
        ],
        msg="$out should reject decimal128 as granularity type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_granularity_type_bool",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": "ts", "granularity": True},
                }
            }
        ],
        msg="$out should reject bool as granularity type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_granularity_type_array_with_object",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": "ts", "granularity": [{"timeField": "ts"}]},
                }
            }
        ],
        msg="$out should reject array_with_object as granularity type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_granularity_type_binary",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": "ts", "granularity": Binary(b"\x01")},
                }
            }
        ],
        msg="$out should reject binary as granularity type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_granularity_type_objectid",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {
                        "timeField": "ts",
                        "granularity": ObjectId("507f1f77bcf86cd799439011"),
                    },
                }
            }
        ],
        msg="$out should reject objectid as granularity type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_granularity_type_datetime",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": "ts", "granularity": datetime(2024, 1, 1)},
                }
            }
        ],
        msg="$out should reject datetime as granularity type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_granularity_type_regex",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": "ts", "granularity": Regex("abc")},
                }
            }
        ],
        msg="$out should reject regex as granularity type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_granularity_type_timestamp",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": "ts", "granularity": Timestamp(1, 1)},
                }
            }
        ],
        msg="$out should reject timestamp as granularity type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_granularity_type_minkey",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": "ts", "granularity": MinKey()},
                }
            }
        ],
        msg="$out should reject minkey as granularity type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_granularity_type_maxkey",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": "ts", "granularity": MaxKey()},
                }
            }
        ],
        msg="$out should reject maxkey as granularity type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_granularity_type_code",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": "ts", "granularity": Code("function() {}")},
                }
            }
        ],
        msg="$out should reject code as granularity type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_granularity_type_object",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {"timeField": "ts", "granularity": {"x": 1}},
                }
            }
        ],
        msg="$out should reject object as granularity type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_bucket_max_type_bool",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {
                        "timeField": "ts",
                        "bucketMaxSpanSeconds": True,
                        "bucketRoundingSeconds": 100,
                    },
                }
            }
        ],
        msg="$out should reject bool as bucketMaxSpanSeconds type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_bucket_max_type_string",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {
                        "timeField": "ts",
                        "bucketMaxSpanSeconds": "invalid",
                        "bucketRoundingSeconds": 100,
                    },
                }
            }
        ],
        msg="$out should reject string as bucketMaxSpanSeconds type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_bucket_max_type_array_with_object",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {
                        "timeField": "ts",
                        "bucketMaxSpanSeconds": [{"timeField": "ts"}],
                        "bucketRoundingSeconds": 100,
                    },
                }
            }
        ],
        msg="$out should reject array_with_object as bucketMaxSpanSeconds type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_bucket_max_type_binary",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {
                        "timeField": "ts",
                        "bucketMaxSpanSeconds": Binary(b"\x01"),
                        "bucketRoundingSeconds": 100,
                    },
                }
            }
        ],
        msg="$out should reject binary as bucketMaxSpanSeconds type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_bucket_max_type_objectid",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {
                        "timeField": "ts",
                        "bucketMaxSpanSeconds": ObjectId("507f1f77bcf86cd799439011"),
                        "bucketRoundingSeconds": 100,
                    },
                }
            }
        ],
        msg="$out should reject objectid as bucketMaxSpanSeconds type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_bucket_max_type_datetime",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {
                        "timeField": "ts",
                        "bucketMaxSpanSeconds": datetime(2024, 1, 1),
                        "bucketRoundingSeconds": 100,
                    },
                }
            }
        ],
        msg="$out should reject datetime as bucketMaxSpanSeconds type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_bucket_max_type_regex",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {
                        "timeField": "ts",
                        "bucketMaxSpanSeconds": Regex("abc"),
                        "bucketRoundingSeconds": 100,
                    },
                }
            }
        ],
        msg="$out should reject regex as bucketMaxSpanSeconds type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_bucket_max_type_timestamp",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {
                        "timeField": "ts",
                        "bucketMaxSpanSeconds": Timestamp(1, 1),
                        "bucketRoundingSeconds": 100,
                    },
                }
            }
        ],
        msg="$out should reject timestamp as bucketMaxSpanSeconds type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_bucket_max_type_minkey",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {
                        "timeField": "ts",
                        "bucketMaxSpanSeconds": MinKey(),
                        "bucketRoundingSeconds": 100,
                    },
                }
            }
        ],
        msg="$out should reject minkey as bucketMaxSpanSeconds type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_bucket_max_type_maxkey",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {
                        "timeField": "ts",
                        "bucketMaxSpanSeconds": MaxKey(),
                        "bucketRoundingSeconds": 100,
                    },
                }
            }
        ],
        msg="$out should reject maxkey as bucketMaxSpanSeconds type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_bucket_max_type_code",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {
                        "timeField": "ts",
                        "bucketMaxSpanSeconds": Code("function() {}"),
                        "bucketRoundingSeconds": 100,
                    },
                }
            }
        ],
        msg="$out should reject code as bucketMaxSpanSeconds type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_bucket_max_type_object",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {
                        "timeField": "ts",
                        "bucketMaxSpanSeconds": {"x": 1},
                        "bucketRoundingSeconds": 100,
                    },
                }
            }
        ],
        msg="$out should reject object as bucketMaxSpanSeconds type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_bucket_round_type_bool",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {
                        "timeField": "ts",
                        "bucketRoundingSeconds": True,
                        "bucketMaxSpanSeconds": 100,
                    },
                }
            }
        ],
        msg="$out should reject bool as bucketRoundingSeconds type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_bucket_round_type_string",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {
                        "timeField": "ts",
                        "bucketRoundingSeconds": "invalid",
                        "bucketMaxSpanSeconds": 100,
                    },
                }
            }
        ],
        msg="$out should reject string as bucketRoundingSeconds type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_bucket_round_type_array_with_object",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {
                        "timeField": "ts",
                        "bucketRoundingSeconds": [{"timeField": "ts"}],
                        "bucketMaxSpanSeconds": 100,
                    },
                }
            }
        ],
        msg="$out should reject array_with_object as bucketRoundingSeconds type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_bucket_round_type_binary",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {
                        "timeField": "ts",
                        "bucketRoundingSeconds": Binary(b"\x01"),
                        "bucketMaxSpanSeconds": 100,
                    },
                }
            }
        ],
        msg="$out should reject binary as bucketRoundingSeconds type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_bucket_round_type_objectid",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {
                        "timeField": "ts",
                        "bucketRoundingSeconds": ObjectId("507f1f77bcf86cd799439011"),
                        "bucketMaxSpanSeconds": 100,
                    },
                }
            }
        ],
        msg="$out should reject objectid as bucketRoundingSeconds type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_bucket_round_type_datetime",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {
                        "timeField": "ts",
                        "bucketRoundingSeconds": datetime(2024, 1, 1),
                        "bucketMaxSpanSeconds": 100,
                    },
                }
            }
        ],
        msg="$out should reject datetime as bucketRoundingSeconds type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_bucket_round_type_regex",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {
                        "timeField": "ts",
                        "bucketRoundingSeconds": Regex("abc"),
                        "bucketMaxSpanSeconds": 100,
                    },
                }
            }
        ],
        msg="$out should reject regex as bucketRoundingSeconds type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_bucket_round_type_timestamp",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {
                        "timeField": "ts",
                        "bucketRoundingSeconds": Timestamp(1, 1),
                        "bucketMaxSpanSeconds": 100,
                    },
                }
            }
        ],
        msg="$out should reject timestamp as bucketRoundingSeconds type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_bucket_round_type_minkey",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {
                        "timeField": "ts",
                        "bucketRoundingSeconds": MinKey(),
                        "bucketMaxSpanSeconds": 100,
                    },
                }
            }
        ],
        msg="$out should reject minkey as bucketRoundingSeconds type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_bucket_round_type_maxkey",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {
                        "timeField": "ts",
                        "bucketRoundingSeconds": MaxKey(),
                        "bucketMaxSpanSeconds": 100,
                    },
                }
            }
        ],
        msg="$out should reject maxkey as bucketRoundingSeconds type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_bucket_round_type_code",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {
                        "timeField": "ts",
                        "bucketRoundingSeconds": Code("function() {}"),
                        "bucketMaxSpanSeconds": 100,
                    },
                }
            }
        ],
        msg="$out should reject code as bucketRoundingSeconds type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_bucket_round_type_object",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$out": {
                    "db": "test",
                    "coll": "target",
                    "timeseries": {
                        "timeField": "ts",
                        "bucketRoundingSeconds": {"x": 1},
                        "bucketMaxSpanSeconds": 100,
                    },
                }
            }
        ],
        msg="$out should reject object as bucketRoundingSeconds type",
        error_code=TYPE_MISMATCH_ERROR,
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_TIMESERIES_BUCKET_TYPE_ERROR_TESTS))
def test_out_error(collection, test_case: OutTestCase):
    """Test $out rejects invalid configurations with the expected error code."""
    populate_collection(collection, test_case)
    pipeline = test_case.pipeline
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)
