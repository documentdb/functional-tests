"""Tests for the $vectorSearch stage: filter predicate errors."""

from __future__ import annotations

import pytest
from bson import (
    Code,
    MaxKey,
    MinKey,
    Regex,
    Timestamp,
)
from bson.binary import Binary

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
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

# Property [filter Unsupported Operator Rejection]: a parseable filter operator
# that is not a supported comparison operator is rejected, each surfacing its own
# diagnostic message.
VECTORSEARCH_FILTER_OPERATOR_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "filter_operator_regex",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "filter": {"year": {"$regex": "x"}},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should reject an unsupported per-field filter operator",
    ),
    VectorSearchTest(
        "filter_operator_expr",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "filter": {"$expr": {"$gt": ["$year", 1]}},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should reject a $expr filter operator",
    ),
    VectorSearchTest(
        "filter_operator_json_schema",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "filter": {"$jsonSchema": {"required": ["year"]}},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should reject a $jsonSchema filter operator",
    ),
]

# Property [filter Value Type Rejection]: a predicate value whose BSON type is
# not among the supported filter value types is rejected.
VECTORSEARCH_FILTER_VALUE_TYPE_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"filter_value_type_{tid}",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "filter": {"year": val},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$vectorSearch should reject a {tid} filter value as an unsupported type",
    )
    for tid, val in [
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("object", {"a": 1}),
        ("array", [1, 2]),
        ("timestamp", Timestamp(1, 1)),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("non_uuid_binary", Binary(b"\x01\x02\x03")),
        ("minkey", {"$gt": MinKey()}),
        ("maxkey", {"$gt": MaxKey()}),
    ]
]

# Property [filter Field Not Indexed]: a filter referencing a field not indexed
# as the filter type is rejected, and a dollar-prefixed key is parsed as a
# top-level operator rather than a field name.
VECTORSEARCH_FILTER_FIELD_NOT_INDEXED_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "filter_field_not_indexed",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "filter": {"_id": 1},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should reject a filter on a field not indexed as the filter type",
    ),
    VectorSearchTest(
        "filter_dollar_prefixed_key",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "filter": {"$year": 1},
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$vectorSearch should parse a dollar-prefixed filter key as a top-level "
        "operator and reject it",
    ),
]

# Property [filter Element Constraints]: $in element lists must be non-empty,
# same-type, and free of null elements, and $exists requires a boolean argument.
VECTORSEARCH_FILTER_ELEMENT_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "filter_in_empty",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "filter": {"year": {"$in": []}},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should reject an empty $in list in a filter",
    ),
    VectorSearchTest(
        "filter_in_mixed_type",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "filter": {"year": {"$in": [1, "x"]}},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should reject a mixed-type $in list in a filter",
    ),
    VectorSearchTest(
        "filter_in_null_element",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "filter": {"year": {"$in": [None]}},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should reject a null element in a filter $in list",
    ),
    VectorSearchTest(
        "filter_exists_non_boolean",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "filter": {"year": {"$exists": 1}},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should reject a non-boolean $exists argument in a filter",
    ),
]

VECTORSEARCH_FILTER_PREDICATE_ERRORS_ALL_TESTS = (
    VECTORSEARCH_FILTER_OPERATOR_ERROR_TESTS
    + VECTORSEARCH_FILTER_VALUE_TYPE_ERROR_TESTS
    + VECTORSEARCH_FILTER_FIELD_NOT_INDEXED_ERROR_TESTS
    + VECTORSEARCH_FILTER_ELEMENT_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(VECTORSEARCH_FILTER_PREDICATE_ERRORS_ALL_TESTS))
def test_vectorSearch_filter_predicate_errors(test_case: VectorSearchTest, engine_client, request):
    """$vectorSearch: filter predicate errors."""
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
