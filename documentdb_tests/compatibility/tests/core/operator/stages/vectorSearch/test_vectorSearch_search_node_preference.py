"""Tests for the $vectorSearch stage: searchNodePreference behavior and errors."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Code,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)
from bson.binary import Binary

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    UNKNOWN_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import (
    Contains,
    Len,
)
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
    DOUBLE_ZERO,
)

from .utils.vectorSearch_common import (
    VectorSearchTest,
)

pytestmark = pytest.mark.requires(search=True)

# Property [searchNodePreference Accepted No Effect]: a searchNodePreference
# specification is accepted and recognized without changing the result set,
# whether it carries extra keys alongside a valid key or is null (treated as
# omitted).
VECTORSEARCH_SEARCH_NODE_PREFERENCE_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "search_node_preference_key",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "searchNodePreference": {"key": "n1"},
                }
            },
        ],
        expected={
            "cursor.firstBatch": [
                Len(5),
                Contains("_id", 1),
                Contains("_id", 2),
                Contains("_id", 3),
                Contains("_id", 4),
                Contains("_id", 5),
            ]
        },
        msg="$vectorSearch should accept a searchNodePreference key with no effect "
        "on the result set",
    ),
    VectorSearchTest(
        "search_node_preference_extra_keys",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "searchNodePreference": {"key": "n1", "extra": "x"},
                }
            },
        ],
        expected={
            "cursor.firstBatch": [
                Len(5),
                Contains("_id", 1),
                Contains("_id", 2),
                Contains("_id", 3),
                Contains("_id", 4),
                Contains("_id", 5),
            ]
        },
        msg="$vectorSearch should silently ignore extra keys alongside a valid "
        "searchNodePreference key",
    ),
    VectorSearchTest(
        "search_node_preference_null",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "searchNodePreference": None,
                }
            },
        ],
        expected={
            "cursor.firstBatch": [
                Len(5),
                Contains("_id", 1),
                Contains("_id", 2),
                Contains("_id", 3),
                Contains("_id", 4),
                Contains("_id", 5),
            ]
        },
        msg="$vectorSearch should treat a null searchNodePreference as omitted and succeed",
    ),
]

# Property [searchNodePreference Type Rejection]: a searchNodePreference value of
# any non-document BSON type, including an array, is rejected as not a document
# with no coercion.
VECTORSEARCH_SEARCH_NODE_PREFERENCE_TYPE_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"search_node_preference_type_{tid}",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "searchNodePreference": val,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$vectorSearch should reject a {tid} searchNodePreference value as not a document",
    )
    for tid, val in [
        ("string", "n1"),
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("array", []),
        ("objectid", ObjectId("5a9427648b0beebeb69537a5")),
        ("datetime", datetime(2020, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [searchNodePreference Key Required]: a searchNodePreference that omits
# its key, or gives a null key (treated as field-absent, not a type error),
# requires the key.
VECTORSEARCH_SEARCH_NODE_PREFERENCE_KEY_REQUIRED_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"search_node_preference_{tid}",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "searchNodePreference": snp,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=msg,
    )
    for tid, snp, msg in [
        (
            "key_omitted",
            {},
            "$vectorSearch should require the searchNodePreference key when it is omitted",
        ),
        (
            "key_null",
            {"key": None},
            "$vectorSearch should treat a null searchNodePreference key as field-absent "
            "and require it",
        ),
    ]
]

# Property [searchNodePreference Key Type Rejection]: a searchNodePreference key
# of any non-string BSON type is rejected as a non-string with no coercion.
VECTORSEARCH_SEARCH_NODE_PREFERENCE_KEY_TYPE_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"search_node_preference_key_type_{tid}",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "searchNodePreference": {"key": val},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$vectorSearch should reject a {tid} searchNodePreference key as a non-string",
    )
    for tid, val in [
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("array", ["a"]),
        ("object", {"a": 1}),
        ("objectid", ObjectId("5a9427648b0beebeb69537a5")),
        ("datetime", datetime(2020, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

VECTORSEARCH_SEARCH_NODE_PREFERENCE_ALL_TESTS = (
    VECTORSEARCH_SEARCH_NODE_PREFERENCE_TESTS
    + VECTORSEARCH_SEARCH_NODE_PREFERENCE_TYPE_ERROR_TESTS
    + VECTORSEARCH_SEARCH_NODE_PREFERENCE_KEY_REQUIRED_ERROR_TESTS
    + VECTORSEARCH_SEARCH_NODE_PREFERENCE_KEY_TYPE_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(VECTORSEARCH_SEARCH_NODE_PREFERENCE_ALL_TESTS))
def test_vectorSearch_search_node_preference(test_case: VectorSearchTest, engine_client, request):
    """$vectorSearch: searchNodePreference behavior and errors."""
    coll = request.getfixturevalue(test_case.collection_fixture)
    result = execute_command(
        coll,
        {"aggregate": coll.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        raw_res=test_case.raw_res,
    )
