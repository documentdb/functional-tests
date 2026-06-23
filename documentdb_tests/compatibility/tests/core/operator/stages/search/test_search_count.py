"""Tests for the $search count option and count metadata."""

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
    Contains,
    Eq,
    Len,
)
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
)

pytestmark = pytest.mark.requires(search=True)


# Property [Count Option Default]: an empty count document is accepted (the
# default lowerBound behavior) and the search still returns its matches.
SEARCH_COUNT_OPTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "count_empty_document",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}, "count": {}}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search should accept an empty count document and still return its matches",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_COUNT_OPTION_TESTS))
def test_search_count_option_cases(indexed_collection, test_case: StageTestCase):
    """Test $search accepts the count option document."""
    result = execute_command(
        indexed_collection,
        {"aggregate": indexed_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(
        result,
        expected=test_case.expected,
        msg=test_case.msg,
        raw_res=True,
    )


# Property [Count Metadata]: a count option exposes the result count through
# $$SEARCH_META.count under the requested type key, and accepts count.threshold
# for both count types.
SEARCH_COUNT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "count_total",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}, "count": {"type": "total"}}},
            {"$limit": 1},
            {"$project": {"_id": 0, "count": "$$SEARCH_META.count"}},
        ],
        expected={"count": {"total": Eq(Int64(3))}},
        msg="$search should expose an exact total result count through $$SEARCH_META",
    ),
    StageTestCase(
        "count_lower_bound",
        pipeline=[
            {
                "$search": {
                    "text": {"query": "quick", "path": "title"},
                    "count": {"type": "lowerBound"},
                }
            },
            {"$limit": 1},
            {"$project": {"_id": 0, "count": "$$SEARCH_META.count"}},
        ],
        expected={"count": {"lowerBound": Eq(Int64(3))}},
        msg="$search should expose a lowerBound result count through $$SEARCH_META",
    ),
    StageTestCase(
        "count_total_threshold",
        pipeline=[
            {
                "$search": {
                    "text": {"query": "quick", "path": "title"},
                    "count": {"type": "total", "threshold": 10_000},
                }
            },
            {"$limit": 1},
            {"$project": {"_id": 0, "count": "$$SEARCH_META.count"}},
        ],
        expected={"count": {"total": Eq(Int64(3))}},
        msg="$search should accept count.threshold for a total count and still expose the "
        "exact count",
    ),
    StageTestCase(
        "count_lower_bound_threshold",
        pipeline=[
            {
                "$search": {
                    "text": {"query": "quick", "path": "title"},
                    "count": {"type": "lowerBound", "threshold": 10_000},
                }
            },
            {"$limit": 1},
            {"$project": {"_id": 0, "count": "$$SEARCH_META.count"}},
        ],
        expected={"count": {"lowerBound": Eq(Int64(3))}},
        msg="$search should accept count.threshold for a lowerBound count and still expose "
        "the exact count",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_COUNT_TESTS))
def test_search_count_metadata(indexed_collection, test_case: StageTestCase):
    """Test $search exposes a result count through $$SEARCH_META.count."""
    result = execute_command(
        indexed_collection,
        {"aggregate": indexed_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, expected=test_case.expected, msg=test_case.msg)


# Property [Count Type Enum]: count.type must be one of the recognized count-type
# strings, so an unrecognized string or a non-string type is rejected (null is
# the default).
SEARCH_COUNT_TYPE_ENUM_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "count_type_bogus",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}, "count": {"type": "bogus"}}},
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search should reject a count.type outside the recognized set of count types",
    ),
    *[
        StageTestCase(
            f"count_type_type_{tid}",
            pipeline=[
                {"$search": {"text": {"query": "quick", "path": "title"}, "count": {"type": val}}},
            ],
            error_code=SEARCH_EXECUTOR_ERROR,
            msg=f"$search should reject a {tid} count.type as a non-string",
        )
        for tid, val in [
            ("int32", 1),
            ("int64", Int64(1)),
            ("double", 1.5),
            ("bool", True),
            ("object", {"a": 1}),
            ("array", ["total"]),
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
    ],
]

# Property [Count threshold Value And Type]: count.threshold must be a
# non-negative integer (null is the default).
SEARCH_COUNT_THRESHOLD_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "count_threshold_negative",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}, "count": {"threshold": -1}}},
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search should reject a negative count.threshold",
    ),
    *[
        StageTestCase(
            f"count_threshold_type_{tid}",
            pipeline=[
                {
                    "$search": {
                        "text": {"query": "quick", "path": "title"},
                        "count": {"threshold": val},
                    }
                },
            ],
            error_code=SEARCH_EXECUTOR_ERROR,
            msg=f"$search should reject a {tid} count.threshold as a non-integer",
        )
        for tid, val in [
            ("string", "10"),
            ("double", 1.5),
            ("bool", True),
            ("object", {"a": 1}),
            ("array", [10]),
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
    ],
]

SEARCH_COUNT_ERROR_TESTS = SEARCH_COUNT_TYPE_ENUM_ERROR_TESTS + SEARCH_COUNT_THRESHOLD_ERROR_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_COUNT_ERROR_TESTS))
def test_search_count_errors(indexed_collection, test_case: StageTestCase):
    """Test $search count type/enum and threshold validation errors."""
    result = execute_command(
        indexed_collection,
        {"aggregate": indexed_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)
