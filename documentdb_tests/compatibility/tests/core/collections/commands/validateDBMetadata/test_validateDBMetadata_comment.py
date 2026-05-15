"""Tests for validateDBMetadata comment field acceptance."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF

# Property [comment Acceptance (Smoke)]: all BSON types are accepted for
# the comment field without affecting command output.
VALIDATE_DB_METADATA_COMMENT_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"comment_{tid}",
        command=lambda ctx, v=val: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": ctx.database,
            "collection": ctx.collection,
            "comment": v,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg=f"validateDBMetadata should accept {tid} comment",
    )
    for tid, val in [
        ("int32", 42),
        ("int64", Int64(99)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("string", "a useful comment"),
        ("null", None),
        ("array", [1, "two", 3]),
        ("object", {"key": "value"}),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"data")),
        ("regex", Regex(".*")),
        ("code", Code("function(){}")),
        ("code_with_scope", Code("function(){}", {"x": 1})),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("large_string", "x" * 1_000_000),
        ("large_array", list(range(10_000))),
        ("deeply_nested", {"a": {"b": {"c": {"d": {"e": {"f": "deep"}}}}}}),
    ]
]


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(VALIDATE_DB_METADATA_COMMENT_ACCEPTANCE_TESTS))
def test_validateDBMetadata_comment(database_client, collection, test):
    """Test validateDBMetadata comment field acceptance."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
