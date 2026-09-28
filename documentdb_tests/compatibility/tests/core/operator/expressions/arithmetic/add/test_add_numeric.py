"""Tests for $add numeric operations including same-type and mixed-type addition, multiple
operands, empty/single operands, and sign handling.
"""

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

# Property [Same-Type Addition]: $add of two values of the same numeric type returns a value of
# that type.
ADD_SAME_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "same_type_int32",
        doc={"a": 1, "b": 2},
        expression={"$add": ["$a", "$b"]},
        expected=3,
        msg="$add should add two int32 values",
    ),
    ExpressionTestCase(
        "same_type_int64",
        doc={"a": Int64(10), "b": Int64(20)},
        expression={"$add": ["$a", "$b"]},
        expected=Int64(30),
        msg="$add should add two int64 values",
    ),
    ExpressionTestCase(
        "same_type_double",
        doc={"a": 1.5, "b": 2.5},
        expression={"$add": ["$a", "$b"]},
        expected=4.0,
        msg="$add should add two double values",
    ),
    ExpressionTestCase(
        "same_type_decimal",
        doc={"a": Decimal128("10.5"), "b": Decimal128("20.5")},
        expression={"$add": ["$a", "$b"]},
        expected=Decimal128("31.0"),
        msg="$add should add two decimal128 values",
    ),
]

# Property [Type Promotion]: $add promotes to the wider type when operands have different numeric
# types. Precedence: decimal128 > double > int64 > int32.
ADD_MIXED_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_int64",
        doc={"a": 1, "b": Int64(20)},
        expression={"$add": ["$a", "$b"]},
        expected=Int64(21),
        msg="$add should return int64 when adding int32 and int64",
    ),
    ExpressionTestCase(
        "int32_double",
        doc={"a": 1, "b": 2.5},
        expression={"$add": ["$a", "$b"]},
        expected=3.5,
        msg="$add should return double when adding int32 and double",
    ),
    ExpressionTestCase(
        "int32_decimal",
        doc={"a": 1, "b": Decimal128("2.5")},
        expression={"$add": ["$a", "$b"]},
        expected=Decimal128("3.5"),
        msg="$add should return decimal128 when adding int32 and decimal128",
    ),
    ExpressionTestCase(
        "int64_double",
        doc={"a": Int64(10), "b": 2.5},
        expression={"$add": ["$a", "$b"]},
        expected=12.5,
        msg="$add should return double when adding int64 and double",
    ),
    ExpressionTestCase(
        "int64_decimal",
        doc={"a": Int64(10), "b": Decimal128("2.5")},
        expression={"$add": ["$a", "$b"]},
        expected=Decimal128("12.5"),
        msg="$add should return decimal128 when adding int64 and decimal128",
    ),
    ExpressionTestCase(
        "double_decimal",
        doc={"a": 1.5, "b": Decimal128("2.5")},
        expression={"$add": ["$a", "$b"]},
        expected=pytest.approx(Decimal128("4.00000000000000")),
        msg="$add should return decimal128 when adding double and decimal128",
    ),
    ExpressionTestCase(
        "three_mixed_types",
        doc={"a": Decimal128("1.5"), "b": 2.5, "c": Int64(3)},
        expression={"$add": ["$a", "$b", "$c"]},
        expected=pytest.approx(Decimal128("7.00000000000000")),
        msg="$add should return decimal128 when adding decimal128, double, and int64",
    ),
]

# Property [Multiple Operands]: $add correctly sums three or more operands.
ADD_MULTIPLE_OPERANDS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "multiple_int32",
        doc={"a": 1, "b": 2, "c": 3},
        expression={"$add": ["$a", "$b", "$c"]},
        expected=6,
        msg="$add should add multiple int32 values",
    ),
    ExpressionTestCase(
        "multiple_int64",
        doc={"a": Int64(1), "b": Int64(2), "c": Int64(3)},
        expression={"$add": ["$a", "$b", "$c"]},
        expected=Int64(6),
        msg="$add should add multiple int64 values",
    ),
    ExpressionTestCase(
        "multiple_double",
        doc={"a": 1.1, "b": 2.2, "c": 3.3},
        expression={"$add": ["$a", "$b", "$c"]},
        expected=pytest.approx(6.6),
        msg="$add should add multiple double values",
    ),
    ExpressionTestCase(
        "multiple_decimal",
        doc={
            "a": Decimal128("1"),
            "b": Decimal128("2"),
            "c": Decimal128("3"),
            "d": Decimal128("4"),
        },
        expression={"$add": ["$a", "$b", "$c", "$d"]},
        expected=Decimal128("10"),
        msg="$add should add multiple decimal128 values",
    ),
    ExpressionTestCase(
        "five_operands",
        doc={"a": 1, "b": 2, "c": 3, "d": 4, "e": 5},
        expression={"$add": ["$a", "$b", "$c", "$d", "$e"]},
        expected=15,
        msg="$add should correctly sum five int32 operands",
    ),
    ExpressionTestCase(
        "ten_operands",
        doc={
            "a": 1,
            "b": 2,
            "c": 3,
            "d": 4,
            "e": 5,
            "f": 6,
            "g": 7,
            "h": 8,
            "i": 9,
            "j": 10,
        },
        expression={"$add": ["$a", "$b", "$c", "$d", "$e", "$f", "$g", "$h", "$i", "$j"]},
        expected=55,
        msg="$add should correctly sum ten int32 operands",
    ),
]

# Property [Empty and Single Operand]: $add of zero operands returns 0; single operand returns
# that value unchanged.
ADD_SINGLE_AND_EMPTY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "empty",
        doc={},
        expression={"$add": []},
        expected=0,
        msg="$add should return 0 for empty operand list",
    ),
    ExpressionTestCase(
        "single_int32",
        doc={"a": 5},
        expression={"$add": ["$a"]},
        expected=5,
        msg="$add should return the value for a single int32 operand",
    ),
    ExpressionTestCase(
        "single_int64",
        doc={"a": Int64(0)},
        expression={"$add": ["$a"]},
        expected=Int64(0),
        msg="$add should return the value for a single int64 operand",
    ),
    ExpressionTestCase(
        "single_double",
        doc={"a": 0.0},
        expression={"$add": ["$a"]},
        expected=0.0,
        msg="$add should return the value for a single double operand",
    ),
    ExpressionTestCase(
        "single_decimal",
        doc={"a": Decimal128("0")},
        expression={"$add": ["$a"]},
        expected=Decimal128("0"),
        msg="$add should return the value for a single decimal128 operand",
    ),
]

# Property [Sign Handling]: $add handles negative values and zero correctly.
ADD_SIGN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "negative_positive",
        doc={"a": -5, "b": 3},
        expression={"$add": ["$a", "$b"]},
        expected=-2,
        msg="$add should add a negative and a positive int32 value",
    ),
    ExpressionTestCase(
        "both_negative",
        doc={"a": -10, "b": -20},
        expression={"$add": ["$a", "$b"]},
        expected=-30,
        msg="$add should add two negative int32 values",
    ),
    ExpressionTestCase(
        "zeros",
        doc={"a": 0, "b": 0},
        expression={"$add": ["$a", "$b"]},
        expected=0,
        msg="$add should return 0 when adding two int32 zeros",
    ),
    ExpressionTestCase(
        "zero_negative_zero",
        doc={"a": 0, "b": -0.0},
        expression={"$add": ["$a", "$b"]},
        expected=0.0,
        msg="$add should return 0.0 when adding int32 zero and negative zero double",
    ),
    ExpressionTestCase(
        "sum_to_zero",
        doc={"a": 1, "b": 0, "c": -1},
        expression={"$add": ["$a", "$b", "$c"]},
        expected=0,
        msg="$add should return 0 when operands sum to zero",
    ),
]

ADD_NUMERIC_ALL_TESTS = (
    ADD_SAME_TYPE_TESTS
    + ADD_MIXED_TYPE_TESTS
    + ADD_MULTIPLE_OPERANDS_TESTS
    + ADD_SINGLE_AND_EMPTY_TESTS
    + ADD_SIGN_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(ADD_NUMERIC_ALL_TESTS))
def test_add_numeric(collection, test_case: ExpressionTestCase):
    """Test $add numeric type combinations, multiple operands, and sign handling."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
