"""Tests for removeQuerySettings command behavioral verification.

Verifies that removeQuerySettings actually removes query settings from the
cluster, not just that it returns ok: 1.0. Uses $querySettings to observe
settings state before and after removal.
"""

from __future__ import annotations

from typing import Any

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

pytestmark = [pytest.mark.no_parallel]

# Property [Remove By Query Shape]: removeQuerySettings removes settings
# when given the original query shape, verified via $querySettings.
# Property [Remove By Hash]: removeQuerySettings removes settings when given
# the query shape hash string, verified via $querySettings.
# Property [Remove Distinct Shape]: removeQuerySettings removes settings for
# distinct query shapes, verified via $querySettings.
# Property [Remove Aggregate Shape]: removeQuerySettings removes settings for
# aggregate query shapes, verified via $querySettings.
# Property [Shape Matching Ignores Filter Values]: query shape matching uses
# field structure, not values. Removing with different filter values removes
# the original setting.
REMOVEQUERYSETTINGS_SETTING_REMOVED_TESTS: list[SettingsTestCase] = [
    SettingsTestCase(
        "removes_by_query_shape",
        setup_commands=lambda ctx: [
            {
                "setQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"r1": 1},
                    "$db": ctx.database,
                },
                "settings": {
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
            "removeQuerySettings": {
                "find": ctx.collection,
                "filter": {"r1": 1},
                "$db": ctx.database,
            }
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"r1": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="removeQuerySettings should remove the setting by query shape",
    ),
    SettingsTestCase(
        "removes_by_hash",
        setup_commands=lambda ctx: [
            {
                "setQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"r2": 1},
                    "$db": ctx.database,
                },
                "settings": {
                    "indexHints": [
                        {
                            "ns": {"db": ctx.database, "coll": ctx.collection},
                            "allowedIndexes": ["_id_"],
                        }
                    ],
                },
            }
        ],
        command=lambda ctx: {"removeQuerySettings": ctx.setup_results[0]["queryShapeHash"]},
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"r2": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="removeQuerySettings should remove the setting by hash",
    ),
    SettingsTestCase(
        "removes_distinct_shape",
        setup_commands=lambda ctx: [
            {
                "setQuerySettings": {
                    "distinct": ctx.collection,
                    "key": "x",
                    "$db": ctx.database,
                },
                "settings": {
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
            "removeQuerySettings": {
                "distinct": ctx.collection,
                "key": "x",
                "$db": ctx.database,
            }
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "distinct": ctx.collection,
                    "key": "x",
                    "$db": ctx.database,
                }
            }
        ],
        msg="removeQuerySettings should remove the distinct setting",
    ),
    SettingsTestCase(
        "removes_aggregate_shape",
        setup_commands=lambda ctx: [
            {
                "setQuerySettings": {
                    "aggregate": ctx.collection,
                    "pipeline": [{"$match": {"x": 1}}],
                    "$db": ctx.database,
                },
                "settings": {
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
            "removeQuerySettings": {
                "aggregate": ctx.collection,
                "pipeline": [{"$match": {"x": 1}}],
                "$db": ctx.database,
            }
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "aggregate": ctx.collection,
                    "pipeline": [{"$match": {"x": 1}}],
                    "$db": ctx.database,
                }
            }
        ],
        msg="removeQuerySettings should remove the aggregate setting",
    ),
    SettingsTestCase(
        "shape_ignores_filter_values",
        setup_commands=lambda ctx: [
            {
                "setQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"sm1": 1},
                    "$db": ctx.database,
                },
                "settings": {
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
            "removeQuerySettings": {
                "find": ctx.collection,
                "filter": {"sm1": 999},
                "$db": ctx.database,
            }
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"sm1": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="shape matching should ignore filter values and remove the setting",
    ),
]


@pytest.mark.admin
@pytest.mark.requires(change_streams=True)
@pytest.mark.parametrize("test", pytest_params(REMOVEQUERYSETTINGS_SETTING_REMOVED_TESTS))
def test_removeQuerySettings_setting_removed(collection, test):
    """Test that removeQuerySettings actually removes settings, verified via $querySettings."""
    ctx = CommandContext.from_collection(collection)
    try:
        for cmd in test.build_setup(ctx):
            r = execute_admin_command(collection, cmd)
            ctx.setup_results.append(r)
        expected_hash = ctx.setup_results[0]["queryShapeHash"]

        execute_admin_command(collection, test.build_command(ctx))

        admin = collection.database.client.admin
        qs_result = admin.command(
            {"aggregate": 1, "pipeline": [{"$querySettings": {}}], "cursor": {}}
        )
        batch: list[dict[str, Any]] = qs_result.get("cursor", {}).get("firstBatch", [])
        count = sum(1 for s in batch if s.get("queryShapeHash") == expected_hash)
        assertSuccessPartial(
            {"count": count},
            {"count": 0},
            msg=test.msg,
        )
    finally:
        for cmd in test.build_cleanup(ctx):
            try:
                execute_admin_command(collection, cmd)
            except Exception:
                pass


# Property [Idempotent Removal]: calling removeQuerySettings a second time
# for the same query shape succeeds silently without error.
REMOVEQUERYSETTINGS_IDEMPOTENT_TESTS: list[SettingsTestCase] = [
    SettingsTestCase(
        "idempotent_removal",
        setup_commands=lambda ctx: [
            {
                "setQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"r3": 1},
                    "$db": ctx.database,
                },
                "settings": {
                    "indexHints": [
                        {
                            "ns": {"db": ctx.database, "coll": ctx.collection},
                            "allowedIndexes": ["_id_"],
                        }
                    ],
                },
            },
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"r3": 1},
                    "$db": ctx.database,
                }
            },
        ],
        command=lambda ctx: {
            "removeQuerySettings": {
                "find": ctx.collection,
                "filter": {"r3": 1},
                "$db": ctx.database,
            }
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"r3": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="removeQuerySettings should succeed silently on second removal",
    ),
]


@pytest.mark.admin
@pytest.mark.requires(change_streams=True)
@pytest.mark.parametrize("test", pytest_params(REMOVEQUERYSETTINGS_IDEMPOTENT_TESTS))
def test_removeQuerySettings_idempotent(collection, test):
    """Test removeQuerySettings is idempotent on second call."""
    ctx = CommandContext.from_collection(collection)
    try:
        for cmd in test.build_setup(ctx):
            r = execute_admin_command(collection, cmd)
            ctx.setup_results.append(r)
        result = execute_admin_command(collection, test.build_command(ctx))
        assertSuccessPartial(result, test.build_expected(ctx), msg=test.msg)
    finally:
        for cmd in test.build_cleanup(ctx):
            try:
                execute_admin_command(collection, cmd)
            except Exception:
                pass


# Property [Shape Matching Includes Collection]: collection name is part of
# the query shape. Removing with a different collection does not affect the
# original setting.
# Property [Shape Matching Includes $db]: $db is part of the query shape.
# Removing with a different $db does not affect the original setting.
# Property [Shape Matching Includes Sort Direction]: sort direction is part
# of the query shape. Removing with a different sort direction does not
# affect the original setting.
# Property [Shape Matching Includes Extra Fields]: adding extra fields
# changes the query shape. Removing with extra fields does not affect the
# original filter-only setting.
REMOVEQUERYSETTINGS_SHAPE_PERSISTS_TESTS: list[SettingsTestCase] = [
    SettingsTestCase(
        "shape_collection_name_matters",
        setup_commands=lambda ctx: [
            {
                "setQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"sm2": 1},
                    "$db": ctx.database,
                },
                "settings": {
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
            "removeQuerySettings": {
                "find": "other_collection",
                "filter": {"sm2": 1},
                "$db": ctx.database,
            }
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"sm2": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="removing with different collection should not affect original setting",
    ),
    SettingsTestCase(
        "shape_db_matters",
        setup_commands=lambda ctx: [
            {
                "setQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"sm3": 1},
                    "$db": ctx.database,
                },
                "settings": {
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
            "removeQuerySettings": {
                "find": ctx.collection,
                "filter": {"sm3": 1},
                "$db": "other_database",
            }
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"sm3": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="removing with different $db should not affect original setting",
    ),
    SettingsTestCase(
        "shape_sort_direction_matters",
        setup_commands=lambda ctx: [
            {
                "setQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"sm4": 1},
                    "sort": {"sm4": 1},
                    "$db": ctx.database,
                },
                "settings": {
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
            "removeQuerySettings": {
                "find": ctx.collection,
                "filter": {"sm4": 1},
                "sort": {"sm4": -1},
                "$db": ctx.database,
            }
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"sm4": 1},
                    "sort": {"sm4": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="removing with different sort direction should not affect original setting",
    ),
    SettingsTestCase(
        "shape_extra_fields_change_shape",
        setup_commands=lambda ctx: [
            {
                "setQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"sm5": 1},
                    "$db": ctx.database,
                },
                "settings": {
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
            "removeQuerySettings": {
                "find": ctx.collection,
                "filter": {"sm5": 1},
                "sort": {"sm5": 1},
                "$db": ctx.database,
            }
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"sm5": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="removing with extra fields should not affect filter-only setting",
    ),
]


@pytest.mark.admin
@pytest.mark.requires(change_streams=True)
@pytest.mark.parametrize("test", pytest_params(REMOVEQUERYSETTINGS_SHAPE_PERSISTS_TESTS))
def test_removeQuerySettings_shape_persists(collection, test):
    """Test that mismatched shapes do not remove original settings."""
    ctx = CommandContext.from_collection(collection)
    try:
        for cmd in test.build_setup(ctx):
            r = execute_admin_command(collection, cmd)
            ctx.setup_results.append(r)
        expected_hash = ctx.setup_results[0]["queryShapeHash"]

        execute_admin_command(collection, test.build_command(ctx))

        admin = collection.database.client.admin
        qs_result = admin.command(
            {"aggregate": 1, "pipeline": [{"$querySettings": {}}], "cursor": {}}
        )
        batch: list[dict[str, Any]] = qs_result.get("cursor", {}).get("firstBatch", [])
        count = sum(1 for s in batch if s.get("queryShapeHash") == expected_hash)
        assertSuccessPartial({"count": count}, {"count": 1}, msg=test.msg)
    finally:
        for cmd in test.build_cleanup(ctx):
            try:
                execute_admin_command(collection, cmd)
            except Exception:
                pass


# Property [Reject Removal Restores Query]: removing a reject: true setting
# allows the previously-rejected query to succeed again.
REMOVEQUERYSETTINGS_REJECT_REMOVAL_TESTS: list[SettingsTestCase] = [
    SettingsTestCase(
        "reject_removal_restores_query",
        setup_commands=lambda ctx: [
            {
                "setQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"rj1": 1},
                    "$db": ctx.database,
                },
                "settings": {"reject": True},
            }
        ],
        command=lambda ctx: {
            "removeQuerySettings": {
                "find": ctx.collection,
                "filter": {"rj1": 1},
                "$db": ctx.database,
            }
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"rj1": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="query should succeed after removing reject: true setting",
    ),
]


@pytest.mark.admin
@pytest.mark.requires(change_streams=True)
@pytest.mark.parametrize("test", pytest_params(REMOVEQUERYSETTINGS_REJECT_REMOVAL_TESTS))
def test_removeQuerySettings_reject_removal(collection, test):
    """Test that removing reject: true setting restores the query."""
    ctx = CommandContext.from_collection(collection)
    try:
        for cmd in test.build_setup(ctx):
            r = execute_admin_command(collection, cmd)
            ctx.setup_results.append(r)

        # Remove the reject setting
        execute_admin_command(collection, test.build_command(ctx))

        # Verify query succeeds after removal
        restored = execute_command(collection, {"find": ctx.collection, "filter": {"rj1": 1}})
        assertSuccessPartial(restored, {"ok": 1.0}, msg=test.msg)
    finally:
        for cmd in test.build_cleanup(ctx):
            try:
                execute_admin_command(collection, cmd)
            except Exception:
                pass
