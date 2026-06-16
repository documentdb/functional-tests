"""
Special value tests for $mul update field operator.

Tests NaN propagation, Infinity arithmetic, negative zero handling,
and multiplication by identity/zero/sign-flip values.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessNaN
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NEGATIVE_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

NAN_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "nan_field_x_positive",
        setup_docs=[{"_id": 1, "val": FLOAT_NAN}],
        query={"_id": 1},
        update={"$mul": {"val": 5.0}},
        expected={"_id": 1, "val": FLOAT_NAN},
        msg="NaN × positive should produce NaN",
    ),
    UpdateTestCase(
        "nan_field_x_negative",
        setup_docs=[{"_id": 1, "val": FLOAT_NAN}],
        query={"_id": 1},
        update={"$mul": {"val": -5.0}},
        expected={"_id": 1, "val": FLOAT_NAN},
        msg="NaN × negative should produce NaN",
    ),
    UpdateTestCase(
        "nan_field_x_zero",
        setup_docs=[{"_id": 1, "val": FLOAT_NAN}],
        query={"_id": 1},
        update={"$mul": {"val": 0.0}},
        expected={"_id": 1, "val": FLOAT_NAN},
        msg="NaN × 0 should produce NaN",
    ),
    UpdateTestCase(
        "numeric_x_nan",
        setup_docs=[{"_id": 1, "val": 10.0}],
        query={"_id": 1},
        update={"$mul": {"val": FLOAT_NAN}},
        expected={"_id": 1, "val": FLOAT_NAN},
        msg="numeric × NaN should produce NaN",
    ),
    UpdateTestCase(
        "decimal128_nan_x_one",
        setup_docs=[{"_id": 1, "val": Decimal128("NaN")}],
        query={"_id": 1},
        update={"$mul": {"val": Decimal128("1")}},
        expected={"_id": 1, "val": Decimal128("NaN")},
        msg="Decimal128 NaN × 1 should produce Decimal128 NaN",
    ),
]

INFINITY_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "inf_x_positive",
        setup_docs=[{"_id": 1, "val": FLOAT_INFINITY}],
        query={"_id": 1},
        update={"$mul": {"val": 5.0}},
        expected={"_id": 1, "val": FLOAT_INFINITY},
        msg="Infinity × positive should produce Infinity",
    ),
    UpdateTestCase(
        "inf_x_negative",
        setup_docs=[{"_id": 1, "val": FLOAT_INFINITY}],
        query={"_id": 1},
        update={"$mul": {"val": -5.0}},
        expected={"_id": 1, "val": FLOAT_NEGATIVE_INFINITY},
        msg="Infinity × negative should produce -Infinity",
    ),
    UpdateTestCase(
        "inf_x_zero",
        setup_docs=[{"_id": 1, "val": FLOAT_INFINITY}],
        query={"_id": 1},
        update={"$mul": {"val": 0.0}},
        expected={"_id": 1, "val": FLOAT_NAN},
        msg="Infinity × 0 should produce NaN",
    ),
    UpdateTestCase(
        "neg_inf_x_positive",
        setup_docs=[{"_id": 1, "val": FLOAT_NEGATIVE_INFINITY}],
        query={"_id": 1},
        update={"$mul": {"val": 5.0}},
        expected={"_id": 1, "val": FLOAT_NEGATIVE_INFINITY},
        msg="-Infinity × positive should produce -Infinity",
    ),
    UpdateTestCase(
        "neg_inf_x_negative",
        setup_docs=[{"_id": 1, "val": FLOAT_NEGATIVE_INFINITY}],
        query={"_id": 1},
        update={"$mul": {"val": -5.0}},
        expected={"_id": 1, "val": FLOAT_INFINITY},
        msg="-Infinity × negative should produce Infinity",
    ),
    UpdateTestCase(
        "neg_inf_x_zero",
        setup_docs=[{"_id": 1, "val": FLOAT_NEGATIVE_INFINITY}],
        query={"_id": 1},
        update={"$mul": {"val": 0.0}},
        expected={"_id": 1, "val": FLOAT_NAN},
        msg="-Infinity × 0 should produce NaN",
    ),
    UpdateTestCase(
        "zero_x_inf",
        setup_docs=[{"_id": 1, "val": 0.0}],
        query={"_id": 1},
        update={"$mul": {"val": FLOAT_INFINITY}},
        expected={"_id": 1, "val": FLOAT_NAN},
        msg="0 × Infinity should produce NaN",
    ),
    UpdateTestCase(
        "inf_x_inf",
        setup_docs=[{"_id": 1, "val": FLOAT_INFINITY}],
        query={"_id": 1},
        update={"$mul": {"val": FLOAT_INFINITY}},
        expected={"_id": 1, "val": FLOAT_INFINITY},
        msg="Infinity × Infinity should produce Infinity",
    ),
    UpdateTestCase(
        "inf_x_neg_inf",
        setup_docs=[{"_id": 1, "val": FLOAT_INFINITY}],
        query={"_id": 1},
        update={"$mul": {"val": FLOAT_NEGATIVE_INFINITY}},
        expected={"_id": 1, "val": FLOAT_NEGATIVE_INFINITY},
        msg="Infinity × (-Infinity) should produce -Infinity",
    ),
    UpdateTestCase(
        "neg_inf_x_neg_inf",
        setup_docs=[{"_id": 1, "val": FLOAT_NEGATIVE_INFINITY}],
        query={"_id": 1},
        update={"$mul": {"val": FLOAT_NEGATIVE_INFINITY}},
        expected={"_id": 1, "val": FLOAT_INFINITY},
        msg="(-Infinity) × (-Infinity) should produce Infinity",
    ),
    UpdateTestCase(
        "decimal128_inf_x_zero",
        setup_docs=[{"_id": 1, "val": Decimal128("Infinity")}],
        query={"_id": 1},
        update={"$mul": {"val": Decimal128("0")}},
        expected={"_id": 1, "val": Decimal128("NaN")},
        msg="Decimal128 Infinity × 0 should produce Decimal128 NaN",
    ),
]


ALL_NAN_TESTS = NAN_TESTS + INFINITY_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_NAN_TESTS))
def test_mul_nan_and_infinity(collection, test: UpdateTestCase):
    """Test $mul NaN propagation and infinity arithmetic."""
    collection.insert_many(test.setup_docs)
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": test.expected["_id"]}}
    )
    assertSuccessNaN(result, [test.expected], msg=test.msg)


NEGATIVE_ZERO_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "neg_zero_x_positive",
        setup_docs=[{"_id": 1, "val": DOUBLE_NEGATIVE_ZERO}],
        query={"_id": 1},
        update={"$mul": {"val": 5.0}},
        expected={"_id": 1, "val": DOUBLE_NEGATIVE_ZERO},
        msg="-0.0 × positive should produce -0.0",
    ),
    UpdateTestCase(
        "positive_x_neg_zero",
        setup_docs=[{"_id": 1, "val": 5.0}],
        query={"_id": 1},
        update={"$mul": {"val": DOUBLE_NEGATIVE_ZERO}},
        expected={"_id": 1, "val": DOUBLE_NEGATIVE_ZERO},
        msg="positive × -0.0 should produce -0.0",
    ),
    UpdateTestCase(
        "neg_zero_x_neg_zero",
        setup_docs=[{"_id": 1, "val": DOUBLE_NEGATIVE_ZERO}],
        query={"_id": 1},
        update={"$mul": {"val": DOUBLE_NEGATIVE_ZERO}},
        expected={"_id": 1, "val": DOUBLE_NEGATIVE_ZERO},
        msg="-0.0 × -0.0 produces -0.0 (engine behavior, differs from IEEE-754)",
    ),
    UpdateTestCase(
        "negative_x_neg_zero",
        setup_docs=[{"_id": 1, "val": -5.0}],
        query={"_id": 1},
        update={"$mul": {"val": DOUBLE_NEGATIVE_ZERO}},
        expected={"_id": 1, "val": 0.0},
        msg="negative × -0.0 should produce +0.0",
    ),
    UpdateTestCase(
        "decimal128_neg_zero_x_one",
        setup_docs=[{"_id": 1, "val": DECIMAL128_NEGATIVE_ZERO}],
        query={"_id": 1},
        update={"$mul": {"val": Decimal128("1")}},
        expected={"_id": 1, "val": DECIMAL128_NEGATIVE_ZERO},
        msg="Decimal128(-0) × 1 should produce Decimal128(-0)",
    ),
    UpdateTestCase(
        "decimal128_neg_zero_x_neg_one",
        setup_docs=[{"_id": 1, "val": DECIMAL128_NEGATIVE_ZERO}],
        query={"_id": 1},
        update={"$mul": {"val": Decimal128("-1")}},
        expected={"_id": 1, "val": DECIMAL128_NEGATIVE_ZERO},
        msg="Decimal128(-0) × (-1) produces Decimal128(-0) (engine, differs from IEEE-754)",
    ),
    UpdateTestCase(
        "decimal128_neg_x_zero",
        setup_docs=[{"_id": 1, "val": Decimal128("-5")}],
        query={"_id": 1},
        update={"$mul": {"val": Decimal128("0")}},
        expected={"_id": 1, "val": DECIMAL128_NEGATIVE_ZERO},
        msg="Decimal128(-5) × 0 should produce Decimal128(-0)",
    ),
    UpdateTestCase(
        "decimal128_neg_zero_positive_exponent",
        setup_docs=[{"_id": 1, "val": Decimal128("-0E+10")}],
        query={"_id": 1},
        update={"$mul": {"val": Decimal128("1")}},
        expected={"_id": 1, "val": Decimal128("-0E+10")},
        msg="Decimal128(-0E+10) × 1 should preserve negative-zero exponent",
    ),
    UpdateTestCase(
        "decimal128_neg_zero_negative_exponent",
        setup_docs=[{"_id": 1, "val": Decimal128("-0E-10")}],
        query={"_id": 1},
        update={"$mul": {"val": Decimal128("1")}},
        expected={"_id": 1, "val": Decimal128("-0E-10")},
        msg="Decimal128(-0E-10) × 1 should preserve negative-zero exponent",
    ),
]

SPECIAL_MULTIPLIER_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "identity_int32",
        setup_docs=[{"_id": 1, "val": 42}],
        query={"_id": 1},
        update={"$mul": {"val": 1}},
        expected={"_id": 1, "val": 42},
        msg="int32 × 1 should be unchanged (identity)",
    ),
    UpdateTestCase(
        "zero_int32",
        setup_docs=[{"_id": 1, "val": 100}],
        query={"_id": 1},
        update={"$mul": {"val": 0}},
        expected={"_id": 1, "val": 0},
        msg="int32 × 0 should produce zero",
    ),
    UpdateTestCase(
        "sign_flip_int32",
        setup_docs=[{"_id": 1, "val": 42}],
        query={"_id": 1},
        update={"$mul": {"val": -1}},
        expected={"_id": 1, "val": -42},
        msg="int32 × (-1) should flip sign",
    ),
    UpdateTestCase(
        "identity_int64",
        setup_docs=[{"_id": 1, "val": Int64(42)}],
        query={"_id": 1},
        update={"$mul": {"val": Int64(1)}},
        expected={"_id": 1, "val": Int64(42)},
        msg="int64 × 1 should be unchanged (identity)",
    ),
    UpdateTestCase(
        "zero_int64",
        setup_docs=[{"_id": 1, "val": Int64(100)}],
        query={"_id": 1},
        update={"$mul": {"val": Int64(0)}},
        expected={"_id": 1, "val": Int64(0)},
        msg="int64 × 0 should produce int64 zero",
    ),
    UpdateTestCase(
        "sign_flip_int64",
        setup_docs=[{"_id": 1, "val": Int64(42)}],
        query={"_id": 1},
        update={"$mul": {"val": Int64(-1)}},
        expected={"_id": 1, "val": Int64(-42)},
        msg="int64 × (-1) should flip sign",
    ),
    UpdateTestCase(
        "identity_double",
        setup_docs=[{"_id": 1, "val": 3.14}],
        query={"_id": 1},
        update={"$mul": {"val": 1.0}},
        expected={"_id": 1, "val": 3.14},
        msg="double × 1.0 should be unchanged",
    ),
    UpdateTestCase(
        "sign_flip_double",
        setup_docs=[{"_id": 1, "val": 3.14}],
        query={"_id": 1},
        update={"$mul": {"val": -1.0}},
        expected={"_id": 1, "val": -3.14},
        msg="double × (-1.0) should flip sign",
    ),
    UpdateTestCase(
        "identity_decimal128",
        setup_docs=[{"_id": 1, "val": Decimal128("3.14")}],
        query={"_id": 1},
        update={"$mul": {"val": Decimal128("1")}},
        expected={"_id": 1, "val": Decimal128("3.14")},
        msg="Decimal128 × 1 should be unchanged",
    ),
    UpdateTestCase(
        "sign_flip_decimal128",
        setup_docs=[{"_id": 1, "val": Decimal128("3.14")}],
        query={"_id": 1},
        update={"$mul": {"val": Decimal128("-1")}},
        expected={"_id": 1, "val": Decimal128("-3.14")},
        msg="Decimal128 × (-1) should flip sign",
    ),
]

ALL_EXACT_TESTS = NEGATIVE_ZERO_TESTS + SPECIAL_MULTIPLIER_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_EXACT_TESTS))
def test_mul_special_values(collection, test: UpdateTestCase):
    """Test $mul negative zero, identity, zero, and sign-flip multipliers."""
    collection.insert_many(test.setup_docs)
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": test.expected["_id"]}}
    )
    assertSuccess(result, [test.expected], msg=test.msg)
