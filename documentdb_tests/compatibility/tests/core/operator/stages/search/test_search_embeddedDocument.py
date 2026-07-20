"""Tests for the $search embeddedDocument operator."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.search.utils.search_common import (
    create_search_index,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework import fixtures
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import UNKNOWN_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Contains, Len

pytestmark = pytest.mark.requires(search=True)

_EMBEDDED_DOCS = [
    {"_id": 1, "items": [{"name": "quick fox"}, {"name": "slow dog"}]},
    {"_id": 2, "items": [{"name": "quick cat"}]},
    {"_id": 3, "items": [{"name": "lazy bird"}]},
]

_EMBEDDED_INDEX_DEFINITION = {
    "mappings": {
        "dynamic": False,
        "fields": {"items": {"type": "embeddedDocuments", "dynamic": True}},
    }
}


@pytest.fixture(scope="module")
def embedded_collection(engine_client, worker_id):
    """A module-scoped collection whose items array is indexed as embeddedDocuments,
    so the embeddedDocument operator can match embedded fields independently."""
    db_name = fixtures.generate_database_name("stages_search_embedded", worker_id)
    fixtures.cleanup_database(engine_client, db_name)
    db = engine_client[db_name]
    coll = db["embedded"]
    coll.insert_many(_EMBEDDED_DOCS)
    create_search_index(coll, _EMBEDDED_INDEX_DEFINITION)
    yield coll
    fixtures.cleanup_database(engine_client, db_name)


# Property [embeddedDocument Matching]: the operator runs its inner operator
# against the embedded documents on the indexed path and returns the parent
# documents that contain a matching embedded document.
SEARCH_EMBEDDED_MATCHING_TESTS: list[StageTestCase] = [
    StageTestCase(
        "embedded_matches_parents",
        pipeline=[
            {
                "$search": {
                    "embeddedDocument": {
                        "path": "items",
                        "operator": {"text": {"query": "quick", "path": "items.name"}},
                    }
                }
            }
        ],
        expected={"cursor.firstBatch": [Len(2), Contains("_id", 1), Contains("_id", 2)]},
        msg="$search embeddedDocument should return parents whose embedded document matches the "
        "inner operator",
    ),
    StageTestCase(
        "embedded_matches_single_parent",
        pipeline=[
            {
                "$search": {
                    "embeddedDocument": {
                        "path": "items",
                        "operator": {"text": {"query": "lazy", "path": "items.name"}},
                    }
                }
            }
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 3)]},
        msg="$search embeddedDocument should return only the parent whose embedded document "
        "matches",
    ),
]

# Property [embeddedDocument Validation]: the operator requires both a path and
# an inner operator.
SEARCH_EMBEDDED_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "embedded_missing_operator",
        pipeline=[{"$search": {"embeddedDocument": {"path": "items"}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search embeddedDocument should reject a spec missing the required operator",
    ),
    StageTestCase(
        "embedded_missing_path",
        pipeline=[
            {
                "$search": {
                    "embeddedDocument": {
                        "operator": {"text": {"query": "quick", "path": "items.name"}}
                    }
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search embeddedDocument should reject a spec missing the required path",
    ),
]

SEARCH_EMBEDDED_TESTS = SEARCH_EMBEDDED_MATCHING_TESTS + SEARCH_EMBEDDED_ERROR_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_EMBEDDED_TESTS))
def test_search_embeddedDocument_cases(embedded_collection, test_case: StageTestCase):
    """Test $search embeddedDocument matching and validation."""
    result = execute_command(
        embedded_collection,
        {"aggregate": embedded_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        raw_res=True,
    )
