"""Tests for $bucket aggregation stage — default bucket value handling."""

from __future__ import annotations

import math
from datetime import datetime, timezone

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

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DOUBLE_MAX,
    DOUBLE_MIN,
    DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)

# Property [Default _id Type Preservation]: the default bucket's _id
# preserves the exact BSON type of the default value; all BSON types are
# accepted and the default can differ in type from the boundaries.
BUCKET_DEFAULT_ID_TYPE_TESTS: list[StageTestCase] = [
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": Decimal128("99"),
                }
            }
        ],
        expected=[{"_id": Decimal128("99"), "count": 1}],
        msg="$bucket default _id should preserve Decimal128 type",
        id="default_id_preserves_decimal128",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": datetime(2099, 1, 1, tzinfo=timezone.utc),
                }
            }
        ],
        expected=[{"_id": datetime(2099, 1, 1, tzinfo=timezone.utc), "count": 1}],
        msg="$bucket default _id should preserve datetime type",
        id="default_id_preserves_datetime",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": ObjectId("ffffffffffffffffffffffff"),
                }
            }
        ],
        expected=[{"_id": ObjectId("ffffffffffffffffffffffff"), "count": 1}],
        msg="$bucket default _id should preserve ObjectId type",
        id="default_id_preserves_objectid",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": Binary(b"hi"),
                }
            }
        ],
        expected=[{"_id": b"hi", "count": 1}],
        msg="$bucket default _id should preserve Binary type",
        id="default_id_preserves_binary",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": Regex("abc"),
                }
            }
        ],
        expected=[{"_id": Regex("abc"), "count": 1}],
        msg="$bucket default _id should preserve Regex type",
        id="default_id_preserves_regex",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": Timestamp(99, 1),
                }
            }
        ],
        expected=[{"_id": Timestamp(99, 1), "count": 1}],
        msg="$bucket default _id should preserve Timestamp type",
        id="default_id_preserves_timestamp",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": Code("f", {"a": 1}),
                }
            }
        ],
        expected=[{"_id": Code("f", {"a": 1}), "count": 1}],
        msg="$bucket default _id should preserve Code with scope type",
        id="default_id_preserves_code_with_scope",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": Code("func"),
                }
            }
        ],
        expected=[{"_id": "func", "count": 1}],
        msg="$bucket default Code without scope should be returned as a plain string",
        id="default_id_code_without_scope_becomes_string",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": True,
                }
            }
        ],
        expected=[{"_id": True, "count": 1}],
        msg="$bucket default _id should preserve bool type",
        id="default_id_preserves_bool",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": None,
                }
            }
        ],
        expected=[{"_id": None, "count": 1}],
        msg="$bucket default _id should preserve null type",
        id="default_id_preserves_null",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": [-1],
                }
            }
        ],
        expected=[{"_id": [-1], "count": 1}],
        msg="$bucket default _id should preserve array type",
        id="default_id_preserves_array",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": {"z": -1},
                }
            }
        ],
        expected=[{"_id": {"z": -1}, "count": 1}],
        msg="$bucket default _id should preserve document type",
        id="default_id_preserves_document",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": -0.5,
                }
            }
        ],
        expected=[{"_id": -0.5, "count": 1}],
        msg="$bucket default _id should preserve float type",
        id="default_id_preserves_float",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": "default_bucket",
                }
            }
        ],
        expected=[{"_id": "default_bucket", "count": 1}],
        msg="$bucket default _id should preserve string type",
        id="default_id_preserves_string",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": -2,
                }
            }
        ],
        expected=[{"_id": -2, "count": 1}],
        msg="$bucket default _id should preserve int type",
        id="default_id_preserves_int",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": Int64(-3),
                }
            }
        ],
        expected=[{"_id": Int64(-3), "count": 1}],
        msg="$bucket default _id should preserve Int64 type",
        id="default_id_preserves_int64",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": MinKey(),
                }
            }
        ],
        expected=[{"_id": {"": MinKey()}, "count": 1}],
        msg="$bucket default MinKey should be wrapped in a document",
        id="default_id_wraps_minkey",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": MaxKey(),
                }
            }
        ],
        expected=[{"_id": {"": MaxKey()}, "count": 1}],
        msg="$bucket default MaxKey should be wrapped in a document",
        id="default_id_wraps_maxkey",
    ),
]

# Property [Default Range Acceptance]: the default value at exactly the
# highest boundary is accepted; a value strictly less than the lowest
# boundary is also accepted.
BUCKET_DEFAULT_RANGE_ACCEPTANCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": 10,
                }
            }
        ],
        expected=[{"_id": 10, "count": 1}],
        msg="$bucket should accept a default value at exactly the highest boundary",
        id="default_at_exactly_highest_boundary",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": -1,
                }
            }
        ],
        expected=[{"_id": -1, "count": 1}],
        msg="$bucket should accept a default value strictly less than the lowest boundary",
        id="default_strictly_less_than_lowest_boundary",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": 10.0,
                }
            }
        ],
        expected=[{"_id": 10.0, "count": 1}],
        msg="$bucket should accept float default at int highest boundary via cross-type comparison",
        id="default_cross_type_float_at_highest",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": Decimal128("10"),
                }
            }
        ],
        expected=[{"_id": Decimal128("10"), "count": 1}],
        msg=(
            "$bucket should accept Decimal128 default at int highest"
            " boundary via cross-type comparison"
        ),
        id="default_cross_type_decimal128_at_highest",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": DOUBLE_MIN_NEGATIVE_SUBNORMAL,
                }
            }
        ],
        expected=[{"_id": DOUBLE_MIN_NEGATIVE_SUBNORMAL, "count": 1}],
        msg="$bucket should accept negative subnormal below lowest boundary",
        id="default_negative_subnormal_below_lowest",
    ),
]

# Property [Special Numeric Defaults]: NaN (positive and negative) as
# default always satisfies the range check because NaN is less than
# everything in BSON order; infinity values satisfy the range check when
# they fall outside the boundary range.
BUCKET_SPECIAL_NUMERIC_DEFAULT_TESTS: list[StageTestCase] = [
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": FLOAT_NAN,
                }
            }
        ],
        expected=[{"_id": pytest.approx(math.nan, nan_ok=True), "count": 1}],
        msg="$bucket should accept float NaN as default",
        id="float_nan_default",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": FLOAT_NEGATIVE_NAN,
                }
            }
        ],
        expected=[{"_id": pytest.approx(math.nan, nan_ok=True), "count": 1}],
        msg="$bucket should accept float negative NaN as default",
        id="float_negative_nan_default",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": DECIMAL128_NAN,
                }
            }
        ],
        expected=[{"_id": DECIMAL128_NAN, "count": 1}],
        msg="$bucket should accept Decimal128 NaN as default",
        id="decimal128_nan_default",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": DECIMAL128_NEGATIVE_NAN,
                }
            }
        ],
        expected=[{"_id": DECIMAL128_NEGATIVE_NAN, "count": 1}],
        msg="$bucket should accept Decimal128 negative NaN as default",
        id="decimal128_negative_nan_default",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": FLOAT_INFINITY,
                }
            }
        ],
        expected=[{"_id": FLOAT_INFINITY, "count": 1}],
        msg="$bucket should accept float positive infinity as default",
        id="float_pos_infinity_default",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": FLOAT_NEGATIVE_INFINITY,
                }
            }
        ],
        expected=[{"_id": FLOAT_NEGATIVE_INFINITY, "count": 1}],
        msg="$bucket should accept float negative infinity as default",
        id="float_neg_infinity_default",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": DECIMAL128_INFINITY,
                }
            }
        ],
        expected=[{"_id": DECIMAL128_INFINITY, "count": 1}],
        msg="$bucket should accept Decimal128 positive infinity as default",
        id="decimal128_pos_infinity_default",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": DECIMAL128_NEGATIVE_INFINITY,
                }
            }
        ],
        expected=[{"_id": DECIMAL128_NEGATIVE_INFINITY, "count": 1}],
        msg="$bucket should accept Decimal128 negative infinity as default",
        id="decimal128_neg_infinity_default",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": INT32_MIN,
                }
            }
        ],
        expected=[{"_id": INT32_MIN, "count": 1}],
        msg="$bucket should accept int32 min as default",
        id="int32_min_default",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": INT32_MAX,
                }
            }
        ],
        expected=[{"_id": INT32_MAX, "count": 1}],
        msg="$bucket should accept int32 max as default",
        id="int32_max_default",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": INT64_MIN,
                }
            }
        ],
        expected=[{"_id": INT64_MIN, "count": 1}],
        msg="$bucket should accept int64 min as default",
        id="int64_min_default",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": INT64_MAX,
                }
            }
        ],
        expected=[{"_id": INT64_MAX, "count": 1}],
        msg="$bucket should accept int64 max as default",
        id="int64_max_default",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": DOUBLE_MIN,
                }
            }
        ],
        expected=[{"_id": DOUBLE_MIN, "count": 1}],
        msg="$bucket should accept double min as default",
        id="double_min_default",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": DOUBLE_MAX,
                }
            }
        ],
        expected=[{"_id": DOUBLE_MAX, "count": 1}],
        msg="$bucket should accept double max as default",
        id="double_max_default",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": DOUBLE_MIN_NEGATIVE_SUBNORMAL,
                }
            }
        ],
        expected=[{"_id": DOUBLE_MIN_NEGATIVE_SUBNORMAL, "count": 1}],
        msg="$bucket should accept negative subnormal double as default",
        id="double_negative_subnormal_default",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": DECIMAL128_MIN,
                }
            }
        ],
        expected=[{"_id": DECIMAL128_MIN, "count": 1}],
        msg="$bucket should accept Decimal128 min as default",
        id="decimal128_min_default",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": DECIMAL128_MAX,
                }
            }
        ],
        expected=[{"_id": DECIMAL128_MAX, "count": 1}],
        msg="$bucket should accept Decimal128 max as default",
        id="decimal128_max_default",
    ),
]

BUCKET_DEFAULT_VALUE_TESTS = (
    BUCKET_DEFAULT_ID_TYPE_TESTS
    + BUCKET_DEFAULT_RANGE_ACCEPTANCE_TESTS
    + BUCKET_SPECIAL_NUMERIC_DEFAULT_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(BUCKET_DEFAULT_VALUE_TESTS))
def test_bucket_default_values(collection, test_case: StageTestCase):
    """Test $bucket default bucket value handling."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
