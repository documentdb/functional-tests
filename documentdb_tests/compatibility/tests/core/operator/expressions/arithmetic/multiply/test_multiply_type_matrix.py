"""
Numeric type matrix tests for $multiply expression.

Covers $multiply across every same-type and cross-type pairing of the four
numeric BSON types (int32, int64, double, decimal128), plus a three-type mix.
"""

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
        "same_type_int32",
        expression={"$multiply": [2, 3]},
        expected=6,
        msg="Should handle same type int32",
    ),
    ExpressionTestCase(
        "same_type_int64",
        expression={"$multiply": [Int64(10), Int64(20)]},
        expected=Int64(200),
        msg="Should handle same type int64",
    ),
    ExpressionTestCase(
        "same_type_double",
        expression={"$multiply": [1.5, 2.0]},
        expected=3.0,
        msg="Should handle same type double",
    ),
    ExpressionTestCase(
        "same_type_decimal",
        expression={"$multiply": [Decimal128("10.5"), Decimal128("2")]},
        expected=Decimal128("21.0"),
        msg="Should compute $multiply of decimal values",
    ),
    ExpressionTestCase(
        "int32_int64",
        expression={"$multiply": [2, Int64(20)]},
        expected=Int64(40),
        msg="Should handle int32 int64",
    ),
    ExpressionTestCase(
        "int32_double",
        expression={"$multiply": [2, 2.5]},
        expected=5.0,
        msg="Should handle int32 double",
    ),
    ExpressionTestCase(
        "int32_decimal",
        expression={"$multiply": [2, Decimal128("2.5")]},
        expected=Decimal128("5.0"),
        msg="Should handle int32 decimal",
    ),
    ExpressionTestCase(
        "int64_double",
        expression={"$multiply": [Int64(10), 2.5]},
        expected=25.0,
        msg="Should handle int64 double",
    ),
    ExpressionTestCase(
        "int64_decimal",
        expression={"$multiply": [Int64(10), Decimal128("2.5")]},
        expected=Decimal128("25.0"),
        msg="Should handle int64 decimal",
    ),
    ExpressionTestCase(
        "double_decimal",
        expression={"$multiply": [1.5, Decimal128("2.0")]},
        expected=Decimal128("3.000000000000000"),
        msg="Should handle double decimal",
    ),
    ExpressionTestCase(
        "three_mixed_types",
        expression={"$multiply": [Decimal128("2"), 1.5, Int64(3)]},
        expected=Decimal128("9.00000000000000"),
        msg="Should return correct result for three mixed types",
    ),
]


MULTIPLY_FIELD_REF_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "same_type_int32",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": 2, "val1": 3},
        expected=6,
        msg="Should handle same type int32",
    ),
    ExpressionTestCase(
        "same_type_int64",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": Int64(10), "val1": Int64(20)},
        expected=Int64(200),
        msg="Should handle same type int64",
    ),
    ExpressionTestCase(
        "same_type_double",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": 1.5, "val1": 2.0},
        expected=3.0,
        msg="Should handle same type double",
    ),
    ExpressionTestCase(
        "same_type_decimal",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": Decimal128("10.5"), "val1": Decimal128("2")},
        expected=Decimal128("21.0"),
        msg="Should compute $multiply of decimal values",
    ),
    ExpressionTestCase(
        "int32_int64",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": 2, "val1": Int64(20)},
        expected=Int64(40),
        msg="Should handle int32 int64",
    ),
    ExpressionTestCase(
        "int32_double",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": 2, "val1": 2.5},
        expected=5.0,
        msg="Should handle int32 double",
    ),
    ExpressionTestCase(
        "int32_decimal",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": 2, "val1": Decimal128("2.5")},
        expected=Decimal128("5.0"),
        msg="Should handle int32 decimal",
    ),
    ExpressionTestCase(
        "int64_double",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": Int64(10), "val1": 2.5},
        expected=25.0,
        msg="Should handle int64 double",
    ),
    ExpressionTestCase(
        "int64_decimal",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": Int64(10), "val1": Decimal128("2.5")},
        expected=Decimal128("25.0"),
        msg="Should handle int64 decimal",
    ),
    ExpressionTestCase(
        "double_decimal",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": 1.5, "val1": Decimal128("2.0")},
        expected=Decimal128("3.000000000000000"),
        msg="Should handle double decimal",
    ),
    ExpressionTestCase(
        "three_mixed_types",
        expression={"$multiply": ["$val0", "$val1", "$val2"]},
        doc={"val0": Decimal128("2"), "val1": 1.5, "val2": Int64(3)},
        expected=Decimal128("9.00000000000000"),
        msg="Should return correct result for three mixed types",
    ),
    ExpressionTestCase(
        "same_type_int32_mixed",
        expression={"$multiply": ["$val0", 3]},
        doc={"val0": 2},
        expected=6,
        msg="Should handle same type int32",
    ),
    ExpressionTestCase(
        "same_type_int64_mixed",
        expression={"$multiply": ["$val0", Int64(20)]},
        doc={"val0": Int64(10)},
        expected=Int64(200),
        msg="Should handle same type int64",
    ),
    ExpressionTestCase(
        "same_type_double_mixed",
        expression={"$multiply": ["$val0", 2.0]},
        doc={"val0": 1.5},
        expected=3.0,
        msg="Should handle same type double",
    ),
    ExpressionTestCase(
        "same_type_decimal_mixed",
        expression={"$multiply": ["$val0", Decimal128("2")]},
        doc={"val0": Decimal128("10.5")},
        expected=Decimal128("21.0"),
        msg="Should compute $multiply of decimal values",
    ),
    ExpressionTestCase(
        "int32_int64_mixed",
        expression={"$multiply": ["$val0", Int64(20)]},
        doc={"val0": 2},
        expected=Int64(40),
        msg="Should handle int32 int64",
    ),
    ExpressionTestCase(
        "int32_double_mixed",
        expression={"$multiply": ["$val0", 2.5]},
        doc={"val0": 2},
        expected=5.0,
        msg="Should handle int32 double",
    ),
    ExpressionTestCase(
        "int32_decimal_mixed",
        expression={"$multiply": ["$val0", Decimal128("2.5")]},
        doc={"val0": 2},
        expected=Decimal128("5.0"),
        msg="Should handle int32 decimal",
    ),
    ExpressionTestCase(
        "int64_double_mixed",
        expression={"$multiply": ["$val0", 2.5]},
        doc={"val0": Int64(10)},
        expected=25.0,
        msg="Should handle int64 double",
    ),
    ExpressionTestCase(
        "int64_decimal_mixed",
        expression={"$multiply": ["$val0", Decimal128("2.5")]},
        doc={"val0": Int64(10)},
        expected=Decimal128("25.0"),
        msg="Should handle int64 decimal",
    ),
    ExpressionTestCase(
        "double_decimal_mixed",
        expression={"$multiply": ["$val0", Decimal128("2.0")]},
        doc={"val0": 1.5},
        expected=Decimal128("3.000000000000000"),
        msg="Should handle double decimal",
    ),
    ExpressionTestCase(
        "three_mixed_types_mixed",
        expression={"$multiply": ["$val0", 1.5, Int64(3)]},
        doc={"val0": Decimal128("2")},
        expected=Decimal128("9.00000000000000"),
        msg="Should return correct result for three mixed types",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MULTIPLY_LITERAL_TESTS))
def test_multiply_literal(collection, test):
    """Test $multiply from literals"""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(MULTIPLY_FIELD_REF_TESTS))
def test_multiply_field_ref(collection, test):
    """Test $multiply from documents, using all-field-reference and mixed
    literal/field-reference operand forms."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
