from __future__ import annotations

import datetime

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    DROP_DATABASE_VALUE_ERROR,
    MISSING_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_HALF,
    DECIMAL128_INT64_OVERFLOW,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MAX,
    DECIMAL128_NEGATIVE_HALF,
    DECIMAL128_NEGATIVE_ONE_AND_HALF,
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_SMALL_EXPONENT,
    DECIMAL128_TWO_AND_HALF,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
    INT64_ZERO,
)

# Property [Null Optional Fields]: when writeConcern or comment is null or
# omitted, the command succeeds with default behavior.
NULL_OPTIONAL_FIELDS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": None},
        expected={"ok": 1.0},
        msg="Null writeConcern should succeed with default write concern",
        id="null_write_concern",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "comment": None},
        expected={"ok": 1.0},
        msg="Null comment should succeed",
        id="null_comment",
    ),
    CommandTestCase(
        command={"dropDatabase": 1},
        expected={"ok": 1.0},
        msg="Omitted writeConcern and comment should succeed",
        id="omitted_optional_fields",
    ),
]

# Property [Accepted Numeric Types]: each numeric BSON type is accepted
# for the dropDatabase field when its exact value is 1.
ACCEPTED_NUMERIC_TYPES_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"dropDatabase": 1},
        expected={"ok": 1.0},
        msg="int32(1) should be accepted",
        id="int32_1",
    ),
    CommandTestCase(
        command={"dropDatabase": Int64(1)},
        expected={"ok": 1.0},
        msg="Int64(1) should be accepted",
        id="int64_1",
    ),
    CommandTestCase(
        command={"dropDatabase": 1.0},
        expected={"ok": 1.0},
        msg="double(1.0) should be accepted",
        id="double_1_0",
    ),
    CommandTestCase(
        command={"dropDatabase": Decimal128("1")},
        expected={"ok": 1.0},
        msg="Decimal128('1') should be accepted",
        id="decimal128_1",
    ),
]

# Property [dropDatabase Numeric Coercion]: non-exact numeric values that
# resolve to 1 after type-specific coercion are accepted. Doubles
# truncate toward zero, Decimal128 values use banker's rounding, and
# trailing-zero representations are normalized.
DROP_DATABASE_NUMERIC_COERCION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"dropDatabase": 1.999},
        expected={"ok": 1.0},
        msg="double(1.999) should be accepted (truncates to 1)",
        id="double_1_999",
    ),
    CommandTestCase(
        command={"dropDatabase": 1.9},
        expected={"ok": 1.0},
        msg="double(1.9) should be accepted (truncates toward zero)",
        id="double_1_9",
    ),
    CommandTestCase(
        command={"dropDatabase": Decimal128("0.9")},
        expected={"ok": 1.0},
        msg="Decimal128('0.9') should be accepted (banker's rounding)",
        id="decimal128_0_9",
    ),
    CommandTestCase(
        command={"dropDatabase": Decimal128("1.4")},
        expected={"ok": 1.0},
        msg="Decimal128('1.4') should be accepted (rounds to 1)",
        id="decimal128_1_4",
    ),
    CommandTestCase(
        command={"dropDatabase": Decimal128("1." + "0" * 32)},
        expected={"ok": 1.0},
        msg="Decimal128 with many trailing zeros should be accepted",
        id="decimal128_trailing_zeros",
    ),
]

# Property [Null dropDatabase Field]: when the dropDatabase field is null,
# the server treats it as missing and returns a missing-field error.
NULL_DROP_DATABASE_FIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"dropDatabase": None},
        error_code=MISSING_FIELD_ERROR,
        msg="Null dropDatabase field should produce missing-field error",
        id="null_drop_database",
    ),
]

# Property [dropDatabase Type Rejection]: non-numeric BSON types
# produce a type mismatch error for the dropDatabase field.
DROP_DATABASE_TYPE_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"dropDatabase": True},
        error_code=TYPE_MISMATCH_ERROR,
        msg="bool should produce type mismatch error",
        id="dd_type_bool",
    ),
    CommandTestCase(
        command={"dropDatabase": "1"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="string should produce type mismatch error",
        id="dd_type_string",
    ),
    CommandTestCase(
        command={"dropDatabase": [1]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="array should produce type mismatch error",
        id="dd_type_array",
    ),
    CommandTestCase(
        command={"dropDatabase": {"a": 1}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="object should produce type mismatch error",
        id="dd_type_object",
    ),
    CommandTestCase(
        command={"dropDatabase": ObjectId()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="ObjectId should produce type mismatch error",
        id="dd_type_objectid",
    ),
    CommandTestCase(
        command={"dropDatabase": datetime.datetime(2024, 1, 1)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="datetime should produce type mismatch error",
        id="dd_type_datetime",
    ),
    CommandTestCase(
        command={"dropDatabase": Timestamp(1, 1)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Timestamp should produce type mismatch error",
        id="dd_type_timestamp",
    ),
    CommandTestCase(
        command={"dropDatabase": Binary(b"data")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Binary should produce type mismatch error",
        id="dd_type_binary",
    ),
    CommandTestCase(
        command={"dropDatabase": Regex("pattern")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Regex should produce type mismatch error",
        id="dd_type_regex",
    ),
    CommandTestCase(
        command={"dropDatabase": Code("function() {}")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Code should produce type mismatch error",
        id="dd_type_code",
    ),
    CommandTestCase(
        command={"dropDatabase": Code("function() {}", {"x": 1})},
        error_code=TYPE_MISMATCH_ERROR,
        msg="CodeWithScope should produce type mismatch error",
        id="dd_type_code_with_scope",
    ),
    CommandTestCase(
        command={"dropDatabase": MinKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="MinKey should produce type mismatch error",
        id="dd_type_minkey",
    ),
    CommandTestCase(
        command={"dropDatabase": MaxKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="MaxKey should produce type mismatch error",
        id="dd_type_maxkey",
    ),
]

# Property [dropDatabase Value Rejection]: numeric values that do not
# coerce to 1 after type-specific rounding or truncation produce a
# value rejection error.
DROP_DATABASE_VALUE_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"dropDatabase": 0},
        error_code=DROP_DATABASE_VALUE_ERROR,
        msg="int32(0) should produce value error",
        id="dd_val_int32_0",
    ),
    CommandTestCase(
        command={"dropDatabase": -1},
        error_code=DROP_DATABASE_VALUE_ERROR,
        msg="int32(-1) should produce value error",
        id="dd_val_int32_neg1",
    ),
    CommandTestCase(
        command={"dropDatabase": 2},
        error_code=DROP_DATABASE_VALUE_ERROR,
        msg="int32 value other than exact one should produce value error",
        id="dd_val_int32_2",
    ),
    CommandTestCase(
        command={"dropDatabase": 42},
        error_code=DROP_DATABASE_VALUE_ERROR,
        msg="int32(42) should produce value error",
        id="dd_val_int32_42",
    ),
    CommandTestCase(
        command={"dropDatabase": INT32_MAX},
        error_code=DROP_DATABASE_VALUE_ERROR,
        msg="int32 max should produce value error",
        id="dd_val_int32_max",
    ),
    CommandTestCase(
        command={"dropDatabase": INT32_MIN},
        error_code=DROP_DATABASE_VALUE_ERROR,
        msg="int32 min should produce value error",
        id="dd_val_int32_min",
    ),
    CommandTestCase(
        command={"dropDatabase": INT64_ZERO},
        error_code=DROP_DATABASE_VALUE_ERROR,
        msg="Int64(0) should produce value error",
        id="dd_val_int64_0",
    ),
    CommandTestCase(
        command={"dropDatabase": Int64(2)},
        error_code=DROP_DATABASE_VALUE_ERROR,
        msg="Int64 value other than exact one should produce value error",
        id="dd_val_int64_2",
    ),
    CommandTestCase(
        command={"dropDatabase": INT64_MAX},
        error_code=DROP_DATABASE_VALUE_ERROR,
        msg="Int64 max should produce value error",
        id="dd_val_int64_max",
    ),
    CommandTestCase(
        command={"dropDatabase": INT64_MIN},
        error_code=DROP_DATABASE_VALUE_ERROR,
        msg="Int64 min should produce value error",
        id="dd_val_int64_min",
    ),
    CommandTestCase(
        command={"dropDatabase": 2.0},
        error_code=DROP_DATABASE_VALUE_ERROR,
        msg="double value outside truncation range should produce value error",
        id="dd_val_double_2_0",
    ),
    CommandTestCase(
        command={"dropDatabase": FLOAT_NAN},
        error_code=DROP_DATABASE_VALUE_ERROR,
        msg="double(NaN) should produce value error",
        id="dd_val_double_nan",
    ),
    CommandTestCase(
        command={"dropDatabase": FLOAT_NEGATIVE_NAN},
        error_code=DROP_DATABASE_VALUE_ERROR,
        msg="double(negative NaN) should produce value error",
        id="dd_val_double_neg_nan",
    ),
    CommandTestCase(
        command={"dropDatabase": FLOAT_INFINITY},
        error_code=DROP_DATABASE_VALUE_ERROR,
        msg="double(Infinity) should produce value error",
        id="dd_val_double_infinity",
    ),
    CommandTestCase(
        command={"dropDatabase": FLOAT_NEGATIVE_INFINITY},
        error_code=DROP_DATABASE_VALUE_ERROR,
        msg="double(-Infinity) should produce value error",
        id="dd_val_double_neg_infinity",
    ),
    CommandTestCase(
        command={"dropDatabase": DOUBLE_NEGATIVE_ZERO},
        error_code=DROP_DATABASE_VALUE_ERROR,
        msg="double(-0.0) should produce value error",
        id="dd_val_double_neg_zero",
    ),
    CommandTestCase(
        command={"dropDatabase": DECIMAL128_TWO_AND_HALF},
        error_code=DROP_DATABASE_VALUE_ERROR,
        msg="Decimal128 rounding outside accepted range should produce value error",
        id="dd_val_decimal128_2_5",
    ),
    CommandTestCase(
        command={"dropDatabase": DECIMAL128_NEGATIVE_HALF},
        error_code=DROP_DATABASE_VALUE_ERROR,
        msg="Decimal128('-0.5') rounds to 0 and should produce value error",
        id="dd_val_decimal128_neg_0_5",
    ),
    CommandTestCase(
        command={"dropDatabase": DECIMAL128_NEGATIVE_ONE_AND_HALF},
        error_code=DROP_DATABASE_VALUE_ERROR,
        msg="Decimal128('-1.5') rounds to -2 and should produce value error",
        id="dd_val_decimal128_neg_1_5",
    ),
    CommandTestCase(
        command={"dropDatabase": DECIMAL128_MAX},
        error_code=DROP_DATABASE_VALUE_ERROR,
        msg="Decimal128 34-digit max should produce value error",
        id="dd_val_decimal128_max",
    ),
    CommandTestCase(
        command={"dropDatabase": DECIMAL128_SMALL_EXPONENT},
        error_code=DROP_DATABASE_VALUE_ERROR,
        msg="Decimal128('1E-6143') should produce value error",
        id="dd_val_decimal128_tiny",
    ),
    CommandTestCase(
        command={"dropDatabase": DECIMAL128_LARGE_EXPONENT},
        error_code=DROP_DATABASE_VALUE_ERROR,
        msg="Decimal128('1E+6144') should produce value error",
        id="dd_val_decimal128_huge",
    ),
    CommandTestCase(
        command={"dropDatabase": DECIMAL128_INT64_OVERFLOW},
        error_code=DROP_DATABASE_VALUE_ERROR,
        msg="Decimal128 int64 overflow value should produce value error",
        id="dd_val_decimal128_int64_overflow",
    ),
    CommandTestCase(
        command={"dropDatabase": 0.9},
        error_code=DROP_DATABASE_VALUE_ERROR,
        msg="double truncating to zero should produce value error",
        id="dd_val_double_0_9",
    ),
    CommandTestCase(
        command={"dropDatabase": 0.999},
        error_code=DROP_DATABASE_VALUE_ERROR,
        msg="double(0.999) truncates to 0 and should produce value error",
        id="dd_val_double_0_999",
    ),
    CommandTestCase(
        command={"dropDatabase": -0.99},
        error_code=DROP_DATABASE_VALUE_ERROR,
        msg="double(-0.99) truncates to 0 and should produce value error",
        id="dd_val_double_neg_0_99",
    ),
    CommandTestCase(
        command={"dropDatabase": DECIMAL128_HALF},
        error_code=DROP_DATABASE_VALUE_ERROR,
        msg="Decimal128('0.5') rounds to 0 via banker's rounding and should produce value error",
        id="dd_val_decimal128_0_5",
    ),
    CommandTestCase(
        command={"dropDatabase": DECIMAL128_ONE_AND_HALF},
        error_code=DROP_DATABASE_VALUE_ERROR,
        msg="Decimal128('1.5') rounds to 2 via banker's rounding and should produce value error",
        id="dd_val_decimal128_1_5",
    ),
    CommandTestCase(
        command={"dropDatabase": 0.5},
        error_code=DROP_DATABASE_VALUE_ERROR,
        msg="double(0.5) truncates to 0 and should produce value error",
        id="dd_val_double_0_5",
    ),
]

DROP_DATABASE_FIELD_TESTS: list[CommandTestCase] = (
    NULL_OPTIONAL_FIELDS_TESTS
    + ACCEPTED_NUMERIC_TYPES_TESTS
    + DROP_DATABASE_NUMERIC_COERCION_TESTS
    + NULL_DROP_DATABASE_FIELD_TESTS
    + DROP_DATABASE_TYPE_REJECTION_TESTS
    + DROP_DATABASE_VALUE_REJECTION_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(DROP_DATABASE_FIELD_TESTS))
def test_dropDatabase_field(database_client, collection, register_db_cleanup, test):
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
