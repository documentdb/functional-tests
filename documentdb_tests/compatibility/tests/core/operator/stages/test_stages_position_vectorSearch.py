"""Tests for $vectorSearch pipeline position constraints and stage placement."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.stages.vectorSearch.utils.vectorSearch_common import (  # noqa: E501
    wait_for_search_index_ready,
)
from documentdb_tests.framework import fixtures
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    FACET_PIPELINE_INVALID_STAGE_ERROR,
    LOOKUP_SUB_PIPELINE_NOT_ALLOWED_ERROR,
    NOT_FIRST_STAGE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DOUBLE_ZERO

pytestmark = pytest.mark.requires(search=True)

_POSITION_CORPUS = [
    {"_id": 1, "vec": [1.0, DOUBLE_ZERO, DOUBLE_ZERO]},
    {"_id": 2, "vec": [0.8, 0.2, DOUBLE_ZERO]},
    {"_id": 3, "vec": [0.6, 0.4, DOUBLE_ZERO]},
]


@pytest.fixture(scope="module")
def position_collection(engine_client, worker_id):
    """A module-scoped collection with a READY cosine vectorSearch index, shared
    read-only across the placement cases so the index is built and polled once
    rather than per test. The collection carries a fixed name so the
    $unionWith/$lookup sub-pipeline cases can reference it as their source."""
    db_name = fixtures.generate_database_name("stages_vectorSearch_position", worker_id)
    fixtures.cleanup_database(engine_client, db_name)
    db = engine_client[db_name]
    coll = db["position"]
    coll.insert_many([dict(doc) for doc in _POSITION_CORPUS])
    db.command(
        {
            "createSearchIndexes": coll.name,
            "indexes": [
                {
                    "name": "vs_position_index",
                    "type": "vectorSearch",
                    "definition": {
                        "fields": [
                            {
                                "type": "vector",
                                "path": "vec",
                                "numDimensions": 3,
                                "similarity": "cosine",
                            },
                        ]
                    },
                }
            ],
        }
    )
    wait_for_search_index_ready(coll)
    yield coll
    fixtures.cleanup_database(engine_client, db_name)


# Property [Stage Placement Allowed]: $vectorSearch succeeds as the first stage
# of the main pipeline and as the first stage of a $unionWith sub-pipeline.
VECTORSEARCH_PLACEMENT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "first_stage_main_pipeline",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_position_index",
                    "path": "vec",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 3,
                }
            },
            {"$project": {"_id": 1}},
        ],
        expected=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        msg="$vectorSearch should succeed as the first stage of the main pipeline",
    ),
    StageTestCase(
        "first_stage_union_with_sub_pipeline",
        pipeline=[
            {"$match": {"_id": {"$lt": 0}}},
            {
                "$unionWith": {
                    "coll": "position",
                    "pipeline": [
                        {
                            "$vectorSearch": {
                                "index": "vs_position_index",
                                "path": "vec",
                                "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                                "numCandidates": 10,
                                "limit": 3,
                            }
                        },
                        {"$project": {"_id": 1}},
                    ],
                }
            },
        ],
        expected=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        msg="$vectorSearch should succeed as the first stage of a $unionWith sub-pipeline",
    ),
]

# Property [Stage Placement Errors]: $vectorSearch is rejected when it is not the
# first stage of a pipeline, when nested in a $facet sub-pipeline, and when
# nested in a $lookup sub-pipeline.
VECTORSEARCH_PLACEMENT_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "not_first_stage",
        pipeline=[
            {"$match": {"_id": 1}},
            {
                "$vectorSearch": {
                    "index": "vs_position_index",
                    "path": "vec",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 3,
                }
            },
        ],
        error_code=NOT_FIRST_STAGE_ERROR,
        msg="$vectorSearch should be rejected when it is not the first stage",
    ),
    StageTestCase(
        "inside_facet",
        pipeline=[
            {
                "$facet": {
                    "results": [
                        {
                            "$vectorSearch": {
                                "index": "vs_position_index",
                                "path": "vec",
                                "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                                "numCandidates": 10,
                                "limit": 3,
                            }
                        },
                    ],
                }
            },
        ],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$vectorSearch should be rejected inside a $facet sub-pipeline",
    ),
    StageTestCase(
        "inside_lookup_sub_pipeline",
        pipeline=[
            {
                "$lookup": {
                    "from": "position",
                    "pipeline": [
                        {
                            "$vectorSearch": {
                                "index": "vs_position_index",
                                "path": "vec",
                                "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                                "numCandidates": 10,
                                "limit": 3,
                            }
                        },
                    ],
                    "as": "matches",
                }
            },
        ],
        error_code=LOOKUP_SUB_PIPELINE_NOT_ALLOWED_ERROR,
        msg="$vectorSearch should be rejected inside a $lookup sub-pipeline",
    ),
]

VECTORSEARCH_POSITION_TESTS: list[StageTestCase] = (
    VECTORSEARCH_PLACEMENT_TESTS + VECTORSEARCH_PLACEMENT_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(VECTORSEARCH_POSITION_TESTS))
def test_vectorSearch_position(position_collection, test_case: StageTestCase):
    """Test $vectorSearch pipeline position constraints and rejections."""
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
    )
