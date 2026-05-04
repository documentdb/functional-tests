"""
Tests for $mod query operator error cases.

Covers array element count validation, non-array arguments, invalid divisor and
remainder types, NaN/Infinity rejection, both divisor and remainder NaN,
division by zero, 64-bit representability.
"""

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

DOCS = [{"_id": 1, "a": 4}, {"_id": 2, "a": 8}, {"_id": 3, "a": 5}]

ERROR_TESTS: list[QueryTestCase] = [
    # Array element count
    QueryTestCase(
        id="empty_array",
        filter={"a": {"$mod": []}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with empty array should error",
    ),
    QueryTestCase(
        id="single_element",
        filter={"a": {"$mod": [4]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with single element should error",
    ),
    QueryTestCase(
        id="three_elements",
        filter={"a": {"$mod": [4, 0, 1]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with three elements should error",
    ),
    # Non-array argument
    QueryTestCase(
        id="integer_arg",
        filter={"a": {"$mod": 3}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with integer argument should error",
    ),
    QueryTestCase(
        id="string_arg",
        filter={"a": {"$mod": "3"}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with string argument should error",
    ),
    QueryTestCase(
        id="null_arg",
        filter={"a": {"$mod": None}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with null argument should error",
    ),
    QueryTestCase(
        id="object_arg",
        filter={"a": {"$mod": {"divisor": 3, "remainder": 0}}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with object argument should error",
    ),
    # Invalid divisor types
    QueryTestCase(
        id="divisor_string",
        filter={"a": {"$mod": ["4", 0]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with string divisor should error",
    ),
    QueryTestCase(
        id="divisor_bool",
        filter={"a": {"$mod": [True, 0]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with boolean divisor should error",
    ),
    QueryTestCase(
        id="divisor_null",
        filter={"a": {"$mod": [None, 0]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with null divisor should error",
    ),
    QueryTestCase(
        id="divisor_object",
        filter={"a": {"$mod": [{"x": 1}, 0]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with object divisor should error",
    ),
    QueryTestCase(
        id="divisor_array",
        filter={"a": {"$mod": [[4], 0]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with array divisor should error",
    ),
    QueryTestCase(
        id="divisor_date",
        filter={"a": {"$mod": [datetime(2024, 1, 1, tzinfo=timezone.utc), 0]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with date divisor should error",
    ),
    QueryTestCase(
        id="divisor_objectid",
        filter={"a": {"$mod": [ObjectId("000000000000000000000001"), 0]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with ObjectId divisor should error",
    ),
    QueryTestCase(
        id="divisor_bindata",
        filter={"a": {"$mod": [Binary(b"\x01"), 0]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with BinData divisor should error",
    ),
    QueryTestCase(
        id="divisor_regex",
        filter={"a": {"$mod": [Regex(".*"), 0]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with regex divisor should error",
    ),
    QueryTestCase(
        id="divisor_timestamp",
        filter={"a": {"$mod": [Timestamp(1, 1), 0]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with timestamp divisor should error",
    ),
    QueryTestCase(
        id="divisor_minkey",
        filter={"a": {"$mod": [MinKey(), 0]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with MinKey divisor should error",
    ),
    QueryTestCase(
        id="divisor_maxkey",
        filter={"a": {"$mod": [MaxKey(), 0]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with MaxKey divisor should error",
    ),
    # NaN/Infinity divisor
    QueryTestCase(
        id="divisor_nan",
        filter={"a": {"$mod": [FLOAT_NAN, 0]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with NaN divisor should error",
    ),
    QueryTestCase(
        id="divisor_infinity",
        filter={"a": {"$mod": [FLOAT_INFINITY, 0]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with Infinity divisor should error",
    ),
    QueryTestCase(
        id="divisor_neg_infinity",
        filter={"a": {"$mod": [FLOAT_NEGATIVE_INFINITY, 0]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with -Infinity divisor should error",
    ),
    QueryTestCase(
        id="divisor_decimal128_nan",
        filter={"a": {"$mod": [DECIMAL128_NAN, 0]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with Decimal128 NaN divisor should error",
    ),
    QueryTestCase(
        id="divisor_decimal128_infinity",
        filter={"a": {"$mod": [DECIMAL128_INFINITY, 0]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with Decimal128 Infinity divisor should error",
    ),
    QueryTestCase(
        id="divisor_decimal128_neg_infinity",
        filter={"a": {"$mod": [DECIMAL128_NEGATIVE_INFINITY, 0]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with Decimal128 -Infinity divisor should error",
    ),
    # NaN/Infinity remainder
    QueryTestCase(
        id="remainder_nan",
        filter={"a": {"$mod": [4, FLOAT_NAN]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with NaN remainder should error",
    ),
    QueryTestCase(
        id="remainder_infinity",
        filter={"a": {"$mod": [4, FLOAT_INFINITY]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with Infinity remainder should error",
    ),
    QueryTestCase(
        id="remainder_decimal128_nan",
        filter={"a": {"$mod": [4, DECIMAL128_NAN]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with Decimal128 NaN remainder should error",
    ),
    QueryTestCase(
        id="remainder_decimal128_infinity",
        filter={"a": {"$mod": [4, DECIMAL128_INFINITY]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with Decimal128 Infinity remainder should error",
    ),
    QueryTestCase(
        id="remainder_neg_infinity",
        filter={"a": {"$mod": [4, FLOAT_NEGATIVE_INFINITY]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with -Infinity remainder should error",
    ),
    QueryTestCase(
        id="remainder_decimal128_neg_infinity",
        filter={"a": {"$mod": [4, DECIMAL128_NEGATIVE_INFINITY]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with Decimal128 -Infinity remainder should error",
    ),
    # Both divisor and remainder NaN
    QueryTestCase(
        id="divisor_and_remainder_nan",
        filter={"a": {"$mod": [FLOAT_NAN, FLOAT_NAN]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with NaN divisor and NaN remainder should error",
    ),
    # Division by zero
    QueryTestCase(
        id="divisor_int_zero",
        filter={"a": {"$mod": [0, 0]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with divisor 0 should error",
    ),
    QueryTestCase(
        id="divisor_long_zero",
        filter={"a": {"$mod": [Int64(0), 0]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with long 0 divisor should error",
    ),
    QueryTestCase(
        id="divisor_double_zero",
        filter={"a": {"$mod": [0.0, 0]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with double 0.0 divisor should error",
    ),
    QueryTestCase(
        id="divisor_neg_double_zero",
        filter={"a": {"$mod": [DOUBLE_NEGATIVE_ZERO, 0]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with -0.0 divisor should error",
    ),
    QueryTestCase(
        id="divisor_decimal128_zero",
        filter={"a": {"$mod": [DECIMAL128_ZERO, 0]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with Decimal128 0 divisor should error",
    ),
    QueryTestCase(
        id="divisor_decimal128_neg_zero",
        filter={"a": {"$mod": [DECIMAL128_NEGATIVE_ZERO, 0]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with Decimal128 -0 divisor should error",
    ),
    QueryTestCase(
        id="divisor_double_0_5_truncates_to_zero",
        filter={"a": {"$mod": [0.5, 0]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with 0.5 divisor should truncate to 0 and error",
    ),
    QueryTestCase(
        id="divisor_neg_0_5_truncates_to_zero",
        filter={"a": {"$mod": [-0.5, 0]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with -0.5 divisor should truncate toward zero to 0 and error",
    ),
    QueryTestCase(
        id="divisor_decimal128_truncates_to_zero",
        filter={"a": {"$mod": [Decimal128("0.99"), 0]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with Decimal128 0.99 divisor should truncate to 0 and error",
    ),
    # Invalid remainder types
    QueryTestCase(
        id="remainder_string",
        filter={"a": {"$mod": [4, "0"]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with string remainder should error",
    ),
    QueryTestCase(
        id="remainder_bool",
        filter={"a": {"$mod": [4, True]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with boolean remainder should error",
    ),
    QueryTestCase(
        id="remainder_null",
        filter={"a": {"$mod": [4, None]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with null remainder should error",
    ),
    QueryTestCase(
        id="remainder_object",
        filter={"a": {"$mod": [4, {"x": 1}]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with object remainder should error",
    ),
    QueryTestCase(
        id="remainder_array",
        filter={"a": {"$mod": [4, [0]]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with array remainder should error",
    ),
    # 64-bit representability
    QueryTestCase(
        id="divisor_exceeds_int64",
        filter={"a": {"$mod": [1e19, 0]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with divisor exceeding 64-bit range should error",
    ),
    QueryTestCase(
        id="divisor_decimal128_exceeds_int64",
        filter={"a": {"$mod": [Decimal128("9999999999999999999999"), 0]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with Decimal128 divisor exceeding 64-bit range should error",
    ),
    QueryTestCase(
        id="remainder_exceeds_int64",
        filter={"a": {"$mod": [4, 1e19]}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$mod with remainder exceeding 64-bit range should error",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ERROR_TESTS))
def test_mod_errors(collection, test):
    """Parametrized test for $mod error cases."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertFailureCode(result, test.error_code, msg=test.msg)
