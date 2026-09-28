"""Tests for the $vectorSearch stage: limit acceptance and errors."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Code,
    Decimal128,
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
    VECTOR_SEARCH_LIMIT_NOT_NUMBER_ERROR,
    VECTOR_SEARCH_LIMIT_NOT_POSITIVE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import (
    Eq,
    PerDoc,
)
from documentdb_tests.framework.test_constants import (
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_OVERFLOW,
)

from .utils.vectorSearch_common import (
    VectorSearchTest,
)

pytestmark = pytest.mark.requires(search=True)

# Property [limit Numeric Type Acceptance]: limit accepts an int32, Int64, or
# whole-number double and is treated as the integer value, returning exactly that
# many top-similarity documents.
VECTORSEARCH_LIMIT_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"limit_{tid}",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": limit,
                }
            },
        ],
        expected=expected,
        msg=f"$vectorSearch should accept a {tid} limit and return the integer "
        "number of top-similarity documents",
    )
    for tid, limit, expected in [
        ("int32", 2, PerDoc({"_id": Eq(1)}, {"_id": Eq(2)})),
        ("int64", Int64(3), PerDoc({"_id": Eq(1)}, {"_id": Eq(2)}, {"_id": Eq(3)})),
        ("whole_double", 3.0, PerDoc({"_id": Eq(1)}, {"_id": Eq(2)}, {"_id": Eq(3)})),
    ]
]

# Property [limit Type Strictness]: a non-number limit value of any BSON type is
# rejected at the parse layer as not a number, with no coercion.
VECTORSEARCH_LIMIT_TYPE_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"limit_type_{tid}",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": val,
                }
            }
        ],
        error_code=VECTOR_SEARCH_LIMIT_NOT_NUMBER_ERROR,
        msg=f"$vectorSearch should reject a {tid} limit value as a non-number",
    )
    for tid, val in [
        ("bool_true", True),
        ("bool_false", False),
        ("string", "5"),
        ("array", [5]),
        ("object", {"a": 5}),
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

# Property [limit Literal Not Expression]: a limit given as an expression object
# is rejected at the BSON-type layer as a non-number, with no expression
# evaluation.
VECTORSEARCH_LIMIT_LITERAL_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "limit_literal_object",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": {"$literal": 3},
                }
            }
        ],
        error_code=VECTOR_SEARCH_LIMIT_NOT_NUMBER_ERROR,
        msg="$vectorSearch should reject an expression-object limit without evaluating it",
    ),
]

# Property [limit Fractional Rejection]: a double limit whose truncation is at
# least one but is not a whole number is rejected as a non-integer.
VECTORSEARCH_LIMIT_FRACTIONAL_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "limit_fractional_one_point_five",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 1.5,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should reject a fractional double limit",
    ),
]

# Property [limit Decimal128 Rejection]: a Decimal128 limit is rejected as a
# non-integer even when its value is whole, unlike a whole-number double.
VECTORSEARCH_LIMIT_DECIMAL_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "limit_decimal_whole",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": Decimal128("3"),
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should reject a whole-valued Decimal128 limit",
    ),
]

# Property [limit Positivity]: a limit whose truncation is less than one is
# rejected as non-positive, checked before the integer-ness check.
VECTORSEARCH_LIMIT_NOT_POSITIVE_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"limit_not_positive_{tid}",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": val,
                }
            }
        ],
        error_code=VECTOR_SEARCH_LIMIT_NOT_POSITIVE_ERROR,
        msg=f"$vectorSearch should reject a non-positive limit ({tid})",
    )
    for tid, val in [
        ("zero_int32", 0),
        ("zero_double", DOUBLE_ZERO),
        ("negative_zero_double", DOUBLE_NEGATIVE_ZERO),
        ("fractional_half", 0.5),
        ("negative_int", -1),
        ("negative_double", -1.5),
        ("nan", FLOAT_NAN),
        ("negative_infinity", FLOAT_NEGATIVE_INFINITY),
    ]
]

# Property [limit Int32 Overflow]: a positive whole limit that does not fit in a
# 32-bit integer is rejected as overflowing.
VECTORSEARCH_LIMIT_OVERFLOW_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"limit_overflow_{tid}",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": val,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$vectorSearch should reject a limit that exceeds int32 range ({tid})",
    )
    for tid, val in [
        ("int64_just_over", Int64(INT32_OVERFLOW)),
        ("double_just_over", float(INT32_OVERFLOW)),
        ("positive_infinity", FLOAT_INFINITY),
    ]
]

# Property [limit ENN Ceiling]: under ENN (exact true, no numCandidates) a limit
# at or above the exact-search ceiling is rejected during ENN execution.
VECTORSEARCH_LIMIT_ENN_CEILING_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "limit_enn_ceiling",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "exact": True,
                    "limit": 2_147_483_631,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should reject an ENN limit at the exact-search ceiling",
    ),
]

VECTORSEARCH_LIMIT_ALL_TESTS = (
    VECTORSEARCH_LIMIT_TESTS
    + VECTORSEARCH_LIMIT_TYPE_ERROR_TESTS
    + VECTORSEARCH_LIMIT_LITERAL_ERROR_TESTS
    + VECTORSEARCH_LIMIT_FRACTIONAL_ERROR_TESTS
    + VECTORSEARCH_LIMIT_DECIMAL_ERROR_TESTS
    + VECTORSEARCH_LIMIT_NOT_POSITIVE_ERROR_TESTS
    + VECTORSEARCH_LIMIT_OVERFLOW_ERROR_TESTS
    + VECTORSEARCH_LIMIT_ENN_CEILING_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(VECTORSEARCH_LIMIT_ALL_TESTS))
def test_vectorSearch_limit(test_case: VectorSearchTest, engine_client, request):
    """$vectorSearch: limit acceptance and errors."""
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
