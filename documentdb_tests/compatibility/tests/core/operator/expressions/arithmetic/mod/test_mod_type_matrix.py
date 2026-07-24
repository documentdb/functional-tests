"""
Numeric type matrix tests for $mod expression.

Covers $mod across every same-type and cross-type pairing of the four
numeric BSON types (int32, int64, double, decimal128).
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

MOD_TYPE_MATRIX_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "same_type_int32",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": 10, "divisor": 3},
        expected=1,
        msg="Should compute modulo of int32 values",
    ),
    ExpressionTestCase(
        "same_type_int64",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": Int64(10), "divisor": Int64(3)},
        expected=Int64(1),
        msg="Should compute modulo of int64 values",
    ),
    ExpressionTestCase(
        "same_type_double",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": 10.5, "divisor": 3.0},
        expected=1.5,
        msg="Should compute modulo of double values",
    ),
    ExpressionTestCase(
        "same_type_decimal",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": Decimal128("10.5"), "divisor": Decimal128("3")},
        expected=Decimal128("1.5"),
        msg="Should compute modulo of decimal128 values",
    ),
    ExpressionTestCase(
        "int32_int64",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": 10, "divisor": Int64(3)},
        expected=Int64(1),
        msg="Should compute modulo of int32 by int64",
    ),
    ExpressionTestCase(
        "int32_double",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": 10, "divisor": 3.0},
        expected=1.0,
        msg="Should compute modulo of int32 by double",
    ),
    ExpressionTestCase(
        "int32_decimal",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": 10, "divisor": Decimal128("3")},
        expected=Decimal128("1"),
        msg="Should compute modulo of int32 by decimal128",
    ),
    ExpressionTestCase(
        "int64_double",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": Int64(10), "divisor": 3.0},
        expected=1.0,
        msg="Should compute modulo of int64 by double",
    ),
    ExpressionTestCase(
        "int64_decimal",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": Int64(10), "divisor": Decimal128("3")},
        expected=Decimal128("1"),
        msg="Should compute modulo of int64 by decimal128",
    ),
    ExpressionTestCase(
        "double_decimal",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": 10.5, "divisor": Decimal128("3")},
        expected=Decimal128("1.5000000000000"),
        msg="Should compute modulo of double by decimal128",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MOD_TYPE_MATRIX_TESTS))
def test_mod_literal(collection, test):
    """Test $mod from literals"""
    result = execute_expression(collection, {"$mod": [test.doc["dividend"], test.doc["divisor"]]})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(MOD_TYPE_MATRIX_TESTS))
def test_mod_insert(collection, test):
    """Test $mod from documents"""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
