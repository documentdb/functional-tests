"""Tests for the $searchMeta returnScope option (validation, semantics, success)."""

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


@pytest.fixture(scope="module")
def nested_collection(engine_client, worker_id) -> Iterator[Collection]:
    """Collection with nested embeddedDocuments and a stored source on the parent.

    returnScope requires the scope path to be indexed as an embeddedDocuments
    field carrying a non-empty storedSource, so the parent ``groups`` field sets
    ``storedSource`` and nests the ``tags`` embeddedDocuments the operator targets.
    """
    with build_collection(
        engine_client,
        worker_id,
        f"{__name__}::nested_collection",
        "searchmeta_return_scope",
        [
            {"_id": 1, "groups": [{"tags": [{"name": "quick"}, {"name": "slow"}]}]},
            {"_id": 2, "groups": [{"tags": [{"name": "quick"}]}]},
            {"_id": 3, "groups": [{"tags": [{"name": "lazy"}]}]},
        ],
        [
            {
                "name": "default",
                "definition": {
                    "mappings": {
                        "dynamic": False,
                        "fields": {
                            "groups": {
                                "type": "embeddedDocuments",
                                "storedSource": True,
                                "fields": {"tags": {"type": "embeddedDocuments", "dynamic": True}},
                            }
                        },
                    }
                },
            }
        ],
    ) as coll:
        yield coll


# Property [ReturnScope Type]: the returnScope option must be a document, so a
# value of any non-document BSON type is rejected. A null returnScope is treated
# as the default, so it is excluded.
SEARCHMETA_RETURN_SCOPE_TYPE_ERROR_TESTS: list[CollectionFixtureTestCase] = [
    CollectionFixtureTestCase(
        f"return_scope_type_{tid}",
        collection_fixture="search_collection",
        pipeline=[
            {"$searchMeta": {"text": {"query": "quick", "path": "title"}, "returnScope": val}}
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$searchMeta should reject a {tid} returnScope option as a non-document",
    )
    for tid, val in [
        ("string", "title"),
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("bool", True),
        ("array", [{"path": "title"}]),
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

# Property [ReturnScope Path Required]: a returnScope document must carry a path
# field, so a document missing it is rejected.
SEARCHMETA_RETURN_SCOPE_PATH_REQUIRED_ERROR_TESTS: list[CollectionFixtureTestCase] = [
    CollectionFixtureTestCase(
        "return_scope_empty",
        collection_fixture="search_collection",
        pipeline=[
            {"$searchMeta": {"text": {"query": "quick", "path": "title"}, "returnScope": {}}}
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject a returnScope document with no path field",
    ),
    CollectionFixtureTestCase(
        "return_scope_other_field",
        collection_fixture="search_collection",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "returnScope": {"other": "title"},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject a returnScope document that omits the required path field",
    ),
]

# Property [ReturnScope Path Type]: the returnScope path field must be a string,
# so a non-string path is rejected.
SEARCHMETA_RETURN_SCOPE_PATH_TYPE_ERROR_TESTS: list[CollectionFixtureTestCase] = [
    CollectionFixtureTestCase(
        f"return_scope_path_type_{tid}",
        collection_fixture="search_collection",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "returnScope": {"path": val},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$searchMeta should reject a {tid} returnScope path as a non-string",
    )
    for tid, val in [
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("bool", True),
        ("object", {"a": 1}),
        ("array", ["title"]),
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

# Property [ReturnScope Scope Path Index Requirement]: a syntactically valid
# returnScope is rejected when its path is not indexed as an embeddedDocuments
# field carrying a non-empty stored source.
SEARCHMETA_RETURN_SCOPE_INDEX_REQUIREMENT_ERROR_TESTS: list[CollectionFixtureTestCase] = [
    CollectionFixtureTestCase(
        "return_scope_path_not_embedded",
        collection_fixture="search_collection",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "returnScope": {"path": "title"},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject a returnScope whose path is not indexed as an "
        "embeddedDocuments field with a stored source",
    ),
]

# Property [ReturnScope Operator Path Containment]: the operator path must be a
# descendant of returnScope.path, so a returnScope path equal to the operator
# path is rejected.
SEARCHMETA_RETURN_SCOPE_CONTAINMENT_ERROR_TESTS: list[CollectionFixtureTestCase] = [
    CollectionFixtureTestCase(
        "return_scope_path_not_ancestor",
        collection_fixture="nested_collection",
        pipeline=[
            {
                "$searchMeta": {
                    "embeddedDocument": {
                        "path": "groups.tags",
                        "operator": {"text": {"query": "quick", "path": "groups.tags.name"}},
                    },
                    "returnScope": {"path": "groups.tags"},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject a returnScope path that is not a strict ancestor of the "
        "operator path",
    ),
]

# Property [ReturnScope Acceptance]: a returnScope whose path is an ancestor of
# the operator path on an embeddedDocuments field with a stored source is
# accepted, and because a metadata stage returns no documents the count envelope
# is returned unchanged.
SEARCHMETA_RETURN_SCOPE_SUCCESS_TESTS: list[CollectionFixtureTestCase] = [
    CollectionFixtureTestCase(
        "return_scope_ancestor_path",
        collection_fixture="nested_collection",
        pipeline=[
            {
                "$searchMeta": {
                    "embeddedDocument": {
                        "path": "groups.tags",
                        "operator": {"text": {"query": "quick", "path": "groups.tags.name"}},
                    },
                    "returnScope": {"path": "groups"},
                }
            }
        ],
        expected=[{"count": {"lowerBound": Int64(2)}}],
        msg="$searchMeta should accept a returnScope ancestor path and still return only the "
        "match count",
    ),
]

SEARCHMETA_RETURN_SCOPE_TESTS: list[CollectionFixtureTestCase] = (
    SEARCHMETA_RETURN_SCOPE_TYPE_ERROR_TESTS
    + SEARCHMETA_RETURN_SCOPE_PATH_REQUIRED_ERROR_TESTS
    + SEARCHMETA_RETURN_SCOPE_PATH_TYPE_ERROR_TESTS
    + SEARCHMETA_RETURN_SCOPE_INDEX_REQUIREMENT_ERROR_TESTS
    + SEARCHMETA_RETURN_SCOPE_CONTAINMENT_ERROR_TESTS
    + SEARCHMETA_RETURN_SCOPE_SUCCESS_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCHMETA_RETURN_SCOPE_TESTS))
def test_searchMeta_return_scope(engine_client, request, test_case: CollectionFixtureTestCase):
    """Test $searchMeta returnScope validation, scope-path semantics, and acceptance."""
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
