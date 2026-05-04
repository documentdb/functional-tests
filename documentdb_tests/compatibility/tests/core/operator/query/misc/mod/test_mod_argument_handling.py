"""
Tests for $mod query operator valid argument handling and boundary values.

Covers valid divisor and remainder types, cross-type divisor/remainder
combinations, large value divisors, INT32/INT64 boundaries, overflow
prevention, Decimal128/double precision boundaries, and remainder greater
than divisor behavior.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ZERO,
    DOUBLE_MAX_SAFE_INTEGER,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)

DOCS = [{"_id": 1, "a": 4}, {"_id": 2, "a": 8}, {"_id": 3, "a": 5}]

LARGE_DIVISOR = Int64(2**33)


VALID_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="divisor_int",
        filter={"a": {"$mod": [4, 0]}},
        doc=DOCS,
        expected=[{"_id": 1, "a": 4}, {"_id": 2, "a": 8}],
        msg="$mod with int divisor should match",
    ),
    QueryTestCase(
        id="divisor_long",
        filter={"a": {"$mod": [Int64(4), 0]}},
        doc=DOCS,
        expected=[{"_id": 1, "a": 4}, {"_id": 2, "a": 8}],
        msg="$mod with long divisor should match",
    ),
    QueryTestCase(
        id="divisor_double",
        filter={"a": {"$mod": [4.0, 0]}},
        doc=DOCS,
        expected=[{"_id": 1, "a": 4}, {"_id": 2, "a": 8}],
        msg="$mod with double divisor should match",
    ),
    QueryTestCase(
        id="divisor_decimal128",
        filter={"a": {"$mod": [Decimal128("4"), 0]}},
        doc=DOCS,
        expected=[{"_id": 1, "a": 4}, {"_id": 2, "a": 8}],
        msg="$mod with decimal128 divisor should match",
    ),
    QueryTestCase(
        id="divisor_decimal128_fraction_truncated",
        filter={"a": {"$mod": [Decimal128("4.5"), 0]}},
        doc=DOCS,
        expected=[{"_id": 1, "a": 4}, {"_id": 2, "a": 8}],
        msg="$mod with decimal128 4.5 divisor should truncate to 4",
    ),
    QueryTestCase(
        id="remainder_int",
        filter={"a": {"$mod": [4, 1]}},
        doc=DOCS,
        expected=[{"_id": 3, "a": 5}],
        msg="$mod with int remainder should match",
    ),
    QueryTestCase(
        id="remainder_long",
        filter={"a": {"$mod": [4, Int64(0)]}},
        doc=DOCS,
        expected=[{"_id": 1, "a": 4}, {"_id": 2, "a": 8}],
        msg="$mod with long remainder should match",
    ),
    QueryTestCase(
        id="remainder_double",
        filter={"a": {"$mod": [4, 0.0]}},
        doc=DOCS,
        expected=[{"_id": 1, "a": 4}, {"_id": 2, "a": 8}],
        msg="$mod with double remainder should match",
    ),
    QueryTestCase(
        id="remainder_double_fraction_truncated",
        filter={"a": {"$mod": [4, 1.5]}},
        doc=DOCS,
        expected=[{"_id": 3, "a": 5}],
        msg="$mod with double 1.5 remainder should truncate to 1",
    ),
    QueryTestCase(
        id="remainder_decimal128",
        filter={"a": {"$mod": [4, DECIMAL128_ZERO]}},
        doc=DOCS,
        expected=[{"_id": 1, "a": 4}, {"_id": 2, "a": 8}],
        msg="$mod with decimal128 remainder should match",
    ),
    QueryTestCase(
        id="long_divisor_decimal128_remainder",
        filter={"a": {"$mod": [Int64(4), Decimal128("0.5")]}},
        doc=DOCS,
        expected=[{"_id": 1, "a": 4}, {"_id": 2, "a": 8}],
        msg="$mod with long divisor and decimal128 remainder (truncated to 0) should match",
    ),
    QueryTestCase(
        id="decimal128_divisor_decimal128_remainder",
        filter={"a": {"$mod": [Decimal128("4.5"), Decimal128("0.5")]}},
        doc=DOCS,
        expected=[{"_id": 1, "a": 4}, {"_id": 2, "a": 8}],
        msg="$mod with decimal128 divisor and remainder (both truncated) should match",
    ),
    QueryTestCase(
        id="large_divisor_positive_match",
        filter={"a": {"$mod": [LARGE_DIVISOR, 0]}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": LARGE_DIVISOR}, {"_id": 3, "a": 5}],
        expected=[{"_id": 1, "a": 0}, {"_id": 2, "a": LARGE_DIVISOR}],
        msg="$mod with large divisor should match multiples",
    ),
    QueryTestCase(
        id="negative_large_divisor",
        filter={"a": {"$mod": [-LARGE_DIVISOR, 0]}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": LARGE_DIVISOR}, {"_id": 3, "a": 5}],
        expected=[{"_id": 1, "a": 0}, {"_id": 2, "a": LARGE_DIVISOR}],
        msg="$mod with negative large divisor should match same as positive",
    ),
]


BOUNDARY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="int32_max_mod_2_remainder_1",
        filter={"a": {"$mod": [2, 1]}},
        doc=[{"_id": 1, "a": INT32_MAX}],
        expected=[{"_id": 1, "a": INT32_MAX}],
        msg="INT32_MAX % 2 should equal 1",
    ),
    QueryTestCase(
        id="int32_max_mod_self_remainder_0",
        filter={"a": {"$mod": [INT32_MAX, 0]}},
        doc=[{"_id": 1, "a": INT32_MAX}],
        expected=[{"_id": 1, "a": INT32_MAX}],
        msg="INT32_MAX % INT32_MAX should equal 0",
    ),
    QueryTestCase(
        id="int32_min_mod_2_remainder_0",
        filter={"a": {"$mod": [2, 0]}},
        doc=[{"_id": 1, "a": INT32_MIN}],
        expected=[{"_id": 1, "a": INT32_MIN}],
        msg="INT32_MIN % 2 should equal 0",
    ),
    QueryTestCase(
        id="int64_max_mod_2_remainder_1",
        filter={"a": {"$mod": [2, 1]}},
        doc=[{"_id": 1, "a": INT64_MAX}],
        expected=[{"_id": 1, "a": INT64_MAX}],
        msg="INT64_MAX % 2 should equal 1",
    ),
    QueryTestCase(
        id="int64_max_mod_self_remainder_0",
        filter={"a": {"$mod": [INT64_MAX, 0]}},
        doc=[{"_id": 1, "a": INT64_MAX}],
        expected=[{"_id": 1, "a": INT64_MAX}],
        msg="INT64_MAX % INT64_MAX should equal 0",
    ),
    QueryTestCase(
        id="int64_min_mod_2_remainder_0",
        filter={"a": {"$mod": [2, 0]}},
        doc=[{"_id": 1, "a": INT64_MIN}],
        expected=[{"_id": 1, "a": INT64_MIN}],
        msg="INT64_MIN % 2 should equal 0",
    ),
]


OVERFLOW_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="int64_min_div_neg1_remainder_0",
        filter={"a": {"$mod": [-1, 0]}},
        doc=[{"_id": 1, "a": INT64_MIN}, {"_id": 2, "a": INT32_MIN}],
        expected=[{"_id": 1, "a": INT64_MIN}, {"_id": 2, "a": INT32_MIN}],
        msg="INT64_MIN and INT32_MIN divided by -1 should not overflow, remainder 0",
    ),
    QueryTestCase(
        id="int32_min_div_neg1_int_remainder_0",
        filter={"a": {"$mod": [-1, 0]}},
        doc=[{"_id": 1, "a": INT32_MIN}],
        expected=[{"_id": 1, "a": INT32_MIN}],
        msg="INT32_MIN divided by -1 should not overflow, remainder 0",
    ),
    QueryTestCase(
        id="int64_min_div_neg1_long_remainder_0",
        filter={"a": {"$mod": [Int64(-1), 0]}},
        doc=[{"_id": 1, "a": INT64_MIN}],
        expected=[{"_id": 1, "a": INT64_MIN}],
        msg="INT64_MIN divided by long(-1) should not overflow, remainder 0",
    ),
    QueryTestCase(
        id="int64_min_div_neg1_double_remainder_0",
        filter={"a": {"$mod": [-1.0, 0]}},
        doc=[{"_id": 1, "a": INT64_MIN}],
        expected=[{"_id": 1, "a": INT64_MIN}],
        msg="INT64_MIN divided by double(-1) should not overflow, remainder 0",
    ),
    QueryTestCase(
        id="int64_min_div_neg1_decimal128_remainder_0",
        filter={"a": {"$mod": [Decimal128("-1"), 0]}},
        doc=[{"_id": 1, "a": INT64_MIN}],
        expected=[{"_id": 1, "a": INT64_MIN}],
        msg="INT64_MIN divided by Decimal128(-1) should not overflow, remainder 0",
    ),
]


DIVISOR_BOUNDARY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="divisor_neg1_all_match",
        filter={"a": {"$mod": [-1, 0]}},
        doc=[{"_id": 1, "a": 7}, {"_id": 2, "a": -3}, {"_id": 3, "a": 0}],
        expected=[{"_id": 1, "a": 7}, {"_id": 2, "a": -3}, {"_id": 3, "a": 0}],
        msg="$mod with divisor -1 should match all integers (remainder always 0)",
    ),
    QueryTestCase(
        id="divisor_int64_min",
        filter={"a": {"$mod": [INT64_MIN, 0]}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 5}],
        expected=[{"_id": 1, "a": 0}],
        msg="$mod with INT64_MIN as divisor should work",
    ),
    QueryTestCase(
        id="divisor_int32_min",
        filter={"a": {"$mod": [INT32_MIN, 0]}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": INT32_MIN}],
        expected=[{"_id": 1, "a": 0}, {"_id": 2, "a": INT32_MIN}],
        msg="$mod with INT32_MIN as divisor should work",
    ),
    QueryTestCase(
        id="divisor_int64_max",
        filter={"a": {"$mod": [INT64_MAX, 0]}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": INT64_MAX}, {"_id": 3, "a": 5}],
        expected=[{"_id": 1, "a": 0}, {"_id": 2, "a": INT64_MAX}],
        msg="$mod with INT64_MAX divisor should work",
    ),
    QueryTestCase(
        id="divisor_int32_max",
        filter={"a": {"$mod": [INT32_MAX, 0]}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": INT32_MAX}],
        expected=[{"_id": 1, "a": 0}, {"_id": 2, "a": INT32_MAX}],
        msg="$mod with INT32_MAX divisor should work",
    ),
]


PRECISION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="decimal128_high_precision",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": Decimal128("999999999999999999")}],
        expected=[{"_id": 1, "a": Decimal128("999999999999999999")}],
        msg="$mod on high-precision Decimal128 should compute correctly",
    ),
    QueryTestCase(
        id="decimal128_exponent_notation",
        filter={"a": {"$mod": [3, 0]}},
        doc=[{"_id": 1, "a": Decimal128("9E+2")}],
        expected=[{"_id": 1, "a": Decimal128("9E+2")}],
        msg="$mod on Decimal128 with exponent notation should compute correctly (900 % 3 = 0)",
    ),
    QueryTestCase(
        id="double_max_safe_integer",
        filter={"a": {"$mod": [2, 0]}},
        doc=[{"_id": 1, "a": float(DOUBLE_MAX_SAFE_INTEGER)}],
        expected=[{"_id": 1, "a": float(DOUBLE_MAX_SAFE_INTEGER)}],
        msg="$mod on MAX_SAFE_INTEGER double should match",
    ),
]

REMAINDER_GREATER_THAN_DIVISOR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="remainder_greater_than_divisor_no_match",
        filter={"a": {"$mod": [3, 5]}},
        doc=[{"_id": 1, "a": 3}, {"_id": 2, "a": 5}, {"_id": 3, "a": 8}],
        expected=[],
        msg="$mod with remainder > divisor should never match (field % 3 ranges 0-2)",
    ),
    QueryTestCase(
        id="remainder_equal_to_divisor_no_match",
        filter={"a": {"$mod": [4, 4]}},
        doc=[{"_id": 1, "a": 4}, {"_id": 2, "a": 8}, {"_id": 3, "a": 0}],
        expected=[],
        msg="$mod with remainder == divisor should not match (field % 4 ranges 0-3)",
    ),
    QueryTestCase(
        id="negative_remainder_positive_field_no_match",
        filter={"a": {"$mod": [3, -1]}},
        doc=[{"_id": 1, "a": 3}, {"_id": 2, "a": 5}, {"_id": 3, "a": 8}],
        expected=[],
        msg="$mod with negative remainder against positive fields "
        "should not match (positive field % 3 is never -1)",
    ),
]

ALL_TESTS = (
    VALID_TYPE_TESTS
    + BOUNDARY_TESTS
    + OVERFLOW_TESTS
    + DIVISOR_BOUNDARY_TESTS
    + PRECISION_TESTS
    + REMAINDER_GREATER_THAN_DIVISOR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_mod_argument_handling(collection, test):
    """Parametrized test for $mod valid arguments and boundary values."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True, msg=test.msg)
