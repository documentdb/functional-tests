"""Tests for the $vectorSearch stage: filter parse and shape errors."""

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
    BAD_VALUE_ERROR,
    EXPRESSION_NOT_OBJECT_ERROR,
    NEAR_NOT_ALLOWED_ERROR,
    UNKNOWN_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
    DOUBLE_ZERO,
)

from .utils.vectorSearch_common import (
    VectorSearchTest,
)

pytestmark = pytest.mark.requires(search=True)

# Property [filter Scalar Type Rejection]: a non-object, non-array scalar filter
# value is rejected at parse time as not an object.
VECTORSEARCH_FILTER_SCALAR_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"filter_scalar_{tid}",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "filter": val,
                }
            }
        ],
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg=f"$vectorSearch should reject a {tid} scalar filter value as not an object",
    )
    for tid, val in [
        ("string", "x"),
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
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

# Property [filter Array Rejection]: an array filter value is rejected as not a
# document rather than treated as an empty filter.
VECTORSEARCH_FILTER_ARRAY_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "filter_array_empty",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "filter": [],
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should reject an empty-array filter as not a document",
    ),
]

# Property [filter MQL Parse Rejection]: a filter operator rejected by the MQL
# parser surfaces a parse error rather than an executor validation error.
VECTORSEARCH_FILTER_MQL_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"filter_mql_{tid}",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "filter": flt,
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg=f"$vectorSearch should reject a {tid} filter as an MQL parse error",
    )
    for tid, flt in [
        ("text", {"$text": {"$search": "x"}}),
        ("comment", {"year": {"$comment": "x"}}),
        ("unknown_top_level", {"$bad": 1}),
    ]
]

# Property [filter Geo Operator Rejection]: a geospatial filter operator is
# rejected because it requires sorting geospatial data.
VECTORSEARCH_FILTER_GEO_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "filter_geo_near",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "filter": {"year": {"$near": [0, 0]}},
                }
            }
        ],
        error_code=NEAR_NOT_ALLOWED_ERROR,
        msg="$vectorSearch should reject a geo operator in a filter",
    ),
]

# Property [filter Combinator Argument Validation]: a top-level logical
# combinator requires a non-empty array argument.
VECTORSEARCH_FILTER_COMBINATOR_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"filter_combinator_{tid}",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "filter": flt,
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg=f"$vectorSearch should reject a {tid} combinator argument",
    )
    for tid, flt in [
        ("empty_array", {"$and": []}),
        ("non_array", {"$and": {"year": 1}}),
    ]
]

VECTORSEARCH_FILTER_PARSE_ERRORS_ALL_TESTS = (
    VECTORSEARCH_FILTER_SCALAR_ERROR_TESTS
    + VECTORSEARCH_FILTER_ARRAY_ERROR_TESTS
    + VECTORSEARCH_FILTER_MQL_ERROR_TESTS
    + VECTORSEARCH_FILTER_GEO_ERROR_TESTS
    + VECTORSEARCH_FILTER_COMBINATOR_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(VECTORSEARCH_FILTER_PARSE_ERRORS_ALL_TESTS))
def test_vectorSearch_filter_parse_errors(test_case: VectorSearchTest, engine_client, request):
    """$vectorSearch: filter parse and shape errors."""
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
    )
