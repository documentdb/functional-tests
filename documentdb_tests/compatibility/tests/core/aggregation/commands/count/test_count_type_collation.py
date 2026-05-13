"""Tests for count command collation type strictness and locale validation."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    MISSING_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Type Strictness: collation (type rejected)]: only document type is
# accepted for the collation field (in addition to null); all other BSON types
# produce a TypeMismatch error.
COUNT_TYPE_STRICTNESS_COLLATION_TYPE_REJECTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"type_collation_{tid}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {"count": ctx.collection, "collation": v},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"count should reject {tid} for collation",
    )
    for tid, val in [
        ("string", "en"),
        ("int32", 42),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("bool", True),
        ("array", [1, 2]),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02")),
        ("regex", Regex("^abc")),
        ("code", Code("function(){}")),
        ("code_with_scope", Code("function(){}", {"x": 1})),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Type Strictness: collation (locale)]: the locale sub-field is
# required and validates type and value.
COUNT_TYPE_STRICTNESS_COLLATION_LOCALE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "type_collation_locale_missing",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"strength": 2},
        },
        error_code=MISSING_FIELD_ERROR,
        msg="count should reject collation with missing locale",
    ),
    CommandTestCase(
        "type_collation_locale_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"locale": None},
        },
        error_code=MISSING_FIELD_ERROR,
        msg="count should reject collation with null locale",
    ),
    *[
        CommandTestCase(
            f"type_collation_locale_{tid}",
            docs=[{"_id": 1}],
            command=lambda ctx, v=val: {
                "count": ctx.collection,
                "collation": {"locale": v},
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"count should reject {tid} for collation locale",
        )
        for tid, val in [
            ("int32", 42),
            ("int64", Int64(1)),
            ("double", 3.14),
            ("decimal128", Decimal128("1")),
            ("bool", True),
            ("array", ["en"]),
            ("object", {"name": "en"}),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("timestamp", Timestamp(1, 1)),
            ("binary", Binary(b"\x01\x02")),
            ("regex", Regex("^en")),
            ("code", Code("function(){}")),
            ("code_with_scope", Code("function(){}", {"x": 1})),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    *[
        CommandTestCase(
            f"type_collation_locale_{tid}",
            docs=[{"_id": 1}],
            command=lambda ctx, v=val: {
                "count": ctx.collection,
                "collation": {"locale": v},
            },
            error_code=BAD_VALUE_ERROR,
            msg=f"count should reject {tid} for collation locale",
        )
        for tid, val in [
            ("empty", ""),
            ("invalid", "invalid_locale_xyz"),
            ("wrong_case", "EN"),
        ]
    ],
]

COUNT_TYPE_COLLATION_TESTS: list[CommandTestCase] = (
    COUNT_TYPE_STRICTNESS_COLLATION_TYPE_REJECTED_TESTS
    + COUNT_TYPE_STRICTNESS_COLLATION_LOCALE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COUNT_TYPE_COLLATION_TESTS))
def test_count_type_collation(database_client, collection, test):
    """Test count command collation type strictness."""
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
