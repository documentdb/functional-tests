"""Tests for $searchMeta pipeline position constraints and stage combinations."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from bson import Int64
from pymongo.collection import Collection

from documentdb_tests.compatibility.tests.core.operator.stages.searchMeta.utils.searchMeta_common import (  # noqa: E501
    SEARCH_DOCS,
    CollectionFixtureTestCase,
    build_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    FACET_PIPELINE_INVALID_STAGE_ERROR,
    NOT_FIRST_STAGE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.requires(search=True)


@pytest.fixture(scope="module")
def noindex_collection(engine_client, worker_id) -> Iterator[Collection]:
    """Provide a populated collection that has no search index.

    Position and context errors are parse-time rejections, so this collection
    deliberately omits the search index to confirm the position check fires
    regardless of index state and to let sub-pipeline cases self-reference an
    existing collection.
    """
    with build_collection(
        engine_client,
        worker_id,
        f"{__name__}::noindex_collection",
        "searchmeta_noindex",
        SEARCH_DOCS,
        None,
    ) as coll:
        yield coll


@pytest.fixture(scope="module")
def search_collection(engine_client, worker_id) -> Iterator[Collection]:
    """Provide a populated collection with a READY dynamic search index.

    Building a search index is an expensive asynchronous operation, so the
    collection is created once per module and shared across the placement cases,
    which only read from it.
    """
    with build_collection(
        engine_client,
        worker_id,
        f"{__name__}::search_collection",
        "searchmeta",
        SEARCH_DOCS,
        [{"name": "default", "definition": {"mappings": {"dynamic": True}}}],
    ) as coll:
        yield coll


# Property [Stage Position and Context]: a first-position $searchMeta permits a
# single benign trailing stage with the one metadata document passing through,
# and $searchMeta is allowed as the first stage of a $unionWith or $lookup
# sub-pipeline.
SEARCHMETA_PLACEMENT_TESTS: list[CollectionFixtureTestCase] = [
    CollectionFixtureTestCase(
        "placement_trailing_limit",
        collection_fixture="search_collection",
        pipeline=[
            {"$searchMeta": {"text": {"query": "quick", "path": "title"}}},
            {"$limit": 1},
        ],
        expected=[{"count": {"lowerBound": Int64(3)}}],
        msg="$searchMeta should permit a single trailing $limit and pass the one metadata "
        "document through",
    ),
    CollectionFixtureTestCase(
        "placement_unionwith_subpipeline",
        collection_fixture="search_collection",
        pipeline=[
            {"$searchMeta": {"text": {"query": "quick", "path": "title"}}},
            {
                "$unionWith": {
                    "coll": "searchmeta",
                    "pipeline": [{"$searchMeta": {"text": {"query": "quick", "path": "title"}}}],
                }
            },
        ],
        expected=[
            {"count": {"lowerBound": Int64(3)}},
            {"count": {"lowerBound": Int64(3)}},
        ],
        msg="$searchMeta should be allowed as the first stage of a $unionWith sub-pipeline "
        "alongside a first-position main $searchMeta",
    ),
    CollectionFixtureTestCase(
        "placement_lookup_subpipeline",
        collection_fixture="search_collection",
        pipeline=[
            {"$searchMeta": {"text": {"query": "quick", "path": "title"}}},
            {
                "$lookup": {
                    "from": "searchmeta",
                    "pipeline": [{"$searchMeta": {"text": {"query": "quick", "path": "title"}}}],
                    "as": "meta",
                }
            },
        ],
        expected=[
            {
                "count": {"lowerBound": Int64(3)},
                "meta": [{"count": {"lowerBound": Int64(3)}}],
            }
        ],
        msg="$searchMeta should be allowed as the first stage of a $lookup sub-pipeline and "
        "return the metadata document per joined row",
    ),
]

# Property [Stage Position and Context Errors]: $searchMeta is rejected with
# NOT_FIRST_STAGE_ERROR whenever it is not the first stage of its main pipeline
# or of a $unionWith/$lookup sub-pipeline, and with
# FACET_PIPELINE_INVALID_STAGE_ERROR inside a $facet sub-pipeline; the position
# check fires regardless of index state.
SEARCHMETA_POSITION_ERROR_TESTS: list[CollectionFixtureTestCase] = [
    CollectionFixtureTestCase(
        "error_after_match",
        collection_fixture="noindex_collection",
        pipeline=[
            {"$match": {"n": {"$gt": 0}}},
            {"$searchMeta": {"text": {"query": "quick", "path": "title"}}},
        ],
        error_code=NOT_FIRST_STAGE_ERROR,
        msg="$searchMeta after a $match should be rejected as not the first stage",
    ),
    CollectionFixtureTestCase(
        "error_after_project",
        collection_fixture="noindex_collection",
        pipeline=[
            {"$project": {"title": 1}},
            {"$searchMeta": {"text": {"query": "quick", "path": "title"}}},
        ],
        error_code=NOT_FIRST_STAGE_ERROR,
        msg="$searchMeta after a $project should be rejected as not the first stage",
    ),
    CollectionFixtureTestCase(
        "error_after_limit",
        collection_fixture="noindex_collection",
        pipeline=[
            {"$limit": 1},
            {"$searchMeta": {"text": {"query": "quick", "path": "title"}}},
        ],
        error_code=NOT_FIRST_STAGE_ERROR,
        msg="$searchMeta after a $limit should be rejected as not the first stage",
    ),
    CollectionFixtureTestCase(
        "error_after_addfields",
        collection_fixture="noindex_collection",
        pipeline=[
            {"$addFields": {"m": 1}},
            {"$searchMeta": {"text": {"query": "quick", "path": "title"}}},
        ],
        error_code=NOT_FIRST_STAGE_ERROR,
        msg="$searchMeta after an $addFields should be rejected as not the first stage",
    ),
    CollectionFixtureTestCase(
        "error_after_empty_match",
        collection_fixture="noindex_collection",
        pipeline=[
            {"$match": {}},
            {"$searchMeta": {"text": {"query": "quick", "path": "title"}}},
        ],
        error_code=NOT_FIRST_STAGE_ERROR,
        msg="$searchMeta after an empty $match should still be rejected as not the first "
        "stage because the empty $match is not optimized away",
    ),
    CollectionFixtureTestCase(
        "error_second_searchMeta_adjacent",
        collection_fixture="noindex_collection",
        pipeline=[
            {"$searchMeta": {"text": {"query": "quick", "path": "title"}}},
            {"$searchMeta": {"text": {"query": "quick", "path": "title"}}},
        ],
        error_code=NOT_FIRST_STAGE_ERROR,
        msg="A second adjacent $searchMeta should be rejected as not the first stage",
    ),
    CollectionFixtureTestCase(
        "error_second_searchMeta_separated",
        collection_fixture="noindex_collection",
        pipeline=[
            {"$searchMeta": {"text": {"query": "quick", "path": "title"}}},
            {"$limit": 1},
            {"$searchMeta": {"text": {"query": "quick", "path": "title"}}},
        ],
        error_code=NOT_FIRST_STAGE_ERROR,
        msg="A second $searchMeta separated from the first should be rejected as not the "
        "first stage",
    ),
    CollectionFixtureTestCase(
        "error_inside_facet_first",
        collection_fixture="noindex_collection",
        pipeline=[
            {
                "$facet": {
                    "meta": [
                        {"$searchMeta": {"text": {"query": "quick", "path": "title"}}},
                    ],
                }
            },
        ],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$searchMeta as the first stage of a $facet sub-pipeline should be rejected",
    ),
    CollectionFixtureTestCase(
        "error_inside_facet_not_first",
        collection_fixture="noindex_collection",
        pipeline=[
            {
                "$facet": {
                    "meta": [
                        {"$limit": 1},
                        {"$searchMeta": {"text": {"query": "quick", "path": "title"}}},
                    ],
                }
            },
        ],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$searchMeta inside a $facet sub-pipeline should be rejected regardless of its "
        "position within the sub-pipeline",
    ),
    CollectionFixtureTestCase(
        "error_unionwith_subpipeline_not_first",
        collection_fixture="noindex_collection",
        pipeline=[
            {"$searchMeta": {"text": {"query": "quick", "path": "title"}}},
            {
                "$unionWith": {
                    "coll": "searchmeta_noindex",
                    "pipeline": [
                        {"$match": {}},
                        {"$searchMeta": {"text": {"query": "quick", "path": "title"}}},
                    ],
                }
            },
        ],
        error_code=NOT_FIRST_STAGE_ERROR,
        msg="$searchMeta that is not first inside a $unionWith sub-pipeline should be "
        "rejected as not the first stage",
    ),
    CollectionFixtureTestCase(
        "error_lookup_subpipeline_not_first",
        collection_fixture="noindex_collection",
        pipeline=[
            {"$searchMeta": {"text": {"query": "quick", "path": "title"}}},
            {
                "$lookup": {
                    "from": "searchmeta_noindex",
                    "pipeline": [
                        {"$match": {}},
                        {"$searchMeta": {"text": {"query": "quick", "path": "title"}}},
                    ],
                    "as": "meta",
                }
            },
        ],
        error_code=NOT_FIRST_STAGE_ERROR,
        msg="$searchMeta that is not first inside a $lookup sub-pipeline should be "
        "rejected as not the first stage",
    ),
]

SEARCHMETA_POSITION_TESTS: list[CollectionFixtureTestCase] = (
    SEARCHMETA_PLACEMENT_TESTS + SEARCHMETA_POSITION_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCHMETA_POSITION_TESTS))
def test_searchMeta_position(engine_client, request, test_case: CollectionFixtureTestCase):
    """Test $searchMeta pipeline position constraints, combinations, and rejections."""
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
