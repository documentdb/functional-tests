"""
Common tests shared across all four bitwise query operators:
$bitsAllClear, $bitsAllSet, $bitsAnyClear, $bitsAnySet.

Covers behavior that is identical regardless of operator:
- Invalid bitmask arguments (error cases)
- Invalid position list entries (error cases)
- Error precedence behavior
- Silent skip of non-numeric field types
- Silent skip of non-representable numeric values
- Missing field handling
- Non-existent field no match
"""

from dataclasses import replace
from datetime import datetime, timezone

import pytest
from bson import Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR, FAILED_TO_PARSE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_MAX,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

BITWISE_OPERATORS = ["$bitsAllClear", "$bitsAllSet", "$bitsAnyClear", "$bitsAnySet"]


def _build_cases(op: str, templates: list[QueryTestCase]) -> list[QueryTestCase]:
    """Expand templates into operator-specific test cases."""
    op_name = op.lstrip("$")
    return [
        replace(
            t,
            id=f"{op_name}_{t.id}",
            filter={"a": {op: t.filter}},
            msg=f"[{op}] {t.msg}",
        )
        for t in templates
    ]


_NUMERIC_BITMASK_ERROR_TEMPLATES = [
    QueryTestCase(
        id="error_negative_int_bitmask",
        filter=-1,
        doc=[{"_id": 1, "a": 0}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Negative integer bitmask returns error",
    ),
    QueryTestCase(
        id="error_negative_long_bitmask",
        filter=Int64(-1),
        doc=[{"_id": 1, "a": 0}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Negative Int64 bitmask returns error",
    ),
    QueryTestCase(
        id="error_negative_double_bitmask",
        filter=-1.0,
        doc=[{"_id": 1, "a": 0}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Negative double bitmask returns error",
    ),
    QueryTestCase(
        id="error_fractional_double_bitmask",
        filter=1.5,
        doc=[{"_id": 1, "a": 0}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Fractional double bitmask returns error",
    ),
    QueryTestCase(
        id="error_fractional_decimal128_bitmask",
        filter=Decimal128("1.5"),
        doc=[{"_id": 1, "a": 0}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Fractional Decimal128 bitmask returns error",
    ),
    QueryTestCase(
        id="error_decimal128_exceeding_int64_bitmask",
        filter=Decimal128("9223372036854775808"),
        doc=[{"_id": 1, "a": 0}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Decimal128 exceeding int64 range as bitmask returns error",
    ),
    QueryTestCase(
        id="error_decimal128_nan_bitmask",
        filter=DECIMAL128_NAN,
        doc=[{"_id": 1, "a": 0}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Decimal128 NaN as bitmask returns error",
    ),
    QueryTestCase(
        id="error_decimal128_infinity_bitmask",
        filter=DECIMAL128_INFINITY,
        doc=[{"_id": 1, "a": 0}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Decimal128 Infinity as bitmask returns error",
    ),
    QueryTestCase(
        id="error_decimal128_neg_infinity_bitmask",
        filter=DECIMAL128_NEGATIVE_INFINITY,
        doc=[{"_id": 1, "a": 0}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Decimal128 -Infinity as bitmask returns error",
    ),
    QueryTestCase(
        id="error_negative_decimal128_bitmask",
        filter=Decimal128("-1"),
        doc=[{"_id": 1, "a": 0}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Negative Decimal128 as bitmask returns error",
    ),
    QueryTestCase(
        id="error_float_nan_bitmask",
        filter=FLOAT_NAN,
        doc=[{"_id": 1, "a": 0}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Float NaN as bitmask returns error",
    ),
    QueryTestCase(
        id="error_float_infinity_bitmask",
        filter=FLOAT_INFINITY,
        doc=[{"_id": 1, "a": 0}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Float Infinity as bitmask returns error",
    ),
    QueryTestCase(
        id="error_float_neg_inf_bitmask",
        filter=FLOAT_NEGATIVE_INFINITY,
        doc=[{"_id": 1, "a": 0}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Float -Infinity as bitmask returns error",
    ),
    QueryTestCase(
        id="error_double_exceeding_int64_bitmask",
        filter=9.3e18,
        doc=[{"_id": 1, "a": 0}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Double exceeding int64 range as bitmask returns error",
    ),
    QueryTestCase(
        id="error_string_bitmask",
        filter="35_STRING",
        doc=[{"_id": 1, "a": 0}],
        error_code=BAD_VALUE_ERROR,
        msg="String bitmask returns error",
    ),
    QueryTestCase(
        id="error_bool_bitmask",
        filter=True,
        doc=[{"_id": 1, "a": 0}],
        error_code=BAD_VALUE_ERROR,
        msg="Boolean as bitmask returns error",
    ),
    QueryTestCase(
        id="error_null_bitmask",
        filter=None,
        doc=[{"_id": 1, "a": 0}],
        error_code=BAD_VALUE_ERROR,
        msg="Null as bitmask returns error",
    ),
    QueryTestCase(
        id="error_object_bitmask",
        filter={"a": 1},
        doc=[{"_id": 1, "a": 0}],
        error_code=BAD_VALUE_ERROR,
        msg="Object bitmask returns error",
    ),
    QueryTestCase(
        id="error_nested_array_bitmask",
        filter=[[1, 2]],
        doc=[{"_id": 1, "a": 0}],
        error_code=BAD_VALUE_ERROR,
        msg="Nested array bitmask returns error",
    ),
]

_POSITION_LIST_ERROR_TEMPLATES = [
    QueryTestCase(
        id="error_negative_position",
        filter=[-1],
        doc=[{"_id": 1, "a": 0}],
        error_code=BAD_VALUE_ERROR,
        msg="Negative position value returns error",
    ),
    QueryTestCase(
        id="error_negative_long_position",
        filter=[Int64(-1)],
        doc=[{"_id": 1, "a": 0}],
        error_code=BAD_VALUE_ERROR,
        msg="Negative Int64 position returns error",
    ),
    QueryTestCase(
        id="error_fractional_decimal128_position",
        filter=[Decimal128("1.5")],
        doc=[{"_id": 1, "a": 0}],
        error_code=BAD_VALUE_ERROR,
        msg="Fractional Decimal128 position returns error",
    ),
    QueryTestCase(
        id="error_decimal128_exceeding_int32_position",
        filter=[Decimal128("2147483648")],
        doc=[{"_id": 1, "a": 0}],
        error_code=BAD_VALUE_ERROR,
        msg="Decimal128 exceeding int32 range as position returns error",
    ),
    QueryTestCase(
        id="error_negative_decimal128_position",
        filter=[Decimal128("-1")],
        doc=[{"_id": 1, "a": 0}],
        error_code=BAD_VALUE_ERROR,
        msg="Negative Decimal128 as position returns error",
    ),
    QueryTestCase(
        id="error_string_in_position_list",
        filter=["hello"],
        doc=[{"_id": 1, "a": 0}],
        error_code=BAD_VALUE_ERROR,
        msg="String in position list returns error",
    ),
    QueryTestCase(
        id="error_fractional_double_position",
        filter=[1.5],
        doc=[{"_id": 1, "a": 0}],
        error_code=BAD_VALUE_ERROR,
        msg="Fractional double position returns error",
    ),
    QueryTestCase(
        id="error_null_in_position_list",
        filter=[None],
        doc=[{"_id": 1, "a": 0}],
        error_code=BAD_VALUE_ERROR,
        msg="Null in position list returns error",
    ),
    QueryTestCase(
        id="error_bool_in_position_list",
        filter=[True],
        doc=[{"_id": 1, "a": 0}],
        error_code=BAD_VALUE_ERROR,
        msg="Boolean in position list returns error",
    ),
    QueryTestCase(
        id="error_nested_array_in_position_list",
        filter=[[1, 2]],
        doc=[{"_id": 1, "a": 0}],
        error_code=BAD_VALUE_ERROR,
        msg="Nested array in position list returns error",
    ),
    QueryTestCase(
        id="error_nan_in_position_list",
        filter=[FLOAT_NAN],
        doc=[{"_id": 1, "a": 0}],
        error_code=BAD_VALUE_ERROR,
        msg="NaN in position list returns error",
    ),
    QueryTestCase(
        id="error_inf_in_position_list",
        filter=[FLOAT_INFINITY],
        doc=[{"_id": 1, "a": 0}],
        error_code=BAD_VALUE_ERROR,
        msg="Infinity in position list returns error",
    ),
    QueryTestCase(
        id="error_object_in_position_list",
        filter=[{"a": 1}],
        doc=[{"_id": 1, "a": 0}],
        error_code=BAD_VALUE_ERROR,
        msg="Object in position list returns error",
    ),
    QueryTestCase(
        id="error_decimal128_nan_in_position_list",
        filter=[DECIMAL128_NAN],
        doc=[{"_id": 1, "a": 0}],
        error_code=BAD_VALUE_ERROR,
        msg="Decimal128 NaN in position list returns error",
    ),
    QueryTestCase(
        id="error_decimal128_infinity_in_position_list",
        filter=[DECIMAL128_INFINITY],
        doc=[{"_id": 1, "a": 0}],
        error_code=BAD_VALUE_ERROR,
        msg="Decimal128 Infinity in position list returns error",
    ),
]

_ERROR_PRECEDENCE_TEMPLATES = [
    QueryTestCase(
        id="error_precedence_multiple_invalid_positions",
        filter=[-1, "hello"],
        doc=[{"_id": 1, "a": 0}],
        error_code=BAD_VALUE_ERROR,
        msg="Multiple invalid entries in position list reports first error",
    ),
    QueryTestCase(
        id="error_precedence_valid_then_invalid_position",
        filter=[0, -1],
        doc=[{"_id": 1, "a": 0}],
        error_code=BAD_VALUE_ERROR,
        msg="Valid position followed by invalid still returns error",
    ),
]

_INVALID_FIELD_TYPE_TEMPLATES = [
    QueryTestCase(
        id="string_field_skipped",
        filter=1,
        doc=[{"_id": 1, "a": "hello"}],
        expected=[],
        msg="String field silently skipped",
    ),
    QueryTestCase(
        id="bool_false_skipped",
        filter=1,
        doc=[{"_id": 1, "a": False}],
        expected=[],
        msg="Boolean false not treated as integer 0",
    ),
    QueryTestCase(
        id="bool_true_skipped",
        filter=1,
        doc=[{"_id": 1, "a": True}],
        expected=[],
        msg="Boolean true not treated as integer 1",
    ),
    QueryTestCase(
        id="null_field_skipped",
        filter=1,
        doc=[{"_id": 1, "a": None}],
        expected=[],
        msg="Null field silently skipped",
    ),
    QueryTestCase(
        id="object_field_skipped",
        filter=1,
        doc=[{"_id": 1, "a": {"x": 1}}],
        expected=[],
        msg="Object field silently skipped",
    ),
    QueryTestCase(
        id="objectid_field_skipped",
        filter=1,
        doc=[{"_id": 1, "a": ObjectId()}],
        expected=[],
        msg="ObjectId field silently skipped",
    ),
    QueryTestCase(
        id="regex_field_skipped",
        filter=1,
        doc=[{"_id": 1, "a": Regex("pattern")}],
        expected=[],
        msg="Regex field silently skipped",
    ),
    QueryTestCase(
        id="timestamp_field_skipped",
        filter=1,
        doc=[{"_id": 1, "a": Timestamp(1, 1)}],
        expected=[],
        msg="Timestamp field silently skipped",
    ),
    QueryTestCase(
        id="date_field_skipped",
        filter=1,
        doc=[{"_id": 1, "a": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        expected=[],
        msg="Date field silently skipped",
    ),
    QueryTestCase(
        id="minkey_field_skipped",
        filter=1,
        doc=[{"_id": 1, "a": MinKey()}],
        expected=[],
        msg="MinKey field silently skipped",
    ),
    QueryTestCase(
        id="maxkey_field_skipped",
        filter=1,
        doc=[{"_id": 1, "a": MaxKey()}],
        expected=[],
        msg="MaxKey field silently skipped",
    ),
    QueryTestCase(
        id="array_non_numeric_skipped",
        filter=1,
        doc=[{"_id": 1, "a": ["a", "b"]}],
        expected=[],
        msg="Array of non-numeric values silently skipped",
    ),
]

_NON_REPRESENTABLE_TEMPLATES = [
    QueryTestCase(
        id="nan_double_skipped",
        filter=1,
        doc=[{"_id": 1, "a": FLOAT_NAN}],
        expected=[],
        msg="NaN (double) not int64-representable, silently skipped",
    ),
    QueryTestCase(
        id="infinity_double_skipped",
        filter=1,
        doc=[{"_id": 1, "a": FLOAT_INFINITY}],
        expected=[],
        msg="Infinity (double) not int64-representable, silently skipped",
    ),
    QueryTestCase(
        id="fractional_double_skipped",
        filter=1,
        doc=[{"_id": 1, "a": 1.5}],
        expected=[],
        msg="Fractional double not int64-representable, silently skipped",
    ),
    QueryTestCase(
        id="decimal128_exceeding_int64_skipped",
        filter=1,
        doc=[{"_id": 1, "a": DECIMAL128_MAX}],
        expected=[],
        msg="Decimal128 exceeding int64 range silently skipped",
    ),
    QueryTestCase(
        id="double_exceeding_int64_skipped",
        filter=1,
        doc=[{"_id": 1, "a": 1e30}],
        expected=[],
        msg="Double exceeding int64 range silently skipped",
    ),
    QueryTestCase(
        id="decimal128_nan_skipped",
        filter=1,
        doc=[{"_id": 1, "a": DECIMAL128_NAN}],
        expected=[],
        msg="Decimal128 NaN not int64-representable, silently skipped",
    ),
    QueryTestCase(
        id="decimal128_infinity_skipped",
        filter=1,
        doc=[{"_id": 1, "a": DECIMAL128_INFINITY}],
        expected=[],
        msg="Decimal128 Infinity not int64-representable, silently skipped",
    ),
    QueryTestCase(
        id="decimal128_neg_infinity_skipped",
        filter=1,
        doc=[{"_id": 1, "a": DECIMAL128_NEGATIVE_INFINITY}],
        expected=[],
        msg="Decimal128 -Infinity not int64-representable, silently skipped",
    ),
    QueryTestCase(
        id="neg_infinity_double_skipped",
        filter=1,
        doc=[{"_id": 1, "a": FLOAT_NEGATIVE_INFINITY}],
        expected=[],
        msg="-Infinity (double) not int64-representable, silently skipped",
    ),
    QueryTestCase(
        id="neg_double_exceeding_int64_skipped",
        filter=1,
        doc=[{"_id": 1, "a": -1e30}],
        expected=[],
        msg="Negative double exceeding int64 range silently skipped",
    ),
    QueryTestCase(
        id="neg_fractional_double_skipped",
        filter=1,
        doc=[{"_id": 1, "a": -1.5}],
        expected=[],
        msg="Negative fractional double not int64-representable, silently skipped",
    ),
]

_MISSING_FIELD_TEMPLATES = [
    QueryTestCase(
        id="missing_field_no_match",
        filter=1,
        doc=[{"_id": 1, "b": 1}],
        expected=[],
        msg="Missing field should not match",
    ),
]


_NON_STANDARD_FIELD_ERROR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id=f"{op[1:]}_error_precedence_invalid_bitmask_over_missing_field",
        filter={"missing_field": {op: "string"}},
        doc=[{"_id": 1, "a": 0}],
        error_code=BAD_VALUE_ERROR,
        msg=f"[{op}] Invalid bitmask type errors even on missing field",
    )
    for op in BITWISE_OPERATORS
]

_NON_STANDARD_FIELD_SKIP_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id=f"{op[1:]}_non_existent_field_no_match",
        filter={"missing": {op: 0}},
        doc=[{"_id": 1, "a": 20}],
        expected=[],
        msg=f"[{op}] Non-existent field does not match",
    )
    for op in BITWISE_OPERATORS
]

_ALL_ERROR_TEMPLATES = (
    _NUMERIC_BITMASK_ERROR_TEMPLATES + _POSITION_LIST_ERROR_TEMPLATES + _ERROR_PRECEDENCE_TEMPLATES
)

_ALL_SKIP_TEMPLATES = (
    _INVALID_FIELD_TYPE_TEMPLATES + _NON_REPRESENTABLE_TEMPLATES + _MISSING_FIELD_TEMPLATES
)

ALL_ERROR_TESTS: list[QueryTestCase] = _NON_STANDARD_FIELD_ERROR_TESTS.copy()
ALL_SKIP_TESTS: list[QueryTestCase] = _NON_STANDARD_FIELD_SKIP_TESTS.copy()
for _op in BITWISE_OPERATORS:
    ALL_ERROR_TESTS += _build_cases(_op, _ALL_ERROR_TEMPLATES)
    ALL_SKIP_TESTS += _build_cases(_op, _ALL_SKIP_TEMPLATES)


@pytest.mark.parametrize("test", pytest_params(ALL_ERROR_TESTS))
def test_bitwise_common_argument_errors(collection, test):
    """All bitwise operators reject the same invalid bitmask types, values, and positions."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertFailureCode(result, test.error_code)


@pytest.mark.parametrize("test", pytest_params(ALL_SKIP_TESTS))
def test_bitwise_common_silent_skips(collection, test):
    """All bitwise operators silently skip non-numeric types, non-representable values."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
