"""Tests for aggregate command stable API behavior."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import API_STRICT_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [Stable API V1 Acceptance]: with apiStrict true, $collStats with
# only the count field is accepted.
AGGREGATE_STABLE_API_V1_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "stable_api_collstats_count_only",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$collStats": {"count": {}}}],
            "cursor": {},
            "apiVersion": "1",
            "apiStrict": True,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept $collStats with only count field under apiStrict true",
    ),
]

# Property [Stable API V1 Rejection]: with apiStrict true, the explain field
# and non-V1 stages are rejected with an API strict error.
AGGREGATE_STABLE_API_V1_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "stable_api_reject_explain",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "explain": True,
            "apiVersion": "1",
            "apiStrict": True,
        },
        error_code=API_STRICT_ERROR,
        msg="aggregate should reject explain field with apiStrict true",
    ),
    CommandTestCase(
        "stable_api_reject_currentop",
        command={
            "aggregate": 1,
            "pipeline": [{"$currentOp": {}}],
            "cursor": {},
            "apiVersion": "1",
            "apiStrict": True,
        },
        error_code=API_STRICT_ERROR,
        msg="aggregate should reject $currentOp stage with apiStrict true",
    ),
    CommandTestCase(
        "stable_api_reject_indexstats",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$indexStats": {}}],
            "cursor": {},
            "apiVersion": "1",
            "apiStrict": True,
        },
        error_code=API_STRICT_ERROR,
        msg="aggregate should reject $indexStats stage with apiStrict true",
    ),
    CommandTestCase(
        "stable_api_reject_listlocalsessions",
        command={
            "aggregate": 1,
            "pipeline": [{"$listLocalSessions": {}}],
            "cursor": {},
            "apiVersion": "1",
            "apiStrict": True,
        },
        error_code=API_STRICT_ERROR,
        msg="aggregate should reject $listLocalSessions stage with apiStrict true",
    ),
    CommandTestCase(
        "stable_api_reject_listsessions",
        command={
            "aggregate": 1,
            "pipeline": [{"$listSessions": {}}],
            "cursor": {},
            "apiVersion": "1",
            "apiStrict": True,
        },
        error_code=API_STRICT_ERROR,
        msg="aggregate should reject $listSessions stage with apiStrict true",
    ),
    CommandTestCase(
        "stable_api_reject_plancachestats",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$planCacheStats": {}}],
            "cursor": {},
            "apiVersion": "1",
            "apiStrict": True,
        },
        error_code=API_STRICT_ERROR,
        msg="aggregate should reject $planCacheStats stage with apiStrict true",
    ),
    CommandTestCase(
        "stable_api_reject_search",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$search": {"text": {"query": "test", "path": "x"}}}],
            "cursor": {},
            "apiVersion": "1",
            "apiStrict": True,
        },
        error_code=API_STRICT_ERROR,
        msg="aggregate should reject $search stage with apiStrict true",
    ),
    CommandTestCase(
        "stable_api_reject_collstats_latencystats",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$collStats": {"latencyStats": {}}}],
            "cursor": {},
            "apiVersion": "1",
            "apiStrict": True,
        },
        error_code=API_STRICT_ERROR,
        msg="aggregate should reject $collStats with latencyStats under apiStrict true",
    ),
    CommandTestCase(
        "stable_api_reject_collstats_storagestats",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$collStats": {"storageStats": {}}}],
            "cursor": {},
            "apiVersion": "1",
            "apiStrict": True,
        },
        error_code=API_STRICT_ERROR,
        msg="aggregate should reject $collStats with storageStats under apiStrict true",
    ),
]

AGGREGATE_STABLE_API_TESTS = (
    AGGREGATE_STABLE_API_V1_ACCEPTANCE_TESTS + AGGREGATE_STABLE_API_V1_REJECTION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_STABLE_API_TESTS))
def test_aggregate_stable_api(database_client, collection, test):
    """Test aggregate stable API acceptance and rejection."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
