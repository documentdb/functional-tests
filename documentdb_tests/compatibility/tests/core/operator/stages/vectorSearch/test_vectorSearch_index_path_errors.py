"""Tests for the $vectorSearch stage: index and path errors."""

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
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
    DOUBLE_ZERO,
)

from .utils.vectorSearch_common import (
    VectorSearchTest,
)

pytestmark = pytest.mark.requires(search=True)

# Property [index Type Strictness]: a non-string index value of any BSON type is
# rejected as a non-string with no coercion.
VECTORSEARCH_INDEX_TYPE_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"index_type_{tid}",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": val,
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$vectorSearch should reject a {tid} index value as a non-string",
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

# Property [index Empty String]: an empty-string index is rejected as empty,
# distinct from both the non-string type error and the nonexistent-name silent
# miss.
VECTORSEARCH_INDEX_EMPTY_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "index_empty_string",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should reject an empty-string index",
    ),
]

# Property [path Type Strictness]: a non-string path value of any BSON type is
# rejected as a non-string with no coercion.
VECTORSEARCH_PATH_TYPE_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"path_type_{tid}",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": val,
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$vectorSearch should reject a {tid} path value as a non-string",
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

# Property [path Not Indexed As Vector]: a path that does not name a
# vector-indexed field is a hard error, whether the field is nonexistent, an
# existing non-vector field, or a field indexed only as the filter type.
VECTORSEARCH_PATH_NOT_INDEXED_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"path_not_indexed_{tid}",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": path,
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$vectorSearch should reject a {tid} path as not indexed as vector",
    )
    for tid, path in [
        ("nonexistent_field", "no_such_field"),
        ("non_vector_field", "name"),
        ("filter_only_field", "cat"),
    ]
]

# Property [path No Field-Path Syntax Validation]: a malformed field-path string
# is looked up literally and produces the not-indexed-as-vector error, never a
# field-path syntax error.
VECTORSEARCH_PATH_SYNTAX_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"path_syntax_{tid}",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": path,
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$vectorSearch should look up a {tid} path literally and reject it as "
        "not indexed as vector",
    )
    for tid, path in [
        ("empty", ""),
        ("leading_dot", ".x"),
        ("trailing_dot", "x."),
        ("empty_component", "a..b"),
        ("null_byte", "a\x00b"),
        ("deep_nesting", ".".join("a" * 50)),
        ("very_long", "a" * 10_000),
    ]
]

# Property [path Literal Not Expression]: a dollar-prefixed or variable-like path
# string is matched literally with no expression or variable evaluation, yielding
# the not-indexed-as-vector error.
VECTORSEARCH_PATH_LITERAL_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"path_literal_{tid}",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": path,
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$vectorSearch should treat a {tid} path as a literal name, not an "
        "expression, and reject it as not indexed as vector",
    )
    for tid, path in [
        ("field_ref", "$embedding"),
        ("now_variable", "$$NOW"),
        ("root_variable", "$$ROOT"),
        ("dollar_only", "$"),
        ("double_dollar", "$$"),
    ]
]

# Property [path Exact Byte Matching]: path matching is byte-for-byte, so a
# case variant or whitespace-padded form of the real field name does not match
# and yields the not-indexed-as-vector error.
VECTORSEARCH_PATH_EXACT_MATCH_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"path_exact_{tid}",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": path,
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$vectorSearch should not match a {tid} of the real field name and "
        "reject it as not indexed as vector",
    )
    for tid, path in [
        ("case_variant", "vc".upper()),
        ("leading_space", " vc"),
        ("trailing_space", "vc "),
        # "cafe" + combining acute (U+0301): the decomposed (NFD) form of the
        # indexed precomposed "caf\u00e9_vec" (U+00E9), a distinct byte sequence
        # that must not match.
        ("non_normalized_unicode", "cafe\u0301_vec"),
    ]
]

VECTORSEARCH_INDEX_PATH_ERRORS_ALL_TESTS = (
    VECTORSEARCH_INDEX_TYPE_ERROR_TESTS
    + VECTORSEARCH_INDEX_EMPTY_ERROR_TESTS
    + VECTORSEARCH_PATH_TYPE_ERROR_TESTS
    + VECTORSEARCH_PATH_NOT_INDEXED_ERROR_TESTS
    + VECTORSEARCH_PATH_SYNTAX_ERROR_TESTS
    + VECTORSEARCH_PATH_LITERAL_ERROR_TESTS
    + VECTORSEARCH_PATH_EXACT_MATCH_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(VECTORSEARCH_INDEX_PATH_ERRORS_ALL_TESTS))
def test_vectorSearch_index_path_errors(test_case: VectorSearchTest, engine_client, request):
    """$vectorSearch: index and path errors."""
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
