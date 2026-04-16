from __future__ import annotations

import math

import pytest
from bson import Decimal128, MinKey

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [NaN Behavior]: NaN compares less than all numeric values
# including negative infinity.
MAX_NAN_TESTS: list[ExpressionTestCase] = [
    # NaN as sole operand is returned.
    ExpressionTestCase(
        "nan_float_sole",
        expression={"$max": ["$a"]},
        doc={"a": FLOAT_NAN},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="$max should return NaN when float NaN is the sole operand",
    ),
    ExpressionTestCase(
        "nan_decimal128_sole",
        expression={"$max": ["$a"]},
        doc={"a": DECIMAL128_NAN},
        expected=DECIMAL128_NAN,
        msg="$max should return Decimal128 NaN when it is the sole operand",
    ),
    # Decimal128 -NaN is preserved as -NaN.
    ExpressionTestCase(
        "nan_decimal128_neg_nan_preserved",
        expression={"$max": ["$a"]},
        doc={"a": DECIMAL128_NEGATIVE_NAN},
        expected=DECIMAL128_NEGATIVE_NAN,
        msg="$max should return Decimal128 -NaN when it is the sole operand",
    ),
    # NaN alongside numeric values: non-NaN maximum is returned.
    ExpressionTestCase(
        "nan_float_with_ints",
        expression={"$max": ["$a", "$b", "$c", "$d"]},
        doc={"a": 1, "b": 2, "c": 3, "d": FLOAT_NAN},
        expected=3,
        msg="$max should return non-NaN maximum when float NaN is among integers",
    ),
    ExpressionTestCase(
        "nan_decimal128_with_value",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Decimal128("1"), "b": DECIMAL128_NAN},
        expected=Decimal128("1"),
        msg="$max should return non-NaN maximum when Decimal128 NaN is present",
    ),
    ExpressionTestCase(
        "nan_decimal128_neg_nan_with_value",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DECIMAL128_NEGATIVE_NAN, "b": Decimal128("5")},
        expected=Decimal128("5"),
        msg="$max should exclude Decimal128 -NaN and return the non-NaN value",
    ),
    # NaN is less than -Infinity.
    ExpressionTestCase(
        "nan_float_vs_neg_inf",
        expression={"$max": ["$a", "$b"]},
        doc={"a": FLOAT_NAN, "b": FLOAT_NEGATIVE_INFINITY},
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$max should pick -Infinity over float NaN",
    ),
    ExpressionTestCase(
        "nan_float_vs_neg_inf_reversed",
        expression={"$max": ["$a", "$b"]},
        doc={"a": FLOAT_NEGATIVE_INFINITY, "b": FLOAT_NAN},
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$max should pick -Infinity over float NaN regardless of order",
    ),
    ExpressionTestCase(
        "nan_float_vs_decimal128_neg_inf",
        expression={"$max": ["$a", "$b"]},
        doc={"a": FLOAT_NAN, "b": DECIMAL128_NEGATIVE_INFINITY},
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="$max should pick Decimal128 -Infinity over float NaN",
    ),
    ExpressionTestCase(
        "nan_decimal128_vs_float_neg_inf",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DECIMAL128_NAN, "b": FLOAT_NEGATIVE_INFINITY},
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$max should pick float -Infinity over Decimal128 NaN",
    ),
    ExpressionTestCase(
        "nan_decimal128_vs_decimal128_neg_inf",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DECIMAL128_NAN, "b": DECIMAL128_NEGATIVE_INFINITY},
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="$max should pick Decimal128 -Infinity over Decimal128 NaN",
    ),
    # NaN is less than negative numbers.
    ExpressionTestCase(
        "nan_float_vs_negative",
        expression={"$max": ["$a", "$b"]},
        doc={"a": FLOAT_NAN, "b": -1000},
        expected=-1000,
        msg="$max should pick negative number over float NaN",
    ),
    ExpressionTestCase(
        "nan_decimal128_vs_negative",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DECIMAL128_NAN, "b": -1000},
        expected=-1000,
        msg="$max should pick negative number over Decimal128 NaN",
    ),
    # NaN is greater than MinKey (numeric type > MinKey in BSON order).
    ExpressionTestCase(
        "nan_float_vs_minkey",
        expression={"$max": ["$a", "$b"]},
        doc={"a": FLOAT_NAN, "b": MinKey()},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="$max should pick float NaN over MinKey per BSON type order",
    ),
    ExpressionTestCase(
        "nan_minkey_vs_float",
        expression={"$max": ["$a", "$b"]},
        doc={"a": MinKey(), "b": FLOAT_NAN},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="$max should pick float NaN over MinKey regardless of order",
    ),
    ExpressionTestCase(
        "nan_decimal128_vs_minkey",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DECIMAL128_NAN, "b": MinKey()},
        expected=DECIMAL128_NAN,
        msg="$max should pick Decimal128 NaN over MinKey per BSON type order",
    ),
    # NaN as only non-null value (with null).
    ExpressionTestCase(
        "nan_float_only_nonnull",
        expression={"$max": ["$a", "$b"]},
        doc={"a": None, "b": FLOAT_NAN},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="$max should return float NaN when it is the only non-null value",
    ),
    ExpressionTestCase(
        "nan_decimal128_only_nonnull",
        expression={"$max": ["$a", "$b"]},
        doc={"a": None, "b": DECIMAL128_NAN},
        expected=DECIMAL128_NAN,
        msg="$max should return Decimal128 NaN when it is the only non-null value",
    ),
    # Tie-breaking: float NaN vs Decimal128 NaN, first wins.
    ExpressionTestCase(
        "nan_float_vs_decimal128_nan",
        expression={"$max": ["$a", "$b"]},
        doc={"a": FLOAT_NAN, "b": DECIMAL128_NAN},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="$max should return float NaN when it appears before Decimal128 NaN",
    ),
    ExpressionTestCase(
        "nan_decimal128_vs_float_nan",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DECIMAL128_NAN, "b": FLOAT_NAN},
        expected=DECIMAL128_NAN,
        msg="$max should return Decimal128 NaN when it appears before float NaN",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(MAX_NAN_TESTS))
def test_max_nan_cases(collection, test_case: ExpressionTestCase):
    """Test $max NaN behavior cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc or {})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
