"""Tests for $add return type promotion rules across numeric and date operand combinations."""

from datetime import datetime, timezone

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

# Property [Return Type]: $add follows numeric type promotion rules to determine the result type.
# Precedence: decimal128 > double > int64 > int32. Date + numeric always returns date.
ADD_RETURN_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "return_type_int_int",
        doc={"a": 1, "b": 2},
        expression={"$type": {"$add": ["$a", "$b"]}},
        expected="int",
        msg="$add should return int type when adding two int32 values",
    ),
    ExpressionTestCase(
        "return_type_int_long",
        doc={"a": 1, "b": Int64(2)},
        expression={"$type": {"$add": ["$a", "$b"]}},
        expected="long",
        msg="$add should return long type when adding int32 and int64",
    ),
    ExpressionTestCase(
        "return_type_int_double",
        doc={"a": 1, "b": 2.0},
        expression={"$type": {"$add": ["$a", "$b"]}},
        expected="double",
        msg="$add should return double type when adding int32 and double",
    ),
    ExpressionTestCase(
        "return_type_int_decimal",
        doc={"a": 1, "b": Decimal128("2")},
        expression={"$type": {"$add": ["$a", "$b"]}},
        expected="decimal",
        msg="$add should return decimal type when adding int32 and decimal128",
    ),
    ExpressionTestCase(
        "return_type_long_long",
        doc={"a": Int64(1), "b": Int64(2)},
        expression={"$type": {"$add": ["$a", "$b"]}},
        expected="long",
        msg="$add should return long type when adding two int64 values",
    ),
    ExpressionTestCase(
        "return_type_long_double",
        doc={"a": Int64(1), "b": 2.0},
        expression={"$type": {"$add": ["$a", "$b"]}},
        expected="double",
        msg="$add should return double type when adding int64 and double",
    ),
    ExpressionTestCase(
        "return_type_long_decimal",
        doc={"a": Int64(1), "b": Decimal128("2")},
        expression={"$type": {"$add": ["$a", "$b"]}},
        expected="decimal",
        msg="$add should return decimal type when adding int64 and decimal128",
    ),
    ExpressionTestCase(
        "return_type_double_double",
        doc={"a": 1.0, "b": 2.0},
        expression={"$type": {"$add": ["$a", "$b"]}},
        expected="double",
        msg="$add should return double type when adding two double values",
    ),
    ExpressionTestCase(
        "return_type_double_decimal",
        doc={"a": 1.0, "b": Decimal128("2")},
        expression={"$type": {"$add": ["$a", "$b"]}},
        expected="decimal",
        msg="$add should return decimal type when adding double and decimal128",
    ),
    ExpressionTestCase(
        "return_type_decimal_decimal",
        doc={"a": Decimal128("1"), "b": Decimal128("2")},
        expression={"$type": {"$add": ["$a", "$b"]}},
        expected="decimal",
        msg="$add should return decimal type when adding two decimal128 values",
    ),
    ExpressionTestCase(
        "return_type_date_int",
        doc={"a": datetime(2026, 1, 1, tzinfo=timezone.utc), "b": 1000},
        expression={"$type": {"$add": ["$a", "$b"]}},
        expected="date",
        msg="$add should return date type when adding a date and an int32",
    ),
    ExpressionTestCase(
        "return_type_empty",
        doc={},
        expression={"$type": {"$add": []}},
        expected="int",
        msg="$add should return int type for an empty operand list",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(ADD_RETURN_TYPE_TESTS))
def test_add_return_type(collection, test_case: ExpressionTestCase):
    """Test $add return type promotion rules for all numeric type combinations."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
