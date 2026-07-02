from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Same Type]: $subtract returns the correct difference for each numeric type.
SUBTRACT_SAME_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "same_type_int32",
        doc={"a": 10, "b": 3},
        expression={"$subtract": ["$a", "$b"]},
        expected=7,
        msg="Should subtract int32 values",
    ),
    ExpressionTestCase(
        "same_type_int64",
        doc={"a": Int64(20), "b": Int64(5)},
        expression={"$subtract": ["$a", "$b"]},
        expected=Int64(15),
        msg="Should subtract int64 values",
    ),
    ExpressionTestCase(
        "same_type_double",
        doc={"a": 10.5, "b": 2.5},
        expression={"$subtract": ["$a", "$b"]},
        expected=8.0,
        msg="Should subtract double values",
    ),
    ExpressionTestCase(
        "same_type_decimal",
        doc={"a": Decimal128("20.5"), "b": Decimal128("10.5")},
        expression={"$subtract": ["$a", "$b"]},
        expected=Decimal128("10.0"),
        msg="Should subtract decimal128 values",
    ),
]

# Property [Mixed Type]: $subtract promotes mixed numeric types per the arithmetic rules.
SUBTRACT_MIXED_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_int64",
        doc={"a": 10, "b": Int64(3)},
        expression={"$subtract": ["$a", "$b"]},
        expected=Int64(7),
        msg="Should subtract int64 from int32",
    ),
    ExpressionTestCase(
        "int32_double",
        doc={"a": 10, "b": 2.5},
        expression={"$subtract": ["$a", "$b"]},
        expected=7.5,
        msg="Should subtract double from int32",
    ),
    ExpressionTestCase(
        "int32_decimal",
        doc={"a": 10, "b": Decimal128("2.5")},
        expression={"$subtract": ["$a", "$b"]},
        expected=Decimal128("7.5"),
        msg="Should subtract decimal128 from int32",
    ),
    ExpressionTestCase(
        "int64_double",
        doc={"a": Int64(20), "b": 5.5},
        expression={"$subtract": ["$a", "$b"]},
        expected=14.5,
        msg="Should subtract double from int64",
    ),
    ExpressionTestCase(
        "int64_decimal",
        doc={"a": Int64(20), "b": Decimal128("5.5")},
        expression={"$subtract": ["$a", "$b"]},
        expected=Decimal128("14.5"),
        msg="Should subtract decimal128 from int64",
    ),
    ExpressionTestCase(
        "double_decimal",
        doc={"a": 10.5, "b": Decimal128("2.5")},
        expression={"$subtract": ["$a", "$b"]},
        expected=Decimal128("8.0000000000000"),
        msg="Should subtract decimal128 from double",
    ),
]

# Property [Sign and Zero]: $subtract handles positive, negative, and zero operands.
SUBTRACT_SIGN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "positive_positive",
        doc={},
        expression={"$subtract": [10, 3]},
        expected=7,
        msg="Should subtract two positive values",
    ),
    ExpressionTestCase(
        "negative_positive",
        doc={},
        expression={"$subtract": [-10, 3]},
        expected=-13,
        msg="Should subtract positive from negative",
    ),
    ExpressionTestCase(
        "positive_negative",
        doc={},
        expression={"$subtract": [10, -3]},
        expected=13,
        msg="Should subtract negative from positive",
    ),
    ExpressionTestCase(
        "both_negative",
        doc={},
        expression={"$subtract": [-10, -3]},
        expected=-7,
        msg="Should subtract two negative values",
    ),
    ExpressionTestCase(
        "zero_minuend",
        doc={},
        expression={"$subtract": [0, 5]},
        expected=-5,
        msg="Should subtract from zero",
    ),
    ExpressionTestCase(
        "zero_subtrahend",
        doc={},
        expression={"$subtract": [5, 0]},
        expected=5,
        msg="Should subtract zero",
    ),
    ExpressionTestCase(
        "zeros",
        doc={},
        expression={"$subtract": [0, 0]},
        expected=0,
        msg="Should subtract zero from zero",
    ),
    ExpressionTestCase(
        "zero_negative_zero",
        doc={},
        expression={"$subtract": [0, -0.0]},
        expected=0.0,
        msg="Should subtract negative zero from zero",
    ),
    ExpressionTestCase(
        "negative_zero_zero",
        doc={},
        expression={"$subtract": [-0.0, 0]},
        expected=-0.0,
        msg="Should subtract zero from negative zero",
    ),
    ExpressionTestCase(
        "result_negative",
        doc={},
        expression={"$subtract": [5, 10]},
        expected=-5,
        msg="Should produce a negative result",
    ),
    ExpressionTestCase(
        "result_negative_double",
        doc={},
        expression={"$subtract": [5.5, 10]},
        expected=-4.5,
        msg="Should produce a negative double result",
    ),
]

# Property [Precision]: $subtract preserves decimal128 precision.
SUBTRACT_PRECISION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "decimal_precision",
        doc={},
        expression={"$subtract": [Decimal128("10.5"), Decimal128("2.5")]},
        expected=Decimal128("8.0"),
        msg="Should preserve decimal128 precision",
    ),
    ExpressionTestCase(
        "decimal_precision_small",
        doc={},
        expression={"$subtract": [Decimal128("0.3"), Decimal128("0.1")]},
        expected=Decimal128("0.2"),
        msg="Should preserve decimal128 precision for small values",
    ),
    ExpressionTestCase(
        "decimal_large_precision",
        doc={},
        expression={
            "$subtract": [
                Decimal128("1000000000000000000000000000000000"),
                Decimal128("1"),
            ]
        },
        expected=Decimal128("999999999999999999999999999999999"),
        msg="Should preserve decimal128 precision for large values",
    ),
]

SUBTRACT_BASIC_TESTS = (
    SUBTRACT_SAME_TYPE_TESTS
    + SUBTRACT_MIXED_TYPE_TESTS
    + SUBTRACT_SIGN_TESTS
    + SUBTRACT_PRECISION_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SUBTRACT_BASIC_TESTS))
def test_subtract_basic(collection, test_case: ExpressionTestCase):
    """Test $subtract basic numeric cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
