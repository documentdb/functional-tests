import pytest
from bson import (
    Decimal128,
    Int64,
)

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

MULTIPLY_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "multiple_int32",
        expression={"$multiply": [2, 3, 4]},
        expected=24,
        msg="Should handle multiple int32",
    ),
    ExpressionTestCase(
        "multiple_int64",
        expression={"$multiply": [Int64(2), Int64(3), Int64(4)]},
        expected=Int64(24),
        msg="Should handle multiple int64",
    ),
    ExpressionTestCase(
        "multiple_double",
        expression={"$multiply": [1.5, 2.0, 3.0]},
        expected=pytest.approx(9.0),
        msg="Should handle multiple double",
    ),
    ExpressionTestCase(
        "five_operands",
        expression={"$multiply": [1, 2, 3, 4, 5]},
        expected=120,
        msg="Should return correct result for five operands",
    ),
    ExpressionTestCase(
        "ten_operands",
        expression={"$multiply": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]},
        expected=3628800,
        msg="Should return correct result for ten operands",
    ),
    ExpressionTestCase(
        "multiple_decimal",
        expression={"$multiply": [Decimal128("2"), Decimal128("3"), Decimal128("4")]},
        expected=Decimal128("24"),
        msg="Should return correct result for multiple decimal",
    ),
    ExpressionTestCase(
        "empty",
        expression={"$multiply": []},
        expected=1,
        msg="Should return correct result for empty",
    ),
    ExpressionTestCase(
        "single_int32",
        expression={"$multiply": [5]},
        expected=5,
        msg="Should handle single int32",
    ),
    ExpressionTestCase(
        "non_array_single_operand",
        expression={"$multiply": 5},
        expected=5,
        msg="Should handle non-array single operand shorthand",
    ),
    ExpressionTestCase(
        "single_int64",
        expression={"$multiply": [Int64(10)]},
        expected=Int64(10),
        msg="Should handle single int64",
    ),
    ExpressionTestCase(
        "single_double",
        expression={"$multiply": [2.5]},
        expected=2.5,
        msg="Should handle single double",
    ),
    ExpressionTestCase(
        "single_decimal",
        expression={"$multiply": [Decimal128("5")]},
        expected=Decimal128("5"),
        msg="Should return correct result for single decimal",
    ),
    ExpressionTestCase(
        "fifteen_operands",
        expression={"$multiply": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]},
        expected=Int64(1307674368000),
        msg="Should return correct result for fifteen operands",
    ),
    ExpressionTestCase(
        "twenty_operands",
        expression={"$multiply": [2] * 20},
        expected=1048576,
        msg="Should return correct result for twenty operands",
    ),
    ExpressionTestCase(
        "self_nesting",
        expression={"$multiply": [{"$multiply": [2, 3]}, 4]},
        expected=24,
        msg="Should handle $multiply nested inside $multiply",
    ),
]


MULTIPLY_INSERT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "multiple_int32",
        expression={"$multiply": ["$val0", "$val1", "$val2"]},
        doc={"val0": 2, "val1": 3, "val2": 4},
        expected=24,
        msg="Should handle multiple int32",
    ),
    ExpressionTestCase(
        "multiple_int64",
        expression={"$multiply": ["$val0", "$val1", "$val2"]},
        doc={"val0": Int64(2), "val1": Int64(3), "val2": Int64(4)},
        expected=Int64(24),
        msg="Should handle multiple int64",
    ),
    ExpressionTestCase(
        "multiple_double",
        expression={"$multiply": ["$val0", "$val1", "$val2"]},
        doc={"val0": 1.5, "val1": 2.0, "val2": 3.0},
        expected=pytest.approx(9.0),
        msg="Should handle multiple double",
    ),
    ExpressionTestCase(
        "five_operands",
        expression={"$multiply": ["$val0", "$val1", "$val2", "$val3", "$val4"]},
        doc={"val0": 1, "val1": 2, "val2": 3, "val3": 4, "val4": 5},
        expected=120,
        msg="Should return correct result for five operands",
    ),
    ExpressionTestCase(
        "ten_operands",
        expression={
            "$multiply": [
                "$val0",
                "$val1",
                "$val2",
                "$val3",
                "$val4",
                "$val5",
                "$val6",
                "$val7",
                "$val8",
                "$val9",
            ]
        },
        doc={
            "val0": 1,
            "val1": 2,
            "val2": 3,
            "val3": 4,
            "val4": 5,
            "val5": 6,
            "val6": 7,
            "val7": 8,
            "val8": 9,
            "val9": 10,
        },
        expected=3628800,
        msg="Should return correct result for ten operands",
    ),
    ExpressionTestCase(
        "multiple_decimal",
        expression={"$multiply": ["$val0", "$val1", "$val2"]},
        doc={"val0": Decimal128("2"), "val1": Decimal128("3"), "val2": Decimal128("4")},
        expected=Decimal128("24"),
        msg="Should return correct result for multiple decimal",
    ),
    ExpressionTestCase(
        "empty",
        expression={"$multiply": []},
        doc={},
        expected=1,
        msg="Should return correct result for empty",
    ),
    ExpressionTestCase(
        "single_int32",
        expression={"$multiply": ["$val0"]},
        doc={"val0": 5},
        expected=5,
        msg="Should handle single int32",
    ),
    ExpressionTestCase(
        "single_int64",
        expression={"$multiply": ["$val0"]},
        doc={"val0": Int64(10)},
        expected=Int64(10),
        msg="Should handle single int64",
    ),
    ExpressionTestCase(
        "single_double",
        expression={"$multiply": ["$val0"]},
        doc={"val0": 2.5},
        expected=2.5,
        msg="Should handle single double",
    ),
    ExpressionTestCase(
        "single_decimal",
        expression={"$multiply": ["$val0"]},
        doc={"val0": Decimal128("5")},
        expected=Decimal128("5"),
        msg="Should return correct result for single decimal",
    ),
    ExpressionTestCase(
        "fifteen_operands",
        expression={
            "$multiply": [
                "$val0",
                "$val1",
                "$val2",
                "$val3",
                "$val4",
                "$val5",
                "$val6",
                "$val7",
                "$val8",
                "$val9",
                "$val10",
                "$val11",
                "$val12",
                "$val13",
                "$val14",
            ]
        },
        doc={
            "val0": 1,
            "val1": 2,
            "val2": 3,
            "val3": 4,
            "val4": 5,
            "val5": 6,
            "val6": 7,
            "val7": 8,
            "val8": 9,
            "val9": 10,
            "val10": 11,
            "val11": 12,
            "val12": 13,
            "val13": 14,
            "val14": 15,
        },
        expected=Int64(1307674368000),
        msg="Should return correct result for fifteen operands",
    ),
    ExpressionTestCase(
        "twenty_operands",
        expression={
            "$multiply": [
                "$val0",
                "$val1",
                "$val2",
                "$val3",
                "$val4",
                "$val5",
                "$val6",
                "$val7",
                "$val8",
                "$val9",
                "$val10",
                "$val11",
                "$val12",
                "$val13",
                "$val14",
                "$val15",
                "$val16",
                "$val17",
                "$val18",
                "$val19",
            ]
        },
        doc={
            "val0": 2,
            "val1": 2,
            "val2": 2,
            "val3": 2,
            "val4": 2,
            "val5": 2,
            "val6": 2,
            "val7": 2,
            "val8": 2,
            "val9": 2,
            "val10": 2,
            "val11": 2,
            "val12": 2,
            "val13": 2,
            "val14": 2,
            "val15": 2,
            "val16": 2,
            "val17": 2,
            "val18": 2,
            "val19": 2,
        },
        expected=1048576,
        msg="Should return correct result for twenty operands",
    ),
    ExpressionTestCase(
        "self_nesting",
        expression={"$multiply": [{"$multiply": ["$val0", "$val1"]}, "$val2"]},
        doc={"val0": 2, "val1": 3, "val2": 4},
        expected=24,
        msg="Should handle $multiply nested inside $multiply",
    ),
]


MULTIPLY_MIXED_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "multiple_int32",
        expression={"$multiply": ["$val0", 3, 4]},
        doc={"val0": 2},
        expected=24,
        msg="Should handle multiple int32",
    ),
    ExpressionTestCase(
        "multiple_int64",
        expression={"$multiply": ["$val0", Int64(3), Int64(4)]},
        doc={"val0": Int64(2)},
        expected=Int64(24),
        msg="Should handle multiple int64",
    ),
    ExpressionTestCase(
        "multiple_double",
        expression={"$multiply": ["$val0", 2.0, 3.0]},
        doc={"val0": 1.5},
        expected=pytest.approx(9.0),
        msg="Should handle multiple double",
    ),
    ExpressionTestCase(
        "five_operands",
        expression={"$multiply": ["$val0", 2, 3, 4, 5]},
        doc={"val0": 1},
        expected=120,
        msg="Should return correct result for five operands",
    ),
    ExpressionTestCase(
        "ten_operands",
        expression={"$multiply": ["$val0", 2, 3, 4, 5, 6, 7, 8, 9, 10]},
        doc={"val0": 1},
        expected=3628800,
        msg="Should return correct result for ten operands",
    ),
    ExpressionTestCase(
        "multiple_decimal",
        expression={"$multiply": ["$val0", Decimal128("3"), Decimal128("4")]},
        doc={"val0": Decimal128("2")},
        expected=Decimal128("24"),
        msg="Should return correct result for multiple decimal",
    ),
    ExpressionTestCase(
        "fifteen_operands",
        expression={"$multiply": ["$val0", 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]},
        doc={"val0": 1},
        expected=Int64(1307674368000),
        msg="Should return correct result for fifteen operands",
    ),
    ExpressionTestCase(
        "twenty_operands",
        expression={
            "$multiply": ["$val0", 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        },
        doc={"val0": 2},
        expected=1048576,
        msg="Should return correct result for twenty operands",
    ),
    ExpressionTestCase(
        "self_nesting",
        expression={"$multiply": [{"$multiply": ["$val0", 3]}, 4]},
        doc={"val0": 2},
        expected=24,
        msg="Should handle $multiply nested inside $multiply",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MULTIPLY_LITERAL_TESTS))
def test_multiply_literal(collection, test):
    """Test $multiply from literals"""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(MULTIPLY_INSERT_TESTS))
def test_multiply_insert(collection, test):
    """Test $multiply from documents"""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(MULTIPLY_MIXED_TESTS))
def test_multiply_mixed(collection, test):
    """Test $multiply mixed literal and document"""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
