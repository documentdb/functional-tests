"""Tests for accepted $rankFusion combination weight values and handling."""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.stages.rankFusion.utils.rankFusion_common import (  # noqa: E501
    rrf_score,
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
    DECIMAL128_MAX_NEGATIVE,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_MAX,
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_PRECISION_LOSS,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    INT32_ZERO,
    INT64_MAX,
)

# Property [Accepted Weight Types]: a weight of any numeric BSON type (int32,
# int64, double, Decimal128) is accepted and used as-is without truncation or
# rounding, scaling that pipeline's contribution to weight/(60+rank).
RANKFUSION_WEIGHT_NUMERIC_TYPE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "weight_type_int32",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}},
                    "combination": {"weights": {"p1": 2}},
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[{"_id": 1, "score": rrf_score(1, weights=(2,))}],
        msg="$rankFusion should accept an int32 weight and scale the contribution by it",
    ),
    StageTestCase(
        "weight_type_int64",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}},
                    "combination": {"weights": {"p1": Int64(3)}},
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[{"_id": 1, "score": rrf_score(1, weights=(3,))}],
        msg="$rankFusion should accept an int64 weight and scale the contribution by it",
    ),
    StageTestCase(
        "weight_type_double_fractional",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}},
                    "combination": {"weights": {"p1": 2.5}},
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[{"_id": 1, "score": rrf_score(1, weights=(2.5,))}],
        msg="$rankFusion should use a fractional double weight as-is without truncation",
    ),
    StageTestCase(
        "weight_type_decimal_fractional",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}},
                    "combination": {"weights": {"p1": Decimal128("4.5")}},
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[{"_id": 1, "score": rrf_score(1, weights=(4.5,))}],
        msg="$rankFusion should use a fractional Decimal128 weight as-is without truncation",
    ),
]

# Property [Zero Weight]: a zero weight in any numeric form, including negative
# zero, is accepted and contributes nothing to the score.
RANKFUSION_WEIGHT_ZERO_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"weight_zero_{tid}",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}},
                    "combination": {"weights": {"p1": val}},
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[{"_id": 1, "score": DOUBLE_ZERO}],
        msg=f"$rankFusion should accept a {tid} zero weight and contribute nothing to the score",
    )
    for tid, val in [
        ("int32", INT32_ZERO),
        ("double", DOUBLE_ZERO),
        ("neg_double", DOUBLE_NEGATIVE_ZERO),
        ("decimal", DECIMAL128_ZERO),
        ("neg_decimal", DECIMAL128_NEGATIVE_ZERO),
    ]
]

# Property [Infinity Weight]: a positive-infinity weight as a double or as
# Decimal128('Infinity') is accepted and yields an infinite score.
RANKFUSION_WEIGHT_INFINITY_TESTS: list[StageTestCase] = [
    StageTestCase(
        "weight_inf_double",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}},
                    "combination": {"weights": {"p1": FLOAT_INFINITY}},
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[{"_id": 1, "score": FLOAT_INFINITY}],
        msg="$rankFusion should accept a +Infinity double weight and yield an infinite score",
    ),
    StageTestCase(
        "weight_inf_decimal",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}},
                    "combination": {"weights": {"p1": DECIMAL128_INFINITY}},
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[{"_id": 1, "score": FLOAT_INFINITY}],
        msg="$rankFusion should accept a Decimal128 Infinity weight and yield an infinite score",
    ),
]

# Property [Large Finite Weight]: large finite weights are accepted; the score
# stays finite for weights up to DBL_MAX and overflows the double-typed score to
# infinity for a Decimal128 weight beyond the double range.
RANKFUSION_WEIGHT_LARGE_FINITE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "weight_large_int64_max",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}},
                    "combination": {"weights": {"p1": INT64_MAX}},
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[{"_id": 1, "score": rrf_score(1, weights=(INT64_MAX,))}],
        msg="$rankFusion should accept the maximum int64 weight and keep the score finite",
    ),
    StageTestCase(
        "weight_large_double_1e308",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}},
                    "combination": {"weights": {"p1": DOUBLE_NEAR_MAX}},
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[{"_id": 1, "score": rrf_score(1, weights=(DOUBLE_NEAR_MAX,))}],
        msg="$rankFusion should accept a 1e308 double weight and keep the score finite",
    ),
    StageTestCase(
        "weight_large_dbl_max",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}},
                    "combination": {"weights": {"p1": DOUBLE_MAX}},
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[{"_id": 1, "score": rrf_score(1, weights=(DOUBLE_MAX,))}],
        msg="$rankFusion should accept a DBL_MAX weight and keep the score finite after dividing",
    ),
    StageTestCase(
        "weight_large_decimal_34_digit_max",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}},
                    "combination": {"weights": {"p1": DECIMAL128_MAX}},
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[{"_id": 1, "score": FLOAT_INFINITY}],
        msg="$rankFusion should accept the Decimal128 34-digit max weight, overflowing the score",
    ),
]

# Property [Negative Subnormal Weight]: a negative-subnormal Decimal128 weight is
# accepted because the non-negative check runs on its double conversion, which
# underflows to negative zero, yielding a zero score.
RANKFUSION_WEIGHT_SUBNORMAL_TESTS: list[StageTestCase] = [
    StageTestCase(
        "weight_subnormal_neg_decimal",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}},
                    "combination": {"weights": {"p1": DECIMAL128_MAX_NEGATIVE}},
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[{"_id": 1, "score": DOUBLE_ZERO}],
        msg="$rankFusion should accept a negative-subnormal Decimal128 weight underflowing to zero",
    ),
]

# Property [Precision Boundary Weight]: weights at the double precision-loss
# boundary (2^53 and 2^53+1) are both accepted and collapse to the same double,
# producing identical scores.
RANKFUSION_WEIGHT_PRECISION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "weight_precision_pow2_53",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}},
                    "combination": {"weights": {"p1": Int64(DOUBLE_MAX_SAFE_INTEGER)}},
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[{"_id": 1, "score": rrf_score(1, weights=(DOUBLE_MAX_SAFE_INTEGER,))}],
        msg="$rankFusion should accept a 2^53 weight",
    ),
    StageTestCase(
        "weight_precision_pow2_53_plus_1",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}},
                    "combination": {"weights": {"p1": Int64(DOUBLE_PRECISION_LOSS)}},
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[{"_id": 1, "score": rrf_score(1, weights=(DOUBLE_MAX_SAFE_INTEGER,))}],
        msg="$rankFusion should collapse a 2^53+1 weight to the same double as 2^53",
    ),
]

# Property [Mixed Weight Types]: mixing numeric weight types across pipelines is
# accepted in every pairwise combination and produces the identical summed double
# score.
RANKFUSION_WEIGHT_MIXED_TYPE_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"weight_mixed_{n1}_{n2}",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {
                        "pipelines": {
                            "p1": [{"$sort": {"a": -1}}],
                            "p2": [{"$sort": {"a": -1}}],
                        }
                    },
                    "combination": {"weights": {"p1": v1, "p2": v2}},
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[{"_id": 1, "score": rrf_score(1, 1, weights=(2, 2))}],
        msg=f"$rankFusion should sum a {n1} and {n2} weight to the identical double score",
    )
    for n1, v1, n2, v2 in [
        ("int32", 2, "int64", Int64(2)),
        ("int32", 2, "double", 2.0),
        ("int32", 2, "decimal", Decimal128("2")),
        ("int64", Int64(2), "double", 2.0),
        ("int64", Int64(2), "decimal", Decimal128("2")),
        ("double", 2.0, "decimal", Decimal128("2")),
    ]
]

# Property [Weight Key Matching]: a weight-map key applies to a pipeline only
# when it is byte-for-byte identical to the pipeline name.
RANKFUSION_WEIGHT_KEY_MATCH_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"weight_key_match_{tid}",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {name: [{"$sort": {"a": -1}}]}},
                    "combination": {"weights": {name: 2}},
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[{"_id": 1, "score": rrf_score(1, weights=(2,))}],
        msg=f"$rankFusion should apply a weight whose key byte-matches a {tid} pipeline name",
    )
    for tid, name in [
        # CJK name, multi-byte UTF-8.
        ("non_ascii_cjk", "中文"),
        ("trailing_space", "p1 "),
        ("mid_dollar", "a$b"),
    ]
]

RANKFUSION_WEIGHTS_TESTS = (
    RANKFUSION_WEIGHT_NUMERIC_TYPE_TESTS
    + RANKFUSION_WEIGHT_ZERO_TESTS
    + RANKFUSION_WEIGHT_INFINITY_TESTS
    + RANKFUSION_WEIGHT_LARGE_FINITE_TESTS
    + RANKFUSION_WEIGHT_SUBNORMAL_TESTS
    + RANKFUSION_WEIGHT_PRECISION_TESTS
    + RANKFUSION_WEIGHT_MIXED_TYPE_TESTS
    + RANKFUSION_WEIGHT_KEY_MATCH_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(RANKFUSION_WEIGHTS_TESTS))
def test_rankFusion_weights(collection, test_case: StageTestCase):
    """Test accepted $rankFusion combination weight values and handling."""
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
