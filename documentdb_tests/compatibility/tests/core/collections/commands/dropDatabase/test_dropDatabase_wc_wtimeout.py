from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import FAILED_TO_PARSE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
    INT32_MAX,
    INT32_OVERFLOW,
    INT64_MIN,
)

# Property [writeConcern wtimeout Permissive Acceptance]: the wtimeout
# field permissively accepts any numeric BSON type, booleans, strings,
# and null.
WRITE_CONCERN_WTIMEOUT_ACCEPTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"wtimeout": True}},
        expected={"ok": 1.0},
        msg="wtimeout:bool true should be accepted",
        id="wtimeout_bool_true",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"wtimeout": False}},
        expected={"ok": 1.0},
        msg="wtimeout:bool false should be accepted",
        id="wtimeout_bool_false",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"wtimeout": 2.5}},
        expected={"ok": 1.0},
        msg="wtimeout:double should be accepted",
        id="wtimeout_double",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"wtimeout": Int64(42)}},
        expected={"ok": 1.0},
        msg="wtimeout:Int64 should be accepted",
        id="wtimeout_int64",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"wtimeout": Decimal128("99")}},
        expected={"ok": 1.0},
        msg="wtimeout:Decimal128 should be accepted",
        id="wtimeout_decimal128",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"wtimeout": 5}},
        expected={"ok": 1.0},
        msg="wtimeout:int32 should be accepted",
        id="wtimeout_int32",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"wtimeout": "hello"}},
        expected={"ok": 1.0},
        msg="wtimeout:string should be accepted",
        id="wtimeout_string",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"wtimeout": None}},
        expected={"ok": 1.0},
        msg="wtimeout:null should be treated as omitted and succeed",
        id="wtimeout_null",
    ),
]

# Property [writeConcern wtimeout Special Values]: the wtimeout field
# accepts special numeric values, boundary values, and both float and
# Decimal128 forms.
WRITE_CONCERN_WTIMEOUT_SPECIAL_VALUES_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"wtimeout": INT32_MAX}},
        expected={"ok": 1.0},
        msg="wtimeout:max int32 should be accepted",
        id="wtimeout_max_int32",
    ),
    CommandTestCase(
        command={
            "dropDatabase": 1,
            "writeConcern": {"wtimeout": INT64_MIN},
        },
        expected={"ok": 1.0},
        msg="wtimeout:Int64 min should be accepted",
        id="wtimeout_int64_min",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"wtimeout": FLOAT_NAN}},
        expected={"ok": 1.0},
        msg="wtimeout:NaN should be accepted",
        id="wtimeout_float_nan",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"wtimeout": FLOAT_NEGATIVE_NAN}},
        expected={"ok": 1.0},
        msg="wtimeout:negative NaN should be accepted",
        id="wtimeout_float_neg_nan",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"wtimeout": FLOAT_NEGATIVE_INFINITY}},
        expected={"ok": 1.0},
        msg="wtimeout:-Infinity should be accepted",
        id="wtimeout_float_neg_infinity",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"wtimeout": DECIMAL128_NAN}},
        expected={"ok": 1.0},
        msg="wtimeout:Decimal128('NaN') should be accepted",
        id="wtimeout_decimal128_nan",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"wtimeout": DECIMAL128_NEGATIVE_NAN}},
        expected={"ok": 1.0},
        msg="wtimeout:Decimal128 negative NaN should be accepted",
        id="wtimeout_decimal128_neg_nan",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"wtimeout": DECIMAL128_NEGATIVE_INFINITY}},
        expected={"ok": 1.0},
        msg="wtimeout:Decimal128('-Infinity') should be accepted",
        id="wtimeout_decimal128_neg_infinity",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"wtimeout": DOUBLE_NEGATIVE_ZERO}},
        expected={"ok": 1.0},
        msg="wtimeout:float -0.0 should be accepted",
        id="wtimeout_float_neg_zero",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"wtimeout": DECIMAL128_NEGATIVE_ZERO}},
        expected={"ok": 1.0},
        msg="wtimeout:Decimal128 -0 should be accepted",
        id="wtimeout_decimal128_neg_zero",
    ),
]

# Property [writeConcern wtimeout Upper Bound]: wtimeout values that
# exceed the max int32 boundary produce a parse error.
WRITE_CONCERN_WTIMEOUT_UPPER_BOUND_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"wtimeout": INT32_OVERFLOW}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="wtimeout above max int32 should produce a parse error",
        id="wtimeout_above_max_int32",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"wtimeout": FLOAT_INFINITY}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="wtimeout:float('inf') should produce a parse error",
        id="wtimeout_float_inf",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"wtimeout": DECIMAL128_INFINITY}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="wtimeout:Decimal128('Infinity') should produce a parse error",
        id="wtimeout_decimal128_inf",
    ),
]

WRITE_CONCERN_WTIMEOUT_TESTS: list[CommandTestCase] = (
    WRITE_CONCERN_WTIMEOUT_ACCEPTED_TESTS
    + WRITE_CONCERN_WTIMEOUT_SPECIAL_VALUES_TESTS
    + WRITE_CONCERN_WTIMEOUT_UPPER_BOUND_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(WRITE_CONCERN_WTIMEOUT_TESTS))
def test_dropDatabase_wc_wtimeout(database_client, collection, register_db_cleanup, test):
    """Test dropDatabase command inputs and error handling."""
    coll = test.prepare(database_client, collection)
    result = execute_command(coll, test.command)
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
