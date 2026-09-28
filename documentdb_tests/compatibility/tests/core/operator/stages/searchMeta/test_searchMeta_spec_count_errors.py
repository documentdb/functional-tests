"""Tests for $searchMeta count specification errors."""

from __future__ import annotations

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
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import UNKNOWN_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_OVERFLOW,
    INT32_UNDERFLOW,
)

pytestmark = pytest.mark.requires(search=True)


# Property [Count Not A Document]: a present count value that is not a document
# is rejected.
SEARCHMETA_COUNT_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"count_not_document_{tid}",
        pipeline=[{"$searchMeta": {"text": {"query": "quick", "path": "title"}, "count": val}}],
        error_code=UNKNOWN_ERROR,
        msg=f"$searchMeta should reject a {tid} count value as not a document",
    )
    for tid, val in [
        ("string", "x"),
        ("int32", 42),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ZERO),
        ("bool", True),
        ("array", [1, 2]),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Count Type Not A String]: a count.type value that is not a string is
# rejected.
SEARCHMETA_COUNT_TYPE_NOT_STRING_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"count_type_not_string_{tid}",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "count": {"type": val},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$searchMeta should reject a {tid} count.type value as not a string",
    )
    for tid, val in [
        ("int32", 42),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ZERO),
        ("bool", True),
        ("array", [1, 2]),
        ("object", {"a": 1}),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Count Type Unknown String]: a count.type string outside
# {lowerBound, total} is rejected, with matching being case-sensitive and not
# whitespace-trimmed.
SEARCHMETA_COUNT_TYPE_VALUE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"count_type_value_{suffix}",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "count": {"type": value},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$searchMeta should reject a {suffix} count.type string as an unknown count type",
    )
    for value, suffix in [
        ("Total", "capitalized_total"),
        ("total ", "trailing_space_total"),
        ("foo", "foo"),
    ]
]

# Property [Count Threshold Non-Integer Type]: a count.threshold of a
# non-integer-valued type is rejected, including decimal128 even when its value
# is whole.
SEARCHMETA_COUNT_THRESHOLD_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"count_threshold_type_{tid}",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "count": {"threshold": val},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$searchMeta should reject a {tid} count.threshold value as not an integer",
    )
    for tid, val in [
        ("string", "x"),
        ("bool", True),
        ("array", [1, 2]),
        ("object", {"a": 1}),
        ("decimal128_whole", Decimal128("2")),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Count Threshold Non-Integral Double]: a count.threshold that is a
# fractional double or NaN is rejected.
SEARCHMETA_COUNT_THRESHOLD_FRACTIONAL_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"count_threshold_fractional_{suffix}",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "count": {"threshold": val},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$searchMeta should reject a {suffix} count.threshold double as non-integral",
    )
    for val, suffix in [
        (2.5, "fractional"),
        (FLOAT_NAN, "nan"),
    ]
]

# Property [Count Threshold Negative]: a negative count.threshold is rejected.
SEARCHMETA_COUNT_THRESHOLD_NEGATIVE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"count_threshold_negative_{suffix}",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "count": {"threshold": val},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$searchMeta should reject a {suffix} count.threshold as negative",
    )
    for val, suffix in [
        (-1, "minus_one"),
        (-2.0, "negative_double"),
    ]
]

# Property [Count Threshold Overflow]: a count.threshold above int32 max is
# rejected.
SEARCHMETA_COUNT_THRESHOLD_OVERFLOW_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"count_threshold_overflow_{suffix}",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "count": {"threshold": val},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$searchMeta should reject a {suffix} count.threshold above int32 max",
    )
    for val, suffix in [
        (INT32_OVERFLOW, "int32_max_plus_one"),
        (FLOAT_INFINITY, "infinity"),
    ]
]

# Property [Count Threshold Underflow]: a count.threshold below int32 min is
# rejected.
SEARCHMETA_COUNT_THRESHOLD_UNDERFLOW_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"count_threshold_underflow_{suffix}",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "count": {"threshold": val},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$searchMeta should reject a {suffix} count.threshold below int32 min",
    )
    for val, suffix in [
        (INT32_UNDERFLOW, "int32_min_minus_one"),
        (FLOAT_NEGATIVE_INFINITY, "negative_infinity"),
    ]
]

# Property [Count Threshold Validated For Total]: count.threshold is validated
# for integrality, sign, and range even when count.type is total, where its
# value is otherwise ignored.
SEARCHMETA_COUNT_THRESHOLD_TOTAL_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "count_threshold_total_fractional",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "count": {"type": "total", "threshold": 2.5},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should validate count.threshold integrality even when count.type is "
        "total",
    ),
    StageTestCase(
        "count_threshold_total_negative",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "count": {"type": "total", "threshold": -1},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should validate count.threshold sign even when count.type is total",
    ),
    StageTestCase(
        "count_threshold_total_overflow",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "count": {"type": "total", "threshold": INT32_OVERFLOW},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should validate count.threshold range even when count.type is total",
    ),
]

# Property [Count Unrecognized Sub-Field]: an unrecognized sub-field of count is
# rejected, with matching being case-sensitive.
SEARCHMETA_COUNT_UNKNOWN_FIELD_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"count_unknown_field_{suffix}",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "count": count_value,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$searchMeta should reject an unrecognized count sub-field {name!r}",
    )
    for count_value, name, suffix in [
        ({"type": "total", "foo": 1}, "foo", "alongside_type"),
        ({"bar": 1}, "bar", "solo"),
        ({"Type": "total"}, "Type", "capitalized_type"),
    ]
]

SEARCHMETA_SPEC_COUNT_ERROR_TESTS: list[StageTestCase] = (
    SEARCHMETA_COUNT_TYPE_ERROR_TESTS
    + SEARCHMETA_COUNT_TYPE_NOT_STRING_ERROR_TESTS
    + SEARCHMETA_COUNT_TYPE_VALUE_ERROR_TESTS
    + SEARCHMETA_COUNT_THRESHOLD_TYPE_ERROR_TESTS
    + SEARCHMETA_COUNT_THRESHOLD_FRACTIONAL_ERROR_TESTS
    + SEARCHMETA_COUNT_THRESHOLD_NEGATIVE_ERROR_TESTS
    + SEARCHMETA_COUNT_THRESHOLD_OVERFLOW_ERROR_TESTS
    + SEARCHMETA_COUNT_THRESHOLD_UNDERFLOW_ERROR_TESTS
    + SEARCHMETA_COUNT_THRESHOLD_TOTAL_ERROR_TESTS
    + SEARCHMETA_COUNT_UNKNOWN_FIELD_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCHMETA_SPEC_COUNT_ERROR_TESTS))
def test_searchMeta_spec_count_errors(search_collection, test_case: StageTestCase):
    """Test $searchMeta count specification errors."""
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
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
