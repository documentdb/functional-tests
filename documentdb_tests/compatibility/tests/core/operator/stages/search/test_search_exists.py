"""Tests for the $search exists operator."""

from __future__ import annotations

import datetime

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
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
)

pytestmark = pytest.mark.requires(search=True)


# Property [Exists Field Presence]: exists selects only the documents where the
# named field is present, and inside a compound mustNot clause selects the
# complement (the absent-field documents).
SEARCH_EXISTS_PRESENCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "exists_field_present",
        pipeline=[{"$search": {"exists": {"path": "body"}}}],
        expected={"cursor.firstBatch": [Len(2), Contains("_id", 1), Contains("_id", 2)]},
        msg="$search exists should select only the documents where the named field is present",
    ),
    StageTestCase(
        "exists_nonexistent_field",
        pipeline=[{"$search": {"exists": {"path": "nope"}}}],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search exists should match nothing for a field no document carries",
    ),
    StageTestCase(
        "exists_compound_must_not_complement",
        pipeline=[
            {"$search": {"compound": {"mustNot": [{"exists": {"path": "body"}}]}}},
        ],
        expected={
            "cursor.firstBatch": [Len(16), *[Contains("_id", _id) for _id in list(range(3, 19))]]
        },
        msg="$search exists inside a compound mustNot should select the complement of the "
        "present-field documents",
    ),
]

# Property [Exists Path No Validation]: an empty or dotted absent path resolves to
# no covered field and returns no documents without field-path validation or error.
SEARCH_EXISTS_PATH_NO_VALIDATION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "exists_path_empty",
        pipeline=[{"$search": {"exists": {"path": ""}}}],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search exists should treat an empty path as an absent field and match nothing "
        "without error",
    ),
    StageTestCase(
        "exists_path_dotted",
        pipeline=[{"$search": {"exists": {"path": "a.b"}}}],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search exists should treat a dotted absent path as an absent field and match "
        "nothing without field-path validation",
    ),
]

SEARCH_EXISTS_TESTS = SEARCH_EXISTS_PRESENCE_TESTS + SEARCH_EXISTS_PATH_NO_VALIDATION_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_EXISTS_TESTS))
def test_search_exists_cases(indexed_collection, test_case: StageTestCase):
    """Test $search exists field presence and path no-validation."""
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


# Property [Exists Path Type Rejection]: exists.path is string-only, so a path of
# any non-string type - including the document forms and the array of paths that
# text and wildcard accept - is rejected.
SEARCH_EXISTS_PATH_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"exists_path_type_{tid}",
        pipeline=[{"$search": {"exists": {"path": val}}}],
        error_code=UNKNOWN_ERROR,
        msg=f"$search exists should reject a {tid} path as a non-string type",
    )
    for tid, val in [
        ("object", {"value": "body"}),
        ("array", ["body"]),
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("bool", True),
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

# Property [Exists Path Required]: a missing or null exists.path is treated as
# absent and produces a spec validation error.
SEARCH_EXISTS_PATH_REQUIRED_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "exists_path_missing",
        pipeline=[{"$search": {"exists": {}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search exists should reject a missing path as required",
    ),
    StageTestCase(
        "exists_path_null",
        pipeline=[{"$search": {"exists": {"path": None}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search exists should reject a null path treated as missing",
    ),
]

# Property [Exists Unknown Sub-field]: an unrecognized exists sub-field produces a
# spec validation error.
SEARCH_EXISTS_UNKNOWN_FIELD_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "exists_unknown_field",
        pipeline=[{"$search": {"exists": {"path": "body", "bogus": 1}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search exists should reject an unrecognized sub-field",
    ),
]

SEARCH_EXISTS_ERROR_TESTS = (
    SEARCH_EXISTS_PATH_TYPE_ERROR_TESTS
    + SEARCH_EXISTS_PATH_REQUIRED_ERROR_TESTS
    + SEARCH_EXISTS_UNKNOWN_FIELD_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_EXISTS_ERROR_TESTS))
def test_search_exists_errors(indexed_collection, test_case: StageTestCase):
    """Test $search exists rejects non-string, missing/null, and unknown-field paths."""
    result = execute_command(
        indexed_collection,
        {"aggregate": indexed_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)
