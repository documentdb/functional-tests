"""Tests for setQuerySettings observable effects and verification.

Validates query shape hash properties, $querySettings stage output for
distinct and aggregate shapes, showDebugQueryShape, multiple settings
management, comment visibility, settings replacement semantics, and
indexHints namespace mismatch acceptance.
"""

from __future__ import annotations

import re

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

# Property [Hash Format]: queryShapeHash is a 64-character hexadecimal string.
# Property [Hash Consistency]: same query shape produces the same hash.
# Property [Hash Uniqueness]: different query shapes produce different hashes.
# Property [Shape Matching]: filter values do not affect shape identity.
# Property [Sort Direction Matters]: different sort directions produce different hashes.
# Property [$querySettings Distinct]: $querySettings returns correct data for distinct.
# Property [$querySettings Aggregate]: $querySettings returns correct data for aggregate.
# Property [showDebugQueryShape True]: debugQueryShape present when requested.
# Property [showDebugQueryShape False]: debugQueryShape absent when not requested.
# Property [Multiple Settings Visible]: all query settings appear in $querySettings.
# Property [Multiple Settings Remove]: removing one leaves others intact.
# Property [Comment Visibility]: settings.comment appears in $querySettings output.
# Property [Comment Update]: updating settings.comment replaces the old value.
# Property [Settings Replacement]: updating settings preserves unmodified fields.
# Property [No Duplicate On Update]: updating same shape does not duplicate entries.
# Property [ns Mismatch]: indexHints ns.coll can differ from query shape collection.


# ---------------------------------------------------------------------------
# Group 1: ns.coll mismatch acceptance test
# ---------------------------------------------------------------------------

SET_QUERY_SETTINGS_NS_MISMATCH_TESTS: list[SettingsTestCase] = [
    SettingsTestCase(
        "ns_coll_mismatch_accepted",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"mis1": 1},
                "$db": ctx.database,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {
                            "db": ctx.database,
                            "coll": "completely_different_collection",
                        },
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
                    "filter": {"mis1": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="ns.coll mismatch should be accepted",
    ),
]


@pytest.mark.admin
@pytest.mark.requires(change_streams=True)
@pytest.mark.parametrize("test", pytest_params(SET_QUERY_SETTINGS_NS_MISMATCH_TESTS))
def test_setQuerySettings_ns_coll_mismatch_accepted(collection, test):
    """Test that indexHints ns.coll can differ from query shape collection."""
    ctx = CommandContext.from_collection(collection)
    try:
        result = execute_admin_command(collection, test.build_command(ctx))
        assertSuccessPartial(result, test.build_expected(ctx), msg=test.msg)
    finally:
        for cmd in test.build_cleanup(ctx):
            try:
                execute_admin_command(collection, cmd)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Group 2: Hash property tests
# ---------------------------------------------------------------------------

SET_QUERY_SETTINGS_HASH_SAME_TESTS: list[SettingsTestCase] = [
    SettingsTestCase(
        "same_shape_produces_same_hash",
        setup_commands=lambda ctx: [
            {
                "setQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"h2": 1},
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
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"h2": 1},
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
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"h2": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="same query shape should produce identical hashes",
    ),
    SettingsTestCase(
        "filter_values_do_not_affect_shape",
        setup_commands=lambda ctx: [
            {
                "setQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"x": 1},
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
                    "filter": {"x": 1},
                    "$db": ctx.database,
                }
            },
        ],
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"x": 999},
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
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"x": 999},
                    "$db": ctx.database,
                }
            }
        ],
        msg="filter values should not affect query shape hash",
    ),
]

SET_QUERY_SETTINGS_HASH_DIFFERENT_TESTS: list[SettingsTestCase] = [
    SettingsTestCase(
        "different_shapes_different_hashes",
        setup_commands=lambda ctx: [
            {
                "setQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"h3a": 1},
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
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"h3b": 1},
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
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"h3a": 1},
                    "$db": ctx.database,
                }
            },
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"h3b": 1},
                    "$db": ctx.database,
                }
            },
        ],
        msg="different query shapes should produce different hashes",
    ),
    SettingsTestCase(
        "sort_direction_affects_shape",
        setup_commands=lambda ctx: [
            {
                "setQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"sd": 1},
                    "sort": {"a": 1},
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
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"sd": 1},
                "sort": {"a": -1},
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
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"sd": 1},
                    "sort": {"a": 1},
                    "$db": ctx.database,
                }
            },
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"sd": 1},
                    "sort": {"a": -1},
                    "$db": ctx.database,
                }
            },
        ],
        msg="sort direction should produce different query shape hashes",
    ),
]


@pytest.mark.admin
@pytest.mark.requires(change_streams=True)
@pytest.mark.parametrize("test", pytest_params(SET_QUERY_SETTINGS_HASH_SAME_TESTS))
def test_setQuerySettings_hash_same(collection, test):
    """Test that equivalent query shapes produce the same hash."""
    ctx = CommandContext.from_collection(collection)
    try:
        setup_hash = None
        for cmd in test.build_setup(ctx):
            r = execute_admin_command(collection, cmd)
            ctx.setup_results.append(r)
            if "queryShapeHash" in r:
                setup_hash = r["queryShapeHash"]
        result = execute_admin_command(collection, test.build_command(ctx))
        assertSuccessPartial(
            result,
            {"queryShapeHash": setup_hash},
            msg=test.msg,
        )
    finally:
        for cmd in test.build_cleanup(ctx):
            try:
                execute_admin_command(collection, cmd)
            except Exception:
                pass


@pytest.mark.admin
@pytest.mark.requires(change_streams=True)
@pytest.mark.parametrize("test", pytest_params(SET_QUERY_SETTINGS_HASH_DIFFERENT_TESTS))
def test_setQuerySettings_hash_different(collection, test):
    """Test that distinct query shapes produce different hashes."""
    ctx = CommandContext.from_collection(collection)
    try:
        setup_hash = None
        for cmd in test.build_setup(ctx):
            r = execute_admin_command(collection, cmd)
            ctx.setup_results.append(r)
            if "queryShapeHash" in r:
                setup_hash = r["queryShapeHash"]
        result = execute_admin_command(collection, test.build_command(ctx))
        hashes_differ = result["queryShapeHash"] != setup_hash
        assertSuccessPartial(
            {"differ": hashes_differ},
            {"differ": True},
            msg=test.msg,
        )
    finally:
        for cmd in test.build_cleanup(ctx):
            try:
                execute_admin_command(collection, cmd)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Group 3: Hash format test
# ---------------------------------------------------------------------------

SET_QUERY_SETTINGS_HASH_FORMAT_TESTS: list[SettingsTestCase] = [
    SettingsTestCase(
        "hash_is_64_char_hex",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"h1": 1},
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
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"h1": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="queryShapeHash should be 64-char hex",
    ),
]


@pytest.mark.admin
@pytest.mark.requires(change_streams=True)
@pytest.mark.parametrize("test", pytest_params(SET_QUERY_SETTINGS_HASH_FORMAT_TESTS))
def test_setQuerySettings_hash_format(collection, test):
    """Test that queryShapeHash matches expected format."""
    ctx = CommandContext.from_collection(collection)
    try:
        result = execute_admin_command(collection, test.build_command(ctx))
        h = result.get("queryShapeHash", "")
        is_valid = bool(re.fullmatch(r"[0-9A-Fa-f]{64}", h))
        assertSuccessPartial(
            {"valid": is_valid},
            {"valid": True},
            msg=f"{test.msg}, got: {h!r}",
        )
    finally:
        for cmd in test.build_cleanup(ctx):
            try:
                execute_admin_command(collection, cmd)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Group 4: $querySettings inspection tests
# ---------------------------------------------------------------------------

SET_QUERY_SETTINGS_QS_STAGE_TESTS: list[SettingsTestCase] = [
    SettingsTestCase(
        "querySettings_returns_distinct_shape",
        command=lambda ctx: {
            "setQuerySettings": {
                "distinct": ctx.collection,
                "key": "x",
                "query": {"qs_d1": 1},
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
        expected=lambda ctx: {"distinct": ctx.collection},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "distinct": ctx.collection,
                    "key": "x",
                    "query": {"qs_d1": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="representativeQuery should be a distinct shape",
    ),
    SettingsTestCase(
        "querySettings_returns_aggregate_shape",
        command=lambda ctx: {
            "setQuerySettings": {
                "aggregate": ctx.collection,
                "pipeline": [{"$match": {"qs_a1": 1}}],
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
        expected=lambda ctx: {"aggregate": ctx.collection},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "aggregate": ctx.collection,
                    "pipeline": [{"$match": {"qs_a1": 1}}],
                    "$db": ctx.database,
                }
            }
        ],
        msg="representativeQuery should be an aggregate shape",
    ),
]


@pytest.mark.admin
@pytest.mark.requires(change_streams=True)
@pytest.mark.parametrize("test", pytest_params(SET_QUERY_SETTINGS_QS_STAGE_TESTS))
def test_setQuerySettings_qs_stage(collection, test):
    """Test $querySettings returns correct representativeQuery."""
    ctx = CommandContext.from_collection(collection)
    try:
        r = execute_admin_command(collection, test.build_command(ctx))
        settings = get_query_settings(collection)
        matching = [s for s in settings if s.get("queryShapeHash") == r["queryShapeHash"]]
        entry = matching[0] if matching else {}
        assertSuccessPartial(
            entry.get("representativeQuery", {}),
            test.build_expected(ctx),
            msg=test.msg,
        )
    finally:
        for cmd in test.build_cleanup(ctx):
            try:
                execute_admin_command(collection, cmd)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Group 5: showDebugQueryShape tests
# ---------------------------------------------------------------------------

SET_QUERY_SETTINGS_DEBUG_SHAPE_TESTS: list[SettingsTestCase] = [
    SettingsTestCase(
        "debug_query_shape_present_when_enabled",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"dbg1": 1},
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
        expected={"has_debug": True},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"dbg1": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="debugQueryShape should be present with showDebugQueryShape: true",
    ),
    SettingsTestCase(
        "debug_query_shape_absent_when_disabled",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"dbg2": 1},
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
        expected={"has_debug": False},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"dbg2": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="debugQueryShape should be absent with showDebugQueryShape: false",
    ),
]


@pytest.mark.admin
@pytest.mark.requires(change_streams=True)
@pytest.mark.parametrize("test", pytest_params(SET_QUERY_SETTINGS_DEBUG_SHAPE_TESTS))
def test_setQuerySettings_debug_shape(collection, test):
    """Test showDebugQueryShape controls debugQueryShape presence."""
    ctx = CommandContext.from_collection(collection)
    expected = test.build_expected(ctx)
    show_debug = expected["has_debug"]
    try:
        execute_admin_command(collection, test.build_command(ctx))
        settings = list(
            collection.database.client.admin.aggregate(
                [{"$querySettings": {"showDebugQueryShape": show_debug}}]
            )
        )
        filter_key = "dbg1" if show_debug else "dbg2"
        entry = [
            s
            for s in settings
            if s.get("representativeQuery", {}).get("filter", {}).get(filter_key)
        ]
        has_debug = "debugQueryShape" in (entry[0] if entry else {})
        assertSuccessPartial(
            {"has_debug": has_debug},
            expected,
            msg=test.msg,
        )
    finally:
        for cmd in test.build_cleanup(ctx):
            try:
                execute_admin_command(collection, cmd)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Group 6: Settings field verification via $querySettings
# (comment visibility, comment update, settings replacement)
# ---------------------------------------------------------------------------

SET_QUERY_SETTINGS_FIELD_VERIFICATION_TESTS: list[SettingsTestCase] = [
    SettingsTestCase(
        "comment_visible_in_querySettings",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"comvis1": 1},
                "$db": ctx.database,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": ctx.database, "coll": ctx.collection},
                        "allowedIndexes": ["_id_"],
                    }
                ],
                "comment": "my-test-comment",
            },
        },
        expected={"comment": "my-test-comment"},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"comvis1": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="comment should be visible in $querySettings output",
    ),
    SettingsTestCase(
        "comment_replaced_on_update",
        setup_commands=lambda ctx: [
            {
                "setQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"comup1": 1},
                    "$db": ctx.database,
                },
                "settings": {
                    "indexHints": [
                        {
                            "ns": {"db": ctx.database, "coll": ctx.collection},
                            "allowedIndexes": ["_id_"],
                        }
                    ],
                    "comment": "original",
                },
            }
        ],
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"comup1": 1},
                "$db": ctx.database,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": ctx.database, "coll": ctx.collection},
                        "allowedIndexes": ["_id_"],
                    }
                ],
                "comment": "updated",
            },
        },
        expected={"comment": "updated"},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"comup1": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="comment should be replaced by the updated value",
    ),
    SettingsTestCase(
        "update_preserves_unmodified_fields",
        setup_commands=lambda ctx: [
            {
                "setQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"rep1": 1},
                    "$db": ctx.database,
                },
                "settings": {
                    "indexHints": [
                        {
                            "ns": {"db": ctx.database, "coll": ctx.collection},
                            "allowedIndexes": ["_id_"],
                        }
                    ],
                    "queryFramework": "classic",
                },
            }
        ],
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"rep1": 1},
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
        expected={"queryFramework": "classic"},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"rep1": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="queryFramework should be preserved after update with only indexHints",
    ),
]


@pytest.mark.admin
@pytest.mark.requires(change_streams=True)
@pytest.mark.parametrize("test", pytest_params(SET_QUERY_SETTINGS_FIELD_VERIFICATION_TESTS))
def test_setQuerySettings_field_verification(collection, test):
    """Test settings fields are visible and correctly updated in $querySettings."""
    ctx = CommandContext.from_collection(collection)
    try:
        for cmd in test.build_setup(ctx):
            r = execute_admin_command(collection, cmd)
            ctx.setup_results.append(r)
        r = execute_admin_command(collection, test.build_command(ctx))
        settings = get_query_settings(collection)
        matching = [s for s in settings if s.get("queryShapeHash") == r["queryShapeHash"]]
        entry = matching[0] if matching else {}
        assertSuccessPartial(
            entry.get("settings", {}),
            test.build_expected(ctx),
            msg=test.msg,
        )
    finally:
        for cmd in test.build_cleanup(ctx):
            try:
                execute_admin_command(collection, cmd)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Group 7: Multi-setup settings management tests
# ---------------------------------------------------------------------------


SET_QUERY_SETTINGS_MULTI_SETUP_TESTS: list[SettingsTestCase] = [
    SettingsTestCase(
        "no_duplicate_on_update",
        setup_commands=lambda ctx: [
            {
                "setQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"dup1": 1},
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
                "setQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"dup1": 1},
                    "$db": ctx.database,
                },
                "settings": {
                    "indexHints": [
                        {
                            "ns": {"db": ctx.database, "coll": ctx.collection},
                            "allowedIndexes": ["_id_"],
                        }
                    ],
                    "queryFramework": "classic",
                },
            },
        ],
        expected=lambda ctx: {
            "ok": sum(
                1
                for h in ctx.setup_results[-1]["_live_hashes"]
                if h
                == [r["queryShapeHash"] for r in ctx.setup_results if "queryShapeHash" in r][-1]
            )
            == 1
        },
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"dup1": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="updating same shape should not create duplicate entries",
    ),
    SettingsTestCase(
        "multiple_settings_all_visible",
        setup_commands=lambda ctx: [
            {
                "setQuerySettings": {
                    "find": ctx.collection,
                    "filter": {f"multi{i}": 1},
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
            for i in range(1, 4)
        ],
        expected=lambda ctx: {
            "ok": all(
                h in ctx.setup_results[-1]["_live_hashes"]
                for h in [r["queryShapeHash"] for r in ctx.setup_results if "queryShapeHash" in r]
            )
        },
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {f"multi{i}": 1},
                    "$db": ctx.database,
                }
            }
            for i in range(1, 4)
        ],
        msg="all 3 query settings should be visible in $querySettings",
    ),
    SettingsTestCase(
        "remove_one_leaves_others",
        setup_commands=lambda ctx: [
            {
                "setQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"rem1": 1},
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
                "setQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"rem2": 1},
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
                    "filter": {"rem1": 1},
                    "$db": ctx.database,
                }
            },
        ],
        expected=lambda ctx: {
            "ok": [r["queryShapeHash"] for r in ctx.setup_results if "queryShapeHash" in r][0]
            not in ctx.setup_results[-1]["_live_hashes"]
            and [r["queryShapeHash"] for r in ctx.setup_results if "queryShapeHash" in r][1]
            in ctx.setup_results[-1]["_live_hashes"]
        },
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {f"rem{i}": 1},
                    "$db": ctx.database,
                }
            }
            for i in range(1, 3)
        ],
        msg="q1 removed, q2 should remain in $querySettings",
    ),
]


@pytest.mark.admin
@pytest.mark.requires(change_streams=True)
@pytest.mark.parametrize("test", pytest_params(SET_QUERY_SETTINGS_MULTI_SETUP_TESTS))
def test_setQuerySettings_multi_setup(collection, test):
    """Test multi-setup settings management via $querySettings inspection."""
    ctx = CommandContext.from_collection(collection)
    try:
        for cmd in test.build_setup(ctx):
            r = execute_admin_command(collection, cmd)
            ctx.setup_results.append(r)
        all_hashes = {s.get("queryShapeHash") for s in get_query_settings(collection)}
        # Stash live hashes so expected-lambdas can reference them.
        ctx.setup_results.append({"_live_hashes": all_hashes})
        assertSuccessPartial(
            test.build_expected(ctx),
            {"ok": True},
            msg=test.msg,
        )
    finally:
        for cmd in test.build_cleanup(ctx):
            try:
                execute_admin_command(collection, cmd)
            except Exception:
                pass
