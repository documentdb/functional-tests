"""Tests for commitTransaction writeConcern parameter acceptance in a real transaction.

Validates that accepted writeConcern variants (document types, w sub-field
values, j sub-field values, wtimeout sub-field values, and edge cases) succeed
when commitTransaction is issued inside an active transaction on a replica set.
"""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = [pytest.mark.admin, pytest.mark.requires(transactions=True)]

# Property [writeConcern Document Acceptance]: writeConcern accepts document values.
WRITECONCERN_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "writeconcern_empty_doc",
        command={"commitTransaction": 1, "writeConcern": {}},
        msg="commitTransaction should accept empty writeConcern document",
    ),
    CommandTestCase(
        "writeconcern_null",
        command={"commitTransaction": 1, "writeConcern": None},
        msg="commitTransaction should accept writeConcern:null",
    ),
    CommandTestCase(
        "wc_combined_w_j_wtimeout",
        command={
            "commitTransaction": 1,
            "writeConcern": {"w": "majority", "j": True, "wtimeout": 10_000},
        },
        msg="commitTransaction should accept combined w + j + wtimeout",
    ),
    CommandTestCase(
        "wc_w0_j_true",
        command={"commitTransaction": 1, "writeConcern": {"w": 0, "j": True}},
        msg="commitTransaction should accept conflicting w:0 with j:true",
    ),
    CommandTestCase(
        "wc_fsync_true",
        command={"commitTransaction": 1, "writeConcern": {"fsync": True}},
        msg="commitTransaction should accept legacy writeConcern.fsync:true",
    ),
]

# Property [w Accepted Values]: w accepts int and string "majority" values.
W_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "w_int32_one",
        command={"commitTransaction": 1, "writeConcern": {"w": 1}},
        msg="commitTransaction should accept writeConcern.w:1",
    ),
    CommandTestCase(
        "w_int32_zero",
        command={"commitTransaction": 1, "writeConcern": {"w": 0}},
        msg="commitTransaction should accept writeConcern.w:0 (unacknowledged)",
    ),
    CommandTestCase(
        "w_majority",
        command={"commitTransaction": 1, "writeConcern": {"w": "majority"}},
        msg="commitTransaction should accept writeConcern.w:'majority'",
    ),
    CommandTestCase(
        "w_int64",
        command={"commitTransaction": 1, "writeConcern": {"w": Int64(1)}},
        msg="commitTransaction should accept writeConcern.w:Int64(1)",
    ),
    CommandTestCase(
        "w_double_whole",
        command={"commitTransaction": 1, "writeConcern": {"w": 1.0}},
        msg="commitTransaction should accept writeConcern.w:1.0",
    ),
    CommandTestCase(
        "w_double_fractional",
        command={"commitTransaction": 1, "writeConcern": {"w": 1.5}},
        msg="commitTransaction should accept writeConcern.w:1.5",
    ),
    CommandTestCase(
        "w_decimal128",
        command={"commitTransaction": 1, "writeConcern": {"w": Decimal128("1")}},
        msg="commitTransaction should accept writeConcern.w:Decimal128('1')",
    ),
]

# Property [j Accepted Values]: j accepts boolean and numeric types.
J_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "j_bool_true",
        command={"commitTransaction": 1, "writeConcern": {"j": True}},
        msg="commitTransaction should accept writeConcern.j:true",
    ),
    CommandTestCase(
        "j_bool_false",
        command={"commitTransaction": 1, "writeConcern": {"j": False}},
        msg="commitTransaction should accept writeConcern.j:false",
    ),
    CommandTestCase(
        "j_int32_one",
        command={"commitTransaction": 1, "writeConcern": {"j": 1}},
        msg="commitTransaction should accept writeConcern.j:1 (coerced to true)",
    ),
    CommandTestCase(
        "j_int32_zero",
        command={"commitTransaction": 1, "writeConcern": {"j": 0}},
        msg="commitTransaction should accept writeConcern.j:0 (coerced to false)",
    ),
    CommandTestCase(
        "j_null",
        command={"commitTransaction": 1, "writeConcern": {"j": None}},
        msg="commitTransaction should accept writeConcern.j:null",
    ),
]

# Property [wtimeout Accepted Values]: wtimeout accepts numeric types broadly.
WTIMEOUT_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wtimeout_int32_positive",
        command={"commitTransaction": 1, "writeConcern": {"wtimeout": 1000}},
        msg="commitTransaction should accept writeConcern.wtimeout:1000",
    ),
    CommandTestCase(
        "wtimeout_int32_zero",
        command={"commitTransaction": 1, "writeConcern": {"wtimeout": 0}},
        msg="commitTransaction should accept writeConcern.wtimeout:0 (no timeout)",
    ),
    CommandTestCase(
        "wtimeout_int64",
        command={"commitTransaction": 1, "writeConcern": {"wtimeout": Int64(1000)}},
        msg="commitTransaction should accept writeConcern.wtimeout:Int64(1000)",
    ),
    CommandTestCase(
        "wtimeout_double_whole",
        command={"commitTransaction": 1, "writeConcern": {"wtimeout": 1000.0}},
        msg="commitTransaction should accept writeConcern.wtimeout:1000.0",
    ),
    CommandTestCase(
        "wtimeout_negative",
        command={"commitTransaction": 1, "writeConcern": {"wtimeout": -1}},
        msg="commitTransaction should accept writeConcern.wtimeout:-1",
    ),
    CommandTestCase(
        "wtimeout_string",
        command={"commitTransaction": 1, "writeConcern": {"wtimeout": "1000"}},
        msg="commitTransaction should accept writeConcern.wtimeout:'1000'",
    ),
    CommandTestCase(
        "wtimeout_bool",
        command={"commitTransaction": 1, "writeConcern": {"wtimeout": True}},
        msg="commitTransaction should accept writeConcern.wtimeout:true",
    ),
    CommandTestCase(
        "wtimeout_null",
        command={"commitTransaction": 1, "writeConcern": {"wtimeout": None}},
        msg="commitTransaction should accept writeConcern.wtimeout:null",
    ),
    CommandTestCase(
        "wtimeout_object",
        command={"commitTransaction": 1, "writeConcern": {"wtimeout": {}}},
        msg="commitTransaction should accept writeConcern.wtimeout:{}",
    ),
    CommandTestCase(
        "wtimeout_array",
        command={"commitTransaction": 1, "writeConcern": {"wtimeout": []}},
        msg="commitTransaction should accept writeConcern.wtimeout:[]",
    ),
]

WRITECONCERN_TESTS: list[CommandTestCase] = (
    WRITECONCERN_ACCEPTANCE_TESTS
    + W_ACCEPTANCE_TESTS
    + J_ACCEPTANCE_TESTS
    + WTIMEOUT_ACCEPTANCE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(WRITECONCERN_TESTS))
def test_commitTransaction_writeconcern(collection, test):
    """Test commitTransaction writeConcern parameter acceptance in a transaction."""
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        collection.insert_one({"_id": 1}, session=session)
        result = execute_admin_command(collection, test.command, session=session)
    assertSuccessPartial(result, {"ok": 1.0}, msg=test.msg)
