"""Tests for $searchMeta count behavior above the exact-count threshold."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from bson import Int64
from pymongo.collection import Collection

from documentdb_tests.compatibility.tests.core.operator.stages.searchMeta.utils.searchMeta_common import (  # noqa: E501
    LARGE_MATCH_COUNT,
    build_collection,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Gte, Lte

pytestmark = pytest.mark.requires(search=True)


@pytest.fixture(scope="module")
def large_search_collection(engine_client, worker_id) -> Iterator[Collection]:
    """Large indexed collection where every document matches one query."""
    with build_collection(
        engine_client,
        worker_id,
        f"{__name__}::large_search_collection",
        "searchmeta_large",
        [{"_id": i, "title": "widget"} for i in range(LARGE_MATCH_COUNT)],
        [{"name": "default", "definition": {"mappings": {"dynamic": True}}}],
    ) as coll:
        yield coll


# Property [Count Type Above Threshold]: when the match count exceeds the
# threshold, count.type lowerBound returns a value between the threshold and the
# match count, while count.type total stays exact.
SEARCHMETA_THRESHOLD_BOUND_TESTS: list[StageTestCase] = [
    StageTestCase(
        "threshold_bound_explicit_low",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "widget", "path": "title"},
                    "count": {"type": "lowerBound", "threshold": 2000},
                }
            }
        ],
        expected={"count": {"lowerBound": [Gte(2000), Lte(LARGE_MATCH_COUNT)]}},
        msg="$searchMeta count.type lowerBound should return at least the threshold and at "
        "most the match count",
    ),
    StageTestCase(
        "threshold_bound_explicit_high",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "widget", "path": "title"},
                    "count": {"type": "lowerBound", "threshold": 5000},
                }
            }
        ],
        expected={"count": {"lowerBound": [Gte(5000), Lte(LARGE_MATCH_COUNT)]}},
        msg="$searchMeta count.type lowerBound should track a higher threshold and stay at "
        "most the match count",
    ),
    StageTestCase(
        "threshold_bound_default",
        pipeline=[{"$searchMeta": {"text": {"query": "widget", "path": "title"}}}],
        expected={"count": {"lowerBound": [Gte(1000), Lte(LARGE_MATCH_COUNT)]}},
        msg="$searchMeta should apply a default threshold of 1000 when count is omitted, so the "
        "result is at least 1000 and at most the match count",
    ),
    StageTestCase(
        "threshold_bound_total_exact_above_threshold",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "widget", "path": "title"},
                    "count": {"type": "total"},
                }
            }
        ],
        expected=[{"count": {"total": Int64(LARGE_MATCH_COUNT)}}],
        msg="$searchMeta count.type total should return the exact match count even when it far "
        "exceeds the threshold",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCHMETA_THRESHOLD_BOUND_TESTS))
def test_searchMeta_threshold_bounds(large_search_collection, test_case: StageTestCase):
    """Test $searchMeta count behavior above the threshold."""
    result = execute_command(
        large_search_collection,
        {
            "aggregate": large_search_collection.name,
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
