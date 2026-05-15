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

# Property [writeConcern j Accepted Types]: the j field accepts any
# numeric BSON type and booleans; null is treated as omitted.
WRITE_CONCERN_J_ACCEPTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"j": True}},
        expected={"ok": 1.0},
        msg="j:true should be accepted",
        id="j_bool_true",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"j": False}},
        expected={"ok": 1.0},
        msg="j:false should be accepted",
        id="j_bool_false",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"j": 3.14}},
        expected={"ok": 1.0},
        msg="j:double should be accepted with any value",
        id="j_double",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"j": Int64(42)}},
        expected={"ok": 1.0},
        msg="j:Int64 should be accepted with any value",
        id="j_int64",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"j": Decimal128("99")}},
        expected={"ok": 1.0},
        msg="j:Decimal128 should be accepted with any value",
        id="j_decimal128",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"j": 7}},
        expected={"ok": 1.0},
        msg="j:int32 should be accepted with any value",
        id="j_int32",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"j": None}},
        expected={"ok": 1.0},
        msg="j:null should be treated as omitted and succeed",
        id="j_null",
    ),
]

# Property [writeConcern j Special Values]: the j field accepts special
# numeric values in both float and Decimal128 forms.
WRITE_CONCERN_J_SPECIAL_VALUES_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"j": FLOAT_NAN}},
        expected={"ok": 1.0},
        msg="j:NaN float should be accepted",
        id="j_float_nan",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"j": FLOAT_NEGATIVE_NAN}},
        expected={"ok": 1.0},
        msg="j:negative NaN float should be accepted",
        id="j_float_neg_nan",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"j": FLOAT_INFINITY}},
        expected={"ok": 1.0},
        msg="j:Infinity float should be accepted",
        id="j_float_infinity",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"j": FLOAT_NEGATIVE_INFINITY}},
        expected={"ok": 1.0},
        msg="j:-Infinity float should be accepted",
        id="j_float_neg_infinity",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"j": DOUBLE_NEGATIVE_ZERO}},
        expected={"ok": 1.0},
        msg="j:negative zero float should be accepted",
        id="j_float_neg_zero",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"j": DECIMAL128_NAN}},
        expected={"ok": 1.0},
        msg="j:Decimal128 NaN should be accepted",
        id="j_decimal128_nan",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"j": DECIMAL128_NEGATIVE_NAN}},
        expected={"ok": 1.0},
        msg="j:Decimal128 negative NaN should be accepted",
        id="j_decimal128_neg_nan",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"j": DECIMAL128_INFINITY}},
        expected={"ok": 1.0},
        msg="j:Decimal128 Infinity should be accepted",
        id="j_decimal128_infinity",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"j": DECIMAL128_NEGATIVE_INFINITY}},
        expected={"ok": 1.0},
        msg="j:Decimal128 -Infinity should be accepted",
        id="j_decimal128_neg_infinity",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"j": DECIMAL128_NEGATIVE_ZERO}},
        expected={"ok": 1.0},
        msg="j:Decimal128 negative zero should be accepted",
        id="j_decimal128_neg_zero",
    ),
]

# Property [writeConcern j Type Rejection]: all non-numeric, non-boolean
# BSON types produce a type mismatch error for the j field.
WRITE_CONCERN_J_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"j": "true"}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="j:string should produce type mismatch error",
        id="j_string",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"j": [1]}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="j:array should produce type mismatch error",
        id="j_array",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"j": {"a": 1}}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="j:object should produce type mismatch error",
        id="j_object",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"j": ObjectId()}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="j:ObjectId should produce type mismatch error",
        id="j_objectid",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"j": datetime.datetime(2024, 1, 1)}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="j:datetime should produce type mismatch error",
        id="j_datetime",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"j": Timestamp(1, 1)}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="j:Timestamp should produce type mismatch error",
        id="j_timestamp",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"j": Binary(b"x")}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="j:Binary should produce type mismatch error",
        id="j_binary",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"j": Regex("a")}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="j:Regex should produce type mismatch error",
        id="j_regex",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"j": Code("x")}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="j:Code should produce type mismatch error",
        id="j_code",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"j": Code("x", {"a": 1})}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="j:Code with scope should produce type mismatch error",
        id="j_code_with_scope",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"j": MinKey()}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="j:MinKey should produce type mismatch error",
        id="j_minkey",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"j": MaxKey()}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="j:MaxKey should produce type mismatch error",
        id="j_maxkey",
    ),
]

WRITE_CONCERN_J_TESTS: list[CommandTestCase] = (
    WRITE_CONCERN_J_ACCEPTED_TESTS
    + WRITE_CONCERN_J_SPECIAL_VALUES_TESTS
    + WRITE_CONCERN_J_TYPE_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(WRITE_CONCERN_J_TESTS))
def test_dropDatabase_wc_j(database_client, collection, register_db_cleanup, test):
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
