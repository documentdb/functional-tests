"""Tests for aggregate command readConcern afterClusterTime sub-field."""

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
from documentdb_tests.framework.error_codes import (
    ILLEGAL_OPERATION_ERROR,
    INVALID_OPTIONS_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [readConcern Sub-field afterClusterTime Rejection]: invalid afterClusterTime
# types are rejected.
AGGREGATE_READCONCERN_SUBFIELD_AFTERCLUSTERTIME_TESTS: list[CommandTestCase] = [
    # afterClusterTime type rejection.
    CommandTestCase(
        "rc_reject_afterclustertime_int",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"afterClusterTime": 123},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject int type for afterClusterTime",
    ),
    CommandTestCase(
        "rc_reject_afterclustertime_int64",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"afterClusterTime": Int64(1)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Int64 type for afterClusterTime",
    ),
    CommandTestCase(
        "rc_reject_afterclustertime_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"afterClusterTime": 1.0},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject double type for afterClusterTime",
    ),
    CommandTestCase(
        "rc_reject_afterclustertime_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"afterClusterTime": Decimal128("1")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Decimal128 type for afterClusterTime",
    ),
    CommandTestCase(
        "rc_reject_afterclustertime_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"afterClusterTime": "hello"},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject string type for afterClusterTime",
    ),
    CommandTestCase(
        "rc_reject_afterclustertime_bool",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"afterClusterTime": True},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject boolean type for afterClusterTime",
    ),
    CommandTestCase(
        "rc_reject_afterclustertime_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"afterClusterTime": None},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject null type for afterClusterTime",
    ),
    CommandTestCase(
        "rc_reject_afterclustertime_array",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"afterClusterTime": [1, 2]},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject array type for afterClusterTime",
    ),
    CommandTestCase(
        "rc_reject_afterclustertime_document",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"afterClusterTime": {"a": 1}},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject document type for afterClusterTime",
    ),
    CommandTestCase(
        "rc_reject_afterclustertime_binary",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"afterClusterTime": Binary(b"data")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Binary type for afterClusterTime",
    ),
    CommandTestCase(
        "rc_reject_afterclustertime_objectid",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"afterClusterTime": ObjectId()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject ObjectId type for afterClusterTime",
    ),
    CommandTestCase(
        "rc_reject_afterclustertime_datetime",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"afterClusterTime": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject datetime type for afterClusterTime",
    ),
    CommandTestCase(
        "rc_reject_afterclustertime_regex",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"afterClusterTime": Regex(".*")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Regex type for afterClusterTime",
    ),
    CommandTestCase(
        "rc_reject_afterclustertime_code",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"afterClusterTime": Code("function(){}")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Code type for afterClusterTime",
    ),
    CommandTestCase(
        "rc_reject_afterclustertime_code_with_scope",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"afterClusterTime": Code("function(){}", {"x": 1})},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Code with scope type for afterClusterTime",
    ),
    CommandTestCase(
        "rc_reject_afterclustertime_minkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"afterClusterTime": MinKey()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject MinKey type for afterClusterTime",
    ),
    CommandTestCase(
        "rc_reject_afterclustertime_maxkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"afterClusterTime": MaxKey()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject MaxKey type for afterClusterTime",
    ),
    CommandTestCase(
        "rc_reject_afterclustertime_null_timestamp",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"afterClusterTime": Timestamp(0, 0)},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="aggregate should reject Timestamp(0,0) for afterClusterTime as null timestamp",
    ),
    CommandTestCase(
        "rc_reject_afterclustertime_nonzero_standalone",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"afterClusterTime": Timestamp(1, 1)},
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="aggregate should reject non-zero afterClusterTime on standalone",
    ),
]


@pytest.mark.parametrize(
    "test", pytest_params(AGGREGATE_READCONCERN_SUBFIELD_AFTERCLUSTERTIME_TESTS)
)
def test_aggregate_readconcern_subfield_afterclustertime(database_client, collection, test):
    """Test aggregate readConcern afterClusterTime sub-field."""
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
