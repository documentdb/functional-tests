"""Tests for explain verbosity modes and response structure.

Covers the response sections produced by each verbosity mode (queryPlanner,
executionStats, allPlansExecution) and the behavioral differences between modes
(query execution and rejected-plan statistics).
"""

import pytest
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Exists, IsType, NotExists

pytestmark = pytest.mark.admin


RESPONSE_FIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="queryPlanner_root",
        docs=[{"_id": i, "a": i % 5} for i in range(20)],
        command=lambda ctx: {
            "explain": {"find": ctx.collection, "filter": {"a": 1}},
            "verbosity": "queryPlanner",
        },
        expected={"queryPlanner": Exists()},
        msg="queryPlanner should contain queryPlanner",
    ),
    CommandTestCase(
        id="queryPlanner_parsedQuery",
        docs=[{"_id": i, "a": i % 5} for i in range(20)],
        command=lambda ctx: {
            "explain": {"find": ctx.collection, "filter": {"a": 1}},
            "verbosity": "queryPlanner",
        },
        expected={"queryPlanner.parsedQuery": Exists()},
        msg="queryPlanner should contain queryPlanner.parsedQuery",
    ),
    CommandTestCase(
        id="queryPlanner_winningPlan",
        docs=[{"_id": i, "a": i % 5} for i in range(20)],
        command=lambda ctx: {
            "explain": {"find": ctx.collection, "filter": {"a": 1}},
            "verbosity": "queryPlanner",
        },
        expected={"queryPlanner.winningPlan": Exists()},
        msg="queryPlanner should contain queryPlanner.winningPlan",
    ),
    CommandTestCase(
        id="queryPlanner_namespace",
        docs=[{"_id": i, "a": i % 5} for i in range(20)],
        command=lambda ctx: {
            "explain": {"find": ctx.collection, "filter": {"a": 1}},
            "verbosity": "queryPlanner",
        },
        expected={"queryPlanner.namespace": IsType("string")},
        msg="queryPlanner should contain queryPlanner.namespace",
    ),
    CommandTestCase(
        id="executionStats_root",
        docs=[{"_id": i, "a": i % 5} for i in range(20)],
        command=lambda ctx: {
            "explain": {"find": ctx.collection, "filter": {"a": 1}},
            "verbosity": "executionStats",
        },
        expected={"executionStats": Exists()},
        msg="executionStats should contain executionStats",
    ),
    CommandTestCase(
        id="executionStats_executionSuccess",
        docs=[{"_id": i, "a": i % 5} for i in range(20)],
        command=lambda ctx: {
            "explain": {"find": ctx.collection, "filter": {"a": 1}},
            "verbosity": "executionStats",
        },
        expected={"executionStats.executionSuccess": IsType("bool")},
        msg="executionStats should contain executionStats.executionSuccess",
    ),
    CommandTestCase(
        id="executionStats_nReturned",
        docs=[{"_id": i, "a": i % 5} for i in range(20)],
        command=lambda ctx: {
            "explain": {"find": ctx.collection, "filter": {"a": 1}},
            "verbosity": "executionStats",
        },
        expected={"executionStats.nReturned": IsType("int")},
        msg="executionStats should contain executionStats.nReturned",
    ),
    CommandTestCase(
        id="executionStats_executionTimeMillis",
        docs=[{"_id": i, "a": i % 5} for i in range(20)],
        command=lambda ctx: {
            "explain": {"find": ctx.collection, "filter": {"a": 1}},
            "verbosity": "executionStats",
        },
        expected={"executionStats.executionTimeMillis": Exists()},
        msg="executionStats should contain executionStats.executionTimeMillis",
    ),
    CommandTestCase(
        id="executionStats_totalKeysExamined",
        docs=[{"_id": i, "a": i % 5} for i in range(20)],
        command=lambda ctx: {
            "explain": {"find": ctx.collection, "filter": {"a": 1}},
            "verbosity": "executionStats",
        },
        expected={"executionStats.totalKeysExamined": IsType("int")},
        msg="executionStats should contain executionStats.totalKeysExamined",
    ),
    CommandTestCase(
        id="executionStats_totalDocsExamined",
        docs=[{"_id": i, "a": i % 5} for i in range(20)],
        command=lambda ctx: {
            "explain": {"find": ctx.collection, "filter": {"a": 1}},
            "verbosity": "executionStats",
        },
        expected={"executionStats.totalDocsExamined": IsType("int")},
        msg="executionStats should contain executionStats.totalDocsExamined",
    ),
    CommandTestCase(
        id="allPlans_queryPlanner",
        docs=[{"_id": i, "a": i % 5} for i in range(20)],
        command=lambda ctx: {
            "explain": {"find": ctx.collection, "filter": {"a": 1}},
            "verbosity": "allPlansExecution",
        },
        expected={"queryPlanner": Exists()},
        msg="allPlansExecution should contain queryPlanner",
    ),
    CommandTestCase(
        id="allPlans_executionStats",
        docs=[{"_id": i, "a": i % 5} for i in range(20)],
        command=lambda ctx: {
            "explain": {"find": ctx.collection, "filter": {"a": 1}},
            "verbosity": "allPlansExecution",
        },
        expected={"executionStats": Exists()},
        msg="allPlansExecution should contain executionStats",
    ),
    CommandTestCase(
        id="allPlans_rejectedPlans",
        docs=[{"_id": i, "a": i % 5} for i in range(20)],
        command=lambda ctx: {
            "explain": {"find": ctx.collection, "filter": {"a": 1}},
            "verbosity": "allPlansExecution",
        },
        expected={"queryPlanner.rejectedPlans": IsType("array")},
        msg="allPlansExecution should contain queryPlanner.rejectedPlans",
    ),
]


@pytest.mark.parametrize("test", pytest_params(RESPONSE_FIELD_TESTS))
def test_explain_response_contains_field(collection, test):
    """Test each verbosity-mode response contains the expected response field."""
    collection = test.prepare(collection.database, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


MODE_BEHAVIOR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="queryPlanner_omits_executionStats",
        docs=[{"_id": i, "a": i % 5} for i in range(20)],
        command=lambda ctx: {
            "explain": {"find": ctx.collection, "filter": {"a": 1}},
            "verbosity": "queryPlanner",
        },
        expected={"executionStats": NotExists()},
        msg="queryPlanner must not execute",
    ),
    CommandTestCase(
        id="executionStats_excludes_rejected_plan_stats",
        docs=[{"_id": i, "a": i % 5, "b": i % 3} for i in range(60)],
        indexes=[IndexModel([("a", 1)]), IndexModel([("a", 1), ("b", 1)])],
        command=lambda ctx: {
            "explain": {"find": ctx.collection, "filter": {"a": 2, "b": 1}},
            "verbosity": "executionStats",
        },
        expected={"executionStats.allPlansExecution": NotExists()},
        msg="executionStats mode should not include rejected-plan execution",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MODE_BEHAVIOR_TESTS))
def test_explain_verbosity_mode_behavior(collection, test):
    """Test verbosity modes include/exclude execution sections as documented."""
    collection = test.prepare(collection.database, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
