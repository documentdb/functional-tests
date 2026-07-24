"""Tests for the $vectorSearch stage: filter pre-filtering."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Int64,
)

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import (
    Contains,
    Len,
)
from documentdb_tests.framework.test_constants import (
    DOUBLE_ZERO,
)

from .utils.vectorSearch_common import (
    _FILTER_OID_A,
    _FILTER_UUID_A,
    VectorSearchTest,
)

pytestmark = pytest.mark.requires(search=True)

# Property [filter Match All]: an empty filter document applies no predicate and
# retains every document.
VECTORSEARCH_FILTER_MATCH_ALL_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "match_all_empty_filter",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "filter": {},
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
        msg="$vectorSearch should retain every document for an empty filter",
    ),
]

# Property [filter Per-Field Operators]: each supported per-field operator, and
# the $eq shorthand, pre-filters to exactly the documents matching that predicate.
VECTORSEARCH_FILTER_OPERATOR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"operator_{tid}",
        raw_res=True,
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
            },
        ],
        expected={"cursor.firstBatch": [Len(len(ids)), *(Contains("_id", i) for i in ids)]},
        msg=f"$vectorSearch should pre-filter with the {tid} operator",
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

# Property [filter Combinators]: top-level $and, $or, $nor, and implicit
# multi-field AND compose their arms into the correct combined predicate.
VECTORSEARCH_FILTER_COMBINATOR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"combinator_{tid}",
        raw_res=True,
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
            },
        ],
        expected={"cursor.firstBatch": [Len(len(ids)), *(Contains("_id", i) for i in ids)]},
        msg=f"$vectorSearch should compose the {tid} combinator correctly",
    )
    for tid, flt, ids in [
        ("and", {"$and": [{"cat": "y"}, {"year": {"$gte": 2010}}]}, [4, 5]),
        ("or", {"$or": [{"cat": "x"}, {"year": 2001}]}, [1, 2, 3]),
        ("nor", {"$nor": [{"cat": "x"}]}, [3, 4, 5]),
        ("implicit_and", {"cat": "y", "active": True}, [3, 5]),
    ]
]

# Property [filter Value Types]: each supported predicate value type pre-filters
# correctly, including null as a direct value and element membership on an
# array-valued field.
VECTORSEARCH_FILTER_VALUE_TYPE_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"value_type_{tid}",
        raw_res=True,
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
            },
        ],
        expected={"cursor.firstBatch": [Len(len(ids)), *(Contains("_id", i) for i in ids)]},
        msg=f"$vectorSearch should pre-filter with a {tid} predicate value",
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

# Property [filter Numeric In Mixing]: a $in/$nin list mixing int and double
# elements is accepted as same-type numeric and brackets by numeric value.
VECTORSEARCH_FILTER_NUMERIC_IN_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"numeric_in_{tid}",
        raw_res=True,
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
            },
        ],
        expected={"cursor.firstBatch": [Len(len(ids)), *(Contains("_id", i) for i in ids)]},
        msg=f"$vectorSearch should accept a mixed int/double {tid} list",
    )
    for tid, flt, ids in [
        ("in", {"rating": {"$in": [4.0, 5]}}, [3, 5]),
        ("nin", {"rating": {"$nin": [4.0, 5]}}, [1, 2, 4]),
    ]
]

# Property [filter Cross-Type Bracketing]: a predicate whose value type differs
# from the indexed field's type brackets to no match without erroring.
VECTORSEARCH_FILTER_CROSS_TYPE_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "cross_type_string_vs_numeric",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "filter": {"year": {"$gt": "a"}},
                }
            },
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$vectorSearch should return no results for a cross-type comparison without erroring",
    ),
]

# Property [filter Limit And Mode]: the filter is applied before limit, a filter
# matching nothing yields an empty result, and filtering is identical under ANN
# and ENN.
VECTORSEARCH_FILTER_LIMIT_MODE_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "applied_before_limit",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 1,
                    "filter": {"cat": "y"},
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 3)]},
        msg="$vectorSearch should apply the filter before limit truncates by score",
    ),
    VectorSearchTest(
        "matches_nothing_empty",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "filter": {"year": 3000},
                }
            },
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$vectorSearch should return an empty result for a filter that matches nothing",
    ),
    VectorSearchTest(
        "enn_filter",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "exact": True,
                    "limit": 5,
                    "filter": {"cat": "x"},
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(2), Contains("_id", 1), Contains("_id", 2)]},
        msg="$vectorSearch should apply the filter identically under ENN",
    ),
]

VECTORSEARCH_FILTER_ALL_TESTS = (
    VECTORSEARCH_FILTER_MATCH_ALL_TESTS
    + VECTORSEARCH_FILTER_OPERATOR_TESTS
    + VECTORSEARCH_FILTER_COMBINATOR_TESTS
    + VECTORSEARCH_FILTER_VALUE_TYPE_TESTS
    + VECTORSEARCH_FILTER_NUMERIC_IN_TESTS
    + VECTORSEARCH_FILTER_CROSS_TYPE_TESTS
    + VECTORSEARCH_FILTER_LIMIT_MODE_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(VECTORSEARCH_FILTER_ALL_TESTS))
def test_vectorSearch_filter(test_case: VectorSearchTest, engine_client, request):
    """$vectorSearch: filter pre-filtering."""
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
