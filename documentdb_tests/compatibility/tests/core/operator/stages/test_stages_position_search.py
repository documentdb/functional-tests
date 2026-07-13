"""Tests for $search pipeline position constraints and stage combinations."""

from __future__ import annotations

import time

import pytest
from pymongo.operations import SearchIndexModel

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework import fixtures
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    FACET_PIPELINE_INVALID_STAGE_ERROR,
    NOT_FIRST_STAGE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.requires(search=True)

_POSITION_DOCS = [
    {"_id": 1, "title": "quick brown fox"},
    {"_id": 2, "title": "lazy sleeping dog"},
    {"_id": 3, "title": "green sea turtle"},
]


@pytest.fixture(scope="module")
def position_collection(engine_client, worker_id):
    """A module-scoped collection with a ready dynamic search index, shared
    read-only across the placement cases so the index is built and polled once
    rather than per test. The collection carries a fixed name so the
    $unionWith/$lookup sub-pipeline cases can reference it as their source."""
    db_name = fixtures.generate_database_name("stages_search_position", worker_id)
    fixtures.cleanup_database(engine_client, db_name)
    db = engine_client[db_name]
    coll = db["position"]
    coll.insert_many(_POSITION_DOCS)
    coll.create_search_index(
        SearchIndexModel(definition={"mappings": {"dynamic": True}}, name="default")
    )
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        indexes = list(coll.list_search_indexes("default"))
        if indexes and indexes[0].get("queryable"):
            break
        time.sleep(1)
    else:
        raise RuntimeError("search index 'default' did not become queryable within 120s")
    yield coll
    fixtures.cleanup_database(engine_client, db_name)


# Property [Sub-pipeline Placement]: the first-stage-only rule is enforced per
# pipeline, so $search is allowed as the first stage of a $unionWith or $lookup
# sub-pipeline and may be followed by other stages within that sub-pipeline.
SEARCH_SUBPIPELINE_PLACEMENT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "placement_unionwith_subpipeline",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}}},
            {"$project": {"_id": 1}},
            {
                "$unionWith": {
                    "coll": "position",
                    "pipeline": [
                        {"$search": {"text": {"query": "turtle", "path": "title"}}},
                        {"$project": {"_id": 1}},
                    ],
                }
            },
        ],
        expected=[{"_id": 1}, {"_id": 3}],
        msg="$search should be allowed as the first stage of a $unionWith sub-pipeline, "
        "unioning the sub-pipeline matches with the main-pipeline matches",
    ),
    StageTestCase(
        "placement_lookup_subpipeline",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}}},
            {"$project": {"_id": 1}},
            {
                "$lookup": {
                    "from": "position",
                    "pipeline": [
                        {"$search": {"text": {"query": "turtle", "path": "title"}}},
                        {"$project": {"_id": 1}},
                    ],
                    "as": "joined",
                }
            },
        ],
        expected=[{"_id": 1, "joined": [{"_id": 3}]}],
        msg="$search should be allowed as the first stage of a $lookup sub-pipeline and "
        "attach the sub-pipeline matches to each joined row",
    ),
    StageTestCase(
        "placement_subpipeline_trailing_stages",
        pipeline=[
            {"$search": {"text": {"query": "dog", "path": "title"}}},
            {"$project": {"_id": 1}},
            {
                "$unionWith": {
                    "coll": "position",
                    "pipeline": [
                        {"$search": {"text": {"query": "quick", "path": "title"}}},
                        {"$match": {"_id": {"$gt": 0}}},
                        {"$project": {"_id": 1}},
                    ],
                }
            },
        ],
        expected=[{"_id": 2}, {"_id": 1}],
        msg="$search as the first stage of a sub-pipeline should permit trailing stages "
        "($match, $project) after it within that sub-pipeline",
    ),
]

# Property [Stage Placement Errors]: $search anywhere other than the first stage
# of its pipeline is rejected with NOT_FIRST_STAGE_ERROR, and $search nested
# inside a $facet stage is rejected with FACET_PIPELINE_INVALID_STAGE_ERROR.
SEARCH_STAGE_PLACEMENT_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "not_first_after_match",
        pipeline=[
            {"$match": {"_id": 1}},
            {"$search": {"text": {"query": "quick", "path": "title"}}},
        ],
        error_code=NOT_FIRST_STAGE_ERROR,
        msg="$search should be rejected when it follows another stage in the pipeline",
    ),
    StageTestCase(
        "not_first_second_search",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}}},
            {"$search": {"text": {"query": "quick", "path": "title"}}},
        ],
        error_code=NOT_FIRST_STAGE_ERROR,
        msg="$search should be rejected when a second $search follows the first stage",
    ),
    StageTestCase(
        "in_facet",
        pipeline=[
            {"$facet": {"results": [{"$search": {"text": {"query": "quick", "path": "title"}}}]}}
        ],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$search should be rejected when nested inside a $facet stage",
    ),
]

SEARCH_POSITION_TESTS: list[StageTestCase] = (
    SEARCH_SUBPIPELINE_PLACEMENT_TESTS + SEARCH_STAGE_PLACEMENT_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_POSITION_TESTS))
def test_search_position(position_collection, test_case: StageTestCase):
    """Test $search pipeline position constraints, sub-pipeline combinations, and rejections."""
    result = execute_command(
        position_collection,
        {
            "aggregate": position_collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        ignore_doc_order=True,
    )
