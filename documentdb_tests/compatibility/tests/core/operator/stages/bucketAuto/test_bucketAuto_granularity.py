"""Tests for $bucketAuto aggregation stage — 'granularity' option."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.bucketAuto.utils.bucketAuto_common import (  # noqa: E501
    GRANULARITY_VALUES,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertNotError, assertResult
from documentdb_tests.framework.error_codes import (
    BUCKET_AUTO_GRANULARITY_NAN_ERROR,
    BUCKET_AUTO_GRANULARITY_NEGATIVE_ERROR,
    BUCKET_AUTO_GRANULARITY_NON_NUMERIC_ERROR,
    BUCKET_AUTO_GRANULARITY_NOT_STRING_ERROR,
    BUCKET_AUTO_GRANULARITY_UNKNOWN_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

_GRAN_DOCS = [{"_id": 1, "x": 1}, {"_id": 2, "x": 10}, {"_id": 3, "x": 100}, {"_id": 4, "x": 1000}]

# Property [Granularity Value Acceptance]: each documented preferred-number
# series string is accepted as a 'granularity' value.
BUCKET_AUTO_GRANULARITY_ACCEPT_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"granularity_accept_{series}",
        docs=_GRAN_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 2, "granularity": series}}],
        msg=f"$bucketAuto should accept granularity '{series}'",
    )
    for series in GRANULARITY_VALUES
]

# Property [Granularity Rounds Boundaries]: granularity rounds bucket
# boundaries to the preferred-number series for a known dataset.
BUCKET_AUTO_GRANULARITY_ROUNDING_TESTS: list[StageTestCase] = [
    StageTestCase(
        "granularity_R5_rounds_boundaries",
        docs=_GRAN_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 3, "granularity": "R5"}}],
        expected=[
            {"_id": {"min": 0.63, "max": 1.6}, "count": 1},
            {"_id": {"min": 1.6, "max": 16.0}, "count": 1},
            {"_id": {"min": 16.0, "max": 1600.0}, "count": 2},
        ],
        msg="$bucketAuto granularity 'R5' should round boundaries to the R5 series",
    ),
    StageTestCase(
        "granularity_powersof2_rounds_boundaries",
        docs=_GRAN_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 3, "granularity": "POWERSOF2"}}],
        expected=[
            {"_id": {"min": 0.5, "max": 2}, "count": 1},
            {"_id": {"min": 2, "max": 16}, "count": 1},
            {"_id": {"min": 16, "max": 1024}, "count": 2},
        ],
        msg="$bucketAuto granularity 'POWERSOF2' should round boundaries to powers of two",
    ),
    StageTestCase(
        "granularity_1_2_5_rounds_boundaries",
        docs=_GRAN_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 3, "granularity": "1-2-5"}}],
        expected=[
            {"_id": {"min": 0.5, "max": 2.0}, "count": 1},
            {"_id": {"min": 2.0, "max": 20.0}, "count": 1},
            {"_id": {"min": 20.0, "max": 2000.0}, "count": 2},
        ],
        msg="$bucketAuto granularity '1-2-5' should round boundaries to the 1-2-5 series",
    ),
    StageTestCase(
        "granularity_E6_rounds_boundaries",
        docs=_GRAN_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 3, "granularity": "E6"}}],
        expected=[
            {"_id": {"min": 0.68, "max": 1.5}, "count": 1},
            {"_id": {"min": 1.5, "max": 15.0}, "count": 1},
            {"_id": {"min": 15.0, "max": 1500.0}, "count": 2},
        ],
        msg="$bucketAuto granularity 'E6' should round boundaries to the E6 series",
    ),
    StageTestCase(
        "granularity_fewer_buckets_when_coarse",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 10, "granularity": "R5"}}],
        expected=[
            {"_id": {"min": 0.63, "max": 1.6}, "count": 1},
            {"_id": {"min": 1.6, "max": 2.5}, "count": 1},
        ],
        msg="$bucketAuto granularity should produce fewer buckets than requested when coarse",
    ),
]

# Property [Granularity Value Rejection]: unknown and empty-string granularity
# values are rejected.
BUCKET_AUTO_GRANULARITY_VALUE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "granularity_unknown_string",
        docs=_GRAN_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 2, "granularity": "BOGUS"}}],
        error_code=BUCKET_AUTO_GRANULARITY_UNKNOWN_ERROR,
        msg="$bucketAuto should reject an unrecognized granularity string",
    ),
    StageTestCase(
        "granularity_empty_string",
        docs=_GRAN_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 2, "granularity": ""}}],
        error_code=BUCKET_AUTO_GRANULARITY_UNKNOWN_ERROR,
        msg="$bucketAuto should reject an empty granularity string",
    ),
]

# Property [Granularity Type Rejection]: 'granularity' must be a string; all
# non-string BSON types are rejected.
BUCKET_AUTO_GRANULARITY_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "granularity_int",
        docs=_GRAN_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 2, "granularity": 5}}],
        error_code=BUCKET_AUTO_GRANULARITY_NOT_STRING_ERROR,
        msg="$bucketAuto should reject an int granularity value",
    ),
    StageTestCase(
        "granularity_double",
        docs=_GRAN_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 2, "granularity": 1.0}}],
        error_code=BUCKET_AUTO_GRANULARITY_NOT_STRING_ERROR,
        msg="$bucketAuto should reject a double granularity value",
    ),
    StageTestCase(
        "granularity_bool",
        docs=_GRAN_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 2, "granularity": True}}],
        error_code=BUCKET_AUTO_GRANULARITY_NOT_STRING_ERROR,
        msg="$bucketAuto should reject a bool granularity value",
    ),
    StageTestCase(
        "granularity_null",
        docs=_GRAN_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 2, "granularity": None}}],
        error_code=BUCKET_AUTO_GRANULARITY_NOT_STRING_ERROR,
        msg="$bucketAuto should reject a null granularity value",
    ),
    StageTestCase(
        "granularity_array",
        docs=_GRAN_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 2, "granularity": ["R5"]}}],
        error_code=BUCKET_AUTO_GRANULARITY_NOT_STRING_ERROR,
        msg="$bucketAuto should reject an array granularity value",
    ),
    StageTestCase(
        "granularity_object",
        docs=_GRAN_DOCS,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 2, "granularity": {"s": "R5"}}}],
        error_code=BUCKET_AUTO_GRANULARITY_NOT_STRING_ERROR,
        msg="$bucketAuto should reject an object granularity value",
    ),
]

# Property [Granularity Numeric-Only Constraint]: granularity requires all
# groupBy values to be non-negative numbers with none NaN.
BUCKET_AUTO_GRANULARITY_NUMERIC_CONSTRAINT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "granularity_non_numeric_groupBy",
        docs=[{"_id": 1, "x": "a"}, {"_id": 2, "x": "b"}],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 2, "granularity": "R5"}}],
        error_code=BUCKET_AUTO_GRANULARITY_NON_NUMERIC_ERROR,
        msg="$bucketAuto granularity should be rejected when a groupBy value is non-numeric",
    ),
    StageTestCase(
        "granularity_nan_groupBy",
        docs=[{"_id": 1, "x": FLOAT_NAN}, {"_id": 2, "x": FLOAT_NAN}],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 2, "granularity": "R5"}}],
        error_code=BUCKET_AUTO_GRANULARITY_NAN_ERROR,
        msg="$bucketAuto granularity should be rejected when a groupBy value is NaN",
    ),
    StageTestCase(
        "granularity_negative_groupBy",
        docs=[{"_id": 1, "x": -5}, {"_id": 2, "x": -1}],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 2, "granularity": "R5"}}],
        error_code=BUCKET_AUTO_GRANULARITY_NEGATIVE_ERROR,
        msg="$bucketAuto granularity should be rejected when a groupBy value is negative",
    ),
    StageTestCase(
        "granularity_negative_infinity_groupBy",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": FLOAT_NEGATIVE_INFINITY}],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 1, "granularity": "POWERSOF2"}}],
        error_code=BUCKET_AUTO_GRANULARITY_NEGATIVE_ERROR,
        msg="$bucketAuto granularity rejects -Infinity via the negative-value check",
    ),
]

BUCKET_AUTO_GRANULARITY_TESTS = (
    BUCKET_AUTO_GRANULARITY_ROUNDING_TESTS
    + BUCKET_AUTO_GRANULARITY_VALUE_ERROR_TESTS
    + BUCKET_AUTO_GRANULARITY_TYPE_ERROR_TESTS
    + BUCKET_AUTO_GRANULARITY_NUMERIC_CONSTRAINT_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(BUCKET_AUTO_GRANULARITY_ACCEPT_TESTS))
def test_bucketAuto_granularity_accepted(collection, test_case: StageTestCase):
    """Test that $bucketAuto accepts each documented granularity series value."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertNotError(result, msg=test_case.msg)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(BUCKET_AUTO_GRANULARITY_TESTS))
def test_bucketAuto_granularity(collection, test_case: StageTestCase):
    """Test $bucketAuto 'granularity' rounding behavior and validation."""
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
