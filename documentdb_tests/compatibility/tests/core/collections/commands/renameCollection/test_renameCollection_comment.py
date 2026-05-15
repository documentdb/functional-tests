"""Tests for renameCollection comment field."""

import functools
from datetime import datetime, timezone
from typing import Any

import pytest
from bson import Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp
from bson.binary import Binary

from documentdb_tests.compatibility.tests.core.collections.commands.renameCollection.utils.renameCollection_common import (  # noqa: E501
    cross_db_cleanup_ns,
)
from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import (
    assertResult,
)
from documentdb_tests.framework.error_codes import (
    COMMAND_NOT_FOUND_ERROR,
    OVERFLOW_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Comment Field (Success)]: the comment field accepts all
# BSON types without error; comment is not echoed in the response.
RENAME_COMMENT_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"comment_{tid}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_renamed",
            "comment": v,
        },
        expected={"ok": 1.0},
        msg=f"comment={tid} should succeed",
    )
    for tid, val in [
        ("string", "hello"),
        ("int32", 42),
        ("int64", Int64(42)),
        ("double", 3.14),
        ("decimal128", Decimal128("42")),
        ("bool", True),
        ("object", {"key": "value"}),
        ("array", [1, 2, 3]),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(0, 1)),
        ("binary", Binary(b"data")),
        ("regex", Regex(".*")),
        ("code", Code("function(){}")),
        ("code_with_scope", Code("function(){}", {})),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Comment Field (Nesting Boundary)]: 200 levels of nesting
# is accepted; 201 levels exceeds the BSON depth limit.
RENAME_COMMENT_NESTING_BOUNDARY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "comment_nested_object_200_levels",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_renamed",
            "comment": functools.reduce(
                lambda inner, _: {"n": inner}, range(199), dict[str, Any]()
            ),
        },
        expected={"ok": 1.0},
        msg="comment with 200 levels of object nesting should succeed",
    ),
    CommandTestCase(
        "comment_nested_array_200_levels",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_renamed",
            "comment": functools.reduce(lambda inner, _: [inner], range(199), list[Any]()),
        },
        expected={"ok": 1.0},
        msg="comment with 200 levels of array nesting should succeed",
    ),
]

# Property [Comment Field (Errors)]: deeply nested comment (201 levels)
# exceeds BSON nesting depth and produces an overflow error; comment as
# the first field causes the server to interpret it as the command name.
RENAME_COMMENT_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "comment_nested_object_201_levels",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_renamed",
            "comment": functools.reduce(
                lambda inner, _: {"n": inner}, range(200), dict[str, Any]()
            ),
        },
        error_code=OVERFLOW_ERROR,
        msg="comment with 201 levels of nesting should produce overflow error",
    ),
    CommandTestCase(
        "comment_nested_array_201_levels",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_renamed",
            "comment": functools.reduce(lambda inner, _: [inner], range(200), list[Any]()),
        },
        error_code=OVERFLOW_ERROR,
        msg="comment with 201 levels of array nesting should produce overflow error",
    ),
    CommandTestCase(
        "comment_as_first_field",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "comment": "first",
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_renamed",
        },
        error_code=COMMAND_NOT_FOUND_ERROR,
        msg="comment as first field should be interpreted as command name",
    ),
]

RENAME_COMMENT_TESTS: list[CommandTestCase] = (
    RENAME_COMMENT_SUCCESS_TESTS
    + RENAME_COMMENT_NESTING_BOUNDARY_TESTS
    + RENAME_COMMENT_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(RENAME_COMMENT_TESTS))
def test_renameCollection_comment(database_client, collection, register_db_cleanup, test):
    """Test renameCollection comment field."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    cmd = test.build_command(ctx)
    cross_db_cleanup_ns(cmd, ctx, register_db_cleanup)
    result = execute_admin_command(collection, cmd)
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
