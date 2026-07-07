"""Tests for the $searchMeta returnStoredSource option and behavior."""

from __future__ import annotations

import datetime
from collections.abc import Iterator

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp
from pymongo.collection import Collection

from documentdb_tests.compatibility.tests.core.operator.stages.searchMeta.utils.searchMeta_common import (  # noqa: E501
    CollectionFixtureTestCase,
    build_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import UNKNOWN_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF

pytestmark = pytest.mark.requires(search=True)


_STORED_SOURCE_DOCS = [
    {"_id": 1, "title": "the quick brown fox", "body": "lazy dog"},
    {"_id": 2, "title": "slow green turtle", "body": "quick nap"},
    {"_id": 3, "title": "a quick quick rabbit", "body": "fast"},
]


@pytest.fixture(scope="module")
def stored_source_collection(engine_client, worker_id) -> Iterator[Collection]:
    """Module-scoped collection whose index stores only the title source field."""
    with build_collection(
        engine_client,
        worker_id,
        f"{__name__}::stored_source_collection",
        "searchmeta_stored_source",
        _STORED_SOURCE_DOCS,
        [
            {
                "name": "default",
                "definition": {
                    "mappings": {"dynamic": True},
                    "storedSource": {"include": ["title"]},
                },
            }
        ],
    ) as coll:
        yield coll


# Property [ReturnStoredSource Acceptance]: returnStoredSource accepts a boolean
# with no coercion, and because a metadata stage returns no documents the count
# envelope is returned unchanged whether it is true or false.
SEARCHMETA_RETURN_STORED_SOURCE_TESTS: list[CollectionFixtureTestCase] = [
    CollectionFixtureTestCase(
        "return_stored_source_false",
        collection_fixture="search_collection",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "returnStoredSource": False,
                }
            }
        ],
        expected=[{"count": {"lowerBound": Int64(3)}}],
        msg="$searchMeta should accept returnStoredSource false and still return its count",
    ),
    CollectionFixtureTestCase(
        "return_stored_source_true",
        collection_fixture="stored_source_collection",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "returnStoredSource": True,
                }
            }
        ],
        expected=[{"count": {"lowerBound": Int64(2)}}],
        msg="$searchMeta should accept returnStoredSource true against a storedSource-configured "
        "index and still return only the count",
    ),
]

# Property [ReturnStoredSource Without Configured Source]: returnStoredSource true
# against an index that does not configure storedSource is rejected.
SEARCHMETA_RETURN_STORED_SOURCE_CONFIG_ERROR_TESTS: list[CollectionFixtureTestCase] = [
    CollectionFixtureTestCase(
        "return_stored_source_unconfigured",
        collection_fixture="search_collection",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "returnStoredSource": True,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject returnStoredSource true against an index with no "
        "storedSource configured",
    ),
]

# Property [ReturnStoredSource Boolean Type]: the returnStoredSource option must
# be a boolean, so a value of any non-boolean BSON type is rejected. A null
# returnStoredSource is treated as the default, so it is excluded.
SEARCHMETA_RETURN_STORED_SOURCE_TYPE_ERROR_TESTS: list[CollectionFixtureTestCase] = [
    CollectionFixtureTestCase(
        f"return_stored_source_type_{tid}",
        collection_fixture="search_collection",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "returnStoredSource": val,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$searchMeta should reject a {tid} returnStoredSource as a non-boolean",
    )
    for tid, val in [
        ("string", "true"),
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("object", {"a": 1}),
        ("array", [True]),
        ("objectid", ObjectId("0123456789abcdef01234567")),
        ("datetime", datetime.datetime(2020, 1, 1)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
    ]
]

SEARCHMETA_STORED_SOURCE_TESTS: list[CollectionFixtureTestCase] = (
    SEARCHMETA_RETURN_STORED_SOURCE_TESTS
    + SEARCHMETA_RETURN_STORED_SOURCE_CONFIG_ERROR_TESTS
    + SEARCHMETA_RETURN_STORED_SOURCE_TYPE_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCHMETA_STORED_SOURCE_TESTS))
def test_searchMeta_stored_source(engine_client, request, test_case: CollectionFixtureTestCase):
    """Test $searchMeta returnStoredSource acceptance, config, and type validation."""
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
