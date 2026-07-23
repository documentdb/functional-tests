"""Tests for $search stage value typing and silent-empty behavior."""

from __future__ import annotations

import datetime

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.search.utils.search_common import (
    FIXTURE_DOCS,
    create_dynamic_search_index,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    EXPRESSION_NOT_OBJECT_ERROR,
    FAILED_TO_PARSE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import (
    Len,
)
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ZERO,
)

pytestmark = pytest.mark.requires(search=True)


# Property [Stage Value Array Type]: a $search stage value that is an array is
# rejected with the array-specific parse error, a distinct code path from the
# non-object scalar value.
SEARCH_STAGE_VALUE_ARRAY_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "stage_value_empty_array",
        pipeline=[{"$search": []}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$search should reject an empty-array stage value with the array-specific parse error",
    ),
    StageTestCase(
        "stage_value_array_of_object",
        pipeline=[{"$search": [{"text": {"query": "quick", "path": "title"}}]}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$search should reject an array stage value even when it wraps a valid operator object",
    ),
    StageTestCase(
        "stage_value_array_of_scalar",
        pipeline=[{"$search": [1]}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$search should reject an array stage value of a scalar element with the array error",
    ),
]

# Property [Stage Value Scalar Type]: a $search stage value that is any scalar or
# null is rejected as a non-object, and null is not treated as a missing argument.
SEARCH_STAGE_VALUE_SCALAR_ERROR_TESTS: list[StageTestCase] = [
    *[
        StageTestCase(
            f"stage_value_{tid}",
            pipeline=[{"$search": val}],
            error_code=EXPRESSION_NOT_OBJECT_ERROR,
            msg=f"$search should reject a {tid} stage value as a non-object",
        )
        for tid, val in [
            ("string", "quick"),
            ("int32", 1),
            ("int64", Int64(1)),
            ("double", 1.5),
            ("decimal128", DECIMAL128_ZERO),
            ("bool", True),
            ("object_id", ObjectId("0123456789abcdef01234567")),
            ("datetime", datetime.datetime(2020, 1, 1)),
            ("timestamp", Timestamp(1, 1)),
            ("binary", Binary(b"\x00")),
            ("regex", Regex("a")),
            ("code", Code("x")),
            ("min_key", MinKey()),
            ("max_key", MaxKey()),
        ]
    ],
    StageTestCase(
        "stage_value_null",
        pipeline=[{"$search": None}],
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="$search should reject a null stage value as a non-object, not treat it as missing",
    ),
]

SEARCH_STAGE_VALUE_ERROR_TESTS = (
    SEARCH_STAGE_VALUE_ARRAY_ERROR_TESTS + SEARCH_STAGE_VALUE_SCALAR_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_STAGE_VALUE_ERROR_TESTS))
def test_search_stage_value_type_errors(indexed_collection, test_case: StageTestCase):
    """Test $search rejects a non-object stage value, distinguishing array from scalar/null."""
    result = execute_command(
        indexed_collection,
        {"aggregate": indexed_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)


# Property [Silent Empty Result]: a $search against a nonexistent collection or a
# collection with no search index returns no documents and no error.
SEARCH_SILENT_EMPTY_TESTS: list[StageTestCase] = [
    StageTestCase(
        "empty_nonexistent_collection",
        docs=None,
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}}},
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search on a nonexistent collection should return no documents without error",
    ),
    StageTestCase(
        "empty_no_search_index",
        docs=FIXTURE_DOCS,
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}}},
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search on a collection with no search index should return no documents without error",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_SILENT_EMPTY_TESTS))
def test_search_silent_empty_cases(collection, test_case: StageTestCase):
    """Test $search returns a silent empty result for a missing collection or missing index."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection, {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}}
    )
    assertResult(
        result,
        expected=test_case.expected,
        msg=test_case.msg,
        raw_res=True,
    )


# Property [Empty Indexed Collection]: a $search against a collection that has a
# search index but no documents returns no documents and no error.
@pytest.mark.aggregate
def test_search_empty_indexed_collection(collection):
    """Test $search returns a silent empty result on an empty but indexed collection."""
    collection.database.create_collection(collection.name)
    create_dynamic_search_index(collection)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$search": {"text": {"query": "quick", "path": "title"}}}],
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected={"cursor.firstBatch": Len(0)},
        msg="$search on an empty indexed collection should return no documents without error",
        raw_res=True,
    )
