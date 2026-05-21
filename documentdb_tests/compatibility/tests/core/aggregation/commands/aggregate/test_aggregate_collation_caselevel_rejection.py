"""Tests for aggregate command collation caseLevel sub-field rejection."""

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

# Property [caseLevel Type Strictness]: all non-boolean types for caseLevel
# produce TYPE_MISMATCH_ERROR with no coercion from truthy/falsy values.
COLLATION_CASELEVEL_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "caselevel_type_int32",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseLevel": 1},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject int32 caseLevel",
    ),
    CommandTestCase(
        "caselevel_type_int64",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseLevel": Int64(1)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Int64 caseLevel",
    ),
    CommandTestCase(
        "caselevel_type_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseLevel": 1.0},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject double caseLevel",
    ),
    CommandTestCase(
        "caselevel_type_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseLevel": Decimal128("1")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Decimal128 caseLevel",
    ),
    CommandTestCase(
        "caselevel_type_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseLevel": "true"},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject string caseLevel",
    ),
    CommandTestCase(
        "caselevel_type_array",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseLevel": [True]},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject array caseLevel",
    ),
    CommandTestCase(
        "caselevel_type_object",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseLevel": {"value": True}},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject object caseLevel",
    ),
    CommandTestCase(
        "caselevel_type_objectid",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseLevel": ObjectId()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject ObjectId caseLevel",
    ),
    CommandTestCase(
        "caselevel_type_datetime",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseLevel": datetime(2021, 1, 1, tzinfo=timezone.utc)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject datetime caseLevel",
    ),
    CommandTestCase(
        "caselevel_type_timestamp",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseLevel": Timestamp(1, 1)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Timestamp caseLevel",
    ),
    CommandTestCase(
        "caselevel_type_binary",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseLevel": Binary(b"x")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Binary caseLevel",
    ),
    CommandTestCase(
        "caselevel_type_regex",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseLevel": Regex(".*")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Regex caseLevel",
    ),
    CommandTestCase(
        "caselevel_type_code",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseLevel": Code("function(){}")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Code caseLevel",
    ),
    CommandTestCase(
        "caselevel_type_code_with_scope",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseLevel": Code("function(){}", {"x": 1})},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject CodeWithScope caseLevel",
    ),
    CommandTestCase(
        "caselevel_type_minkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseLevel": MinKey()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject MinKey caseLevel",
    ),
    CommandTestCase(
        "caselevel_type_maxkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "caseLevel": MaxKey()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject MaxKey caseLevel",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COLLATION_CASELEVEL_TYPE_ERROR_TESTS))
def test_aggregate_collation_caselevel_rejection(database_client, collection, test):
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
