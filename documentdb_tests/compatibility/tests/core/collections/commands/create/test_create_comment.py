"""Tests for the create command comment parameter."""

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Comment Type Acceptance]: the comment field accepts all BSON types
# without type validation.
CREATE_COMMENT_TYPE_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id=f"comment_{tid}",
        command=lambda ctx, v=val, t=tid: {"create": f"{ctx.collection}_custom", "comment": v},
        expected={"ok": 1.0},
        msg=f"{tid} comment should succeed",
    )
    for tid, val in [
        ("null", None),
        ("string", "hello"),
        ("int32", 42),
        ("int64", Int64(99)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("bool", True),
        ("array", [1, "two", None]),
        ("object", {"key": "value"}),
        ("binary", Binary(b"x")),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("regex", Regex("t")),
        ("code", Code("x")),
        ("code_with_scope", Code("x", {"x": 1})),
        ("timestamp", Timestamp(0, 0)),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Comment Does Not Affect Validation]: the presence of a comment
# field does not interfere with error codes from other validation failures.
CREATE_COMMENT_NO_INTERFERENCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="comment_does_not_interfere_with_errors",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": "invalid",
            "comment": "test",
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="Comment does not interfere with error codes from other validation failures",
    ),
]

CREATE_COMMENT_TESTS: list[CommandTestCase] = (
    CREATE_COMMENT_TYPE_ACCEPTANCE_TESTS + CREATE_COMMENT_NO_INTERFERENCE_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(CREATE_COMMENT_TESTS))
def test_create_comment_cases(database_client, collection, test):
    """Test create command comment behavior."""
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
