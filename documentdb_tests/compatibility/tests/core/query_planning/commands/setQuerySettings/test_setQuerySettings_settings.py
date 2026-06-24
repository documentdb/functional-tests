"""Tests for setQuerySettings command settings configurations.

Validates that the setQuerySettings command accepts valid settings
combinations including indexHints, reject, queryFramework, and comment
fields, as well as allowedIndexes variations and update behavior.
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

# Property [indexHints Acceptance]: setQuerySettings accepts valid indexHints configurations.
# Property [reject Acceptance]: setQuerySettings accepts reject: true alone or with indexHints.
# Property [queryFramework Acceptance]: setQuerySettings accepts classic and sbe frameworks.
# Property [comment Acceptance]: setQuerySettings accepts comment as any BSON type.
# Property [Combined Settings]: setQuerySettings accepts all settings fields together.
# Property [$natural Hint]: setQuerySettings accepts $natural in allowedIndexes.
# Property [Multiple indexHints]: setQuerySettings accepts multiple indexHints documents.
# Property [Non-Existent Index]: setQuerySettings accepts non-existent index names.
# Property [Text Index Spec]: setQuerySettings accepts text index key pattern in allowedIndexes.
# Property [2dsphere Index Spec]: setQuerySettings accepts 2dsphere index key pattern.
# Property [2d Index Spec]: setQuerySettings accepts 2d index key pattern.
# Property [Hashed Index Spec]: setQuerySettings accepts hashed index key pattern.
SET_QUERY_SETTINGS_SETTINGS_TESTS: list[SettingsTestCase] = [
    SettingsTestCase(
        "indexHints_single_index",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"a1": 1},
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
                    "filter": {"a1": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept indexHints with single index",
    ),
    SettingsTestCase(
        "indexHints_multiple_indexes",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"a2": 1},
                "$db": ctx.database,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": ctx.database, "coll": ctx.collection},
                        "allowedIndexes": ["_id_", {"a2": 1}],
                    }
                ],
            },
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"a2": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept multiple indexes",
    ),
    SettingsTestCase(
        "indexHints_key_pattern",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"a3": 1},
                "$db": ctx.database,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": ctx.database, "coll": ctx.collection},
                        "allowedIndexes": [{"a3": 1}],
                    }
                ],
            },
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"a3": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept indexHints with key pattern",
    ),
    SettingsTestCase(
        "reject_true",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"a5": 1},
                "$db": ctx.database,
            },
            "settings": {"reject": True},
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"a5": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept settings with reject: true",
    ),
    SettingsTestCase(
        "reject_with_indexHints",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"a6": 1},
                "$db": ctx.database,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": ctx.database, "coll": ctx.collection},
                        "allowedIndexes": ["_id_"],
                    }
                ],
                "reject": True,
            },
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"a6": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept reject with indexHints",
    ),
    SettingsTestCase(
        "queryFramework_classic",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"a7": 1},
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
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"a7": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept queryFramework: classic",
    ),
    SettingsTestCase(
        "queryFramework_sbe",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"a8": 1},
                "$db": ctx.database,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": ctx.database, "coll": ctx.collection},
                        "allowedIndexes": ["_id_"],
                    }
                ],
                "queryFramework": "sbe",
            },
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"a8": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept queryFramework: sbe",
    ),
    SettingsTestCase(
        "with_comment_string",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"a9": 1},
                "$db": ctx.database,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": ctx.database, "coll": ctx.collection},
                        "allowedIndexes": ["_id_"],
                    }
                ],
                "comment": "test comment for setQuerySettings",
            },
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"a9": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept settings with comment string",
    ),
    SettingsTestCase(
        "all_settings_combined",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"a12": 1},
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
                "reject": True,
            },
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"a12": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept all settings combined",
    ),
    SettingsTestCase(
        "indexHints_natural",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"a13": 1},
                "$db": ctx.database,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": ctx.database, "coll": ctx.collection},
                        "allowedIndexes": ["$natural"],
                    }
                ],
            },
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"a13": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept $natural in allowedIndexes",
    ),
    SettingsTestCase(
        "indexHints_multiple_ns_documents",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"a14": 1},
                "$db": ctx.database,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": ctx.database, "coll": ctx.collection},
                        "allowedIndexes": ["_id_"],
                    },
                    {
                        "ns": {"db": ctx.database, "coll": "other_collection"},
                        "allowedIndexes": ["_id_"],
                    },
                ],
            },
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"a14": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept multiple indexHints documents",
    ),
    SettingsTestCase(
        "indexHints_nonexistent_index",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"a15": 1},
                "$db": ctx.database,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": ctx.database, "coll": ctx.collection},
                        "allowedIndexes": ["nonexistent_index"],
                    }
                ],
            },
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"a15": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept non-existent index name",
    ),
    SettingsTestCase(
        "comment_object",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"a16": 1},
                "$db": ctx.database,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": ctx.database, "coll": ctx.collection},
                        "allowedIndexes": ["_id_"],
                    }
                ],
                "comment": {"body": {"msg": "Updated"}},
            },
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"a16": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept settings with comment as object",
    ),
    SettingsTestCase(
        "comment_int",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"a17": 1},
                "$db": ctx.database,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": ctx.database, "coll": ctx.collection},
                        "allowedIndexes": ["_id_"],
                    }
                ],
                "comment": 42,
            },
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"a17": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept settings with comment as int",
    ),
    SettingsTestCase(
        "comment_bool",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"a18": 1},
                "$db": ctx.database,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": ctx.database, "coll": ctx.collection},
                        "allowedIndexes": ["_id_"],
                    }
                ],
                "comment": True,
            },
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"a18": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept settings with comment as bool",
    ),
    SettingsTestCase(
        "comment_array",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"a19": 1},
                "$db": ctx.database,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": ctx.database, "coll": ctx.collection},
                        "allowedIndexes": ["_id_"],
                    }
                ],
                "comment": ["tag1", "tag2"],
            },
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"a19": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept settings with comment as array",
    ),
    SettingsTestCase(
        "comment_null",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"a20": 1},
                "$db": ctx.database,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": ctx.database, "coll": ctx.collection},
                        "allowedIndexes": ["_id_"],
                    }
                ],
                "comment": None,
            },
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"a20": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept settings with comment as null",
    ),
    SettingsTestCase(
        "indexHints_text_index_spec",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"a21": 1},
                "$db": ctx.database,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": ctx.database, "coll": ctx.collection},
                        "allowedIndexes": [{"a21": "text"}],
                    }
                ],
            },
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"a21": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept text index key pattern in allowedIndexes",
    ),
    SettingsTestCase(
        "indexHints_2dsphere_index_spec",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"a22": 1},
                "$db": ctx.database,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": ctx.database, "coll": ctx.collection},
                        "allowedIndexes": [{"geo": "2dsphere"}],
                    }
                ],
            },
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"a22": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept 2dsphere index key pattern in allowedIndexes",
    ),
    SettingsTestCase(
        "indexHints_2d_index_spec",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"a23": 1},
                "$db": ctx.database,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": ctx.database, "coll": ctx.collection},
                        "allowedIndexes": [{"loc": "2d"}],
                    }
                ],
            },
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"a23": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept 2d index key pattern in allowedIndexes",
    ),
    SettingsTestCase(
        "indexHints_hashed_index_spec",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"a24": 1},
                "$db": ctx.database,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": ctx.database, "coll": ctx.collection},
                        "allowedIndexes": [{"a24": "hashed"}],
                    }
                ],
            },
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"a24": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept hashed index key pattern in allowedIndexes",
    ),
]


@pytest.mark.admin
@pytest.mark.requires(change_streams=True)
@pytest.mark.parametrize("test", pytest_params(SET_QUERY_SETTINGS_SETTINGS_TESTS))
def test_setQuerySettings_settings(collection, test):
    """Test setQuerySettings accepts valid settings configurations."""
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


# Property [Update Behavior]: setQuerySettings can update existing settings by query or hash.
SET_QUERY_SETTINGS_UPDATE_TESTS: list[SettingsTestCase] = [
    SettingsTestCase(
        "update_existing_settings",
        setup_commands=lambda ctx: [
            {
                "setQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"a10": 1},
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
                "filter": {"a10": 1},
                "$db": ctx.database,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": ctx.database, "coll": ctx.collection},
                        "allowedIndexes": ["_id_", {"a10": 1}],
                    }
                ],
            },
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"a10": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="update setQuerySettings should succeed",
    ),
    SettingsTestCase(
        "update_via_hash",
        setup_commands=lambda ctx: [
            {
                "setQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"a11": 1},
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
            "setQuerySettings": ctx.setup_results[0]["queryShapeHash"],
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": ctx.database, "coll": ctx.collection},
                        "allowedIndexes": ["_id_", {"a11": 1}],
                    }
                ],
            },
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"a11": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="update via hash should succeed",
    ),
]


@pytest.mark.admin
@pytest.mark.requires(change_streams=True)
@pytest.mark.parametrize("test", pytest_params(SET_QUERY_SETTINGS_UPDATE_TESTS))
def test_setQuerySettings_update(collection, test):
    """Test setQuerySettings can update existing settings by query or hash."""
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
