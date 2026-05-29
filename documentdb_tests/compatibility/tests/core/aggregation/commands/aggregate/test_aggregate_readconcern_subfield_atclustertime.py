"""Tests for aggregate command readConcern atClusterTime sub-field."""

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

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    INVALID_OPTIONS_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [readConcern Sub-field atClusterTime Rejection]: invalid atClusterTime
# types are rejected.
AGGREGATE_READCONCERN_SUBFIELD_ATCLUSTERTIME_TESTS: list[CommandTestCase] = [
    # atClusterTime type rejection.
    CommandTestCase(
        "rc_reject_atclustertime_int",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"atClusterTime": 123},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject int type for atClusterTime",
    ),
    CommandTestCase(
        "rc_reject_atclustertime_int64",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"atClusterTime": Int64(1)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Int64 type for atClusterTime",
    ),
    CommandTestCase(
        "rc_reject_atclustertime_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"atClusterTime": 1.0},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject double type for atClusterTime",
    ),
    CommandTestCase(
        "rc_reject_atclustertime_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"atClusterTime": Decimal128("1")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Decimal128 type for atClusterTime",
    ),
    CommandTestCase(
        "rc_reject_atclustertime_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"atClusterTime": "hello"},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject string type for atClusterTime",
    ),
    CommandTestCase(
        "rc_reject_atclustertime_bool",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"atClusterTime": True},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject boolean type for atClusterTime",
    ),
    CommandTestCase(
        "rc_reject_atclustertime_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"atClusterTime": None},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject null type for atClusterTime",
    ),
    CommandTestCase(
        "rc_reject_atclustertime_array",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"atClusterTime": [1, 2]},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject array type for atClusterTime",
    ),
    CommandTestCase(
        "rc_reject_atclustertime_document",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"atClusterTime": {"a": 1}},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject document type for atClusterTime",
    ),
    CommandTestCase(
        "rc_reject_atclustertime_binary",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"atClusterTime": Binary(b"data")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Binary type for atClusterTime",
    ),
    CommandTestCase(
        "rc_reject_atclustertime_objectid",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"atClusterTime": ObjectId()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject ObjectId type for atClusterTime",
    ),
    CommandTestCase(
        "rc_reject_atclustertime_datetime",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"atClusterTime": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject datetime type for atClusterTime",
    ),
    CommandTestCase(
        "rc_reject_atclustertime_regex",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"atClusterTime": Regex(".*")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Regex type for atClusterTime",
    ),
    CommandTestCase(
        "rc_reject_atclustertime_code",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"atClusterTime": Code("function(){}")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Code type for atClusterTime",
    ),
    CommandTestCase(
        "rc_reject_atclustertime_code_with_scope",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"atClusterTime": Code("function(){}", {"x": 1})},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Code with scope type for atClusterTime",
    ),
    CommandTestCase(
        "rc_reject_atclustertime_minkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"atClusterTime": MinKey()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject MinKey type for atClusterTime",
    ),
    CommandTestCase(
        "rc_reject_atclustertime_maxkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"atClusterTime": MaxKey()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject MaxKey type for atClusterTime",
    ),
    CommandTestCase(
        "rc_reject_atclustertime_no_snapshot",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"atClusterTime": Timestamp(1, 1)},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="aggregate should reject atClusterTime without level snapshot",
    ),
    CommandTestCase(
        "rc_reject_atclustertime_null_timestamp",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"level": "snapshot", "atClusterTime": Timestamp(0, 0)},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="aggregate should reject Timestamp(0,0) for atClusterTime as null timestamp",
    ),
    CommandTestCase(
        "rc_reject_atclustertime_zero_one_timestamp",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"level": "snapshot", "atClusterTime": Timestamp(0, 1)},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="aggregate should reject Timestamp(0,1) for atClusterTime as null timestamp",
    ),
]


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_READCONCERN_SUBFIELD_ATCLUSTERTIME_TESTS))
def test_aggregate_readconcern_subfield_atclustertime(database_client, collection, test):
    """Test aggregate readConcern atClusterTime sub-field."""
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
