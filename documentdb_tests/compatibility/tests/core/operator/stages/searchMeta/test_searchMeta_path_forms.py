"""Tests for $searchMeta operator path-construction forms and multi-analyzer paths."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from bson import Int64
from pymongo.collection import Collection

from documentdb_tests.compatibility.tests.core.operator.stages.searchMeta.utils.searchMeta_common import (  # noqa: E501
    CollectionFixtureTestCase,
    build_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import UNKNOWN_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.requires(search=True)


@pytest.fixture(scope="module")
def multi_analyzer_collection(engine_client, worker_id) -> Iterator[Collection]:
    """Collection whose title field carries a keyword multi-analyzer beside the default."""
    with build_collection(
        engine_client,
        worker_id,
        f"{__name__}::multi_analyzer_collection",
        "searchmeta_multi_analyzer",
        [
            {"_id": 1, "title": "the quick brown fox"},
            {"_id": 2, "title": "quick red fox"},
            {"_id": 3, "title": "quick"},
            {"_id": 4, "title": "slow green turtle"},
        ],
        [
            {
                "name": "default",
                "definition": {
                    "mappings": {
                        "dynamic": False,
                        "fields": {
                            "title": {
                                "type": "string",
                                "analyzer": "lucene.standard",
                                "multi": {"kw": {"type": "string", "analyzer": "lucene.keyword"}},
                            }
                        },
                    }
                },
            }
        ],
    ) as coll:
        yield coll


# Property [Operator Path Forms]: the embedded operator path accepts an array of
# field paths, a {value} document, and a {wildcard} document, each resolving to
# its covered field(s) and returning the match count as metadata.
SEARCHMETA_PATH_FORM_TESTS: list[CollectionFixtureTestCase] = [
    CollectionFixtureTestCase(
        "path_array",
        collection_fixture="search_collection",
        pipeline=[{"$searchMeta": {"text": {"query": "quick", "path": ["title", "cat"]}}}],
        expected=[{"count": {"lowerBound": Int64(3)}}],
        msg="$searchMeta should accept an array of paths and return the match count across them",
    ),
    CollectionFixtureTestCase(
        "path_value_document",
        collection_fixture="search_collection",
        pipeline=[{"$searchMeta": {"text": {"query": "quick", "path": {"value": "title"}}}}],
        expected=[{"count": {"lowerBound": Int64(3)}}],
        msg="$searchMeta should accept a {value} path document and return the match count",
    ),
    CollectionFixtureTestCase(
        "path_wildcard_document",
        collection_fixture="search_collection",
        pipeline=[{"$searchMeta": {"text": {"query": "quick", "path": {"wildcard": "*"}}}}],
        expected=[{"count": {"lowerBound": Int64(3)}}],
        msg="$searchMeta should accept a {wildcard} path document spanning the covered fields",
    ),
    CollectionFixtureTestCase(
        "path_multi_absent_analyzer",
        collection_fixture="search_collection",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": {"value": "title", "multi": "nope"}}
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject a {value, multi} path referencing an undefined "
        "multi-analyzer",
    ),
]

# Property [Operator Path Multi-Analyzer Selection]: a {value, multi} path
# resolves through the named alternate analyzer, so its match count differs from
# the field's default analyzer for the same query.
SEARCHMETA_PATH_MULTI_ANALYZER_TESTS: list[CollectionFixtureTestCase] = [
    CollectionFixtureTestCase(
        "path_default_analyzer",
        collection_fixture="multi_analyzer_collection",
        pipeline=[{"$searchMeta": {"text": {"query": "quick", "path": "title"}}}],
        expected=[{"count": {"lowerBound": Int64(3)}}],
        msg="$searchMeta should count every standard-analyzed title containing the term",
    ),
    CollectionFixtureTestCase(
        "path_multi_keyword_analyzer",
        collection_fixture="multi_analyzer_collection",
        pipeline=[
            {"$searchMeta": {"text": {"query": "quick", "path": {"value": "title", "multi": "kw"}}}}
        ],
        expected=[{"count": {"lowerBound": Int64(1)}}],
        msg="$searchMeta should count only the keyword-analyzed title equal to the term when the "
        "multi keyword analyzer is selected",
    ),
]

SEARCHMETA_PATH_TESTS: list[CollectionFixtureTestCase] = (
    SEARCHMETA_PATH_FORM_TESTS + SEARCHMETA_PATH_MULTI_ANALYZER_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCHMETA_PATH_TESTS))
def test_searchMeta_path_forms(engine_client, request, test_case: CollectionFixtureTestCase):
    """Test $searchMeta operator path forms and multi-analyzer path selection."""
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
