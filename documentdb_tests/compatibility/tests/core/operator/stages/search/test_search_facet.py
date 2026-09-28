"""Tests for the $search facet collector."""

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
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import (
    Contains,
    Len,
)

pytestmark = pytest.mark.requires(search=True)


_FACET_DOCS = [
    {"_id": 1, "title": "the quick brown fox", "cat": "a"},
    {"_id": 2, "title": "slow green turtle", "cat": "b"},
    {"_id": 3, "title": "a quick quick rabbit", "cat": "a"},
]

_FACET_INDEX_DEFINITION = {
    "mappings": {
        "dynamic": False,
        "fields": {
            "title": {"type": "string"},
            "cat": {"type": "token"},
        },
    }
}


@pytest.fixture(scope="module")
def facet_collection(engine_client, worker_id):
    """A module-scoped collection with a static search index mapping a
    text-analyzed field driving the inner operator and a token-mapped field that
    is facetable, shared read-only across the facet cases so the index is built
    and polled once."""
    db_name = fixtures.generate_database_name("stages_search_facet", worker_id)
    fixtures.cleanup_database(engine_client, db_name)
    db = engine_client[db_name]
    coll = db["facet"]
    coll.insert_many(_FACET_DOCS)
    create_search_index(coll, _FACET_INDEX_DEFINITION)
    yield coll
    fixtures.cleanup_database(engine_client, db_name)


# Property [Facet Collector Recognition]: the facet collector is recognized in the
# operator slot and executed, returning the documents selected by its inner search
# operator.
SEARCH_FACET_RECOGNITION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "facet_collector_executes",
        pipeline=[
            {
                "$search": {
                    "facet": {
                        "operator": {"text": {"query": "quick", "path": "title"}},
                        "facets": {"catF": {"type": "string", "path": "cat"}},
                    }
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(2), Contains("_id", 1), Contains("_id", 3)]},
        msg="$search should recognize the facet collector and execute it, returning the "
        "documents selected by its inner operator",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_FACET_RECOGNITION_TESTS))
def test_search_facet_recognition(facet_collection, test_case: StageTestCase):
    """Test $search recognizes and executes the facet collector."""
    result = execute_command(
        facet_collection,
        {"aggregate": facet_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(
        result,
        expected=test_case.expected,
        msg=test_case.msg,
        raw_res=True,
    )
