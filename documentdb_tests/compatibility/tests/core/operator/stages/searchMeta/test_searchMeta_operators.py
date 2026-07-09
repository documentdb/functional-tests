"""Tests for $searchMeta recognized-operator compatibility (acceptance matrix)."""

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
from documentdb_tests.framework.test_constants import DOUBLE_ZERO

pytestmark = pytest.mark.requires(search=True)


@pytest.fixture(scope="module")
def autocomplete_collection(engine_client, worker_id) -> Iterator[Collection]:
    """Collection whose title field is statically indexed as an autocomplete type."""
    with build_collection(
        engine_client,
        worker_id,
        f"{__name__}::autocomplete_collection",
        "searchmeta_autocomplete",
        [
            {"_id": 1, "title": "quick brown fox"},
            {"_id": 2, "title": "quiet night"},
            {"_id": 3, "title": "quick red fox"},
            {"_id": 4, "title": "lazy dog"},
        ],
        [
            {
                "name": "default",
                "definition": {
                    "mappings": {"dynamic": False, "fields": {"title": {"type": "autocomplete"}}}
                },
            }
        ],
    ) as coll:
        yield coll


@pytest.fixture(scope="module")
def geo_collection(engine_client, worker_id) -> Iterator[Collection]:
    """Collection whose loc field is statically indexed as a geo type with shapes."""
    with build_collection(
        engine_client,
        worker_id,
        f"{__name__}::geo_collection",
        "searchmeta_geo",
        [
            {"_id": 1, "loc": {"type": "Point", "coordinates": [DOUBLE_ZERO, DOUBLE_ZERO]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [10.0, 10.0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [0.1, 0.1]}},
        ],
        [
            {
                "name": "default",
                "definition": {
                    "mappings": {
                        "dynamic": False,
                        "fields": {"loc": {"type": "geo", "indexShapes": True}},
                    }
                },
            }
        ],
    ) as coll:
        yield coll


@pytest.fixture(scope="module")
def embedded_collection(engine_client, worker_id) -> Iterator[Collection]:
    """Collection whose items array is statically indexed as embeddedDocuments."""
    with build_collection(
        engine_client,
        worker_id,
        f"{__name__}::embedded_collection",
        "searchmeta_embedded",
        [
            {"_id": 1, "items": [{"name": "quick fox"}, {"name": "slow dog"}]},
            {"_id": 2, "items": [{"name": "quick cat"}]},
            {"_id": 3, "items": [{"name": "lazy bird"}]},
        ],
        [
            {
                "name": "default",
                "definition": {
                    "mappings": {
                        "dynamic": False,
                        "fields": {"items": {"type": "embeddedDocuments", "dynamic": True}},
                    }
                },
            }
        ],
    ) as coll:
        yield coll


# Property [Operator Acceptance On A Dynamic Mapping]: each recognized search
# operator that a dynamic mapping can serve is accepted and returns its match
# count as the operator-independent {count:{lowerBound:n}} metadata envelope.
SEARCHMETA_DYNAMIC_OPERATOR_TESTS: list[CollectionFixtureTestCase] = [
    CollectionFixtureTestCase(
        f"operator_{label}",
        collection_fixture="search_collection",
        pipeline=[{"$searchMeta": {op: spec}}],
        expected=[{"count": {"lowerBound": Int64(count)}}],
        msg=f"$searchMeta should accept a {label} operator and return its match count as metadata",
    )
    for label, op, spec, count in [
        ("text", "text", {"query": "quick", "path": "title"}, 3),
        ("phrase", "phrase", {"query": "brown fox", "path": "title"}, 1),
        (
            "wildcard",
            "wildcard",
            {"query": "quick*", "path": "title", "allowAnalyzedField": True},
            3,
        ),
        ("exists", "exists", {"path": "title"}, 5),
        ("equals", "equals", {"path": "n", "value": 5}, 1),
        ("range", "range", {"path": "n", "gte": 5, "lte": 15}, 3),
        ("near", "near", {"path": "n", "origin": 10, "pivot": 5}, 5),
        (
            "compound",
            "compound",
            {"must": [{"text": {"query": "quick", "path": "title"}}]},
            3,
        ),
        ("in", "in", {"path": "n", "value": [5, 10]}, 2),
        (
            "regex",
            "regex",
            {"query": "quick.*", "path": "title", "allowAnalyzedField": True},
            3,
        ),
        ("queryString", "queryString", {"defaultPath": "title", "query": "quick"}, 3),
        ("moreLikeThis", "moreLikeThis", {"like": {"title": "quick brown fox"}}, 4),
        ("term", "term", {"query": "quick", "path": "title"}, 3),
        (
            "span",
            "span",
            {
                "first": {
                    "operator": {"term": {"query": "quick", "path": "title"}},
                    "endPositionLte": 5,
                }
            },
            3,
        ),
    ]
]

# Property [Operator Acceptance With A Required Index Type]: operators that
# depend on a specific field index type (autocomplete, geo, embeddedDocuments)
# are accepted and return their match count once the field is indexed for them.
SEARCHMETA_REQUIRED_INDEX_OPERATOR_TESTS: list[CollectionFixtureTestCase] = [
    CollectionFixtureTestCase(
        "operator_autocomplete",
        collection_fixture="autocomplete_collection",
        pipeline=[{"$searchMeta": {"autocomplete": {"query": "qui", "path": "title"}}}],
        expected=[{"count": {"lowerBound": Int64(3)}}],
        msg="$searchMeta should accept an autocomplete operator against an autocomplete-indexed "
        "field and return its match count",
    ),
    CollectionFixtureTestCase(
        "operator_geoWithin",
        collection_fixture="geo_collection",
        pipeline=[
            {
                "$searchMeta": {
                    "geoWithin": {
                        "path": "loc",
                        "circle": {
                            "center": {"type": "Point", "coordinates": [DOUBLE_ZERO, DOUBLE_ZERO]},
                            "radius": 50000,
                        },
                    }
                }
            }
        ],
        expected=[{"count": {"lowerBound": Int64(2)}}],
        msg="$searchMeta should accept a geoWithin operator against a geo-indexed field and "
        "return its match count",
    ),
    CollectionFixtureTestCase(
        "operator_geoShape",
        collection_fixture="geo_collection",
        pipeline=[
            {
                "$searchMeta": {
                    "geoShape": {
                        "path": "loc",
                        "relation": "intersects",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]]],
                        },
                    }
                }
            }
        ],
        expected=[{"count": {"lowerBound": Int64(2)}}],
        msg="$searchMeta should accept a geoShape operator against a shape-indexed geo field and "
        "return its match count",
    ),
    CollectionFixtureTestCase(
        "operator_embeddedDocument",
        collection_fixture="embedded_collection",
        pipeline=[
            {
                "$searchMeta": {
                    "embeddedDocument": {
                        "path": "items",
                        "operator": {"text": {"query": "quick", "path": "items.name"}},
                    }
                }
            }
        ],
        expected=[{"count": {"lowerBound": Int64(2)}}],
        msg="$searchMeta should accept an embeddedDocument operator against an "
        "embeddedDocuments-indexed field and return its match count",
    ),
]

# Property [Operators Requiring An Absent Index Feature]: operators that depend
# on a specific index type or feature are recognized but rejected at execution
# when that index type or feature is not present on the collection.
SEARCHMETA_UNSUPPORTED_OPERATOR_TESTS: list[CollectionFixtureTestCase] = [
    CollectionFixtureTestCase(
        "operator_autocomplete_no_index",
        collection_fixture="search_collection",
        pipeline=[{"$searchMeta": {"autocomplete": {"query": "qui", "path": "title"}}}],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject an autocomplete operator when the path is not indexed as "
        "an autocomplete field",
    ),
    CollectionFixtureTestCase(
        "operator_geoWithin_no_index",
        collection_fixture="search_collection",
        pipeline=[
            {
                "$searchMeta": {
                    "geoWithin": {
                        "path": "loc",
                        "circle": {
                            "center": {"type": "Point", "coordinates": [DOUBLE_ZERO, DOUBLE_ZERO]},
                            "radius": 50000,
                        },
                    }
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject a geoWithin operator when the path is not indexed as a geo "
        "field",
    ),
    CollectionFixtureTestCase(
        "operator_geoShape_no_index",
        collection_fixture="search_collection",
        pipeline=[
            {
                "$searchMeta": {
                    "geoShape": {
                        "path": "loc",
                        "relation": "intersects",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]]],
                        },
                    }
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject a geoShape operator when the path is not indexed as a "
        "shape-enabled geo field",
    ),
    CollectionFixtureTestCase(
        "operator_embeddedDocument_no_index",
        collection_fixture="search_collection",
        pipeline=[
            {
                "$searchMeta": {
                    "embeddedDocument": {
                        "path": "items",
                        "operator": {"text": {"query": "quick", "path": "items.name"}},
                    }
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject an embeddedDocument operator when the path is not indexed "
        "as an embeddedDocuments field",
    ),
    CollectionFixtureTestCase(
        "operator_hasAncestor",
        collection_fixture="search_collection",
        pipeline=[{"$searchMeta": {"hasAncestor": {"ancestorPath": "title"}}}],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject a hasAncestor operator without an indexed document "
        "hierarchy",
    ),
    CollectionFixtureTestCase(
        "operator_hasRoot",
        collection_fixture="search_collection",
        pipeline=[
            {
                "$searchMeta": {
                    "hasRoot": {"operator": {"text": {"query": "quick", "path": "title"}}}
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject a hasRoot operator without an indexed document hierarchy",
    ),
    CollectionFixtureTestCase(
        "operator_knnBeta",
        collection_fixture="search_collection",
        pipeline=[{"$searchMeta": {"knnBeta": {"path": "title", "vector": [0.1, 0.2], "k": 2}}}],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject a knnBeta operator without a vector-indexed field",
    ),
    CollectionFixtureTestCase(
        "operator_vectorSearch",
        collection_fixture="search_collection",
        pipeline=[
            {
                "$searchMeta": {
                    "vectorSearch": {
                        "path": "title",
                        "queryVector": [0.1, 0.2],
                        "numCandidates": 10,
                        "limit": 5,
                    }
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject a vectorSearch operator without a vector-indexed field",
    ),
    CollectionFixtureTestCase(
        "operator_search",
        collection_fixture="search_collection",
        pipeline=[{"$searchMeta": {"search": {"text": {"query": "quick", "path": "title"}}}}],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject a nested search operator",
    ),
]

SEARCHMETA_OPERATOR_TESTS: list[CollectionFixtureTestCase] = (
    SEARCHMETA_DYNAMIC_OPERATOR_TESTS
    + SEARCHMETA_REQUIRED_INDEX_OPERATOR_TESTS
    + SEARCHMETA_UNSUPPORTED_OPERATOR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCHMETA_OPERATOR_TESTS))
def test_searchMeta_operator_compatibility(
    engine_client, request, test_case: CollectionFixtureTestCase
):
    """Test $searchMeta acceptance of every recognized search operator."""
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
