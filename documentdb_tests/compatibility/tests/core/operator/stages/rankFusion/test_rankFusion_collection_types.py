"""Tests for $rankFusion behavior across collection types."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.rankFusion.utils.rankFusion_common import (  # noqa: E501
    rrf_score,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import RANK_FUSION_TIMESERIES_UNSUPPORTED_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import (
    CappedCollection,
    ClusteredCollection,
    CollatedCollection,
    SystemBucketsCollection,
    TimeseriesCollection,
    ValidatedCollection,
    ViewChainCollection,
    ViewCollection,
    ViewWithPipelineCollection,
)

# Property [Collection Existence]: running $rankFusion against a non-existent or
# an empty collection returns zero documents with no error.
RANKFUSION_EXISTENCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "existence_nonexistent",
        docs=None,
        pipeline=[{"$rankFusion": {"input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}}}}],
        expected=[],
        msg="$rankFusion on a non-existent collection should return zero documents with no error",
    ),
    StageTestCase(
        "existence_empty",
        docs=[],
        pipeline=[{"$rankFusion": {"input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}}}}],
        expected=[],
        msg="$rankFusion on an empty collection should return zero documents with no error",
    ),
]

# Property [View Compatibility]: $rankFusion runs against a view, ranking over
# the view's resolved output.
RANKFUSION_VIEW_TESTS: list[StageTestCase] = [
    StageTestCase(
        "view_empty_pipeline",
        target_collection=ViewCollection(),
        docs=[{"_id": 1, "a": 10}, {"_id": 2, "a": 20}, {"_id": 3, "a": 5}],
        pipeline=[
            {"$rankFusion": {"input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}}}},
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[
            {"_id": 2, "score": rrf_score(1)},
            {"_id": 1, "score": rrf_score(2)},
            {"_id": 3, "score": rrf_score(3)},
        ],
        msg="$rankFusion on a view should rank over the view's documents",
    ),
    StageTestCase(
        "view_with_pipeline",
        target_collection=ViewWithPipelineCollection(),
        docs=[{"_id": 1, "x": 1, "a": 10}, {"_id": 2, "x": 1, "a": 20}, {"_id": 3, "x": 0, "a": 5}],
        pipeline=[
            {"$rankFusion": {"input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}}}},
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[
            {"_id": 2, "score": rrf_score(1)},
            {"_id": 1, "score": rrf_score(2)},
        ],
        msg="$rankFusion on a view should rank over documents surviving the view's pipeline",
    ),
    StageTestCase(
        "view_on_view",
        target_collection=ViewChainCollection(depth=2),
        docs=[{"_id": 1, "a": 10}, {"_id": 2, "a": 20}, {"_id": 3, "a": 5}],
        pipeline=[
            {"$rankFusion": {"input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}}}},
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[
            {"_id": 2, "score": rrf_score(1)},
            {"_id": 1, "score": rrf_score(2)},
            {"_id": 3, "score": rrf_score(3)},
        ],
        msg="$rankFusion on a view defined on another view should rank over the resolved output",
    ),
]

# Property [Collection Type Compatibility]: $rankFusion runs normally regardless
# of a collection's storage type, producing the same ranking as on a regular
# collection.
RANKFUSION_COLLECTION_TYPE_COMPAT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "type_capped",
        target_collection=CappedCollection(size=1_048_576),
        docs=[{"_id": 1, "a": 10}, {"_id": 2, "a": 20}, {"_id": 3, "a": 5}],
        pipeline=[
            {"$rankFusion": {"input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}}}},
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[
            {"_id": 2, "score": rrf_score(1)},
            {"_id": 1, "score": rrf_score(2)},
            {"_id": 3, "score": rrf_score(3)},
        ],
        msg="$rankFusion should rank normally on a capped collection",
    ),
    StageTestCase(
        "type_clustered",
        target_collection=ClusteredCollection(),
        docs=[{"_id": 1, "a": 10}, {"_id": 2, "a": 20}, {"_id": 3, "a": 5}],
        pipeline=[
            {"$rankFusion": {"input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}}}},
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[
            {"_id": 2, "score": rrf_score(1)},
            {"_id": 1, "score": rrf_score(2)},
            {"_id": 3, "score": rrf_score(3)},
        ],
        msg="$rankFusion should rank normally on a clustered collection",
    ),
    StageTestCase(
        "type_validated",
        target_collection=ValidatedCollection(),
        docs=[{"_id": 1, "x": 1, "a": 10}, {"_id": 2, "x": 1, "a": 20}, {"_id": 3, "x": 1, "a": 5}],
        pipeline=[
            {"$rankFusion": {"input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}}}},
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[
            {"_id": 2, "score": rrf_score(1)},
            {"_id": 1, "score": rrf_score(2)},
            {"_id": 3, "score": rrf_score(3)},
        ],
        msg="$rankFusion should rank normally on a schema-validated collection",
    ),
    StageTestCase(
        "type_collated",
        target_collection=CollatedCollection(),
        docs=[{"_id": 1, "a": 10}, {"_id": 2, "a": 20}, {"_id": 3, "a": 5}],
        pipeline=[
            {"$rankFusion": {"input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}}}},
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[
            {"_id": 2, "score": rrf_score(1)},
            {"_id": 1, "score": rrf_score(2)},
            {"_id": 3, "score": rrf_score(3)},
        ],
        msg="$rankFusion should rank normally on a collection with a collation",
    ),
]

# Property [Time Series Unsupported]: $rankFusion is rejected on a time series
# collection and on its underlying system.buckets namespace.
RANKFUSION_TIMESERIES_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "timeseries_collection",
        target_collection=TimeseriesCollection(),
        docs=[{"ts": datetime(2024, 1, 1, tzinfo=timezone.utc), "meta": "a", "a": 1}],
        pipeline=[{"$rankFusion": {"input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}}}}],
        error_code=RANK_FUSION_TIMESERIES_UNSUPPORTED_ERROR,
        msg="$rankFusion on a time series collection should be rejected",
    ),
    StageTestCase(
        "timeseries_system_buckets",
        target_collection=SystemBucketsCollection(),
        docs=[],
        pipeline=[{"$rankFusion": {"input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}}}}],
        error_code=RANK_FUSION_TIMESERIES_UNSUPPORTED_ERROR,
        msg="$rankFusion on a system.buckets namespace should be rejected",
    ),
]

RANKFUSION_COLLECTION_TYPE_TESTS: list[StageTestCase] = (
    RANKFUSION_EXISTENCE_TESTS
    + RANKFUSION_VIEW_TESTS
    + RANKFUSION_COLLECTION_TYPE_COMPAT_TESTS
    + RANKFUSION_TIMESERIES_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(RANKFUSION_COLLECTION_TYPE_TESTS))
def test_rankFusion_collection_types(collection, test_case: StageTestCase):
    """Test $rankFusion behavior across collection types."""
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
