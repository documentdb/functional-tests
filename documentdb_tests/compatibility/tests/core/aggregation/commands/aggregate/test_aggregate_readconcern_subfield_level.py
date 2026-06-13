"""Tests for aggregate command readConcern level sub-field."""

from __future__ import annotations

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
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR, TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [readConcern Sub-field Level Rejection]: invalid level types and values
# are rejected.
AGGREGATE_READCONCERN_SUBFIELD_LEVEL_TESTS: list[CommandTestCase] = [
    # level type rejection (non-string, non-null).
    CommandTestCase(
        "rc_reject_level_int",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"level": 123},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject int type for readConcern level",
    ),
    CommandTestCase(
        "rc_reject_level_int64",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"level": Int64(1)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Int64 type for readConcern level",
    ),
    CommandTestCase(
        "rc_reject_level_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"level": 1.0},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject double type for readConcern level",
    ),
    CommandTestCase(
        "rc_reject_level_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"level": Decimal128("1")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Decimal128 type for readConcern level",
    ),
    CommandTestCase(
        "rc_reject_level_bool",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"level": True},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject boolean type for readConcern level",
    ),
    CommandTestCase(
        "rc_reject_level_array",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"level": ["local"]},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject array type for readConcern level",
    ),
    CommandTestCase(
        "rc_reject_level_document",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"level": {"a": 1}},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject document type for readConcern level",
    ),
    CommandTestCase(
        "rc_reject_level_binary",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"level": Binary(b"local")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Binary type for readConcern level",
    ),
    CommandTestCase(
        "rc_reject_level_objectid",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"level": ObjectId()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject ObjectId type for readConcern level",
    ),
    CommandTestCase(
        "rc_reject_level_datetime",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"level": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject datetime type for readConcern level",
    ),
    CommandTestCase(
        "rc_reject_level_timestamp",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"level": Timestamp(1, 1)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Timestamp type for readConcern level",
    ),
    CommandTestCase(
        "rc_reject_level_regex",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"level": Regex("local")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Regex type for readConcern level",
    ),
    CommandTestCase(
        "rc_reject_level_code",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"level": Code("function(){}")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Code type for readConcern level",
    ),
    CommandTestCase(
        "rc_reject_level_code_with_scope",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"level": Code("function(){}", {"x": 1})},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Code with scope type for readConcern level",
    ),
    CommandTestCase(
        "rc_reject_level_minkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"level": MinKey()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject MinKey type for readConcern level",
    ),
    CommandTestCase(
        "rc_reject_level_maxkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"level": MaxKey()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject MaxKey type for readConcern level",
    ),
    # level value rejection (invalid/unknown/wrong-case strings).
    CommandTestCase(
        "rc_reject_level_empty_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"level": ""},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject empty string as readConcern level",
    ),
    CommandTestCase(
        "rc_reject_level_invalid",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"level": "invalid"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject unknown readConcern level value",
    ),
    CommandTestCase(
        "rc_reject_level_wrong_case",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"level": "Local"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject wrong-case readConcern level",
    ),
]


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_READCONCERN_SUBFIELD_LEVEL_TESTS))
def test_aggregate_readconcern_subfield_level(database_client, collection, test):
    """Test aggregate readConcern level sub-field."""
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
