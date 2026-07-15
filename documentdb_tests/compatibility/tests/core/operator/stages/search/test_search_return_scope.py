"""Tests for the $search returnScope option against embedded-document scopes."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.search.utils.search_common import (
    create_search_index,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework import fixtures
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import UNKNOWN_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Contains, Len

pytestmark = pytest.mark.requires(search=True)

_SCOPE_DOCS = [
    {
        "_id": 1,
        "groups": [
            {"gid": "g1", "tags": [{"name": "quick"}, {"name": "slow"}]},
            {"gid": "g2", "tags": [{"name": "lazy"}]},
        ],
    },
    {"_id": 2, "groups": [{"gid": "g3", "tags": [{"name": "quick"}]}]},
    {"_id": 3, "groups": [{"gid": "g4", "tags": [{"name": "lazy"}]}]},
]

# The scope path (groups) must be indexed as embeddedDocuments with a non-empty
# storedSource for returnScope to reshape results to it.
_SCOPE_INDEX_DEFINITION = {
    "mappings": {
        "dynamic": False,
        "fields": {
            "groups": {
                "type": "embeddedDocuments",
                "storedSource": True,
                "fields": {
                    "gid": {"type": "token"},
                    "tags": {"type": "embeddedDocuments", "dynamic": True},
                },
            }
        },
    }
}


@pytest.fixture(scope="module")
def scoped_collection(engine_client, worker_id):
    """A module-scoped collection with nested embeddedDocuments (groups -> tags)
    and a stored source on groups, so returnScope can return the matched group
    scope rather than the whole parent document."""
    db_name = fixtures.generate_database_name("stages_search_return_scope", worker_id)
    fixtures.cleanup_database(engine_client, db_name)
    db = engine_client[db_name]
    coll = db["scoped"]
    coll.insert_many(_SCOPE_DOCS)
    create_search_index(coll, _SCOPE_INDEX_DEFINITION)
    yield coll
    fixtures.cleanup_database(engine_client, db_name)


_EMBEDDED_OPERATOR = {
    "embeddedDocument": {
        "path": "groups.tags",
        "operator": {"text": {"query": "quick", "path": "groups.tags.name"}},
    }
}

# Property [returnScope Result Shape]: a non-empty returnScope whose path is an
# ancestor of the operator path returns the matched scope sub-documents in place
# of the parent documents.
SEARCH_RETURN_SCOPE_SUCCESS_TESTS: list[StageTestCase] = [
    StageTestCase(
        "return_scope_returns_matched_scopes",
        pipeline=[
            {
                "$search": {
                    **_EMBEDDED_OPERATOR,
                    "returnStoredSource": True,
                    "returnScope": {"path": "groups"},
                }
            }
        ],
        expected={"cursor.firstBatch": [Len(2), Contains("gid", "g1"), Contains("gid", "g3")]},
        msg="$search returnScope should return only the matched group scopes, not the parent "
        "documents",
    ),
]

# Property [returnScope Requires Stored Source]: a non-empty returnScope is
# rejected unless returnStoredSource is enabled, even when the scope path is
# correctly indexed.
SEARCH_RETURN_SCOPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "return_scope_without_return_stored_source",
        pipeline=[{"$search": {**_EMBEDDED_OPERATOR, "returnScope": {"path": "groups"}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search should reject a non-empty returnScope when returnStoredSource is not enabled",
    ),
]

SEARCH_RETURN_SCOPE_TESTS = SEARCH_RETURN_SCOPE_SUCCESS_TESTS + SEARCH_RETURN_SCOPE_ERROR_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_RETURN_SCOPE_TESTS))
def test_search_return_scope_cases(scoped_collection, test_case: StageTestCase):
    """Test $search returnScope result reshaping and its returnStoredSource requirement."""
    result = execute_command(
        scoped_collection,
        {"aggregate": scoped_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        raw_res=True,
    )
