"""Tests for $searchMeta on empty, unindexed, and nonexistent collections."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from pymongo.collection import Collection

from documentdb_tests.compatibility.tests.core.operator.stages.searchMeta.utils.searchMeta_common import (  # noqa: E501
    SEARCH_DOCS,
    CollectionFixtureTestCase,
    build_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import INT64_ZERO

pytestmark = pytest.mark.requires(search=True)


@pytest.fixture(scope="module")
def empty_search_collection(engine_client, worker_id) -> Iterator[Collection]:
    """Indexed but empty collection."""
    with build_collection(
        engine_client,
        worker_id,
        f"{__name__}::empty_search_collection",
        "searchmeta_empty",
        [],
        [{"name": "default", "definition": {"mappings": {"dynamic": True}}}],
    ) as coll:
        yield coll


# Property [Empty Collection Count]: on an indexed but empty collection,
# $searchMeta returns a zero count respecting the requested count.type,
# defaulting to lowerBound.
SEARCHMETA_EMPTY_COLLECTION_TESTS: list[CollectionFixtureTestCase] = [
    CollectionFixtureTestCase(
        "empty_default",
        collection_fixture="empty_search_collection",
        pipeline=[{"$searchMeta": {"text": {"query": "quick", "path": "title"}}}],
        expected=[{"count": {"lowerBound": INT64_ZERO}}],
        msg="$searchMeta should default to a lower-bound zero count on an indexed empty "
        "collection",
    ),
    CollectionFixtureTestCase(
        "empty_total",
        collection_fixture="empty_search_collection",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "count": {"type": "total"},
                }
            }
        ],
        expected=[{"count": {"total": INT64_ZERO}}],
        msg="$searchMeta should return a total-zero count on an indexed empty collection when "
        "count.type is total",
    ),
    CollectionFixtureTestCase(
        "empty_lower_bound",
        collection_fixture="empty_search_collection",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "count": {"type": "lowerBound"},
                }
            }
        ],
        expected=[{"count": {"lowerBound": INT64_ZERO}}],
        msg="$searchMeta should return a lower-bound-zero count on an indexed empty collection "
        "when count.type is lowerBound",
    ),
]


@pytest.fixture(scope="module")
def no_index_collection(engine_client, worker_id) -> Iterator[Collection]:
    """Populated collection with no search index."""
    with build_collection(
        engine_client,
        worker_id,
        f"{__name__}::no_index_collection",
        "searchmeta_no_index",
        SEARCH_DOCS,
        None,
    ) as coll:
        yield coll


# Property [No-Index Behavior]: on a populated collection with no search index,
# $searchMeta succeeds and returns a total-zero count that ignores the requested
# count.type, and a facet collector omits the facet field.
SEARCHMETA_NO_INDEX_TESTS: list[CollectionFixtureTestCase] = [
    CollectionFixtureTestCase(
        "no_index_default",
        collection_fixture="no_index_collection",
        pipeline=[{"$searchMeta": {"text": {"query": "quick", "path": "title"}}}],
        expected=[{"count": {"total": INT64_ZERO}}],
        msg="$searchMeta should return a total-zero count without error on a populated "
        "collection that has no search index",
    ),
    CollectionFixtureTestCase(
        "no_index_lower_bound",
        collection_fixture="no_index_collection",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "count": {"type": "lowerBound"},
                }
            }
        ],
        expected=[{"count": {"total": INT64_ZERO}}],
        msg="$searchMeta should ignore a lowerBound count.type and still key the no-index "
        "count as total",
    ),
    CollectionFixtureTestCase(
        "no_index_facet_omits_facet",
        collection_fixture="no_index_collection",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {
                        "facets": {"nf": {"type": "number", "path": "n", "boundaries": [0, 25]}}
                    }
                }
            }
        ],
        expected=[{"count": {"total": INT64_ZERO}}],
        msg="$searchMeta should omit the facet field and return a total-zero count for a facet "
        "collector on a collection that has no search index",
    ),
]


@pytest.fixture(scope="module")
def nonexistent_collection(engine_client, worker_id) -> Iterator[Collection]:
    """Handle to a collection that is never created."""
    with build_collection(
        engine_client,
        worker_id,
        f"{__name__}::nonexistent_collection",
        "searchmeta_nonexistent",
        None,
        None,
    ) as coll:
        yield coll


# Property [Nonexistent Collection]: on a nonexistent collection, $searchMeta
# returns an empty result with no metadata document, for both an operator and a
# facet collector.
SEARCHMETA_NONEXISTENT_COLLECTION_TESTS: list[CollectionFixtureTestCase] = [
    CollectionFixtureTestCase(
        "nonexistent_operator",
        collection_fixture="nonexistent_collection",
        pipeline=[{"$searchMeta": {"text": {"query": "quick", "path": "title"}}}],
        expected=[],
        msg="$searchMeta should return an empty result with no metadata document for an "
        "operator on a nonexistent collection",
    ),
    CollectionFixtureTestCase(
        "nonexistent_facet",
        collection_fixture="nonexistent_collection",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {
                        "facets": {"nf": {"type": "number", "path": "n", "boundaries": [0, 25]}}
                    }
                }
            }
        ],
        expected=[],
        msg="$searchMeta should return an empty result with no metadata document for a facet "
        "collector on a nonexistent collection",
    ),
]

# All collection-state cases share one execution path; the state is carried as
# data via the fixture each case names.
SEARCHMETA_COLLECTION_STATE_TESTS: list[CollectionFixtureTestCase] = (
    SEARCHMETA_EMPTY_COLLECTION_TESTS
    + SEARCHMETA_NO_INDEX_TESTS
    + SEARCHMETA_NONEXISTENT_COLLECTION_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCHMETA_COLLECTION_STATE_TESTS))
def test_searchMeta_collection_state(engine_client, request, test_case: CollectionFixtureTestCase):
    """Test $searchMeta across empty, no-index, and nonexistent collection states."""
    collection = request.getfixturevalue(test_case.collection_fixture)
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
