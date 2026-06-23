"""Tests for the $search searchAfter and searchBefore pagination options."""

from __future__ import annotations

import datetime

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    SEARCH_EXECUTOR_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import (
    Eq,
    Len,
)
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
)

pytestmark = pytest.mark.requires(search=True)


def _search_ids(collection, spec: dict) -> list:
    """Run a $search spec and return the matched _id values in result order."""
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$search": spec}, {"$project": {"_id": 1}}],
            "cursor": {},
        },
    )
    return [doc["_id"] for doc in result["cursor"]["firstBatch"]]


def _sequence_token(collection, spec: dict, position: int) -> str:
    """Capture the searchSequenceToken of the result at the given position."""
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$search": spec},
                {"$project": {"tok": {"$meta": "searchSequenceToken"}}},
            ],
            "cursor": {},
        },
    )
    return str(result["cursor"]["firstBatch"][position]["tok"])


def _expected_id_order(ids: list) -> dict:
    """Build an assertResult expected dict asserting firstBatch holds exactly these
    _id values in this order."""
    expected: dict = {"cursor.firstBatch": Len(len(ids))}
    for i, _id in enumerate(ids):
        expected[f"cursor.firstBatch.{i}._id"] = Eq(_id)
    return expected


# Property [searchAfter Pagination]: searchAfter resumes the result stream
# immediately after the result whose searchSequenceToken is supplied, so paging
# from the first result's token yields exactly the remaining results in order.
@pytest.mark.aggregate
def test_search_after_pages_to_following_results(indexed_collection):
    """Test $search searchAfter resumes immediately after a captured sequence token."""
    spec = {"text": {"query": "quick", "path": "title"}}
    full_ids = _search_ids(indexed_collection, spec)
    first_token = _sequence_token(indexed_collection, spec, 0)
    result = execute_command(
        indexed_collection,
        {
            "aggregate": indexed_collection.name,
            "pipeline": [
                {"$search": {**spec, "searchAfter": first_token}},
                {"$project": {"_id": 1}},
            ],
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=_expected_id_order(full_ids[1:]),
        msg="$search searchAfter should resume immediately after the first result's token",
        raw_res=True,
    )


# Property [searchBefore Pagination]: searchBefore returns the results preceding
# the result whose searchSequenceToken is supplied, in reverse result order, so
# paging from the last result's token yields the earlier results reversed.
@pytest.mark.aggregate
def test_search_before_pages_to_preceding_results(indexed_collection):
    """Test $search searchBefore returns the results preceding a captured sequence token."""
    spec = {"text": {"query": "quick", "path": "title"}}
    full_ids = _search_ids(indexed_collection, spec)
    last_token = _sequence_token(indexed_collection, spec, len(full_ids) - 1)
    result = execute_command(
        indexed_collection,
        {
            "aggregate": indexed_collection.name,
            "pipeline": [
                {"$search": {**spec, "searchBefore": last_token}},
                {"$project": {"_id": 1}},
            ],
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=_expected_id_order(list(reversed(full_ids[:-1]))),
        msg="$search searchBefore should return the results preceding the last result's token "
        "in reverse order",
        raw_res=True,
    )


# Property [Pagination Token Type]: searchAfter and searchBefore are string-only
# pagination tokens, so a value of any non-string BSON type is rejected with no
# coercion. A null token is treated as omitted (a default), so it is excluded.
SEARCH_PAGINATION_TOKEN_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"{opt}_type_{tid}",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}, opt: val}},
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg=f"$search should reject a {tid} {opt} token as a non-string",
    )
    for opt in ("searchAfter", "searchBefore")
    for tid, val in [
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("bool", True),
        ("object", {"a": 1}),
        ("array", ["abc"]),
        ("objectid", ObjectId("0123456789abcdef01234567")),
        ("datetime", datetime.datetime(2020, 1, 1)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
    ]
]

# Property [Pagination Token Format]: a non-empty string that is not a valid
# encoded sequence token is rejected as a malformed token value.
SEARCH_PAGINATION_TOKEN_FORMAT_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"{opt}_bad_format",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}, opt: "not_a_token"}},
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg=f"$search should reject a malformed {opt} string as an invalid token value",
    )
    for opt in ("searchAfter", "searchBefore")
]

SEARCH_PAGINATION_ERROR_TESTS = (
    SEARCH_PAGINATION_TOKEN_TYPE_ERROR_TESTS + SEARCH_PAGINATION_TOKEN_FORMAT_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_PAGINATION_ERROR_TESTS))
def test_search_pagination_errors(indexed_collection, test_case: StageTestCase):
    """Test $search searchAfter and searchBefore reject non-string and malformed tokens."""
    result = execute_command(
        indexed_collection,
        {"aggregate": indexed_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)
