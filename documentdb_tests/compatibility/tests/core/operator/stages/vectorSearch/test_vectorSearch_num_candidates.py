"""Tests for the $vectorSearch stage: numCandidates acceptance and errors."""

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
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import (
    Eq,
    PerDoc,
)
from documentdb_tests.framework.test_constants import (
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_OVERFLOW,
)

from .utils.vectorSearch_common import (
    VectorSearchTest,
)

pytestmark = pytest.mark.requires(search=True)

# Property [numCandidates Numeric Type and Range Acceptance]: numCandidates
# accepts an int32, Int64, or whole-number double, and both range bounds are
# accepted.
VECTORSEARCH_NUM_CANDIDATES_RANGE_TESTS: list[VectorSearchTest] = [
    *[
        VectorSearchTest(
            f"range_{tid}",
            pipeline=[
                {
                    "$vectorSearch": {
                        "index": "vs_core_index",
                        "path": "vc",
                        "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                        "numCandidates": nc,
                        "limit": 3,
                    }
                },
            ],
            expected=PerDoc({"_id": Eq(1)}, {"_id": Eq(2)}, {"_id": Eq(3)}),
            msg=f"$vectorSearch should accept a {tid} numCandidates within range",
        )
        for tid, nc in [
            ("int32", 5),
            ("int64", Int64(5)),
            ("whole_double", 5.0),
        ]
    ],
    VectorSearchTest(
        "range_lower_boundary_one",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 1,
                    "limit": 1,
                }
            },
        ],
        expected=PerDoc({"_id": Eq(1)}),
        msg="$vectorSearch should accept the lower numCandidates bound of 1",
    ),
    VectorSearchTest(
        "range_upper_boundary_ten_thousand",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10_000,
                    "limit": 5,
                }
            },
        ],
        expected=PerDoc(
            {"_id": Eq(1)}, {"_id": Eq(2)}, {"_id": Eq(3)}, {"_id": Eq(4)}, {"_id": Eq(5)}
        ),
        msg="$vectorSearch should accept the upper numCandidates bound of 10000",
    ),
]

# Property [numCandidates Non-Integer Double]: a double numCandidates whose
# value is not a whole number, including NaN, is rejected as not an integer.
VECTORSEARCH_NUM_CANDIDATES_DOUBLE_NON_INTEGER_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"num_candidates_double_non_integer_{tid}",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": val,
                    "limit": 5,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$vectorSearch should reject a {tid} double numCandidates as not an integer",
    )
    for tid, val in [
        ("fractional", 10.5),
        ("nan", FLOAT_NAN),
    ]
]

# Property [numCandidates Type Strictness]: a numCandidates of any non-integer
# BSON type other than double is rejected as not an integer with no coercion.
VECTORSEARCH_NUM_CANDIDATES_TYPE_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"num_candidates_type_{tid}",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": val,
                    "limit": 5,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$vectorSearch should reject a {tid} numCandidates as not an integer",
    )
    for tid, val in [
        ("decimal128_whole", Decimal128("3")),
        ("bool", True),
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

# Property [numCandidates Literal Not Expression]: a numCandidates given as an
# expression object is rejected at the BSON-type layer as not an integer, with no
# expression evaluation.
VECTORSEARCH_NUM_CANDIDATES_LITERAL_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "num_candidates_literal_object",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": {"$literal": 10},
                    "limit": 5,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should reject an expression-object numCandidates without evaluating it",
    ),
]

# Property [numCandidates Bounds]: an integer-valued numCandidates outside the
# accepted range is rejected as out of bounds, with integer-valued doubles routed
# to the bounds check rather than the type check.
VECTORSEARCH_NUM_CANDIDATES_BOUNDS_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"num_candidates_bounds_{tid}",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": val,
                    "limit": 1,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$vectorSearch should reject a {tid} numCandidates as out of bounds",
    )
    for tid, val in [
        ("lower_zero", 0),
        ("negative_whole_double", -5.0),
        ("upper_10001", 10_001),
        ("int32_max", INT32_MAX),
    ]
]

# Property [numCandidates Int32 Range]: a numCandidates that does not fit in a
# signed 32-bit integer is rejected as overflowing above the range or
# underflowing below it.
VECTORSEARCH_NUM_CANDIDATES_INT32_RANGE_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"num_candidates_int32_range_{tid}",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": val,
                    "limit": 5,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$vectorSearch should reject a {tid} numCandidates as outside int32 range",
    )
    for tid, val in [
        ("int64_just_over", Int64(INT32_OVERFLOW)),
        ("double_just_over", float(INT32_OVERFLOW)),
        ("positive_infinity", FLOAT_INFINITY),
        ("negative_infinity", FLOAT_NEGATIVE_INFINITY),
    ]
]

# Property [numCandidates Less Than Limit]: under ANN a numCandidates smaller
# than limit is rejected because numCandidates must be greater than or equal to
# limit.
VECTORSEARCH_NUM_CANDIDATES_LESS_THAN_LIMIT_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "num_candidates_less_than_limit",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 4,
                    "limit": 5,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should reject a numCandidates smaller than limit under ANN",
    ),
]

# Property [numCandidates Forbidden With Exact]: a non-null numCandidates is
# rejected when exact is true, because ENN forbids numCandidates rather than
# merely ignoring it.
VECTORSEARCH_NUM_CANDIDATES_EXACT_FORBIDDEN_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "num_candidates_forbidden_with_exact",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "exact": True,
                    "numCandidates": 10,
                    "limit": 5,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should reject a non-null numCandidates when exact is true",
    ),
]

VECTORSEARCH_NUM_CANDIDATES_ALL_TESTS = (
    VECTORSEARCH_NUM_CANDIDATES_RANGE_TESTS
    + VECTORSEARCH_NUM_CANDIDATES_DOUBLE_NON_INTEGER_ERROR_TESTS
    + VECTORSEARCH_NUM_CANDIDATES_TYPE_ERROR_TESTS
    + VECTORSEARCH_NUM_CANDIDATES_LITERAL_ERROR_TESTS
    + VECTORSEARCH_NUM_CANDIDATES_BOUNDS_ERROR_TESTS
    + VECTORSEARCH_NUM_CANDIDATES_INT32_RANGE_ERROR_TESTS
    + VECTORSEARCH_NUM_CANDIDATES_LESS_THAN_LIMIT_ERROR_TESTS
    + VECTORSEARCH_NUM_CANDIDATES_EXACT_FORBIDDEN_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(VECTORSEARCH_NUM_CANDIDATES_ALL_TESTS))
def test_vectorSearch_num_candidates(test_case: VectorSearchTest, engine_client, request):
    """$vectorSearch: numCandidates acceptance and errors."""
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
