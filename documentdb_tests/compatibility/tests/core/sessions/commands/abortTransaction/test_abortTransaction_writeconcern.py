"""Tests for abortTransaction writeConcern parameter acceptance.

Validates that accepted writeConcern variants (document types, w sub-field
values, j sub-field values, wtimeout sub-field values, and combinations)
are syntactically accepted by abortTransaction outside a transaction.
"""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import NO_SUCH_TRANSACTION_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.admin

# Property [writeConcern Document Acceptance]: writeConcern accepts document values.
WRITECONCERN_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "writeconcern_empty_doc",
        command={"abortTransaction": 1, "writeConcern": {}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept empty writeConcern document",
    ),
    CommandTestCase(
        "writeconcern_null",
        command={"abortTransaction": 1, "writeConcern": None},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern:null",
    ),
    CommandTestCase(
        "wc_combined_w_j_wtimeout",
        command={
            "abortTransaction": 1,
            "writeConcern": {"w": "majority", "j": True, "wtimeout": 10_000},
        },
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept combined w + j + wtimeout",
    ),
    CommandTestCase(
        "wc_w0_j_true",
        command={"abortTransaction": 1, "writeConcern": {"w": 0, "j": True}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept conflicting w:0 with j:true",
    ),
    CommandTestCase(
        "wc_fsync_true",
        command={"abortTransaction": 1, "writeConcern": {"fsync": True}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept legacy writeConcern.fsync:true",
    ),
]

# Property [w Accepted Values]: w accepts int and string "majority" values.
W_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "w_int32_one",
        command={"abortTransaction": 1, "writeConcern": {"w": 1}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.w:1",
    ),
    CommandTestCase(
        "w_int32_zero",
        command={"abortTransaction": 1, "writeConcern": {"w": 0}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.w:0 (unacknowledged)",
    ),
    CommandTestCase(
        "w_majority",
        command={"abortTransaction": 1, "writeConcern": {"w": "majority"}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.w:'majority'",
    ),
    CommandTestCase(
        "w_int64",
        command={"abortTransaction": 1, "writeConcern": {"w": Int64(1)}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.w:Int64(1)",
    ),
    CommandTestCase(
        "w_double_whole",
        command={"abortTransaction": 1, "writeConcern": {"w": 1.0}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.w:1.0",
    ),
    CommandTestCase(
        "w_double_fractional",
        command={"abortTransaction": 1, "writeConcern": {"w": 1.5}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.w:1.5",
    ),
    CommandTestCase(
        "w_decimal128",
        command={"abortTransaction": 1, "writeConcern": {"w": Decimal128("1")}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.w:Decimal128('1')",
    ),
]

# Property [j Accepted Values]: j accepts boolean and numeric types.
J_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "j_bool_true",
        command={"abortTransaction": 1, "writeConcern": {"j": True}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.j:true",
    ),
    CommandTestCase(
        "j_bool_false",
        command={"abortTransaction": 1, "writeConcern": {"j": False}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.j:false",
    ),
    CommandTestCase(
        "j_int32_one",
        command={"abortTransaction": 1, "writeConcern": {"j": 1}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.j:1 (coerced to true)",
    ),
    CommandTestCase(
        "j_int32_zero",
        command={"abortTransaction": 1, "writeConcern": {"j": 0}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.j:0 (coerced to false)",
    ),
    CommandTestCase(
        "j_null",
        command={"abortTransaction": 1, "writeConcern": {"j": None}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.j:null",
    ),
]

# Property [wtimeout Accepted Values]: wtimeout accepts numeric types broadly.
WTIMEOUT_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wtimeout_int32_positive",
        command={"abortTransaction": 1, "writeConcern": {"wtimeout": 1000}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.wtimeout:1000",
    ),
    CommandTestCase(
        "wtimeout_int32_zero",
        command={"abortTransaction": 1, "writeConcern": {"wtimeout": 0}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.wtimeout:0 (no timeout)",
    ),
    CommandTestCase(
        "wtimeout_int64",
        command={"abortTransaction": 1, "writeConcern": {"wtimeout": Int64(1000)}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.wtimeout:Int64(1000)",
    ),
    CommandTestCase(
        "wtimeout_double_whole",
        command={"abortTransaction": 1, "writeConcern": {"wtimeout": 1000.0}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.wtimeout:1000.0",
    ),
    CommandTestCase(
        "wtimeout_negative",
        command={"abortTransaction": 1, "writeConcern": {"wtimeout": -1}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.wtimeout:-1",
    ),
    CommandTestCase(
        "wtimeout_string",
        command={"abortTransaction": 1, "writeConcern": {"wtimeout": "1000"}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.wtimeout:'1000'",
    ),
    CommandTestCase(
        "wtimeout_bool",
        command={"abortTransaction": 1, "writeConcern": {"wtimeout": True}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.wtimeout:true",
    ),
    CommandTestCase(
        "wtimeout_null",
        command={"abortTransaction": 1, "writeConcern": {"wtimeout": None}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.wtimeout:null",
    ),
    CommandTestCase(
        "wtimeout_object",
        command={"abortTransaction": 1, "writeConcern": {"wtimeout": {}}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.wtimeout:{}",
    ),
    CommandTestCase(
        "wtimeout_array",
        command={"abortTransaction": 1, "writeConcern": {"wtimeout": []}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should accept writeConcern.wtimeout:[]",
    ),
]

WRITECONCERN_ACCEPTANCE_ALL_TESTS: list[CommandTestCase] = (
    WRITECONCERN_ACCEPTANCE_TESTS
    + W_ACCEPTANCE_TESTS
    + J_ACCEPTANCE_TESTS
    + WTIMEOUT_ACCEPTANCE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(WRITECONCERN_ACCEPTANCE_ALL_TESTS))
def test_abortTransaction_writeconcern(collection, test):
    """Test abortTransaction writeConcern parameter acceptance."""
    result = execute_admin_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)
