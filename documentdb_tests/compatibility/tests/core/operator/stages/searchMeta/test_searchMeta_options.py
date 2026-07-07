"""Tests for the $searchMeta concurrent stage option."""

from __future__ import annotations

import datetime

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import UNKNOWN_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF

pytestmark = pytest.mark.requires(search=True)


# Property [Concurrent Option]: the concurrent option is a recognized boolean
# stage option, so both true and false are accepted with no coercion and the
# metadata count is still returned.
SEARCHMETA_CONCURRENT_OPTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"concurrent_{label}",
        pipeline=[
            {"$searchMeta": {"text": {"query": "quick", "path": "title"}, "concurrent": val}}
        ],
        expected=[{"count": {"lowerBound": Int64(3)}}],
        msg=f"$searchMeta should accept a {label} concurrent option and still return its count",
    )
    for label, val in [("true", True), ("false", False)]
]

# Property [Concurrent Option Type]: the concurrent option must be a boolean, so
# a value of any non-boolean BSON type is rejected with no coercion. A null
# concurrent is treated as the default, so it is excluded.
SEARCHMETA_CONCURRENT_OPTION_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"concurrent_type_{tid}",
        pipeline=[
            {"$searchMeta": {"text": {"query": "quick", "path": "title"}, "concurrent": val}}
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$searchMeta should reject a {tid} concurrent option as a non-boolean",
    )
    for tid, val in [
        ("string", "true"),
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("object", {"a": 1}),
        ("array", [True]),
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

SEARCHMETA_OPTION_TESTS: list[StageTestCase] = (
    SEARCHMETA_CONCURRENT_OPTION_TESTS + SEARCHMETA_CONCURRENT_OPTION_TYPE_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCHMETA_OPTION_TESTS))
def test_searchMeta_options(search_collection, test_case: StageTestCase):
    """Test $searchMeta concurrent stage option."""
    result = execute_command(
        search_collection,
        {
            "aggregate": search_collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
