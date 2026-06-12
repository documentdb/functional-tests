"""Tests for collation effects on bucket and bucketAuto stages."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import BUCKET_BOUNDARIES_NOT_SORTED_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Bucket Boundary Grouping]: collation affects $bucket boundary
# comparisons so that strings collation-equal to a boundary are grouped into
# the corresponding bucket.
COLLATION_BUCKET_GROUPING_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "bucket_strength1_case_variants_grouped",
        docs=[
            {"_id": 1, "x": "Apple"},
            {"_id": 2, "x": "APPLE"},
            {"_id": 3, "x": "banana"},
            {"_id": 4, "x": "cherry"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$bucket": {
                        "groupBy": "$x",
                        "boundaries": ["apple", "banana", "cherry", "date"],
                        "default": "other",
                    }
                }
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[
            {"_id": "apple", "count": 2},
            {"_id": "banana", "count": 1},
            {"_id": "cherry", "count": 1},
        ],
        msg="$bucket with strength 1 should group case variants into the matching boundary bucket",
    ),
    CommandTestCase(
        "bucket_no_collation_case_variants_to_default",
        docs=[
            {"_id": 1, "x": "Apple"},
            {"_id": 2, "x": "APPLE"},
            {"_id": 3, "x": "banana"},
            {"_id": 4, "x": "cherry"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$bucket": {
                        "groupBy": "$x",
                        "boundaries": ["apple", "banana", "cherry", "date"],
                        "default": "other",
                    }
                }
            ],
            "cursor": {},
        },
        # Binary comparison: 'A' < 'a', so 'Apple' and 'APPLE' fall below 'apple'
        # boundary and go to default.
        expected=[
            {"_id": "banana", "count": 1},
            {"_id": "cherry", "count": 1},
            {"_id": "other", "count": 2},
        ],
        msg="$bucket without collation should use binary comparison for boundaries",
    ),
]

# Property [Bucket Collation-Equal Boundaries Error]: boundaries that are
# collation-equal produce BUCKET_BOUNDARIES_NOT_SORTED_ERROR because boundary
# validation uses the command-level collation.
COLLATION_BUCKET_BOUNDARY_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "bucket_collation_equal_boundaries_case",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$bucket": {
                        "groupBy": "$x",
                        "boundaries": ["a", "A", "b"],
                        "default": "other",
                    }
                }
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        error_code=BUCKET_BOUNDARIES_NOT_SORTED_ERROR,
        msg="$bucket should reject boundaries that are collation-equal at strength 1",
    ),
    CommandTestCase(
        "bucket_collation_equal_boundaries_diacritics",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$bucket": {
                        "groupBy": "$x",
                        "boundaries": ["cafe", "caf\u00e9", "z"],
                        "default": "other",
                    }
                }
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        error_code=BUCKET_BOUNDARIES_NOT_SORTED_ERROR,
        msg=(
            "$bucket should reject boundaries that are collation-equal"
            " due to diacritics at strength 1"
        ),
    ),
]

# Property [BucketAuto Boundary Comparisons]: collation affects $bucketAuto
# boundary comparisons so that collation-equal strings are placed in the same
# automatically created bucket.
COLLATION_BUCKET_AUTO_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "bucket_auto_strength1_case_variants_same_bucket",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
            {"_id": 4, "x": "cherry"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$bucketAuto": {"groupBy": "$x", "buckets": 3}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[
            {"_id": {"min": "apple", "max": "banana"}, "count": 2},
            {"_id": {"min": "banana", "max": "cherry"}, "count": 1},
            {"_id": {"min": "cherry", "max": "cherry"}, "count": 1},
        ],
        msg="$bucketAuto with strength 1 should place case variants in the same bucket",
    ),
    CommandTestCase(
        "bucket_auto_no_collation_case_variants_separate",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
            {"_id": 4, "x": "cherry"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$bucketAuto": {"groupBy": "$x", "buckets": 3}}],
            "cursor": {},
        },
        # Binary comparison: 'A' < 'a', so 'Apple' is in a separate bucket from
        # 'apple'.
        expected=[
            {"_id": {"min": "Apple", "max": "apple"}, "count": 1},
            {"_id": {"min": "apple", "max": "banana"}, "count": 1},
            {"_id": {"min": "banana", "max": "cherry"}, "count": 2},
        ],
        msg="$bucketAuto without collation should use binary comparison for boundaries",
    ),
]

COLLATION_AGGREGATE_BUCKET_TESTS: list[CommandTestCase] = (
    COLLATION_BUCKET_GROUPING_TESTS
    + COLLATION_BUCKET_BOUNDARY_ERROR_TESTS
    + COLLATION_BUCKET_AUTO_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_AGGREGATE_BUCKET_TESTS))
def test_collation_aggregate_bucket(database_client, collection, test):
    """Test collation effects on $bucket stage boundary comparisons."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
