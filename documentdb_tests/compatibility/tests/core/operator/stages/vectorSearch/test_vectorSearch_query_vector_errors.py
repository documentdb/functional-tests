"""Tests for the $vectorSearch stage: queryVector rejections."""

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
from bson.binary import Binary, BinaryVectorDtype

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    UNKNOWN_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

from .utils.vectorSearch_common import (
    VectorSearchTest,
)

pytestmark = pytest.mark.requires(search=True)

# Property [queryVector Scalar Type Rejection]: a non-array, non-BinData scalar
# queryVector is rejected as an unexpected vector type with no coercion.
VECTORSEARCH_QUERY_VECTOR_SCALAR_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"query_vector_scalar_{tid}",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": val,
                    "numCandidates": 10,
                    "limit": 5,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$vectorSearch should reject a {tid} scalar queryVector as an unexpected type",
    )
    for tid, val in [
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("string", "vec"),
        ("object", {"a": 1}),
        ("objectid", ObjectId("5a9427648b0beebeb69537a5")),
        ("datetime", datetime(2020, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [queryVector Element Type Rejection]: an array queryVector containing a
# non-numeric or Decimal128 element is rejected as an unsupported BSON value.
VECTORSEARCH_QUERY_VECTOR_ELEMENT_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"query_vector_element_{tid}",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [val, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$vectorSearch should reject a queryVector with a {tid} element as an "
        "unsupported BSON value",
    )
    for tid, val in [
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("string", "x"),
        ("null", None),
        ("object", {"a": 1}),
        ("nested_array", [1.0]),
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

# Property [queryVector Literal Not Expression]: a queryVector given as a field
# reference, expression object, or variable is treated as a literal value and
# rejected without evaluation or array unwrapping.
VECTORSEARCH_QUERY_VECTOR_LITERAL_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"query_vector_literal_{tid}",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": qv,
                    "numCandidates": 10,
                    "limit": 5,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$vectorSearch should treat a {tid} queryVector as a literal, not "
        "evaluate it as an expression",
    )
    for tid, qv in [
        ("field_ref", "$embedding"),
        ("now_variable", "$$NOW"),
        ("literal_expr", {"$literal": [1.0, DOUBLE_ZERO, DOUBLE_ZERO]}),
        ("array_element_ref", ["$n", DOUBLE_ZERO, DOUBLE_ZERO]),
    ]
]

# Property [queryVector Binary Subtype Rejection]: a plain Binary queryVector
# whose subtype is not the vector subtype is rejected.
VECTORSEARCH_QUERY_VECTOR_BINARY_SUBTYPE_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "query_vector_binary_subtype_zero",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": Binary(b"\x00\x01\x02", 0),
                    "numCandidates": 10,
                    "limit": 5,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should reject a subtype-0 Binary queryVector",
    ),
]

# Property [queryVector Dimension Mismatch]: a queryVector whose element count
# differs from the index numDimensions is rejected, including an empty array.
VECTORSEARCH_QUERY_VECTOR_DIMENSION_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"query_vector_dimension_{tid}",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": qv,
                    "numCandidates": 10,
                    "limit": 5,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$vectorSearch should reject a queryVector of length {n} against a "
        f"{3}-dimension index",
    )
    for tid, qv, n in [
        ("empty", [], 0),
        ("too_few_one", [1.0], 1),
        ("too_few_two", [1.0, DOUBLE_ZERO], 2),
        ("too_many_four", [1.0, DOUBLE_ZERO, DOUBLE_ZERO, DOUBLE_ZERO], 4),
    ]
]

# Property [queryVector Non-Finite Rejection]: a non-finite queryVector element
# is rejected, including a value that overflows float32 to Infinity.
VECTORSEARCH_QUERY_VECTOR_NON_FINITE_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"query_vector_non_finite_{tid}",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [val, DOUBLE_ZERO, 1.0],
                    "numCandidates": 10,
                    "limit": 5,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$vectorSearch should reject a {tid} queryVector element as non-finite",
    )
    for tid, val in [
        ("nan", FLOAT_NAN),
        ("positive_infinity", FLOAT_INFINITY),
        ("negative_infinity", FLOAT_NEGATIVE_INFINITY),
        ("float32_overflow", 3.5e38),
    ]
]

# Property [queryVector Cosine Zero Vector Rejection]: a zero queryVector,
# including values that float32-narrow to all-zero, is rejected against a cosine
# index.
VECTORSEARCH_QUERY_VECTOR_ZERO_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"query_vector_zero_{tid}",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": qv,
                    "numCandidates": 10,
                    "limit": 5,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$vectorSearch should reject a {tid} queryVector against a cosine index",
    )
    for tid, qv in [
        ("all_zero", [DOUBLE_ZERO, DOUBLE_ZERO, DOUBLE_ZERO]),
        ("negative_zero", [DOUBLE_NEGATIVE_ZERO, DOUBLE_ZERO, DOUBLE_ZERO]),
        ("float32_underflow", [DOUBLE_MIN_SUBNORMAL, DOUBLE_ZERO, DOUBLE_ZERO]),
    ]
]

# Property [queryVector Packed-Bit Cosine Rejection]: a packed_bit BinData
# queryVector is rejected against a cosine-indexed field because binary vectors
# require euclidean similarity.
VECTORSEARCH_QUERY_VECTOR_PACKED_BIT_COSINE_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "query_vector_packed_bit_cosine",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "v8c",
                    "queryVector": Binary.from_vector(
                        [0b10110010], BinaryVectorDtype.PACKED_BIT, padding=0
                    ),
                    "numCandidates": 10,
                    "limit": 5,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should reject a packed_bit queryVector against a cosine index",
    ),
]

# Property [queryVector Packed-Bit Structural Rejection]: a packed_bit BinData
# queryVector with nonzero padding is rejected before the dimension-count and
# similarity checks run.
VECTORSEARCH_QUERY_VECTOR_PACKED_BIT_STRUCTURE_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "query_vector_packed_bit_nonzero_padding",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "v8",
                    "queryVector": Binary.from_vector(
                        [0b10110000], BinaryVectorDtype.PACKED_BIT, padding=3
                    ),
                    "numCandidates": 10,
                    "limit": 5,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should reject a packed_bit queryVector with nonzero padding",
    ),
]

VECTORSEARCH_QUERY_VECTOR_ERRORS_ALL_TESTS = (
    VECTORSEARCH_QUERY_VECTOR_SCALAR_ERROR_TESTS
    + VECTORSEARCH_QUERY_VECTOR_ELEMENT_ERROR_TESTS
    + VECTORSEARCH_QUERY_VECTOR_LITERAL_ERROR_TESTS
    + VECTORSEARCH_QUERY_VECTOR_BINARY_SUBTYPE_ERROR_TESTS
    + VECTORSEARCH_QUERY_VECTOR_DIMENSION_ERROR_TESTS
    + VECTORSEARCH_QUERY_VECTOR_NON_FINITE_ERROR_TESTS
    + VECTORSEARCH_QUERY_VECTOR_ZERO_ERROR_TESTS
    + VECTORSEARCH_QUERY_VECTOR_PACKED_BIT_COSINE_ERROR_TESTS
    + VECTORSEARCH_QUERY_VECTOR_PACKED_BIT_STRUCTURE_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(VECTORSEARCH_QUERY_VECTOR_ERRORS_ALL_TESTS))
def test_vectorSearch_query_vector_errors(test_case: VectorSearchTest, engine_client, request):
    """$vectorSearch: queryVector rejections."""
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
