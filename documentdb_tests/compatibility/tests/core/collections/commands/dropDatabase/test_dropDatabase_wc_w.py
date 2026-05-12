from __future__ import annotations

import datetime

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR, FAILED_TO_PARSE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ONE_AND_HALF,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)

# Property [writeConcern w Accepted Values]: the w field accepts
# numeric BSON types and the string "majority" on standalone.
WRITE_CONCERN_W_ACCEPTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": 0}},
        expected={"ok": 1.0},
        msg="w:0 should be accepted",
        id="w_0",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": 1}},
        expected={"ok": 1.0},
        msg="w:1 should be accepted",
        id="w_1",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": "majority"}},
        expected={"ok": 1.0},
        msg='w:"majority" should be accepted',
        id="w_majority",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": Int64(1)}},
        expected={"ok": 1.0},
        msg="w:Int64(1) should be accepted",
        id="w_int64_1",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": 1.0}},
        expected={"ok": 1.0},
        msg="w:double(1.0) should be accepted",
        id="w_double_1_0",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": Decimal128("1")}},
        expected={"ok": 1.0},
        msg="w:Decimal128('1') should be accepted",
        id="w_decimal128_1",
    ),
]

# Property [writeConcern w Tagged Acceptance]: tagged write concerns are
# non-empty documents whose values must all be numeric. Any numeric
# value is accepted regardless of magnitude or special status.
WRITE_CONCERN_W_TAGGED_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": 1}}},
        expected={"ok": 1.0},
        msg="w:tagged object with int32 value should be accepted",
        id="w_tagged_int32",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": Int64(1)}}},
        expected={"ok": 1.0},
        msg="w:tagged object with Int64 value should be accepted",
        id="w_tagged_int64",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": 1.5}}},
        expected={"ok": 1.0},
        msg="w:tagged object with double value should be accepted",
        id="w_tagged_double",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": Decimal128("1")}}},
        expected={"ok": 1.0},
        msg="w:tagged object with Decimal128 value should be accepted",
        id="w_tagged_decimal128",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": 0}}},
        expected={"ok": 1.0},
        msg="w:tagged object with zero should be accepted",
        id="w_tagged_zero",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": -1}}},
        expected={"ok": 1.0},
        msg="w:tagged object with negative value should be accepted",
        id="w_tagged_negative",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": FLOAT_NAN}}},
        expected={"ok": 1.0},
        msg="w:tagged object with NaN should be accepted",
        id="w_tagged_nan",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": FLOAT_INFINITY}}},
        expected={"ok": 1.0},
        msg="w:tagged object with Infinity should be accepted",
        id="w_tagged_infinity",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": FLOAT_NEGATIVE_INFINITY}}},
        expected={"ok": 1.0},
        msg="w:tagged object with -Infinity should be accepted",
        id="w_tagged_neg_infinity",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": DOUBLE_NEGATIVE_ZERO}}},
        expected={"ok": 1.0},
        msg="w:tagged object with -0.0 should be accepted",
        id="w_tagged_neg_zero",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": INT64_MAX}}},
        expected={"ok": 1.0},
        msg="w:tagged object with Int64 max should be accepted",
        id="w_tagged_int64_max",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": INT64_MIN}}},
        expected={"ok": 1.0},
        msg="w:tagged object with Int64 min should be accepted",
        id="w_tagged_int64_min",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": DECIMAL128_NAN}}},
        expected={"ok": 1.0},
        msg="w:tagged object with Decimal128 NaN should be accepted",
        id="w_tagged_decimal128_nan",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": DECIMAL128_INFINITY}}},
        expected={"ok": 1.0},
        msg="w:tagged object with Decimal128 Infinity should be accepted",
        id="w_tagged_decimal128_infinity",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": 1, "b": 2}}},
        expected={"ok": 1.0},
        msg="w:multi-key tagged object should be accepted",
        id="w_tagged_multi_key",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": FLOAT_NEGATIVE_NAN}}},
        expected={"ok": 1.0},
        msg="w:tagged object with negative NaN should be accepted",
        id="w_tagged_neg_nan",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": DECIMAL128_NEGATIVE_NAN}}},
        expected={"ok": 1.0},
        msg="w:tagged object with Decimal128 negative NaN should be accepted",
        id="w_tagged_decimal128_neg_nan",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": DECIMAL128_NEGATIVE_INFINITY}}},
        expected={"ok": 1.0},
        msg="w:tagged object with Decimal128 -Infinity should be accepted",
        id="w_tagged_decimal128_neg_infinity",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": DECIMAL128_NEGATIVE_ZERO}}},
        expected={"ok": 1.0},
        msg="w:tagged object with Decimal128 -0 should be accepted",
        id="w_tagged_decimal128_neg_zero",
    ),
]

# Property [writeConcern w Numeric Coercion]: non-exact numeric w values
# are coerced to an effective integer. Doubles truncate toward zero,
# Decimal128 values use banker's rounding, and trailing-zero
# representations are normalized.
WRITE_CONCERN_W_NUMERIC_COERCION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": -0.99}},
        expected={"ok": 1.0},
        msg="w:-0.99 should truncate to 0 and succeed",
        id="w_double_neg_0_99",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": 0.999}},
        expected={"ok": 1.0},
        msg="w:0.999 should truncate to 0 and succeed",
        id="w_double_0_999",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": 1.9}},
        expected={"ok": 1.0},
        msg="w:1.9 should truncate to 1 and succeed",
        id="w_double_1_9",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": 1.999}},
        expected={"ok": 1.0},
        msg="w:1.999 should truncate to 1 and succeed",
        id="w_double_1_999",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": Decimal128("0.9")}},
        expected={"ok": 1.0},
        msg="w:Decimal128('0.9') rounds and succeeds",
        id="w_decimal128_0_9",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": Decimal128("1.4")}},
        expected={"ok": 1.0},
        msg="w:Decimal128('1.4') rounds to 1 and succeeds",
        id="w_decimal128_1_4",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": Decimal128("1." + "0" * 32)}},
        expected={"ok": 1.0},
        msg="w:Decimal128 with many trailing zeros should be accepted",
        id="w_decimal128_trailing_zeros",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": DOUBLE_NEGATIVE_ZERO}},
        expected={"ok": 1.0},
        msg="w:double -0.0 should coerce to 0 and succeed",
        id="w_double_neg_zero",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": DECIMAL128_NEGATIVE_ZERO}},
        expected={"ok": 1.0},
        msg="w:Decimal128 -0 should coerce to 0 and succeed",
        id="w_decimal128_neg_zero",
    ),
]

# Property [writeConcern w Out of Range]: w values below zero or above
# the maximum tag count produce a parse error.
WRITE_CONCERN_W_OUT_OF_RANGE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": -1}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:-1 should produce a parse error",
        id="w_neg_1",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": 51}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:51 should produce a parse error",
        id="w_51",
    ),
]

# Property [writeConcern w Unsatisfiable on Standalone]: w values
# between the accepted range and the out-of-range boundary, and
# non-majority strings, are syntactically valid but cannot be
# satisfied on a standalone server, producing a bad value error.
WRITE_CONCERN_W_STANDALONE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": 2}},
        error_code=BAD_VALUE_ERROR,
        msg="w:2 should produce a bad value error on standalone",
        id="w_2_standalone",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": 50}},
        error_code=BAD_VALUE_ERROR,
        msg="w:50 should produce a bad value error on standalone",
        id="w_50_standalone",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": "foobar"}},
        error_code=BAD_VALUE_ERROR,
        msg="w:non-majority string should produce a bad value error on standalone",
        id="w_string_non_majority",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": ""}},
        error_code=BAD_VALUE_ERROR,
        msg="w:empty string should produce a bad value error on standalone",
        id="w_string_empty",
    ),
]

# Property [writeConcern w Type Rejection]: non-numeric, non-string,
# non-document BSON types for w produce a parse error.
WRITE_CONCERN_W_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:bool should produce a parse error",
        id="w_bool",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": [1]}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:array should produce a parse error",
        id="w_array",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": ObjectId()}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:ObjectId should produce a parse error",
        id="w_objectid",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": datetime.datetime(2024, 1, 1)}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:datetime should produce a parse error",
        id="w_datetime",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": Timestamp(1, 1)}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:Timestamp should produce a parse error",
        id="w_timestamp",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": Binary(b"x")}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:Binary should produce a parse error",
        id="w_binary",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": Regex("a")}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:Regex should produce a parse error",
        id="w_regex",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": Code("x")}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:Code should produce a parse error",
        id="w_code",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": Code("x", {"a": 1})}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:Code with scope should produce a parse error",
        id="w_code_with_scope",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": MinKey()}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:MinKey should produce a parse error",
        id="w_minkey",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": MaxKey()}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:MaxKey should produce a parse error",
        id="w_maxkey",
    ),
]

# Property [writeConcern w Tagged Rejection]: tagged write concern
# objects must be non-empty with only numeric values; empty objects and
# objects containing non-numeric values produce a parse error.
WRITE_CONCERN_W_TAGGED_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:empty object should produce a parse error",
        id="w_empty_object",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": {"b": 1}}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:object with nested doc should produce a parse error",
        id="w_nested_doc",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": "str"}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:object with string value should produce a parse error",
        id="w_object_string_value",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": True}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:object with bool value should produce a parse error",
        id="w_object_bool_value",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": None}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:object with null value should produce a parse error",
        id="w_object_null_value",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": [1]}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:object with array value should produce a parse error",
        id="w_object_array_value",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": ObjectId()}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:object with ObjectId value should produce a parse error",
        id="w_object_objectid_value",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": datetime.datetime(2024, 1, 1)}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:object with datetime value should produce a parse error",
        id="w_object_datetime_value",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": Timestamp(1, 1)}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:object with Timestamp value should produce a parse error",
        id="w_object_timestamp_value",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": Binary(b"x")}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:object with Binary value should produce a parse error",
        id="w_object_binary_value",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": Regex("a")}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:object with Regex value should produce a parse error",
        id="w_object_regex_value",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": Code("x")}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:object with Code value should produce a parse error",
        id="w_object_code_value",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": Code("x", {"b": 1})}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:object with Code with scope value should produce a parse error",
        id="w_object_code_with_scope_value",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": MinKey()}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:object with MinKey value should produce a parse error",
        id="w_object_minkey_value",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": MaxKey()}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:object with MaxKey value should produce a parse error",
        id="w_object_maxkey_value",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": 1, "b": "str"}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:multi-key object with one invalid string value should produce a parse error",
        id="w_multi_key_invalid_string",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": 1, "b": True}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:multi-key object with one invalid bool value should produce a parse error",
        id="w_multi_key_invalid_bool",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": 1, "b": None}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:multi-key object with one invalid null value should produce a parse error",
        id="w_multi_key_invalid_null",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": 1, "b": [1]}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:multi-key object with one invalid array value should produce a parse error",
        id="w_multi_key_invalid_array",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": 1, "b": {"c": 1}}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:multi-key object with one invalid nested doc should produce a parse error",
        id="w_multi_key_invalid_doc",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": "str", "b": 1}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:multi-key object with invalid value first should produce a parse error",
        id="w_multi_key_invalid_first",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": {"a": "str", "b": True}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:multi-key object with all invalid values should produce a parse error",
        id="w_multi_key_all_invalid",
    ),
]

# Property [writeConcern w Null]: w:null is treated as an empty string,
# producing a bad value error on standalone.
WRITE_CONCERN_W_NULL_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": None}},
        error_code=BAD_VALUE_ERROR,
        msg="w:null should be treated as empty string and produce a bad value error",
        id="w_null",
    ),
]

# Property [writeConcern w Numeric Boundary Errors]: numeric w values
# at type boundaries or special values (NaN, infinities) that cannot
# resolve to a valid write concern produce a parse error.
WRITE_CONCERN_W_NUMERIC_BOUNDARY_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": INT32_MAX}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:int32 max should produce a parse error",
        id="w_int32_max",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": INT32_MIN}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:int32 min should produce a parse error",
        id="w_int32_min",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": INT64_MAX}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:Int64 max should produce a parse error",
        id="w_int64_max",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": INT64_MIN}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:Int64 min should produce a parse error",
        id="w_int64_min",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": FLOAT_NAN}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:NaN should produce a parse error",
        id="w_nan",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": FLOAT_NEGATIVE_NAN}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:negative NaN should produce a parse error",
        id="w_neg_nan",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": FLOAT_INFINITY}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:Infinity should produce a parse error",
        id="w_infinity",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": FLOAT_NEGATIVE_INFINITY}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:-Infinity should produce a parse error",
        id="w_neg_infinity",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": DECIMAL128_NEGATIVE_INFINITY}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:Decimal128('-Infinity') should produce a parse error",
        id="w_decimal128_neg_infinity",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": Decimal128("-0.51")}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:Decimal128('-0.51') rounds to -1 and should produce a parse error",
        id="w_decimal128_neg_0_51",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": DECIMAL128_NAN}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:Decimal128 NaN should produce a parse error",
        id="w_decimal128_nan",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": DECIMAL128_NEGATIVE_NAN}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:Decimal128 negative NaN should produce a parse error",
        id="w_decimal128_neg_nan",
    ),
]

# Property [writeConcern w Coercion Boundary Errors]: Decimal128
# banker's rounding can push a value across rejection boundaries.
# Rounding from accepted into standalone rejection, or from standalone
# rejection into out-of-range.
WRITE_CONCERN_W_COERCION_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": DECIMAL128_ONE_AND_HALF}},
        error_code=BAD_VALUE_ERROR,
        msg="w:Decimal128('1.5') rounds up, crossing into standalone rejection",
        id="w_decimal128_1_5",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"w": Decimal128("51.4")}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:Decimal128('51.4') rounds to 51, crossing into parse error range",
        id="w_decimal128_51_4",
    ),
]

WRITE_CONCERN_W_TESTS: list[CommandTestCase] = (
    WRITE_CONCERN_W_ACCEPTED_TESTS
    + WRITE_CONCERN_W_TAGGED_ACCEPTANCE_TESTS
    + WRITE_CONCERN_W_NUMERIC_COERCION_TESTS
    + WRITE_CONCERN_W_OUT_OF_RANGE_TESTS
    + WRITE_CONCERN_W_STANDALONE_ERROR_TESTS
    + WRITE_CONCERN_W_TYPE_ERROR_TESTS
    + WRITE_CONCERN_W_TAGGED_REJECTION_TESTS
    + WRITE_CONCERN_W_NULL_ERROR_TESTS
    + WRITE_CONCERN_W_NUMERIC_BOUNDARY_ERROR_TESTS
    + WRITE_CONCERN_W_COERCION_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(WRITE_CONCERN_W_TESTS))
def test_dropDatabase_wc_w(database_client, collection, register_db_cleanup, test):
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
