"""Tests for collMod viewOn."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    GRAPH_CONTAINS_CYCLE_ERROR,
    INVALID_NAMESPACE_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.target_collection import ViewCollection
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
    STRING_SIZE_LIMIT_BYTES,
)

# Property [viewOn Success]: a string viewOn is validated as a namespace but not
# checked for target existence, so any structurally valid name is accepted and
# stored verbatim - including whitespace, control characters, Unicode, and
# interior/trailing dots or database-qualified names - null is accepted as an
# omitted field, and the value has no length limit. (Structurally invalid names
# are rejected by the viewOn Namespace Rejection property.)
COLLMOD_VIEW_ON_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "nonexistent_target",
        target_collection=ViewCollection(),
        command=lambda ctx: {"collMod": ctx.collection, "viewOn": "no_such_collection"},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a viewOn naming a nonexistent target without validating it",
    ),
    CommandTestCase(
        "null",
        target_collection=ViewCollection(),
        command=lambda ctx: {"collMod": ctx.collection, "viewOn": None},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a null viewOn as an omitted field",
    ),
    *[
        CommandTestCase(
            f"content_{tid}",
            target_collection=ViewCollection(),
            command=lambda ctx, v=val: {"collMod": ctx.collection, "viewOn": v},
            expected={"ok": Eq(1.0)},
            msg=f"collMod should accept a viewOn with {tid} content verbatim",
        )
        for tid, val in [
            ("single_space", " "),
            ("nbsp", "a\u00a0b"),  # U+00A0 no-break space.
            ("control_char", "\x01"),  # U+0001 start of heading.
            ("two_byte_unicode", "caf\u00e9"),  # U+00E9 latin small e with acute.
            ("three_byte_unicode", "\u4e2d"),  # U+4E2D CJK ideograph.
            ("four_byte_unicode", "\U0001f600coll"),  # U+1F600 grinning face.
            ("trailing_dot", "trailing."),
            ("interior_dots", "a.b.c"),
            ("database_qualified", "db.coll"),
        ]
    ],
    *[
        CommandTestCase(
            f"length_{tid}",
            target_collection=ViewCollection(),
            command=lambda ctx, v=val: {"collMod": ctx.collection, "viewOn": v},
            expected={"ok": Eq(1.0)},
            msg=f"collMod should accept a {tid} viewOn value with no length-based limit",
        )
        # A viewOn value has no length limit, unlike the collMod target name.
        # These three sizes bracket the 16 MB BSON document size to show none of
        # them hit a length-based limit.
        for tid, val in [
            ("below_16mb", "a" * (STRING_SIZE_LIMIT_BYTES - 1)),
            ("at_16mb", "a" * STRING_SIZE_LIMIT_BYTES),
            ("above_16mb", "a" * (STRING_SIZE_LIMIT_BYTES + 1)),
        ]
    ],
]

# Property [viewOn Type Rejection]: any non-string value for viewOn produces a
# TypeMismatch error.
COLLMOD_VIEW_ON_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"type_{tid}",
        target_collection=ViewCollection(),
        command=lambda ctx, v=val: {"collMod": ctx.collection, "viewOn": v},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"collMod should reject a {tid} viewOn as a non-string",
    )
    for tid, val in [
        ("int32", 42),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool_true", True),
        ("bool_false", False),
        ("array", ["src"]),
        ("object", {"a": 1}),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [viewOn Empty Rejection]: an empty string viewOn produces a BadValue
# error.
COLLMOD_VIEW_ON_EMPTY_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "empty",
        target_collection=ViewCollection(),
        command=lambda ctx: {"collMod": ctx.collection, "viewOn": ""},
        error_code=BAD_VALUE_ERROR,
        msg="collMod should reject an empty string viewOn",
    ),
]

# Property [viewOn Namespace Rejection]: a viewOn string that is structurally
# invalid as a namespace produces an InvalidNamespace error, where a leading
# dollar is treated as name content rather than a field path.
COLLMOD_VIEW_ON_NAMESPACE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"namespace_{tid}",
        target_collection=ViewCollection(),
        command=lambda ctx, v=val: {"collMod": ctx.collection, "viewOn": v},
        error_code=INVALID_NAMESPACE_ERROR,
        msg=f"collMod should reject a {tid} viewOn as a structurally invalid namespace",
    )
    for tid, val in [
        ("dollar_prefixed", "$x"),
        ("embedded_null", "a\x00b"),
        ("leading_dot", ".leading"),
    ]
]

# Property [viewOn Self Reference Rejection]: a viewOn equal to the view's own
# name produces a GraphContainsCycle error.
COLLMOD_VIEW_ON_CYCLE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "self_reference",
        target_collection=ViewCollection(),
        command=lambda ctx: {"collMod": ctx.collection, "viewOn": ctx.collection},
        error_code=GRAPH_CONTAINS_CYCLE_ERROR,
        msg="collMod should reject a viewOn equal to the view's own name as a cycle",
    ),
]

COLLMOD_VIEW_ON_TESTS: list[CommandTestCase] = (
    COLLMOD_VIEW_ON_SUCCESS_TESTS
    + COLLMOD_VIEW_ON_TYPE_ERROR_TESTS
    + COLLMOD_VIEW_ON_EMPTY_ERROR_TESTS
    + COLLMOD_VIEW_ON_NAMESPACE_ERROR_TESTS
    + COLLMOD_VIEW_ON_CYCLE_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COLLMOD_VIEW_ON_TESTS))
def test_collMod_view_on(database_client, collection, test):
    """Test collMod viewOn acceptance and rejection."""
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
