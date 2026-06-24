"""Tests for commitTransaction writeConcern parameter acceptance in a real transaction.

Validates that accepted writeConcern variants (document types, w sub-field
values, j sub-field values, wtimeout sub-field values, and edge cases) succeed
when commitTransaction is issued inside an active transaction on a replica set.
"""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.sessions.commands.utils.session_test_case import (
    SessionOp,
    SessionOperation,
    SessionTestCase,
)
from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_session_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = [pytest.mark.admin, pytest.mark.requires(transactions=True)]

# Property [writeConcern Document Acceptance]: writeConcern accepts document values.
WRITECONCERN_ACCEPTANCE_TESTS: list[SessionTestCase] = [
    SessionTestCase(
        "writeconcern_empty_doc",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": 1, "writeConcern": {}},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept empty writeConcern document",
    ),
    SessionTestCase(
        "writeconcern_null",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": 1, "writeConcern": None},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept writeConcern:null",
    ),
    SessionTestCase(
        "wc_combined_w_j_wtimeout",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={
            "commitTransaction": 1,
            "writeConcern": {"w": "majority", "j": True, "wtimeout": 10_000},
        },
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept combined w + j + wtimeout",
    ),
    SessionTestCase(
        "wc_w0_j_true",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": 1, "writeConcern": {"w": 0, "j": True}},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept conflicting w:0 with j:true",
    ),
    SessionTestCase(
        "wc_fsync_true",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": 1, "writeConcern": {"fsync": True}},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept legacy writeConcern.fsync:true",
    ),
]

# Property [w Accepted Values]: w accepts int and string "majority" values.
W_ACCEPTANCE_TESTS: list[SessionTestCase] = [
    SessionTestCase(
        "w_int32_one",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": 1, "writeConcern": {"w": 1}},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept writeConcern.w:1",
    ),
    SessionTestCase(
        "w_int32_zero",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": 1, "writeConcern": {"w": 0}},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept writeConcern.w:0 (unacknowledged)",
    ),
    SessionTestCase(
        "w_majority",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": 1, "writeConcern": {"w": "majority"}},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept writeConcern.w:'majority'",
    ),
    SessionTestCase(
        "w_int64",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": 1, "writeConcern": {"w": Int64(1)}},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept writeConcern.w:Int64(1)",
    ),
    SessionTestCase(
        "w_double_whole",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": 1, "writeConcern": {"w": 1.0}},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept writeConcern.w:1.0",
    ),
    SessionTestCase(
        "w_double_fractional",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": 1, "writeConcern": {"w": 1.5}},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept writeConcern.w:1.5",
    ),
    SessionTestCase(
        "w_decimal128",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": 1, "writeConcern": {"w": Decimal128("1")}},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept writeConcern.w:Decimal128('1')",
    ),
]

# Property [j Accepted Values]: j accepts boolean and numeric types.
J_ACCEPTANCE_TESTS: list[SessionTestCase] = [
    SessionTestCase(
        "j_bool_true",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": 1, "writeConcern": {"j": True}},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept writeConcern.j:true",
    ),
    SessionTestCase(
        "j_bool_false",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": 1, "writeConcern": {"j": False}},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept writeConcern.j:false",
    ),
    SessionTestCase(
        "j_int32_one",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": 1, "writeConcern": {"j": 1}},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept writeConcern.j:1 (coerced to true)",
    ),
    SessionTestCase(
        "j_int32_zero",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": 1, "writeConcern": {"j": 0}},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept writeConcern.j:0 (coerced to false)",
    ),
    SessionTestCase(
        "j_null",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": 1, "writeConcern": {"j": None}},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept writeConcern.j:null",
    ),
]

# Property [wtimeout Accepted Values]: wtimeout accepts numeric types broadly.
WTIMEOUT_ACCEPTANCE_TESTS: list[SessionTestCase] = [
    SessionTestCase(
        "wtimeout_int32_positive",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": 1, "writeConcern": {"wtimeout": 1000}},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept writeConcern.wtimeout:1000",
    ),
    SessionTestCase(
        "wtimeout_int32_zero",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": 1, "writeConcern": {"wtimeout": 0}},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept writeConcern.wtimeout:0 (no timeout)",
    ),
    SessionTestCase(
        "wtimeout_int64",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": 1, "writeConcern": {"wtimeout": Int64(1000)}},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept writeConcern.wtimeout:Int64(1000)",
    ),
    SessionTestCase(
        "wtimeout_double_whole",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": 1, "writeConcern": {"wtimeout": 1000.0}},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept writeConcern.wtimeout:1000.0",
    ),
    SessionTestCase(
        "wtimeout_negative",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": 1, "writeConcern": {"wtimeout": -1}},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept writeConcern.wtimeout:-1",
    ),
    SessionTestCase(
        "wtimeout_string",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": 1, "writeConcern": {"wtimeout": "1000"}},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept writeConcern.wtimeout:'1000'",
    ),
    SessionTestCase(
        "wtimeout_bool",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": 1, "writeConcern": {"wtimeout": True}},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept writeConcern.wtimeout:true",
    ),
    SessionTestCase(
        "wtimeout_null",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": 1, "writeConcern": {"wtimeout": None}},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept writeConcern.wtimeout:null",
    ),
    SessionTestCase(
        "wtimeout_object",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": 1, "writeConcern": {"wtimeout": {}}},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept writeConcern.wtimeout:{}",
    ),
    SessionTestCase(
        "wtimeout_array",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": 1, "writeConcern": {"wtimeout": []}},
        expected_response={"ok": 1.0},
        msg="commitTransaction should accept writeConcern.wtimeout:[]",
    ),
]

WRITECONCERN_TESTS: list[SessionTestCase] = (
    WRITECONCERN_ACCEPTANCE_TESTS
    + W_ACCEPTANCE_TESTS
    + J_ACCEPTANCE_TESTS
    + WTIMEOUT_ACCEPTANCE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(WRITECONCERN_TESTS))
def test_commitTransaction_writeconcern(collection, test):
    """Test commitTransaction writeConcern parameter acceptance in a transaction."""
    result = execute_session_command(collection, test)
    assertSuccessPartial(result, test.expected_response, msg=test.msg)
