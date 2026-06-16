"""Tests for $rankFusion combination weight value errors."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    RANK_FUSION_WEIGHT_COUNT_ERROR,
    RANK_FUSION_WEIGHT_KEY_NO_MATCH_ERROR,
    RANK_FUSION_WEIGHT_NEGATIVE_ERROR,
    RANK_FUSION_WEIGHT_TYPE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ONE_AND_HALF,
    DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [Weight Value Type Strictness]: a weight value must be a literal
# numeric; any other type produces a numeric-type error, with no boolean
# coercion and no evaluation of expression or field-path values.
RANKFUSION_WEIGHT_VALUE_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"weight_value_type_{tid}",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}},
                    "combination": {"weights": {"p1": val}},
                }
            }
        ],
        error_code=RANK_FUSION_WEIGHT_TYPE_ERROR,
        msg=f"$rankFusion should reject a {tid} weight value",
    )
    for tid, val in [
        ("string", "x"),
        ("bool", True),
        ("null", None),
        ("array", [1]),
        ("object", {"x": 1}),
        ("objectid", ObjectId("000000000000000000000001")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        # Expression subdocuments and field-path strings are not evaluated.
        ("expression_add", {"$add": [1, 1]}),
        ("expression_literal", {"$literal": 2}),
        ("field_path", "$a"),
    ]
]

# Property [Weight Value Range Errors]: a weight that is negative (in any
# numeric type, including the smallest negative subnormal double), NaN, or
# negative infinity falls outside the non-negative range and produces a
# non-negative-check error.
RANKFUSION_WEIGHT_RANGE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"weight_range_{tid}",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}},
                    "combination": {"weights": {"p1": val}},
                }
            }
        ],
        error_code=RANK_FUSION_WEIGHT_NEGATIVE_ERROR,
        msg=f"$rankFusion should reject a {tid} weight",
    )
    for tid, val in [
        ("negative_int32", -1),
        ("negative_int64", Int64(-1)),
        ("negative_double", -1.0),
        ("negative_decimal", DECIMAL128_NEGATIVE_ONE_AND_HALF),
        ("smallest_negative_subnormal_double", DOUBLE_MIN_NEGATIVE_SUBNORMAL),
        ("nan_double", FLOAT_NAN),
        ("nan_decimal", DECIMAL128_NAN),
        ("neg_infinity_double", FLOAT_NEGATIVE_INFINITY),
        ("neg_infinity_decimal", DECIMAL128_NEGATIVE_INFINITY),
    ]
]

# Property [Weight Key No Match]: a weight-map key that is not byte-for-byte
# identical to a declared pipeline name produces a no-matching-name error;
# keys are matched exactly and are exempt from pipeline-name syntax rules, so
# a key that would be invalid as a pipeline name simply fails to match.
RANKFUSION_WEIGHT_KEY_NO_MATCH_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"weight_key_no_match_{tid}",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {pname: [{"$sort": {"a": -1}}]}},
                    "combination": {"weights": {wkey: 2}},
                }
            }
        ],
        error_code=RANK_FUSION_WEIGHT_KEY_NO_MATCH_ERROR,
        msg=f"$rankFusion should reject a {tid} weight key that matches no pipeline name",
    )
    for tid, pname, wkey in [
        ("empty", "p1", ""),
        ("dotted", "p1", "a.b"),
        ("dollar_prefixed", "p1", "$x"),
        ("case_mismatch", "p1", "P1"),
        ("trailing_space", "p1", "p1 "),
        # Pipeline name in NFC form (U+00E9) vs weight key in NFD form
        # (U+0065 U+0301): no Unicode normalization, so they do not match.
        ("nfc_vs_nfd", "\u00e9", "e\u0301"),
    ]
]

# Property [Weight Count Exceeds Pipelines]: a weights map with more entries
# than there are pipelines produces a count error.
RANKFUSION_WEIGHT_COUNT_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "weight_count_exceeds_pipelines",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}},
                    "combination": {"weights": {"p1": 1, "p2": 2}},
                }
            }
        ],
        error_code=RANK_FUSION_WEIGHT_COUNT_ERROR,
        msg="$rankFusion should reject a weights map with more entries than pipelines",
    ),
]

RANKFUSION_WEIGHT_ERROR_TESTS = (
    RANKFUSION_WEIGHT_VALUE_TYPE_ERROR_TESTS
    + RANKFUSION_WEIGHT_RANGE_ERROR_TESTS
    + RANKFUSION_WEIGHT_KEY_NO_MATCH_ERROR_TESTS
    + RANKFUSION_WEIGHT_COUNT_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(RANKFUSION_WEIGHT_ERROR_TESTS))
def test_rankFusion_weight_errors(collection, test_case: StageTestCase):
    """Test $rankFusion combination weight value errors."""
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
