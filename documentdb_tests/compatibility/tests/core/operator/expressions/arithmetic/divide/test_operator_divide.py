"""Tests for $divide operator — core behavior.

Covers type combinations, return types, sign handling,
fractional operations, and identity/self-division.
"""

from dataclasses import dataclass
from typing import Any, Optional

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression_with_insert,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import assertExprResult
from documentdb_tests.framework.test_case import BaseTestCase
from documentdb_tests.framework.parametrize import pytest_params


@dataclass(frozen=True)
class DivideTest(BaseTestCase):
    """Test case for $divide operator."""

    dividend: Any = None
    divisor: Any = None
    expected_type: Optional[str] = None


# --- Type combinations and return types ---
TYPE_COMBINATION_TESTS: list[DivideTest] = [
    DivideTest(
        "int32_int32",
        dividend=10,
        divisor=2,
        expected=5.0,
        expected_type="double",
        msg="int32 / int32 → double",
    ),
    DivideTest(
        "int32_int64",
        dividend=10,
        divisor=Int64(2),
        expected=5.0,
        expected_type="double",
        msg="int32 / int64 → double",
    ),
    DivideTest(
        "int32_double",
        dividend=10,
        divisor=2.0,
        expected=5.0,
        expected_type="double",
        msg="int32 / double → double",
    ),
    DivideTest(
        "int32_decimal128",
        dividend=10,
        divisor=Decimal128("2"),
        expected=Decimal128("5"),
        expected_type="decimal",
        msg="int32 / decimal128 → decimal",
    ),
    DivideTest(
        "int64_int32",
        dividend=Int64(10),
        divisor=2,
        expected=5.0,
        expected_type="double",
        msg="int64 / int32 → double",
    ),
    DivideTest(
        "int64_int64",
        dividend=Int64(10),
        divisor=Int64(2),
        expected=5.0,
        expected_type="double",
        msg="int64 / int64 → double",
    ),
    DivideTest(
        "int64_double",
        dividend=Int64(10),
        divisor=2.0,
        expected=5.0,
        expected_type="double",
        msg="int64 / double → double",
    ),
    DivideTest(
        "int64_decimal128",
        dividend=Int64(10),
        divisor=Decimal128("2"),
        expected=Decimal128("5"),
        expected_type="decimal",
        msg="int64 / decimal128 → decimal",
    ),
    DivideTest(
        "double_int32",
        dividend=10.0,
        divisor=2,
        expected=5.0,
        expected_type="double",
        msg="double / int32 → double",
    ),
    DivideTest(
        "double_int64",
        dividend=10.0,
        divisor=Int64(2),
        expected=5.0,
        expected_type="double",
        msg="double / int64 → double",
    ),
    DivideTest(
        "double_double",
        dividend=10.0,
        divisor=2.0,
        expected=5.0,
        expected_type="double",
        msg="double / double → double",
    ),
    DivideTest(
        "double_decimal128",
        dividend=10.0,
        divisor=Decimal128("2"),
        expected=Decimal128("5.0000000000000"),
        expected_type="decimal",
        msg="double / decimal128 → decimal",
    ),
    DivideTest(
        "decimal128_int32",
        dividend=Decimal128("10"),
        divisor=2,
        expected=Decimal128("5"),
        expected_type="decimal",
        msg="decimal128 / int32 → decimal",
    ),
    DivideTest(
        "decimal128_int64",
        dividend=Decimal128("10"),
        divisor=Int64(2),
        expected=Decimal128("5"),
        expected_type="decimal",
        msg="decimal128 / int64 → decimal",
    ),
    DivideTest(
        "decimal128_double",
        dividend=Decimal128("10"),
        divisor=2.0,
        expected=Decimal128("5"),
        expected_type="decimal",
        msg="decimal128 / double → decimal",
    ),
    DivideTest(
        "decimal128_decimal128",
        dividend=Decimal128("10"),
        divisor=Decimal128("2"),
        expected=Decimal128("5"),
        expected_type="decimal",
        msg="decimal128 / decimal128 → decimal",
    ),
]

# --- Sign handling ---
SIGN_TESTS: list[DivideTest] = [
    DivideTest(
        "pos_pos", dividend=10, divisor=2, expected=5.0, msg="positive / positive → positive"
    ),
    DivideTest(
        "neg_pos", dividend=-10, divisor=2, expected=-5.0, msg="negative / positive → negative"
    ),
    DivideTest(
        "pos_neg", dividend=10, divisor=-2, expected=-5.0, msg="positive / negative → negative"
    ),
    DivideTest(
        "neg_neg", dividend=-10, divisor=-2, expected=5.0, msg="negative / negative → positive"
    ),
    DivideTest("zero_pos", dividend=0, divisor=5, expected=0.0, msg="zero / positive → 0"),
    DivideTest("zero_neg", dividend=0, divisor=-5, expected=-0.0, msg="zero / negative → -0.0"),
]

# --- Fractional operations ---
FRACTIONAL_TESTS: list[DivideTest] = [
    DivideTest(
        "even_division", dividend=20, divisor=4, expected=5.0, msg="Even division → exact result"
    ),
    DivideTest(
        "repeating",
        dividend=10,
        divisor=3,
        expected=pytest.approx(3.333333333333333),
        msg="10/3 → repeating decimal",
    ),
    DivideTest(
        "frac_dividend", dividend=10.5, divisor=3.0, expected=3.5, msg="Fractional dividend"
    ),
    DivideTest("frac_divisor", dividend=10.0, divisor=2.5, expected=4.0, msg="Fractional divisor"),
    DivideTest("both_frac", dividend=10.5, divisor=2.5, expected=4.2, msg="Both fractional"),
    DivideTest("one_div_two", dividend=1, divisor=2, expected=0.5, msg="1/2 → 0.5"),
    DivideTest("one_div_ten", dividend=1, divisor=10, expected=0.1, msg="1/10 → 0.1"),
]

# --- Identity and self-division ---
IDENTITY_TESTS: list[DivideTest] = [
    DivideTest("div_by_one_int", dividend=42, divisor=1, expected=42.0, msg="x / 1 → x as double"),
    DivideTest(
        "div_by_one_double", dividend=42.5, divisor=1.0, expected=42.5, msg="double / 1.0 → same"
    ),
    DivideTest("self_div_int", dividend=7, divisor=7, expected=1.0, msg="x / x → 1.0"),
    DivideTest(
        "self_div_decimal",
        dividend=Decimal128("7"),
        divisor=Decimal128("7"),
        expected=Decimal128("1"),
        msg="decimal / same → 1",
    ),
    DivideTest("one_div_one", dividend=1, divisor=1, expected=1.0, msg="1 / 1 → 1.0"),
]

ALL_TESTS = TYPE_COMBINATION_TESTS + SIGN_TESTS + FRACTIONAL_TESTS + IDENTITY_TESTS
TYPE_TESTS = [t for t in ALL_TESTS if t.expected_type is not None]


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_divide(collection, test):
    """Test $divide operator core behavior."""
    result = execute_expression_with_insert(
        collection,
        {"$divide": ["$dividend", "$divisor"]},
        {"dividend": test.dividend, "divisor": test.divisor},
    )
    assertExprResult(result, test.error_code or test.expected, msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(TYPE_TESTS))
def test_divide_return_type(collection, test):
    """Test $divide returns correct BSON type."""
    result = execute_expression_with_insert(
        collection,
        {"$type": {"$divide": ["$dividend", "$divisor"]}},
        {"dividend": test.dividend, "divisor": test.divisor},
    )
    assertExprResult(result, test.expected_type, msg=test.msg)
