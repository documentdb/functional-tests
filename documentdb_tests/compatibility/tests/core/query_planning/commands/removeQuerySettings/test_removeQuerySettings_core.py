"""Tests for removeQuerySettings command core acceptance behavior.

Validates that the removeQuerySettings command accepts valid query shapes
for find, distinct, and aggregate commands, various shape variations,
$db field variations, hash-based removal, and idempotent behavior.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = [pytest.mark.requires(cluster_admin=True), pytest.mark.no_parallel]

# Property [Find Shape Acceptance]: removeQuerySettings accepts find shapes
# with various field combinations without error.
REMOVEQUERYSETTINGS_FIND_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "accepts_find_filter_only",
        command=lambda ctx: {
            "removeQuerySettings": {
                "find": ctx.collection,
                "filter": {"a": 1},
                "$db": ctx.database,
            }
        },
        expected={"ok": 1.0},
        msg="removeQuerySettings should accept find with filter only",
    ),
    CommandTestCase(
        "accepts_find_filter_sort",
        command=lambda ctx: {
            "removeQuerySettings": {
                "find": ctx.collection,
                "filter": {"b": 1},
                "sort": {"b": 1},
                "$db": ctx.database,
            }
        },
        expected={"ok": 1.0},
        msg="removeQuerySettings should accept find with filter and sort",
    ),
    CommandTestCase(
        "accepts_find_filter_projection",
        command=lambda ctx: {
            "removeQuerySettings": {
                "find": ctx.collection,
                "filter": {"c": 1},
                "projection": {"c": 1},
                "$db": ctx.database,
            }
        },
        expected={"ok": 1.0},
        msg="removeQuerySettings should accept find with filter and projection",
    ),
    CommandTestCase(
        "accepts_find_filter_sort_projection",
        command=lambda ctx: {
            "removeQuerySettings": {
                "find": ctx.collection,
                "filter": {"d": 1},
                "sort": {"d": 1},
                "projection": {"d": 1},
                "$db": ctx.database,
            }
        },
        expected={"ok": 1.0},
        msg="removeQuerySettings should accept find with all shape fields",
    ),
    CommandTestCase(
        "accepts_find_with_collation",
        command=lambda ctx: {
            "removeQuerySettings": {
                "find": ctx.collection,
                "filter": {"e": "abc"},
                "collation": {"locale": "en", "strength": 2},
                "$db": ctx.database,
            }
        },
        expected={"ok": 1.0},
        msg="removeQuerySettings should accept find with collation",
    ),
    CommandTestCase(
        "accepts_find_with_let",
        command=lambda ctx: {
            "removeQuerySettings": {
                "find": ctx.collection,
                "filter": {"$expr": {"$eq": ["$f", "$$target"]}},
                "let": {"target": 1},
                "$db": ctx.database,
            }
        },
        expected={"ok": 1.0},
        msg="removeQuerySettings should accept find with let",
    ),
    CommandTestCase(
        "accepts_find_without_filter",
        command=lambda ctx: {
            "removeQuerySettings": {
                "find": ctx.collection,
                "$db": ctx.database,
            }
        },
        expected={"ok": 1.0},
        msg="removeQuerySettings should accept find without filter",
    ),
]

# Property [Distinct Shape Acceptance]: removeQuerySettings accepts distinct
# shapes with various field combinations without error.
REMOVEQUERYSETTINGS_DISTINCT_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "accepts_distinct_key_only",
        command=lambda ctx: {
            "removeQuerySettings": {
                "distinct": ctx.collection,
                "key": "j",
                "$db": ctx.database,
            }
        },
        expected={"ok": 1.0},
        msg="removeQuerySettings should accept distinct with key only",
    ),
    CommandTestCase(
        "accepts_distinct_key_with_query",
        command=lambda ctx: {
            "removeQuerySettings": {
                "distinct": ctx.collection,
                "key": "k",
                "query": {"$and": [{"k": {"$gt": 0}}, {"k": {"$lt": 100}}]},
                "$db": ctx.database,
            }
        },
        expected={"ok": 1.0},
        msg="removeQuerySettings should accept distinct with query filter",
    ),
]

# Property [Aggregate Shape Acceptance]: removeQuerySettings accepts aggregate
# pipeline shapes with various stage combinations without error.
REMOVEQUERYSETTINGS_AGGREGATE_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "accepts_aggregate_single_stage",
        command=lambda ctx: {
            "removeQuerySettings": {
                "aggregate": ctx.collection,
                "pipeline": [{"$match": {"l": 1}}],
                "$db": ctx.database,
            }
        },
        expected={"ok": 1.0},
        msg="removeQuerySettings should accept aggregate with single stage",
    ),
    CommandTestCase(
        "accepts_aggregate_multi_stage",
        command=lambda ctx: {
            "removeQuerySettings": {
                "aggregate": ctx.collection,
                "pipeline": [
                    {"$match": {"m": 1}},
                    {"$group": {"_id": "$m", "count": {"$sum": 1}}},
                ],
                "$db": ctx.database,
            }
        },
        expected={"ok": 1.0},
        msg="removeQuerySettings should accept aggregate with multiple stages",
    ),
]

# Property [Nonexistent $db Acceptance]: removeQuerySettings accepts
# non-existent database names in the $db field without error.
REMOVEQUERYSETTINGS_DB_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "accepts_nonexistent_db",
        command=lambda ctx: {
            "removeQuerySettings": {
                "find": ctx.collection,
                "filter": {"o": 1},
                "$db": f"{ctx.database}_nonexistent",
            }
        },
        expected={"ok": 1.0},
        msg="removeQuerySettings should accept non-existent $db",
    ),
]

# Property [Silent No-Op]: removeQuerySettings succeeds silently when
# no matching settings exist.
REMOVEQUERYSETTINGS_NOOP_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "noop_nonexistent_query_shape",
        command=lambda ctx: {
            "removeQuerySettings": {
                "find": ctx.collection,
                "filter": {"nonexistent_field": 1},
                "$db": ctx.database,
            }
        },
        expected={"ok": 1.0},
        msg="removeQuerySettings should succeed when no matching settings exist",
    ),
    CommandTestCase(
        "noop_nonexistent_hash",
        command=lambda ctx: {
            "removeQuerySettings": "00000000000000000000000000000000"
            "00000000000000000000000000000000"
        },
        expected={"ok": 1.0},
        msg="removeQuerySettings should succeed with a non-existent hash",
    ),
    CommandTestCase(
        "noop_lowercase_hash",
        command=lambda ctx: {
            "removeQuerySettings": "abcdef0123456789abcdef0123456789"
            "abcdef0123456789abcdef0123456789"
        },
        expected={"ok": 1.0},
        msg="removeQuerySettings should accept lowercase hex hash",
    ),
]

# Property [IDHACK Query Acceptance]: unlike setQuerySettings which rejects
# IDHACK-eligible queries, removeQuerySettings accepts them.
REMOVEQUERYSETTINGS_IDHACK_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "accepts_idhack_query",
        command=lambda ctx: {
            "removeQuerySettings": {
                "find": ctx.collection,
                "filter": {"_id": 1},
                "$db": ctx.database,
            }
        },
        expected={"ok": 1.0},
        msg="removeQuerySettings should accept IDHACK-eligible queries",
    ),
]

# Property [Internal Database Acceptance]: unlike setQuerySettings which
# rejects internal databases, removeQuerySettings accepts them.
REMOVEQUERYSETTINGS_INTERNAL_DB_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "accepts_admin_db",
        command=lambda ctx: {
            "removeQuerySettings": {
                "find": "system.users",
                "filter": {},
                "$db": "admin",
            }
        },
        expected={"ok": 1.0},
        msg="removeQuerySettings should accept admin database query shapes",
    ),
    CommandTestCase(
        "accepts_local_db",
        command=lambda ctx: {
            "removeQuerySettings": {
                "find": "oplog.rs",
                "filter": {},
                "$db": "local",
            }
        },
        expected={"ok": 1.0},
        msg="removeQuerySettings should accept local database query shapes",
    ),
]

# Property [Comment Field Acceptance]: removeQuerySettings accepts the
# comment top-level field without error.
REMOVEQUERYSETTINGS_COMMENT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "accepts_comment_field",
        command=lambda ctx: {
            "removeQuerySettings": {
                "find": ctx.collection,
                "filter": {"cmt1": 1},
                "$db": ctx.database,
            },
            "comment": "test comment",
        },
        expected={"ok": 1.0},
        msg="removeQuerySettings should accept comment field",
    ),
]

REMOVEQUERYSETTINGS_CORE_TESTS: list[CommandTestCase] = (
    REMOVEQUERYSETTINGS_FIND_ACCEPTANCE_TESTS
    + REMOVEQUERYSETTINGS_DISTINCT_ACCEPTANCE_TESTS
    + REMOVEQUERYSETTINGS_AGGREGATE_ACCEPTANCE_TESTS
    + REMOVEQUERYSETTINGS_DB_ACCEPTANCE_TESTS
    + REMOVEQUERYSETTINGS_NOOP_TESTS
    + REMOVEQUERYSETTINGS_IDHACK_TESTS
    + REMOVEQUERYSETTINGS_INTERNAL_DB_TESTS
    + REMOVEQUERYSETTINGS_COMMENT_TESTS
)


@pytest.mark.parametrize("test", pytest_params(REMOVEQUERYSETTINGS_CORE_TESTS))
def test_removeQuerySettings_core(collection, test):
    """Test removeQuerySettings command core acceptance behavior."""
    ctx = CommandContext.from_collection(collection)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertSuccessPartial(result, test.build_expected(ctx), msg=test.msg)
