"""Tests for setQuerySettings reject field error behavior.

Validates that reject: true blocks matching queries for find, distinct, and
aggregate commands at execution time.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.query_planning.utils.settings_test_case import (
    SettingsTestCase,
)
from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import QUERYSETTINGS_QUERY_REJECTED_ERROR
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = [pytest.mark.requires(cluster_admin=True), pytest.mark.no_parallel]

# Property [Reject Blocks Find]: reject: true blocks matching find queries.
# Property [Reject Blocks Distinct]: reject: true blocks matching distinct queries.
# Property [Reject Blocks Aggregate]: reject: true blocks matching aggregate queries.
SET_QUERY_SETTINGS_REJECT_ERROR_TESTS: list[SettingsTestCase] = [
    SettingsTestCase(
        "reject_blocks_find",
        setup_commands=lambda ctx: [
            {
                "setQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"b8": 1},
                    "$db": ctx.database,
                },
                "settings": {"reject": True},
            }
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"b8": 1},
        },
        error_code=QUERYSETTINGS_QUERY_REJECTED_ERROR,
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"b8": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="query matching reject: true setting should be rejected",
    ),
    SettingsTestCase(
        "reject_blocks_distinct",
        setup_commands=lambda ctx: [
            {
                "setQuerySettings": {
                    "distinct": ctx.collection,
                    "key": "x",
                    "query": {"rej_d1": 1},
                    "$db": ctx.database,
                },
                "settings": {"reject": True},
            }
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {"rej_d1": 1},
        },
        error_code=QUERYSETTINGS_QUERY_REJECTED_ERROR,
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "distinct": ctx.collection,
                    "key": "x",
                    "query": {"rej_d1": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="distinct query matching reject: true should be rejected",
    ),
    SettingsTestCase(
        "reject_blocks_aggregate",
        setup_commands=lambda ctx: [
            {
                "setQuerySettings": {
                    "aggregate": ctx.collection,
                    "pipeline": [{"$match": {"rej_a1": 1}}],
                    "$db": ctx.database,
                },
                "settings": {"reject": True},
            }
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"rej_a1": 1}}],
            "cursor": {},
        },
        error_code=QUERYSETTINGS_QUERY_REJECTED_ERROR,
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "aggregate": ctx.collection,
                    "pipeline": [{"$match": {"rej_a1": 1}}],
                    "$db": ctx.database,
                }
            }
        ],
        msg="aggregate query matching reject: true should be rejected",
    ),
]


@pytest.mark.admin
@pytest.mark.parametrize("test", pytest_params(SET_QUERY_SETTINGS_REJECT_ERROR_TESTS))
def test_setQuerySettings_reject_errors(collection, test):
    """Test that reject: true blocks matching queries."""
    ctx = CommandContext.from_collection(collection)
    try:
        for cmd in test.build_setup(ctx):
            r = execute_admin_command(collection, cmd)
            ctx.setup_results.append(r)
        result = execute_command(collection, test.build_command(ctx))
        assertResult(result, error_code=test.error_code, msg=test.msg)
    finally:
        for cmd in test.build_cleanup(ctx):
            try:
                execute_admin_command(collection, cmd)
            except Exception:
                pass
