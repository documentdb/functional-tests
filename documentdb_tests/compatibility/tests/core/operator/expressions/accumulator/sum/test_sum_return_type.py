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
from documentdb_tests.framework.test_constants import (
    INT32_MAX,
    INT64_MAX,
)

# Property [Return Type]: $sum returns the narrowest type that can represent
# the result: int32, int64, double, or Decimal128.
SUM_RETURN_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "rtype_all_int32",
        expression={"$type": {"$sum": ["$a", "$b"]}},
        doc={"a": 1, "b": 2},
        expected="int",
        msg="$sum of int32 values should return int",
    ),
    ExpressionTestCase(
        "rtype_all_int64",
        expression={"$type": {"$sum": ["$a", "$b"]}},
        doc={"a": Int64(1), "b": Int64(2)},
        expected="long",
        msg="$sum of int64 values should return long",
    ),
    ExpressionTestCase(
        "rtype_all_double",
        expression={"$type": {"$sum": ["$a", "$b"]}},
        doc={"a": 1.0, "b": 2.0},
        expected="double",
        msg="$sum of double values should return double",
    ),
    ExpressionTestCase(
        "rtype_all_decimal128",
        expression={"$type": {"$sum": ["$a", "$b"]}},
        doc={"a": Decimal128("1"), "b": Decimal128("2")},
        expected="decimal",
        msg="$sum of Decimal128 values should return decimal",
    ),
    ExpressionTestCase(
        "rtype_int32_int64",
        expression={"$type": {"$sum": ["$a", "$b"]}},
        doc={"a": 1, "b": Int64(2)},
        expected="long",
        msg="$sum of mixed int32 and int64 should return long",
    ),
    ExpressionTestCase(
        "rtype_int32_double",
        expression={"$type": {"$sum": ["$a", "$b"]}},
        doc={"a": 1, "b": 2.0},
        expected="double",
        msg="$sum of mixed int32 and double should return double",
    ),
    ExpressionTestCase(
        "rtype_int64_double",
        expression={"$type": {"$sum": ["$a", "$b"]}},
        doc={"a": Int64(1), "b": 2.0},
        expected="double",
        msg="$sum of mixed int64 and double should return double",
    ),
    ExpressionTestCase(
        "rtype_int32_decimal128",
        expression={"$type": {"$sum": ["$a", "$b"]}},
        doc={"a": 1, "b": Decimal128("2")},
        expected="decimal",
        msg="$sum of mixed int32 and Decimal128 should return decimal",
    ),
    ExpressionTestCase(
        "rtype_int64_decimal128",
        expression={"$type": {"$sum": ["$a", "$b"]}},
        doc={"a": Int64(1), "b": Decimal128("2")},
        expected="decimal",
        msg="$sum of mixed int64 and Decimal128 should return decimal",
    ),
    ExpressionTestCase(
        "rtype_double_decimal128",
        expression={"$type": {"$sum": ["$a", "$b"]}},
        doc={"a": 1.0, "b": Decimal128("2")},
        expected="decimal",
        msg="$sum of mixed double and Decimal128 should return decimal",
    ),
    ExpressionTestCase(
        "rtype_all_nonnumeric",
        expression={"$type": {"$sum": ["$a", "$b"]}},
        doc={"a": "hello", "b": True},
        expected="int",
        msg="$sum of all non-numeric values should return int (0)",
    ),
    ExpressionTestCase(
        "rtype_int32_max",
        expression={"$type": {"$sum": "$a"}},
        doc={"a": INT32_MAX},
        expected="int",
        msg="$sum should preserve INT32_MAX as int type",
    ),
    ExpressionTestCase(
        "rtype_int64_max",
        expression={"$type": {"$sum": "$a"}},
        doc={"a": INT64_MAX},
        expected="long",
        msg="$sum should preserve INT64_MAX as long type",
    ),
    ExpressionTestCase(
        "rtype_array_traversal_mixed",
        expression={"$type": {"$sum": "$a"}},
        doc={"a": [1, Int64(2), 3.0]},
        expected="double",
        msg="$sum should apply type promotion within a traversed array",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(SUM_RETURN_TYPE_TESTS))
def test_sum_return_type(collection, test_case: ExpressionTestCase):
    """Test $sum return type promotion."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
