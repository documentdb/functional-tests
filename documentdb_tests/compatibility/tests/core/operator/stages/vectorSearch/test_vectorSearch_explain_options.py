"""Tests for the $vectorSearch stage: explainOptions behavior and errors."""

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
    Eq,
    Exists,
)
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
    DOUBLE_ZERO,
)

from .utils.vectorSearch_common import (
    VectorSearchTest,
)

pytestmark = pytest.mark.requires(search=True)

# Property [explainOptions Trace Element Type Non-Validation]: on a genuine
# explain aggregate explainOptions.traceDocumentIds accepts an element of any
# non-null BSON type (the documented "array of objectIDs" is not enforced) and
# echoes the supplied ids back into the explain output.
VECTORSEARCH_EXPLAIN_OPTIONS_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"explain_options_{tid}",
        explain=True,
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 3,
                    "explainOptions": {"traceDocumentIds": ids},
                }
            }
        ],
        expected={
            "ok": Eq(1.0),
            # pymongo decodes a subtype-0 BSON binary element to plain bytes,
            # whose equality with the Binary input is subtype-sensitive, so the
            # binary case asserts the echoed field is present rather than equal.
            "stages.0.$vectorSearch.explainOptions.traceDocumentIds": (
                Exists() if tid == "binary" else Eq(ids)
            ),
        },
        msg=f"$vectorSearch should accept a {tid} traceDocumentIds element on a "
        "genuine explain and echo it into the explain output",
    )
    for tid, ids in [
        ("objectid", [ObjectId("5a9427648b0beebeb69537a5"), ObjectId("5a9427648b0beebeb69537b6")]),
        ("int32", [1, 2]),
        ("int64", [Int64(1), Int64(2)]),
        ("double", [1.5, 2.5]),
        ("decimal128", [DECIMAL128_ONE_AND_HALF]),
        ("string", ["x", "y"]),
        ("bool", [True, False]),
        ("object", [{"a": 1}]),
        ("array", [[1, 2]]),
        ("datetime", [datetime(2020, 1, 1, tzinfo=timezone.utc)]),
        ("timestamp", [Timestamp(1, 1)]),
        ("binary", [Binary(b"\x01\x02\x03")]),
        ("regex", [Regex(".*", "i")]),
        ("code", [Code("function(){}")]),
        ("minkey", [MinKey()]),
        ("maxkey", [MaxKey()]),
        ("mixed", [1, "x", 1.5, ObjectId("5a9427648b0beebeb69537a5")]),
    ]
]

# Property [explainOptions Structure Validation]: explainOptions and its
# traceDocumentIds sub-field are structurally validated independent of index
# existence, so a malformed shape is rejected against a collection with no index.
VECTORSEARCH_EXPLAIN_OPTIONS_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"explain_options_{tid}",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "explainOptions": explain_options,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=msg,
    )
    for tid, explain_options, msg in [
        (
            "non_document",
            5,
            "$vectorSearch should reject a non-document explainOptions value",
        ),
        (
            "unknown_subfield",
            {"bogus": 1},
            "$vectorSearch should reject an unknown explainOptions sub-field",
        ),
        (
            "trace_document_ids_non_array",
            {"traceDocumentIds": 5},
            "$vectorSearch should reject a non-array traceDocumentIds",
        ),
        (
            "trace_document_ids_empty",
            {"traceDocumentIds": []},
            "$vectorSearch should reject an empty traceDocumentIds array",
        ),
    ]
]

# Property [explainOptions Requires Explain Mode]: explainOptions present on a
# non-explain query is rejected once the index resolves, because the option is
# only valid when the query is run in explain mode.
VECTORSEARCH_EXPLAIN_OPTIONS_NON_EXPLAIN_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "explain_options_non_explain_query",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "explainOptions": {"traceDocumentIds": [1, 2]},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should reject explainOptions on a non-explain query",
    ),
]

# Property [explainOptions Requires Non-Empty traceDocumentIds]: on a genuine
# explain query, explainOptions must carry a non-empty traceDocumentIds, so
# omitting it entirely and supplying a null element are both rejected.
VECTORSEARCH_EXPLAIN_OPTIONS_EXPLAIN_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "explain_options_empty_document",
        explain=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "explainOptions": {},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should reject an explainOptions with no traceDocumentIds "
        "on an explain query",
    ),
    VectorSearchTest(
        "explain_options_trace_null_element",
        explain=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "explainOptions": {"traceDocumentIds": [None]},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should reject a null traceDocumentIds element on an explain query",
    ),
]

VECTORSEARCH_EXPLAIN_OPTIONS_ALL_TESTS = (
    VECTORSEARCH_EXPLAIN_OPTIONS_TESTS
    + VECTORSEARCH_EXPLAIN_OPTIONS_ERROR_TESTS
    + VECTORSEARCH_EXPLAIN_OPTIONS_NON_EXPLAIN_ERROR_TESTS
    + VECTORSEARCH_EXPLAIN_OPTIONS_EXPLAIN_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(VECTORSEARCH_EXPLAIN_OPTIONS_ALL_TESTS))
def test_vectorSearch_explain_options(test_case: VectorSearchTest, engine_client, request):
    """$vectorSearch: explainOptions behavior and errors."""
    coll = request.getfixturevalue(test_case.collection_fixture)
    aggregate = {"aggregate": coll.name, "pipeline": test_case.pipeline, "cursor": {}}
    command = (
        {"explain": aggregate, "verbosity": "queryPlanner"} if test_case.explain else aggregate
    )
    result = execute_command(coll, command)
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        raw_res=test_case.raw_res,
    )
