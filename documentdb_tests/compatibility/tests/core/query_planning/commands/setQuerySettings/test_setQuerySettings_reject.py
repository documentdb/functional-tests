"""Tests for setQuerySettings reject field success behavior.

Validates that rejection does not affect unrelated query shapes,
and that reject can be reversed via update or removal.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.query_planning.utils.settings_test_case import (
    SettingsTestCase,
)
from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
)
from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = [pytest.mark.requires(cluster_admin=True), pytest.mark.no_parallel]

# Property [Reject Scope]: reject: true does not affect unrelated query shapes.
# Property [Reject Reversal via Update]: updating reject to false re-enables the query.
# Property [Reject Reversal via Remove]: removing the query setting re-enables the query.
# Property [Reject False Succeeds]: reject: false with indexHints allows the query.
SET_QUERY_SETTINGS_REJECT_SUCCESS_TESTS: list[SettingsTestCase] = [
    SettingsTestCase(
        "reject_does_not_affect_different_shape",
        setup_commands=lambda ctx: [
            {
                "setQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"rej_s1": 1},
                    "$db": ctx.database,
                },
                "settings": {"reject": True},
            }
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"rej_s2": 1},
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"rej_s1": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="different query shape should not be rejected",
    ),
    SettingsTestCase(
        "reject_reversed_by_update",
        setup_commands=lambda ctx: [
            {
                "setQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"rej_u1": 1},
                    "$db": ctx.database,
                },
                "settings": {"reject": True},
            },
            {
                "setQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"rej_u1": 1},
                    "$db": ctx.database,
                },
                "settings": {
                    "reject": False,
                    "indexHints": [
                        {
                            "ns": {"db": ctx.database, "coll": ctx.collection},
                            "allowedIndexes": ["_id_"],
                        }
                    ],
                },
            },
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"rej_u1": 1},
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"rej_u1": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="query should succeed after reject updated to false",
    ),
    SettingsTestCase(
        "reject_reversed_by_remove",
        setup_commands=lambda ctx: [
            {
                "setQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"rej_r1": 1},
                    "$db": ctx.database,
                },
                "settings": {"reject": True},
            },
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"rej_r1": 1},
                    "$db": ctx.database,
                }
            },
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"rej_r1": 1},
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"rej_r1": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="query should succeed after removeQuerySettings",
    ),
    SettingsTestCase(
        "reject_false_allows_query",
        setup_commands=lambda ctx: [
            {
                "setQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"rej_f1": 1},
                    "$db": ctx.database,
                },
                "settings": {
                    "reject": False,
                    "indexHints": [
                        {
                            "ns": {"db": ctx.database, "coll": ctx.collection},
                            "allowedIndexes": ["_id_"],
                        }
                    ],
                },
            }
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"rej_f1": 1},
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"rej_f1": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="query with reject: false should succeed",
    ),
]


@pytest.mark.admin
@pytest.mark.parametrize("test", pytest_params(SET_QUERY_SETTINGS_REJECT_SUCCESS_TESTS))
def test_setQuerySettings_reject_success(collection, test):
    """Test that reject scope and reversal work correctly."""
    ctx = CommandContext.from_collection(collection)
    try:
        for cmd in test.build_setup(ctx):
            r = execute_admin_command(collection, cmd)
            ctx.setup_results.append(r)
        result = execute_command(collection, test.build_command(ctx))
        assertSuccessPartial(result, test.build_expected(ctx), msg=test.msg)
    finally:
        for cmd in test.build_cleanup(ctx):
            try:
                execute_admin_command(collection, cmd)
            except Exception:
                pass
