"""Tests for the $vectorSearch stage: parentFilter pre-filtering and errors."""

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
    _FILTER_OID_A,
    _FILTER_UUID_A,
    VectorSearchTest,
)

pytestmark = pytest.mark.requires(search=True)

# Property [parentFilter Null As Omitted]: parentFilter null is treated as
# field-absent and the query succeeds as if parentFilter were not specified,
# diverging from filter where null errors.
VECTORSEARCH_PARENT_FILTER_NULL_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "parent_filter_null_omitted",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "parentFilter": None,
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
        msg="$vectorSearch should treat parentFilter null as omitted and return all documents",
    ),
]

# Property [parentFilter Flat Index Acceptance]: parentFilter is accepted on a
# flat index as a second pre-filter on filter-type fields, where an empty
# document matches all and a real predicate AND-combines with filter.
VECTORSEARCH_PARENT_FILTER_FLAT_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "parent_filter_empty_matches_all",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "parentFilter": {},
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
        msg="$vectorSearch should retain every document for an empty parentFilter on a flat index",
    ),
    VectorSearchTest(
        "parent_filter_second_prefilter",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "parentFilter": {"cat": "x"},
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(2), Contains("_id", 1), Contains("_id", 2)]},
        msg="$vectorSearch should apply parentFilter as a pre-filter on a flat index",
    ),
    VectorSearchTest(
        "parent_filter_and_combines_with_filter",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "filter": {"cat": "x"},
                    "parentFilter": {"year": {"$gte": 2000}},
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 2)]},
        msg="$vectorSearch should AND-combine parentFilter with filter on a flat index",
    ),
]

# Property [parentFilter Operator Parity]: parentFilter supports the same
# per-field operators and $eq shorthand as filter.
VECTORSEARCH_PARENT_FILTER_OPERATOR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"parent_operator_{tid}",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "parentFilter": flt,
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(len(ids)), *(Contains("_id", i) for i in ids)]},
        msg=f"$vectorSearch should pre-filter parentFilter with the {tid} operator",
    )
    for tid, flt, ids in [
        ("shorthand_eq", {"year": 2001}, [3]),
        ("eq", {"year": {"$eq": 2010}}, [4, 5]),
        ("ne", {"year": {"$ne": 2010}}, [1, 2, 3]),
        ("gt", {"year": {"$gt": 2000}}, [3, 4, 5]),
        ("gte", {"year": {"$gte": 2001}}, [3, 4, 5]),
        ("lt", {"year": {"$lt": 2001}}, [1, 2]),
        ("lte", {"year": {"$lte": 2000}}, [1, 2]),
        ("in", {"year": {"$in": [1999, 2001]}}, [1, 3]),
        ("nin", {"year": {"$nin": [1999, 2001]}}, [2, 4, 5]),
        ("exists", {"cat": {"$exists": True}}, [1, 2, 3, 4, 5]),
        ("not", {"year": {"$not": {"$gt": 2000}}}, [1, 2]),
    ]
]

# Property [parentFilter Combinator Parity]: parentFilter composes the same
# top-level combinators and implicit multi-field AND as filter.
VECTORSEARCH_PARENT_FILTER_COMBINATOR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"parent_combinator_{tid}",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "parentFilter": flt,
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(len(ids)), *(Contains("_id", i) for i in ids)]},
        msg=f"$vectorSearch should compose the {tid} combinator in parentFilter",
    )
    for tid, flt, ids in [
        ("and", {"$and": [{"cat": "y"}, {"year": {"$gte": 2010}}]}, [4, 5]),
        ("or", {"$or": [{"cat": "x"}, {"year": 2001}]}, [1, 2, 3]),
        ("nor", {"$nor": [{"cat": "x"}]}, [3, 4, 5]),
        ("implicit_and", {"cat": "y", "active": True}, [3, 5]),
    ]
]

# Property [parentFilter Value Type Parity]: parentFilter pre-filters with the
# same predicate value types as filter, including null as a direct value and
# element membership on an array-valued field.
VECTORSEARCH_PARENT_FILTER_VALUE_TYPE_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"parent_value_type_{tid}",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "parentFilter": flt,
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(len(ids)), *(Contains("_id", i) for i in ids)]},
        msg=f"$vectorSearch should pre-filter parentFilter with a {tid} predicate value",
    )
    for tid, flt, ids in [
        ("string", {"cat": "x"}, [1, 2]),
        ("int32", {"year": 2000}, [2]),
        ("int64", {"count": Int64(20)}, [2]),
        ("double", {"rating": 4.5}, [1]),
        ("boolean", {"active": True}, [1, 3, 5]),
        ("object_id", {"oid": _FILTER_OID_A}, [1, 3, 5]),
        ("date", {"created": {"$gt": datetime(2023, 1, 1, tzinfo=timezone.utc)}}, [4, 5]),
        ("uuid", {"uid": _FILTER_UUID_A}, [1, 3, 5]),
        ("null_direct", {"opt": None}, [3]),
        ("array_element_membership", {"tags": "x"}, [1, 5]),
    ]
]

# Property [parentFilter Type Rejection]: a non-object parentFilter value of any
# BSON type, including an array, is uniformly rejected on the mongot executor as
# not a document, with no parse-time object check (diverging from filter null).
VECTORSEARCH_PARENT_FILTER_TYPE_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"parent_filter_type_{tid}",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "parentFilter": val,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$vectorSearch should reject a {tid} parentFilter value as not a document",
    )
    for tid, val in [
        ("string", "x"),
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

# Property [parentFilter MQL Uniformity]: every MQL violation in parentFilter,
# including constructs that produce distinct error codes under filter, surfaces
# uniformly as the executor validation error with no mongod-side parse layer.
VECTORSEARCH_PARENT_FILTER_MQL_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"parent_mql_{tid}",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "parentFilter": flt,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$vectorSearch should reject a {tid} parentFilter as an executor error",
    )
    for tid, flt in [
        ("geo_near", {"year": {"$near": [0, 0]}}),
        ("text", {"$text": {"$search": "x"}}),
        ("comment", {"year": {"$comment": "x"}}),
        ("regex_op", {"year": {"$regex": "x"}}),
        ("unknown_top_level", {"$bad": 1}),
        ("dollar_prefixed_key", {"$year": 1}),
        ("not_top_level", {"$not": {"year": 1}}),
        ("empty_and", {"$and": []}),
    ]
]

# Property [parentFilter Field Not Indexed]: a parentFilter referencing a field
# not indexed as the filter type is a hard error rather than a silent miss.
VECTORSEARCH_PARENT_FILTER_FIELD_NOT_INDEXED_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "parent_filter_field_not_indexed",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "parentFilter": {"_id": 1},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should reject a parentFilter on a field not indexed as the filter type",
    ),
]

VECTORSEARCH_PARENT_FILTER_ALL_TESTS = (
    VECTORSEARCH_PARENT_FILTER_NULL_TESTS
    + VECTORSEARCH_PARENT_FILTER_FLAT_TESTS
    + VECTORSEARCH_PARENT_FILTER_OPERATOR_TESTS
    + VECTORSEARCH_PARENT_FILTER_COMBINATOR_TESTS
    + VECTORSEARCH_PARENT_FILTER_VALUE_TYPE_TESTS
    + VECTORSEARCH_PARENT_FILTER_TYPE_ERROR_TESTS
    + VECTORSEARCH_PARENT_FILTER_MQL_ERROR_TESTS
    + VECTORSEARCH_PARENT_FILTER_FIELD_NOT_INDEXED_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(VECTORSEARCH_PARENT_FILTER_ALL_TESTS))
def test_vectorSearch_parent_filter(test_case: VectorSearchTest, engine_client, request):
    """$vectorSearch: parentFilter pre-filtering and errors."""
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
