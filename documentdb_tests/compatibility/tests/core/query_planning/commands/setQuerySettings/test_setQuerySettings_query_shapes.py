"""Tests for setQuerySettings command query shape acceptance.

Validates that the setQuerySettings command accepts valid query shapes for
find, distinct, and aggregate commands, including various shape variations,
field combinations, and $db field variations.
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

pytestmark = [pytest.mark.requires(cluster_admin=True), pytest.mark.no_parallel]

# Property [Command Shape Acceptance]: accepts find, distinct, and aggregate shapes.
# Property [Find Shape Variations]: setQuerySettings accepts find shapes with various field combos.
# Property [Distinct Shape Variations]: setQuerySettings accepts distinct shapes with query combos.
# Property [Aggregate Shape Variations]: setQuerySettings accepts aggregate pipeline shapes.
# Property [$db Field Variations]: setQuerySettings accepts non-existent and special-char db names.
SET_QUERY_SETTINGS_QUERY_SHAPE_TESTS: list[SettingsTestCase] = [
    # -- Command shape acceptance --
    SettingsTestCase(
        "find_shape",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"x": 1},
                "sort": {"x": 1},
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
                    "filter": {"x": 1},
                    "sort": {"x": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept valid find shape",
    ),
    SettingsTestCase(
        "distinct_shape",
        command=lambda ctx: {
            "setQuerySettings": {
                "distinct": ctx.collection,
                "key": "x",
                "query": {"x": {"$gt": 0}},
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
                    "distinct": ctx.collection,
                    "key": "x",
                    "query": {"x": {"$gt": 0}},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept valid distinct shape",
    ),
    SettingsTestCase(
        "aggregate_shape",
        command=lambda ctx: {
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
        msg="should accept valid aggregate shape",
    ),
    # -- Find shape variations --
    SettingsTestCase(
        "find_filter_only",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"a": 1},
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
                    "filter": {"a": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept find with filter only",
    ),
    SettingsTestCase(
        "find_filter_sort",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"b": 1},
                "sort": {"b": 1},
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
                    "filter": {"b": 1},
                    "sort": {"b": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept find with filter+sort",
    ),
    SettingsTestCase(
        "find_filter_projection",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"c": 1},
                "projection": {"c": 1},
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
                    "filter": {"c": 1},
                    "projection": {"c": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept find with filter+projection",
    ),
    SettingsTestCase(
        "find_filter_sort_projection",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"d": 1},
                "sort": {"d": 1},
                "projection": {"d": 1},
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
                    "filter": {"d": 1},
                    "sort": {"d": 1},
                    "projection": {"d": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept find with all fields",
    ),
    SettingsTestCase(
        "find_with_collation",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"e": "abc"},
                "collation": {"locale": "en", "strength": 2},
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
                    "filter": {"e": "abc"},
                    "collation": {"locale": "en", "strength": 2},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept find with collation",
    ),
    SettingsTestCase(
        "find_with_let",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"$expr": {"$eq": ["$f", "$$target"]}},
                "let": {"target": 1},
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
                    "filter": {"$expr": {"$eq": ["$f", "$$target"]}},
                    "let": {"target": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept find with let",
    ),
    SettingsTestCase(
        "find_with_limit",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"g": 1},
                "limit": 10,
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
                    "filter": {"g": 1},
                    "limit": 10,
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept find with limit",
    ),
    # -- Distinct shape variations --
    SettingsTestCase(
        "distinct_key_only",
        command=lambda ctx: {
            "setQuerySettings": {
                "distinct": ctx.collection,
                "key": "j",
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
                    "distinct": ctx.collection,
                    "key": "j",
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept distinct key only",
    ),
    SettingsTestCase(
        "distinct_complex_query",
        command=lambda ctx: {
            "setQuerySettings": {
                "distinct": ctx.collection,
                "key": "k",
                "query": {"$and": [{"k": {"$gt": 0}}, {"k": {"$lt": 100}}]},
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
                    "distinct": ctx.collection,
                    "key": "k",
                    "query": {"$and": [{"k": {"$gt": 0}}, {"k": {"$lt": 100}}]},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept distinct complex query",
    ),
    # -- Aggregate shape variations --
    SettingsTestCase(
        "aggregate_match_only",
        command=lambda ctx: {
            "setQuerySettings": {
                "aggregate": ctx.collection,
                "pipeline": [{"$match": {"l": 1}}],
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
                    "aggregate": ctx.collection,
                    "pipeline": [{"$match": {"l": 1}}],
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept aggregate $match only",
    ),
    SettingsTestCase(
        "aggregate_match_group",
        command=lambda ctx: {
            "setQuerySettings": {
                "aggregate": ctx.collection,
                "pipeline": [
                    {"$match": {"m": 1}},
                    {"$group": {"_id": "$m", "count": {"$sum": 1}}},
                ],
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
                    "aggregate": ctx.collection,
                    "pipeline": [
                        {"$match": {"m": 1}},
                        {"$group": {"_id": "$m", "count": {"$sum": 1}}},
                    ],
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept aggregate $match+$group",
    ),
    SettingsTestCase(
        "aggregate_match_sort_limit",
        command=lambda ctx: {
            "setQuerySettings": {
                "aggregate": ctx.collection,
                "pipeline": [{"$match": {"n": 1}}, {"$sort": {"n": 1}}, {"$limit": 5}],
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
                    "aggregate": ctx.collection,
                    "pipeline": [{"$match": {"n": 1}}, {"$sort": {"n": 1}}, {"$limit": 5}],
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept aggregate $match+$sort+$limit",
    ),
    SettingsTestCase(
        "aggregate_empty_pipeline",
        command=lambda ctx: {
            "setQuerySettings": {
                "aggregate": ctx.collection,
                "pipeline": [],
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
                    "aggregate": ctx.collection,
                    "pipeline": [],
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept aggregate with empty pipeline",
    ),
    # -- $db field variations --
    SettingsTestCase(
        "db_nonexistent",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"o": 1},
                "$db": "nonexistent_db_for_query_settings_test",
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {
                            "db": "nonexistent_db_for_query_settings_test",
                            "coll": ctx.collection,
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
                    "filter": {"o": 1},
                    "$db": "nonexistent_db_for_query_settings_test",
                }
            }
        ],
        msg="should accept non-existent $db",
    ),
    SettingsTestCase(
        "db_special_characters",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"p": 1},
                "$db": "test-special-db",
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": "test-special-db", "coll": ctx.collection},
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
                    "filter": {"p": 1},
                    "$db": "test-special-db",
                }
            }
        ],
        msg="should accept $db with special chars",
    ),
]


@pytest.mark.admin
@pytest.mark.parametrize("test", pytest_params(SET_QUERY_SETTINGS_QUERY_SHAPE_TESTS))
def test_setQuerySettings_query_shapes(collection, test):
    """Test setQuerySettings accepts valid query shapes."""
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
