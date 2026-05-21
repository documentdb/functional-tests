"""Tests for aggregate command collation normalization sub-field rejection."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Normalization Type Strictness]: all non-boolean types for
# normalization produce TYPE_MISMATCH_ERROR with no coercion.
COLLATION_NORMALIZATION_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "normalization_type_int32",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "normalization": 1},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject int32 normalization",
    ),
    CommandTestCase(
        "normalization_type_int64",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "normalization": Int64(1)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Int64 normalization",
    ),
    CommandTestCase(
        "normalization_type_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "normalization": 1.0},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject double normalization",
    ),
    CommandTestCase(
        "normalization_type_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "normalization": Decimal128("1")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Decimal128 normalization",
    ),
    CommandTestCase(
        "normalization_type_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "normalization": "true"},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject string normalization",
    ),
    CommandTestCase(
        "normalization_type_array",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "normalization": [True]},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject array normalization",
    ),
    CommandTestCase(
        "normalization_type_object",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "normalization": {"value": True}},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject object normalization",
    ),
    CommandTestCase(
        "normalization_type_objectid",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "normalization": ObjectId()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject ObjectId normalization",
    ),
    CommandTestCase(
        "normalization_type_datetime",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {
                "locale": "en",
                "normalization": datetime(2021, 1, 1, tzinfo=timezone.utc),
            },
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject datetime normalization",
    ),
    CommandTestCase(
        "normalization_type_timestamp",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "normalization": Timestamp(1, 1)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Timestamp normalization",
    ),
    CommandTestCase(
        "normalization_type_binary",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "normalization": Binary(b"x")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Binary normalization",
    ),
    CommandTestCase(
        "normalization_type_regex",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "normalization": Regex(".*")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Regex normalization",
    ),
    CommandTestCase(
        "normalization_type_code",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "normalization": Code("function(){}")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Code normalization",
    ),
    CommandTestCase(
        "normalization_type_code_with_scope",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "normalization": Code("function(){}", {"x": 1})},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject CodeWithScope normalization",
    ),
    CommandTestCase(
        "normalization_type_minkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "normalization": MinKey()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject MinKey normalization",
    ),
    CommandTestCase(
        "normalization_type_maxkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "normalization": MaxKey()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject MaxKey normalization",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COLLATION_NORMALIZATION_TYPE_ERROR_TESTS))
def test_aggregate_collation_normalization_rejection(database_client, collection, test):
    """Test aggregate command collation sub-field rejection."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
