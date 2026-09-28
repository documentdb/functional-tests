"""Tests for the $search queryString operator."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import UNKNOWN_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Contains, Len

pytestmark = pytest.mark.requires(search=True)


# Property [queryString Default Path]: a bare query term is matched against the
# defaultPath, returning every document whose defaultPath contains the term.
SEARCH_QUERYSTRING_DEFAULT_PATH_TESTS: list[StageTestCase] = [
    StageTestCase(
        "querystring_default_path_term",
        pipeline=[{"$search": {"queryString": {"defaultPath": "title", "query": "quick"}}}],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search queryString should match a bare term against the defaultPath",
    ),
]

# Property [queryString Boolean Operators]: the Lucene AND and OR operators
# intersect and union the per-term matches respectively.
SEARCH_QUERYSTRING_BOOLEAN_TESTS: list[StageTestCase] = [
    StageTestCase(
        "querystring_boolean_and",
        pipeline=[
            {"$search": {"queryString": {"defaultPath": "title", "query": "quick AND brown"}}}
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 1)]},
        msg="$search queryString AND should match only documents containing both terms",
    ),
    StageTestCase(
        "querystring_boolean_or",
        pipeline=[
            {"$search": {"queryString": {"defaultPath": "title", "query": "quick OR turtle"}}}
        ],
        expected={
            "cursor.firstBatch": [
                Len(4),
                Contains("_id", 1),
                Contains("_id", 2),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search queryString OR should match documents containing either term",
    ),
]

# Property [queryString Field Scoping]: a field:term clause overrides the
# defaultPath and matches against the named field instead.
SEARCH_QUERYSTRING_FIELD_TESTS: list[StageTestCase] = [
    StageTestCase(
        "querystring_field_scoped",
        pipeline=[{"$search": {"queryString": {"defaultPath": "title", "query": "body:quick"}}}],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 2)]},
        msg="$search queryString should scope a field:term clause to the named field, not the "
        "defaultPath",
    ),
]

SEARCH_QUERYSTRING_SUCCESS_TESTS = (
    SEARCH_QUERYSTRING_DEFAULT_PATH_TESTS
    + SEARCH_QUERYSTRING_BOOLEAN_TESTS
    + SEARCH_QUERYSTRING_FIELD_TESTS
)

# Property [queryString Validation]: queryString requires both defaultPath and
# query, and an unparseable query string is rejected.
SEARCH_QUERYSTRING_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "querystring_missing_query",
        pipeline=[{"$search": {"queryString": {"defaultPath": "title"}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search queryString should reject a spec missing the required query",
    ),
    StageTestCase(
        "querystring_missing_default_path",
        pipeline=[{"$search": {"queryString": {"query": "quick"}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search queryString should reject a spec missing the required defaultPath",
    ),
    StageTestCase(
        "querystring_unparseable_query",
        pipeline=[{"$search": {"queryString": {"defaultPath": "title", "query": "quick AND AND"}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search queryString should reject an unparseable Lucene query string",
    ),
]

SEARCH_QUERYSTRING_TESTS = SEARCH_QUERYSTRING_SUCCESS_TESTS + SEARCH_QUERYSTRING_ERROR_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_QUERYSTRING_TESTS))
def test_search_queryString_cases(indexed_collection, test_case: StageTestCase):
    """Test $search queryString default-path, boolean, field-scoped, and error cases."""
    result = execute_command(
        indexed_collection,
        {"aggregate": indexed_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        raw_res=True,
    )
