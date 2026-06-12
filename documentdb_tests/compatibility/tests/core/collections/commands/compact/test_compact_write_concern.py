"""Tests for compact command writeConcern rejection."""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import INVALID_OPTIONS_ERROR, TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [writeConcern Rejection]: compact does not support
# writeConcern; object values produce an invalid options error, non-object
# types produce a type mismatch error, and null is treated as omitted.
COMPACT_WRITE_CONCERN_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "write_concern_w_1",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "writeConcern": {"w": 1}},
        error_code=INVALID_OPTIONS_ERROR,
        msg="writeConcern with w:1 should be rejected",
    ),
    CommandTestCase(
        "write_concern_w_majority",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "writeConcern": {"w": "majority"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="writeConcern with w:majority should be rejected",
    ),
    CommandTestCase(
        "write_concern_empty_object",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "writeConcern": {}},
        error_code=INVALID_OPTIONS_ERROR,
        msg="writeConcern as empty object should be rejected",
    ),
    CommandTestCase(
        "write_concern_w_0",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "writeConcern": {"w": 0}},
        error_code=INVALID_OPTIONS_ERROR,
        msg="writeConcern with w:0 should be rejected",
    ),
    CommandTestCase(
        "write_concern_wtimeout",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "writeConcern": {"w": 1, "wtimeout": 1000},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="writeConcern with wtimeout should be rejected",
    ),
    CommandTestCase(
        "write_concern_j_true",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "writeConcern": {"j": True},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="writeConcern with j:true should be rejected",
    ),
    CommandTestCase(
        "write_concern_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "writeConcern": "majority"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="writeConcern as string should be rejected as wrong type",
    ),
    CommandTestCase(
        "write_concern_int",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "writeConcern": 1},
        error_code=TYPE_MISMATCH_ERROR,
        msg="writeConcern as int should be rejected as wrong type",
    ),
    CommandTestCase(
        "write_concern_bool",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "writeConcern": True},
        error_code=TYPE_MISMATCH_ERROR,
        msg="writeConcern as bool should be rejected as wrong type",
    ),
    CommandTestCase(
        "write_concern_array",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "writeConcern": [{"w": 1}]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="writeConcern as array should be rejected as wrong type",
    ),
]


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COMPACT_WRITE_CONCERN_REJECTION_TESTS))
def test_compact_write_concern(database_client, collection, test):
    """Test compact command rejects writeConcern."""
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
