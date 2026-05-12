from __future__ import annotations

import datetime

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
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
)

# Property [writeConcern fsync Accepted Types]: the fsync field accepts
# any numeric BSON type and booleans; null is treated as omitted.
WRITE_CONCERN_FSYNC_ACCEPTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"fsync": True}},
        expected={"ok": 1.0},
        msg="fsync:true should be accepted",
        id="fsync_bool_true",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"fsync": False}},
        expected={"ok": 1.0},
        msg="fsync:false should be accepted",
        id="fsync_bool_false",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"fsync": 2.5}},
        expected={"ok": 1.0},
        msg="fsync:double should be accepted with any value",
        id="fsync_double",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"fsync": Int64(17)}},
        expected={"ok": 1.0},
        msg="fsync:Int64 should be accepted with any value",
        id="fsync_int64",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"fsync": Decimal128("55")}},
        expected={"ok": 1.0},
        msg="fsync:Decimal128 should be accepted with any value",
        id="fsync_decimal128",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"fsync": 3}},
        expected={"ok": 1.0},
        msg="fsync:int32 should be accepted with any value",
        id="fsync_int32",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"fsync": None}},
        expected={"ok": 1.0},
        msg="fsync:null should be treated as omitted and succeed",
        id="fsync_null",
    ),
]

# Property [writeConcern fsync Special Values]: the fsync field accepts
# special numeric values in both float and Decimal128 forms.
WRITE_CONCERN_FSYNC_SPECIAL_VALUES_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"fsync": FLOAT_NAN}},
        expected={"ok": 1.0},
        msg="fsync:NaN float should be accepted",
        id="fsync_float_nan",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"fsync": FLOAT_NEGATIVE_NAN}},
        expected={"ok": 1.0},
        msg="fsync:negative NaN float should be accepted",
        id="fsync_float_neg_nan",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"fsync": FLOAT_INFINITY}},
        expected={"ok": 1.0},
        msg="fsync:Infinity float should be accepted",
        id="fsync_float_infinity",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"fsync": FLOAT_NEGATIVE_INFINITY}},
        expected={"ok": 1.0},
        msg="fsync:-Infinity float should be accepted",
        id="fsync_float_neg_infinity",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"fsync": DOUBLE_NEGATIVE_ZERO}},
        expected={"ok": 1.0},
        msg="fsync:negative zero float should be accepted",
        id="fsync_float_neg_zero",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"fsync": DECIMAL128_NAN}},
        expected={"ok": 1.0},
        msg="fsync:Decimal128 NaN should be accepted",
        id="fsync_decimal128_nan",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"fsync": DECIMAL128_NEGATIVE_NAN}},
        expected={"ok": 1.0},
        msg="fsync:Decimal128 negative NaN should be accepted",
        id="fsync_decimal128_neg_nan",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"fsync": DECIMAL128_INFINITY}},
        expected={"ok": 1.0},
        msg="fsync:Decimal128 Infinity should be accepted",
        id="fsync_decimal128_infinity",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"fsync": DECIMAL128_NEGATIVE_INFINITY}},
        expected={"ok": 1.0},
        msg="fsync:Decimal128 -Infinity should be accepted",
        id="fsync_decimal128_neg_infinity",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"fsync": DECIMAL128_NEGATIVE_ZERO}},
        expected={"ok": 1.0},
        msg="fsync:Decimal128 negative zero should be accepted",
        id="fsync_decimal128_neg_zero",
    ),
]

# Property [writeConcern fsync Type Rejection]: all non-numeric,
# non-boolean BSON types produce a type mismatch error for the fsync
# field.
WRITE_CONCERN_FSYNC_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"fsync": "true"}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="fsync:string should produce type mismatch error",
        id="fsync_string",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"fsync": [1]}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="fsync:array should produce type mismatch error",
        id="fsync_array",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"fsync": {"a": 1}}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="fsync:object should produce type mismatch error",
        id="fsync_object",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"fsync": ObjectId()}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="fsync:ObjectId should produce type mismatch error",
        id="fsync_objectid",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"fsync": datetime.datetime(2024, 1, 1)}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="fsync:datetime should produce type mismatch error",
        id="fsync_datetime",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"fsync": Timestamp(1, 1)}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="fsync:Timestamp should produce type mismatch error",
        id="fsync_timestamp",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"fsync": Binary(b"x")}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="fsync:Binary should produce type mismatch error",
        id="fsync_binary",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"fsync": Regex("a")}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="fsync:Regex should produce type mismatch error",
        id="fsync_regex",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"fsync": Code("x")}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="fsync:Code should produce type mismatch error",
        id="fsync_code",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"fsync": Code("x", {"a": 1})}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="fsync:Code with scope should produce type mismatch error",
        id="fsync_code_with_scope",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"fsync": MinKey()}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="fsync:MinKey should produce type mismatch error",
        id="fsync_minkey",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"fsync": MaxKey()}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="fsync:MaxKey should produce type mismatch error",
        id="fsync_maxkey",
    ),
]

WRITE_CONCERN_FSYNC_TESTS: list[CommandTestCase] = (
    WRITE_CONCERN_FSYNC_ACCEPTED_TESTS
    + WRITE_CONCERN_FSYNC_SPECIAL_VALUES_TESTS
    + WRITE_CONCERN_FSYNC_TYPE_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(WRITE_CONCERN_FSYNC_TESTS))
def test_dropDatabase_wc_fsync(database_client, collection, register_db_cleanup, test):
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
