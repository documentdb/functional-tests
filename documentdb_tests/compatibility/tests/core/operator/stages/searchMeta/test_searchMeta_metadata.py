"""Tests for $searchMeta metadata and count result semantics."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    EXPRESSION_NOT_OBJECT_ERROR,
    FAILED_TO_PARSE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Gte, Lte
from documentdb_tests.framework.test_constants import DECIMAL128_ZERO, INT32_MAX

pytestmark = pytest.mark.requires(search=True)


# Property [Count Result Shape and Defaults]: count.type selects the result
# flavor (an exact {count:{total:n}} for total, a {count:{lowerBound:n}} for
# lowerBound), and an empty, null, or type-less count defaults to a
# lower-bound count.
SEARCHMETA_COUNT_SHAPE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "count_type_total",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "count": {"type": "total"},
                }
            }
        ],
        expected=[{"count": {"total": Int64(3)}}],
        msg="$searchMeta count.type total should return an exact total count",
    ),
    StageTestCase(
        "count_type_lower_bound",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "count": {"type": "lowerBound"},
                }
            }
        ],
        expected=[{"count": {"lowerBound": Int64(3)}}],
        msg="$searchMeta count.type lowerBound should return a lower-bound count",
    ),
    StageTestCase(
        "count_default_empty",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "count": {},
                }
            }
        ],
        expected=[{"count": {"lowerBound": Int64(3)}}],
        msg="$searchMeta should default to a lower-bound count when count is an empty document",
    ),
    StageTestCase(
        "count_default_null",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "count": None,
                }
            }
        ],
        expected=[{"count": {"lowerBound": Int64(3)}}],
        msg="$searchMeta should default to a lower-bound count when count is null",
    ),
    StageTestCase(
        "count_default_type_null",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "count": {"type": None},
                }
            }
        ],
        expected=[{"count": {"lowerBound": Int64(3)}}],
        msg="$searchMeta should default to a lower-bound count when count.type is null",
    ),
    StageTestCase(
        "count_threshold_no_type",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "count": {"threshold": 10},
                }
            }
        ],
        expected=[{"count": {"lowerBound": Int64(3)}}],
        msg="$searchMeta should default to a lower-bound count when a threshold has no type",
    ),
]

# Property [Count Threshold Exactness]: count.type total returns an exact count
# regardless of threshold, and count.type lowerBound returns the exact match
# count whenever the threshold is at least the match count.
SEARCHMETA_THRESHOLD_EXACT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "threshold_total_ignores_below_match",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "count": {"type": "total", "threshold": 1},
                }
            }
        ],
        expected=[{"count": {"total": Int64(3)}}],
        msg="$searchMeta count.type total should ignore a threshold below the match count and "
        "stay exact",
    ),
    StageTestCase(
        "threshold_lower_bound_exact_when_equal",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "count": {"type": "lowerBound", "threshold": 3},
                }
            }
        ],
        expected=[{"count": {"lowerBound": Int64(3)}}],
        msg="$searchMeta count.type lowerBound should be exact when threshold equals the "
        "match count",
    ),
]

# Property [Count Threshold Type Acceptance]: count.threshold accepts any
# non-negative integer-valued number (int32, in-range int64, whole-number
# double), including the boundaries 0 and int32 max, without error.
SEARCHMETA_THRESHOLD_TYPE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "threshold_type_int32_zero",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "count": {"type": "lowerBound", "threshold": 0},
                }
            }
        ],
        expected={"count": {"lowerBound": [Gte(0), Lte(3)]}},
        msg="$searchMeta should accept a zero threshold and return a count within the bound",
    ),
    StageTestCase(
        "threshold_type_int32_max",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "count": {"type": "lowerBound", "threshold": INT32_MAX},
                }
            }
        ],
        expected=[{"count": {"lowerBound": Int64(3)}}],
        msg="$searchMeta should accept an int32-max threshold boundary",
    ),
    StageTestCase(
        "threshold_type_int64",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "count": {"type": "lowerBound", "threshold": Int64(5)},
                }
            }
        ],
        expected=[{"count": {"lowerBound": Int64(3)}}],
        msg="$searchMeta should accept an in-range int64 threshold",
    ),
    StageTestCase(
        "threshold_type_double_whole",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "count": {"type": "lowerBound", "threshold": 5.0},
                }
            }
        ],
        expected=[{"count": {"lowerBound": Int64(3)}}],
        msg="$searchMeta should accept a whole-number double threshold",
    ),
]

SEARCHMETA_RESULT_TESTS: list[StageTestCase] = (
    SEARCHMETA_COUNT_SHAPE_TESTS
    + SEARCHMETA_THRESHOLD_EXACT_TESTS
    + SEARCHMETA_THRESHOLD_TYPE_TESTS
)

# Property [Stage Value Scalar Type Error]: a scalar or null stage value is
# rejected at parse time as not an object.
SEARCHMETA_STAGE_VALUE_SCALAR_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"stage_value_scalar_{tid}",
        pipeline=[{"$searchMeta": val}],
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg=f"$searchMeta should reject a {tid} stage value as a non-object",
    )
    for tid, val in [
        ("string", "x"),
        ("int32", 42),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ZERO),
        ("bool", True),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("null", None),
    ]
]

# Property [Stage Value Array Type Error]: an array stage value, including an
# empty array, is rejected at parse time and distinguished from a scalar.
SEARCHMETA_STAGE_VALUE_ARRAY_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "stage_value_array_empty",
        pipeline=[{"$searchMeta": []}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$searchMeta should reject an empty array stage value as a non-object",
    ),
    StageTestCase(
        "stage_value_array_non_empty",
        pipeline=[{"$searchMeta": [{"text": {"query": "quick", "path": "title"}}]}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$searchMeta should reject a non-empty array stage value as a non-object",
    ),
]

SEARCHMETA_STAGE_VALUE_ERROR_TESTS: list[StageTestCase] = (
    SEARCHMETA_STAGE_VALUE_SCALAR_ERROR_TESTS + SEARCHMETA_STAGE_VALUE_ARRAY_ERROR_TESTS
)

# Result/count semantics and stage-value type errors share one execution path.
SEARCHMETA_TESTS: list[StageTestCase] = SEARCHMETA_RESULT_TESTS + SEARCHMETA_STAGE_VALUE_ERROR_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCHMETA_TESTS))
def test_searchMeta_metadata(search_collection, test_case: StageTestCase):
    """Test $searchMeta metadata, count result semantics, and stage-value errors."""
    result = execute_command(
        search_collection,
        {
            "aggregate": search_collection.name,
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
