"""
Tests numeric value matching for the $elemMatch projection operator.
"""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.projection.utils.projection_test_case import (  # noqa: E501
    ProjectionTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_HALF,
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_ZERO,
    DOUBLE_MAX,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
)

# Property [Numeric Cross-Type Matching]: a numeric condition matches array elements of
# any numeric type by value, preserving the matched element's original type.
ELEMMATCH_NUMERIC_CROSS_TYPE_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "numeric_eq_int_matches_double",
        doc=[{"_id": 1, "arr": [5.0]}],
        projection={"arr": {"$elemMatch": {"$eq": 5}}},
        expected=[{"_id": 1, "arr": [5.0]}],
        msg="$elemMatch int condition should match a double element by value",
    ),
    ProjectionTestCase(
        "numeric_eq_int_matches_int64",
        doc=[{"_id": 1, "arr": [Int64(5)]}],
        projection={"arr": {"$elemMatch": {"$eq": 5}}},
        expected=[{"_id": 1, "arr": [Int64(5)]}],
        msg="$elemMatch int condition should match an int64 element by value",
    ),
    ProjectionTestCase(
        "numeric_eq_int_matches_decimal",
        doc=[{"_id": 1, "arr": [Decimal128("5")]}],
        projection={"arr": {"$elemMatch": {"$eq": 5}}},
        expected=[{"_id": 1, "arr": [Decimal128("5")]}],
        msg="$elemMatch int condition should match a Decimal128 element by value",
    ),
    ProjectionTestCase(
        "numeric_eq_double_matches_int64",
        doc=[{"_id": 1, "arr": [Int64(5)]}],
        projection={"arr": {"$elemMatch": {"$eq": 5.0}}},
        expected=[{"_id": 1, "arr": [Int64(5)]}],
        msg="$elemMatch double condition should match an int64 element by value",
    ),
    ProjectionTestCase(
        "numeric_eq_double_matches_decimal",
        doc=[{"_id": 1, "arr": [Decimal128("5")]}],
        projection={"arr": {"$elemMatch": {"$eq": 5.0}}},
        expected=[{"_id": 1, "arr": [Decimal128("5")]}],
        msg="$elemMatch double condition should match a Decimal128 element by value",
    ),
    ProjectionTestCase(
        "numeric_eq_int64_matches_double",
        doc=[{"_id": 1, "arr": [5.0]}],
        projection={"arr": {"$elemMatch": {"$eq": Int64(5)}}},
        expected=[{"_id": 1, "arr": [5.0]}],
        msg="$elemMatch int64 condition should match a double element by value",
    ),
    ProjectionTestCase(
        "numeric_eq_int64_matches_decimal",
        doc=[{"_id": 1, "arr": [Decimal128("5")]}],
        projection={"arr": {"$elemMatch": {"$eq": Int64(5)}}},
        expected=[{"_id": 1, "arr": [Decimal128("5")]}],
        msg="$elemMatch int64 condition should match a Decimal128 element by value",
    ),
    ProjectionTestCase(
        "numeric_eq_decimal_matches_double",
        doc=[{"_id": 1, "arr": [5.0]}],
        projection={"arr": {"$elemMatch": {"$eq": Decimal128("5")}}},
        expected=[{"_id": 1, "arr": [5.0]}],
        msg="$elemMatch Decimal128 condition should match a double element by value",
    ),
    ProjectionTestCase(
        "numeric_eq_decimal_matches_int",
        doc=[{"_id": 1, "arr": [5]}],
        projection={"arr": {"$elemMatch": {"$eq": Decimal128("5")}}},
        expected=[{"_id": 1, "arr": [5]}],
        msg="$elemMatch Decimal128 condition should match an int32 element by value",
    ),
    ProjectionTestCase(
        "numeric_eq_decimal_matches_int64",
        doc=[{"_id": 1, "arr": [Int64(5)]}],
        projection={"arr": {"$elemMatch": {"$eq": Decimal128("5")}}},
        expected=[{"_id": 1, "arr": [Int64(5)]}],
        msg="$elemMatch Decimal128 condition should match an int64 element by value",
    ),
    ProjectionTestCase(
        "numeric_eq_double_fraction_matches_decimal",
        doc=[{"_id": 1, "arr": [DECIMAL128_HALF]}],
        projection={"arr": {"$elemMatch": {"$eq": 0.5}}},
        expected=[{"_id": 1, "arr": [DECIMAL128_HALF]}],
        msg="$elemMatch double condition should match a fractional Decimal128 element by value",
    ),
    ProjectionTestCase(
        "numeric_eq_decimal_fraction_matches_double",
        doc=[{"_id": 1, "arr": [0.5]}],
        projection={"arr": {"$elemMatch": {"$eq": DECIMAL128_HALF}}},
        expected=[{"_id": 1, "arr": [0.5]}],
        msg="$elemMatch Decimal128 condition should match a fractional double element by value",
    ),
    ProjectionTestCase(
        "numeric_gte_double_matches_int",
        doc=[{"_id": 1, "arr": [1, 3]}],
        projection={"arr": {"$elemMatch": {"$gte": 2.5}}},
        expected=[{"_id": 1, "arr": [3]}],
        msg="$elemMatch double condition should match an int32 element by value",
    ),
    ProjectionTestCase(
        "numeric_in_matches_int64",
        doc=[{"_id": 1, "arr": [Int64(5)]}],
        projection={"arr": {"$elemMatch": {"$in": [5]}}},
        expected=[{"_id": 1, "arr": [Int64(5)]}],
        msg="$elemMatch $in with an int value should match an int64 element by value",
    ),
]

# Property [Numeric Signed Zero]: a zero condition of any numeric type matches a
# negative-zero element, preserving the element's sign.
ELEMMATCH_NUMERIC_SIGNED_ZERO_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "special_double_zero_matches_negative_zero",
        doc=[{"_id": 1, "arr": [DOUBLE_NEGATIVE_ZERO]}],
        projection={"arr": {"$elemMatch": {"$eq": DOUBLE_ZERO}}},
        expected=[{"_id": 1, "arr": [DOUBLE_NEGATIVE_ZERO]}],
        msg="$elemMatch positive-zero condition should match a negative-zero element",
    ),
    ProjectionTestCase(
        "special_negative_zero_matches_double_zero",
        doc=[{"_id": 1, "arr": [DOUBLE_ZERO]}],
        projection={"arr": {"$elemMatch": {"$eq": DOUBLE_NEGATIVE_ZERO}}},
        expected=[{"_id": 1, "arr": [DOUBLE_ZERO]}],
        msg="$elemMatch negative-zero condition should match a positive-zero element",
    ),
    ProjectionTestCase(
        "special_int_zero_matches_negative_zero",
        doc=[{"_id": 1, "arr": [DOUBLE_NEGATIVE_ZERO]}],
        projection={"arr": {"$elemMatch": {"$eq": 0}}},
        expected=[{"_id": 1, "arr": [DOUBLE_NEGATIVE_ZERO]}],
        msg="$elemMatch int-zero condition should match a negative-zero element",
    ),
    ProjectionTestCase(
        "special_decimal_zero_matches_negative_zero",
        doc=[{"_id": 1, "arr": [DOUBLE_NEGATIVE_ZERO]}],
        projection={"arr": {"$elemMatch": {"$eq": DECIMAL128_ZERO}}},
        expected=[{"_id": 1, "arr": [DOUBLE_NEGATIVE_ZERO]}],
        msg="$elemMatch Decimal128-zero condition should match a negative-zero element",
    ),
]

# Property [Numeric Infinity]: positive and negative infinity conditions match infinity
# elements of either double or Decimal128 type by value, preserving the element's type,
# and infinity of one sign does not match infinity of the other sign.
ELEMMATCH_NUMERIC_INFINITY_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "special_pos_inf_double_matches_double",
        doc=[{"_id": 1, "arr": [1.0, FLOAT_INFINITY]}],
        projection={"arr": {"$elemMatch": {"$eq": FLOAT_INFINITY}}},
        expected=[{"_id": 1, "arr": [FLOAT_INFINITY]}],
        msg="$elemMatch double +infinity condition should match a double +infinity element",
    ),
    ProjectionTestCase(
        "special_neg_inf_double_matches_double",
        doc=[{"_id": 1, "arr": [1.0, FLOAT_NEGATIVE_INFINITY]}],
        projection={"arr": {"$elemMatch": {"$eq": FLOAT_NEGATIVE_INFINITY}}},
        expected=[{"_id": 1, "arr": [FLOAT_NEGATIVE_INFINITY]}],
        msg="$elemMatch double -infinity condition should match a double -infinity element",
    ),
    ProjectionTestCase(
        "special_pos_inf_double_matches_decimal",
        doc=[{"_id": 1, "arr": [DECIMAL128_INFINITY]}],
        projection={"arr": {"$elemMatch": {"$eq": FLOAT_INFINITY}}},
        expected=[{"_id": 1, "arr": [DECIMAL128_INFINITY]}],
        msg="$elemMatch double +infinity condition should match a Decimal128 +infinity element",
    ),
    ProjectionTestCase(
        "special_neg_inf_double_matches_decimal",
        doc=[{"_id": 1, "arr": [DECIMAL128_NEGATIVE_INFINITY]}],
        projection={"arr": {"$elemMatch": {"$eq": FLOAT_NEGATIVE_INFINITY}}},
        expected=[{"_id": 1, "arr": [DECIMAL128_NEGATIVE_INFINITY]}],
        msg="$elemMatch double -infinity condition should match a Decimal128 -infinity element",
    ),
    ProjectionTestCase(
        "special_pos_inf_decimal_matches_double",
        doc=[{"_id": 1, "arr": [FLOAT_INFINITY]}],
        projection={"arr": {"$elemMatch": {"$eq": DECIMAL128_INFINITY}}},
        expected=[{"_id": 1, "arr": [FLOAT_INFINITY]}],
        msg="$elemMatch Decimal128 +infinity condition should match a double +infinity element",
    ),
    ProjectionTestCase(
        "special_neg_inf_decimal_matches_double",
        doc=[{"_id": 1, "arr": [FLOAT_NEGATIVE_INFINITY]}],
        projection={"arr": {"$elemMatch": {"$eq": DECIMAL128_NEGATIVE_INFINITY}}},
        expected=[{"_id": 1, "arr": [FLOAT_NEGATIVE_INFINITY]}],
        msg="$elemMatch Decimal128 -infinity condition should match a double -infinity element",
    ),
    ProjectionTestCase(
        "special_pos_inf_decimal_matches_decimal",
        doc=[{"_id": 1, "arr": [Decimal128("1"), DECIMAL128_INFINITY]}],
        projection={"arr": {"$elemMatch": {"$eq": DECIMAL128_INFINITY}}},
        expected=[{"_id": 1, "arr": [DECIMAL128_INFINITY]}],
        msg="$elemMatch Decimal128 +infinity condition should match a Decimal128 +infinity element",
    ),
    ProjectionTestCase(
        "special_neg_inf_decimal_matches_decimal",
        doc=[{"_id": 1, "arr": [Decimal128("1"), DECIMAL128_NEGATIVE_INFINITY]}],
        projection={"arr": {"$elemMatch": {"$eq": DECIMAL128_NEGATIVE_INFINITY}}},
        expected=[{"_id": 1, "arr": [DECIMAL128_NEGATIVE_INFINITY]}],
        msg="$elemMatch Decimal128 -infinity condition should match a Decimal128 -infinity element",
    ),
    ProjectionTestCase(
        "special_pos_inf_does_not_match_neg_inf",
        doc=[{"_id": 1, "arr": [FLOAT_NEGATIVE_INFINITY]}],
        projection={"arr": {"$elemMatch": {"$eq": FLOAT_INFINITY}}},
        expected=[{"_id": 1}],
        msg="$elemMatch +infinity condition should not match a -infinity element",
    ),
    ProjectionTestCase(
        "special_gt_double_max_matches_infinity",
        doc=[{"_id": 1, "arr": [1.0, FLOAT_INFINITY]}],
        projection={"arr": {"$elemMatch": {"$gt": DOUBLE_MAX}}},
        expected=[{"_id": 1, "arr": [FLOAT_INFINITY]}],
        msg="$elemMatch $gt of the largest finite double should match an infinity element",
    ),
]

# Property [Numeric NaN]: a NaN condition of either double or Decimal128 type, of either
# sign, matches a NaN element of either type, preserving the element's type, but never
# matches an ordinary number.
ELEMMATCH_NUMERIC_NAN_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "special_nan_double_matches_double",
        doc=[{"_id": 1, "arr": [1.0, FLOAT_NAN]}],
        projection={"arr": {"$elemMatch": {"$eq": FLOAT_NAN}}},
        expected=[{"_id": 1, "arr": [pytest.approx(FLOAT_NAN, nan_ok=True)]}],
        msg="$elemMatch double NaN condition should match a double NaN element",
    ),
    ProjectionTestCase(
        "special_nan_double_matches_decimal",
        doc=[{"_id": 1, "arr": [DECIMAL128_NAN]}],
        projection={"arr": {"$elemMatch": {"$eq": FLOAT_NAN}}},
        expected=[{"_id": 1, "arr": [DECIMAL128_NAN]}],
        msg="$elemMatch double NaN condition should match a Decimal128 NaN element",
    ),
    ProjectionTestCase(
        "special_nan_decimal_matches_double",
        doc=[{"_id": 1, "arr": [FLOAT_NAN]}],
        projection={"arr": {"$elemMatch": {"$eq": DECIMAL128_NAN}}},
        expected=[{"_id": 1, "arr": [pytest.approx(FLOAT_NAN, nan_ok=True)]}],
        msg="$elemMatch Decimal128 NaN condition should match a double NaN element",
    ),
    ProjectionTestCase(
        "special_nan_decimal_matches_decimal",
        doc=[{"_id": 1, "arr": [Decimal128("1"), DECIMAL128_NAN]}],
        projection={"arr": {"$elemMatch": {"$eq": DECIMAL128_NAN}}},
        expected=[{"_id": 1, "arr": [DECIMAL128_NAN]}],
        msg="$elemMatch Decimal128 NaN condition should match a Decimal128 NaN element",
    ),
    ProjectionTestCase(
        "special_negative_nan_double_matches_nan",
        doc=[{"_id": 1, "arr": [1.0, FLOAT_NAN]}],
        projection={"arr": {"$elemMatch": {"$eq": FLOAT_NEGATIVE_NAN}}},
        expected=[{"_id": 1, "arr": [pytest.approx(FLOAT_NAN, nan_ok=True)]}],
        msg="$elemMatch negative-NaN double condition should match a NaN element",
    ),
    ProjectionTestCase(
        "special_negative_nan_decimal_matches_nan",
        doc=[{"_id": 1, "arr": [DECIMAL128_NAN]}],
        projection={"arr": {"$elemMatch": {"$eq": DECIMAL128_NEGATIVE_NAN}}},
        expected=[{"_id": 1, "arr": [DECIMAL128_NAN]}],
        msg="$elemMatch negative-NaN Decimal128 condition should match a NaN element",
    ),
    ProjectionTestCase(
        "special_nan_does_not_match_number",
        doc=[{"_id": 1, "arr": [1.0, 2.0]}],
        projection={"arr": {"$elemMatch": {"$eq": FLOAT_NAN}}},
        expected=[{"_id": 1}],
        msg="$elemMatch NaN condition should omit the field when no element is NaN",
    ),
]

NUMERIC_TESTS = (
    ELEMMATCH_NUMERIC_CROSS_TYPE_TESTS
    + ELEMMATCH_NUMERIC_SIGNED_ZERO_TESTS
    + ELEMMATCH_NUMERIC_INFINITY_TESTS
    + ELEMMATCH_NUMERIC_NAN_TESTS
)


@pytest.mark.parametrize("test", pytest_params(NUMERIC_TESTS))
def test_elemmatch_numeric(collection, test):
    """Test $elemMatch projection numeric matching cases."""
    collection.insert_many(test.doc)
    cmd = {
        "find": collection.name,
        "projection": test.projection,
    }
    if test.filter is not None:
        cmd["filter"] = test.filter
    result = execute_command(collection, cmd)
    assertResult(result, expected=test.expected, error_code=test.error_code, msg=test.msg)
