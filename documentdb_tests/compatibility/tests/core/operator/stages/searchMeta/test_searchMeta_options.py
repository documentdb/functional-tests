"""Tests for $searchMeta stage options (concurrent, returnScope)."""

from __future__ import annotations

import datetime
from collections.abc import Iterator

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp
from pymongo.collection import Collection

from documentdb_tests.compatibility.tests.core.operator.stages.searchMeta.utils.searchMeta_common import (  # noqa: E501
    open_search_collection,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import UNKNOWN_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF

pytestmark = pytest.mark.requires(search=True)


@pytest.fixture(scope="module")
def search_collection(engine_client, worker_id) -> Iterator[Collection]:
    """Module-scoped metadata search collection (default + alt_idx indexes)."""
    with open_search_collection(engine_client, worker_id, f"{__name__}::search_collection") as coll:
        yield coll


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

# Property [ReturnScope Type]: the returnScope option must be a document, so a
# value of any non-document BSON type is rejected. A null returnScope is treated
# as the default, so it is excluded.
SEARCHMETA_RETURN_SCOPE_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"return_scope_type_{tid}",
        pipeline=[
            {"$searchMeta": {"text": {"query": "quick", "path": "title"}, "returnScope": val}}
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$searchMeta should reject a {tid} returnScope option as a non-document",
    )
    for tid, val in [
        ("string", "title"),
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("bool", True),
        ("array", [{"path": "title"}]),
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

# Property [ReturnScope Path Required]: a returnScope document must carry a path
# field, so a document missing it is rejected.
SEARCHMETA_RETURN_SCOPE_PATH_REQUIRED_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "return_scope_empty",
        pipeline=[
            {"$searchMeta": {"text": {"query": "quick", "path": "title"}, "returnScope": {}}}
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject a returnScope document with no path field",
    ),
    StageTestCase(
        "return_scope_other_field",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "returnScope": {"other": "title"},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject a returnScope document that omits the required path field",
    ),
]

# Property [ReturnScope Path Type]: the returnScope path field must be a string,
# so a non-string path is rejected.
SEARCHMETA_RETURN_SCOPE_PATH_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"return_scope_path_type_{tid}",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "returnScope": {"path": val},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$searchMeta should reject a {tid} returnScope path as a non-string",
    )
    for tid, val in [
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("bool", True),
        ("object", {"a": 1}),
        ("array", ["title"]),
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
    SEARCHMETA_CONCURRENT_OPTION_TESTS
    + SEARCHMETA_CONCURRENT_OPTION_TYPE_ERROR_TESTS
    + SEARCHMETA_RETURN_SCOPE_TYPE_ERROR_TESTS
    + SEARCHMETA_RETURN_SCOPE_PATH_REQUIRED_ERROR_TESTS
    + SEARCHMETA_RETURN_SCOPE_PATH_TYPE_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCHMETA_OPTION_TESTS))
def test_searchMeta_options(search_collection, test_case: StageTestCase):
    """Test $searchMeta concurrent and returnScope stage options."""
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
