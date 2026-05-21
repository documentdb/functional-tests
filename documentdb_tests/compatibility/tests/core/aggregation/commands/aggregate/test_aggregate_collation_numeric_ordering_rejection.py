"""Tests for aggregate command collation numericOrdering sub-field rejection."""

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

# Property [numericOrdering Type Strictness]: all non-boolean types for
# numericOrdering produce TYPE_MISMATCH_ERROR with no coercion.
COLLATION_NUMERIC_ORDERING_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "numeric_ordering_type_int32",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": 1},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject int32 numericOrdering",
    ),
    CommandTestCase(
        "numeric_ordering_type_int64",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": Int64(1)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Int64 numericOrdering",
    ),
    CommandTestCase(
        "numeric_ordering_type_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": 1.0},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject double numericOrdering",
    ),
    CommandTestCase(
        "numeric_ordering_type_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": Decimal128("1")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Decimal128 numericOrdering",
    ),
    CommandTestCase(
        "numeric_ordering_type_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": "true"},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject string numericOrdering",
    ),
    CommandTestCase(
        "numeric_ordering_type_array",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": [True]},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject array numericOrdering",
    ),
    CommandTestCase(
        "numeric_ordering_type_object",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": {"value": True}},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject object numericOrdering",
    ),
    CommandTestCase(
        "numeric_ordering_type_objectid",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": ObjectId()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject ObjectId numericOrdering",
    ),
    CommandTestCase(
        "numeric_ordering_type_datetime",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {
                "locale": "en",
                "numericOrdering": datetime(2021, 1, 1, tzinfo=timezone.utc),
            },
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject datetime numericOrdering",
    ),
    CommandTestCase(
        "numeric_ordering_type_timestamp",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": Timestamp(1, 1)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Timestamp numericOrdering",
    ),
    CommandTestCase(
        "numeric_ordering_type_binary",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": Binary(b"x")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Binary numericOrdering",
    ),
    CommandTestCase(
        "numeric_ordering_type_regex",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": Regex(".*")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Regex numericOrdering",
    ),
    CommandTestCase(
        "numeric_ordering_type_code",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": Code("function(){}")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Code numericOrdering",
    ),
    CommandTestCase(
        "numeric_ordering_type_code_with_scope",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": Code("function(){}", {"x": 1})},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject CodeWithScope numericOrdering",
    ),
    CommandTestCase(
        "numeric_ordering_type_minkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": MinKey()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject MinKey numericOrdering",
    ),
    CommandTestCase(
        "numeric_ordering_type_maxkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": MaxKey()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject MaxKey numericOrdering",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COLLATION_NUMERIC_ORDERING_TYPE_ERROR_TESTS))
def test_aggregate_collation_numeric_ordering_rejection(database_client, collection, test):
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
