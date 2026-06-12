"""Tests for aggregate command readConcern provenance sub-field."""

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

# Property [readConcern Sub-field provenance Rejection]: invalid provenance types
# and values are rejected.
AGGREGATE_READCONCERN_SUBFIELD_PROVENANCE_TESTS: list[CommandTestCase] = [
    # provenance type rejection.
    CommandTestCase(
        "rc_reject_provenance_int",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"provenance": 123},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject int type for provenance",
    ),
    CommandTestCase(
        "rc_reject_provenance_int64",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"provenance": Int64(1)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Int64 type for provenance",
    ),
    CommandTestCase(
        "rc_reject_provenance_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"provenance": 1.0},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject double type for provenance",
    ),
    CommandTestCase(
        "rc_reject_provenance_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"provenance": Decimal128("1")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Decimal128 type for provenance",
    ),
    CommandTestCase(
        "rc_reject_provenance_bool",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"provenance": True},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject boolean type for provenance",
    ),
    CommandTestCase(
        "rc_reject_provenance_array",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"provenance": ["clientSupplied"]},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject array type for provenance",
    ),
    CommandTestCase(
        "rc_reject_provenance_document",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"provenance": {"a": 1}},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject document type for provenance",
    ),
    CommandTestCase(
        "rc_reject_provenance_binary",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"provenance": Binary(b"data")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Binary type for provenance",
    ),
    CommandTestCase(
        "rc_reject_provenance_objectid",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"provenance": ObjectId()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject ObjectId type for provenance",
    ),
    CommandTestCase(
        "rc_reject_provenance_datetime",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"provenance": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject datetime type for provenance",
    ),
    CommandTestCase(
        "rc_reject_provenance_timestamp",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"provenance": Timestamp(1, 1)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Timestamp type for provenance",
    ),
    CommandTestCase(
        "rc_reject_provenance_regex",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"provenance": Regex(".*")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Regex type for provenance",
    ),
    CommandTestCase(
        "rc_reject_provenance_code",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"provenance": Code("function(){}")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Code type for provenance",
    ),
    CommandTestCase(
        "rc_reject_provenance_code_with_scope",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"provenance": Code("function(){}", {"x": 1})},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Code with scope type for provenance",
    ),
    CommandTestCase(
        "rc_reject_provenance_minkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"provenance": MinKey()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject MinKey type for provenance",
    ),
    CommandTestCase(
        "rc_reject_provenance_maxkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"provenance": MaxKey()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject MaxKey type for provenance",
    ),
    # provenance invalid string value.
    CommandTestCase(
        "rc_reject_provenance_invalid",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"provenance": "invalid"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject invalid provenance string value",
    ),
]


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_READCONCERN_SUBFIELD_PROVENANCE_TESTS))
def test_aggregate_readconcern_subfield_provenance(database_client, collection, test):
    """Test aggregate readConcern provenance sub-field."""
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
