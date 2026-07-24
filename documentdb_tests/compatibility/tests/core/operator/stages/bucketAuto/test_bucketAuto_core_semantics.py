"""Tests for $bucketAuto aggregation stage — core distribution semantics."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Empty Input]: $bucketAuto over an empty or non-existent collection
# returns no buckets without error.
BUCKET_AUTO_EMPTY_INPUT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "empty_collection",
        docs=[],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 2}}],
        expected=[],
        msg="$bucketAuto over an empty collection should return no buckets",
    ),
    StageTestCase(
        "nonexistent_collection",
        docs=None,
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 2}}],
        expected=[],
        msg="$bucketAuto over a non-existent collection should return no buckets",
    ),
]

# Property [Bucket Count Bounds]: the number of buckets never exceeds the
# number of distinct groupBy values or the document count.
BUCKET_AUTO_COUNT_BOUNDS_TESTS: list[StageTestCase] = [
    StageTestCase(
        "single_document",
        docs=[{"_id": 1, "x": 5}],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 3}}],
        expected=[{"_id": {"min": 5, "max": 5}, "count": 1}],
        msg="$bucketAuto with a single document should return exactly one bucket",
    ),
    StageTestCase(
        "all_identical_values",
        docs=[{"_id": 1, "x": 5}, {"_id": 2, "x": 5}, {"_id": 3, "x": 5}],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 2}}],
        expected=[{"_id": {"min": 5, "max": 5}, "count": 3}],
        msg="$bucketAuto with all identical values should return one bucket",
    ),
    StageTestCase(
        "fewer_unique_than_buckets",
        docs=[
            {"_id": 1, "x": 1},
            {"_id": 2, "x": 1},
            {"_id": 3, "x": 2},
            {"_id": 4, "x": 2},
        ],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 4}}],
        expected=[
            {"_id": {"min": 1, "max": 2}, "count": 2},
            {"_id": {"min": 2, "max": 2}, "count": 2},
        ],
        msg="$bucketAuto should return fewer buckets than requested when unique values are fewer",
    ),
    StageTestCase(
        "fewer_documents_than_buckets",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 5}}],
        expected=[
            {"_id": {"min": 1, "max": 2}, "count": 1},
            {"_id": {"min": 2, "max": 2}, "count": 1},
        ],
        msg="$bucketAuto should return at most one bucket per document",
    ),
]

# Property [Document Distribution]: documents are distributed as evenly as
# possible; when they do not divide evenly, earlier buckets absorb the extras.
BUCKET_AUTO_DISTRIBUTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "even_distribution",
        docs=[{"_id": i, "x": i} for i in range(1, 9)],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 4}}],
        expected=[
            {"_id": {"min": 1, "max": 3}, "count": 2},
            {"_id": {"min": 3, "max": 5}, "count": 2},
            {"_id": {"min": 5, "max": 7}, "count": 2},
            {"_id": {"min": 7, "max": 8}, "count": 2},
        ],
        msg="$bucketAuto should distribute documents evenly when count divides evenly",
    ),
    StageTestCase(
        "uneven_distribution_earlier_absorbs",
        docs=[{"_id": i, "x": i} for i in range(1, 8)],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 2}}],
        expected=[
            {"_id": {"min": 1, "max": 5}, "count": 4},
            {"_id": {"min": 5, "max": 7}, "count": 3},
        ],
        msg="$bucketAuto should give extra documents to earlier buckets when uneven",
    ),
]

BUCKET_AUTO_CORE_TESTS = (
    BUCKET_AUTO_EMPTY_INPUT_TESTS + BUCKET_AUTO_COUNT_BOUNDS_TESTS + BUCKET_AUTO_DISTRIBUTION_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(BUCKET_AUTO_CORE_TESTS))
def test_bucketAuto_core_semantics(collection, test_case: StageTestCase):
    """Test $bucketAuto core distribution semantics."""
    coll = populate_collection(collection, test_case)
    result = execute_command(
        coll,
        {
            "aggregate": coll.name,
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
