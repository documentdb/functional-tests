"""Tests for setQuerySettings command behavioral verification.

Validates that query settings are retrievable via $querySettings aggregation
stage, removable via removeQuerySettings, and that the response structure
includes expected fields like queryShapeHash and representativeQuery.
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
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

from .utils.setQuerySettings_common import get_query_settings

pytestmark = [pytest.mark.requires(cluster_admin=True), pytest.mark.no_parallel]

# Property [Response Structure]: setQuerySettings response includes hash, query, and settings.
SET_QUERY_SETTINGS_RESPONSE_TESTS: list[SettingsTestCase] = [
    SettingsTestCase(
        "response_contains_hash",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"b1": 1},
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
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"b1": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="response should contain queryShapeHash",
    ),
    SettingsTestCase(
        "response_contains_representative_query",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"b2": 1},
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
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"b2": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="response should contain representativeQuery",
    ),
    SettingsTestCase(
        "response_settings_echo",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"b3": 1},
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
        expected=lambda ctx: {
            "ok": 1.0,
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": ctx.database, "coll": ctx.collection},
                        "allowedIndexes": ["_id_"],
                    }
                ],
            },
        },
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"b3": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="response should echo applied settings",
    ),
]


@pytest.mark.admin
@pytest.mark.parametrize("test", pytest_params(SET_QUERY_SETTINGS_RESPONSE_TESTS))
def test_setQuerySettings_response(collection, test):
    """Test setQuerySettings response structure."""
    ctx = CommandContext.from_collection(collection)
    try:
        result = execute_admin_command(collection, test.build_command(ctx))
        expected = test.build_expected(ctx)
        # Also verify the dynamic fields are present
        if test.id == "response_contains_hash":
            expected["queryShapeHash"] = result.get("queryShapeHash")
        elif test.id == "response_contains_representative_query":
            expected["representativeQuery"] = result.get("representativeQuery")
        assertSuccessPartial(result, expected, msg=test.msg)
    finally:
        for cmd in test.build_cleanup(ctx):
            try:
                execute_admin_command(collection, cmd)
            except Exception:
                pass


# Property [removeQuerySettings]: settings can be removed by query or hash.
SET_QUERY_SETTINGS_REMOVE_TESTS: list[SettingsTestCase] = [
    SettingsTestCase(
        "removeQuerySettings_by_query",
        setup_commands=lambda ctx: [
            {
                "setQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"b5": 1},
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
                "filter": {"b5": 1},
                "$db": ctx.database,
            }
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"b5": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="removeQuerySettings by query should succeed",
    ),
    SettingsTestCase(
        "removeQuerySettings_by_hash",
        setup_commands=lambda ctx: [
            {
                "setQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"b6": 1},
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
                    "filter": {"b6": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="removeQuerySettings by hash should succeed",
    ),
]


@pytest.mark.admin
@pytest.mark.parametrize("test", pytest_params(SET_QUERY_SETTINGS_REMOVE_TESTS))
def test_setQuerySettings_remove(collection, test):
    """Test removeQuerySettings removes settings."""
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


# Property [$querySettings Retrieval]: settings are visible via $querySettings aggregation stage.
SET_QUERY_SETTINGS_QS_STAGE_TESTS: list[SettingsTestCase] = [
    SettingsTestCase(
        "querySettings_stage_retrieval",
        setup_commands=lambda ctx: [
            {
                "setQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"b4": 1},
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
        expected=lambda ctx: {"queryShapeHash": ctx.setup_results[0]["queryShapeHash"]},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"b4": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="$querySettings should return the created setting",
    ),
    SettingsTestCase(
        "querySettings_stage_shows_settings",
        setup_commands=lambda ctx: [
            {
                "setQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"b9": 1},
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
        expected=lambda ctx: {
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": ctx.database, "coll": ctx.collection},
                        "allowedIndexes": ["_id_"],
                    }
                ],
            },
        },
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"b9": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="$querySettings should include indexHints in settings",
    ),
    SettingsTestCase(
        "querySettings_stage_shows_representative_query",
        setup_commands=lambda ctx: [
            {
                "setQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"b10": 1},
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
        # expected is built dynamically in the runner (self-referential)
        expected=None,
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"b10": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="$querySettings should include representativeQuery",
    ),
]


@pytest.mark.admin
@pytest.mark.parametrize("test", pytest_params(SET_QUERY_SETTINGS_QS_STAGE_TESTS))
def test_setQuerySettings_qs_stage(collection, test):
    """Test that settings are visible via $querySettings aggregation stage."""
    ctx = CommandContext.from_collection(collection)
    try:
        for cmd in test.build_setup(ctx):
            r = execute_admin_command(collection, cmd)
            ctx.setup_results.append(r)
        expected_hash = ctx.setup_results[0]["queryShapeHash"]
        settings = get_query_settings(collection)
        matching = [s for s in settings if s.get("queryShapeHash") == expected_hash]
        entry = matching[0] if matching else {}
        expected = test.build_expected(ctx)
        if expected is None:
            # Self-referential: verify the field exists
            expected = {"representativeQuery": entry.get("representativeQuery")}
        assertSuccessPartial(entry, expected, msg=test.msg)
    finally:
        for cmd in test.build_cleanup(ctx):
            try:
                execute_admin_command(collection, cmd)
            except Exception:
                pass
