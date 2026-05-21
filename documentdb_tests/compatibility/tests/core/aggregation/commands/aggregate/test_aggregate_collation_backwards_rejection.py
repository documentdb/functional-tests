"""Tests for aggregate command collation backwards sub-field rejection."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR, TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Backwards Type and Value Errors]: only boolean true/false is
# accepted for backwards; null produces TYPE_MISMATCH_ERROR (asymmetric with
# other boolean fields), all non-boolean types produce TYPE_MISMATCH_ERROR, and
# backwards:true with strength 1 produces BAD_VALUE_ERROR.
COLLATION_BACKWARDS_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "backwards_null_error",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "backwards": None},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject null backwards (asymmetric with other boolean fields)",
    ),
    CommandTestCase(
        "backwards_type_int32",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "backwards": 1},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject int32 backwards",
    ),
    CommandTestCase(
        "backwards_type_int64",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "backwards": Int64(1)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Int64 backwards",
    ),
    CommandTestCase(
        "backwards_type_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "backwards": 1.0},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject double backwards",
    ),
    CommandTestCase(
        "backwards_type_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "backwards": Decimal128("1")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Decimal128 backwards",
    ),
    CommandTestCase(
        "backwards_type_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "backwards": "true"},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject string backwards",
    ),
    CommandTestCase(
        "backwards_type_array",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "backwards": [True]},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject array backwards",
    ),
    CommandTestCase(
        "backwards_type_object",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "backwards": {"value": True}},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject object backwards",
    ),
    CommandTestCase(
        "backwards_type_objectid",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "backwards": ObjectId()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject ObjectId backwards",
    ),
    CommandTestCase(
        "backwards_type_datetime",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "backwards": datetime(2021, 1, 1, tzinfo=timezone.utc)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject datetime backwards",
    ),
    CommandTestCase(
        "backwards_type_timestamp",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "backwards": Timestamp(1, 1)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Timestamp backwards",
    ),
    CommandTestCase(
        "backwards_type_binary",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "backwards": Binary(b"x")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Binary backwards",
    ),
    CommandTestCase(
        "backwards_type_regex",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "backwards": Regex(".*")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Regex backwards",
    ),
    CommandTestCase(
        "backwards_type_code",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "backwards": Code("function(){}")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Code backwards",
    ),
    CommandTestCase(
        "backwards_type_code_with_scope",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "backwards": Code("function(){}", {"x": 1})},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject CodeWithScope backwards",
    ),
    CommandTestCase(
        "backwards_type_minkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "backwards": MinKey()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject MinKey backwards",
    ),
    CommandTestCase(
        "backwards_type_maxkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "backwards": MaxKey()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject MaxKey backwards",
    ),
    CommandTestCase(
        "backwards_true_strength1_error",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1, "backwards": True},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject backwards:true with strength 1",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COLLATION_BACKWARDS_ERROR_TESTS))
def test_aggregate_collation_backwards_rejection(database_client, collection, test):
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
