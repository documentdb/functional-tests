from __future__ import annotations

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DOUBLE_FROM_INT64_MAX,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MAX_MINUS_1,
    INT64_MIN,
    INT64_MIN_PLUS_1,
)

# Property [Integer Boundary Behavior]: $sum promotes int32 to int64 on
# overflow and int64 to double when exceeding int64 range.
SUM_INT_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "intbound_int32_max",
        expression={"$sum": "$a"},
        doc={"a": INT32_MAX},
        expected=INT32_MAX,
        msg="$sum should preserve INT32_MAX as int32",
    ),
    ExpressionTestCase(
        "intbound_int32_max_sum",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": INT32_MAX - 1, "b": 1},
        expected=INT32_MAX,
        msg="$sum should produce INT32_MAX from two int32 operands",
    ),
    ExpressionTestCase(
        "intbound_int32_min",
        expression={"$sum": "$a"},
        doc={"a": INT32_MIN},
        expected=INT32_MIN,
        msg="$sum should preserve INT32_MIN as int32",
    ),
    ExpressionTestCase(
        "intbound_int32_min_sum",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": INT32_MIN + 1, "b": -1},
        expected=INT32_MIN,
        msg="$sum should produce INT32_MIN from two int32 operands",
    ),
    ExpressionTestCase(
        "intbound_int64_max",
        expression={"$sum": "$a"},
        doc={"a": INT64_MAX},
        expected=INT64_MAX,
        msg="$sum should preserve INT64_MAX as int64",
    ),
    ExpressionTestCase(
        "intbound_int64_max_sum",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": INT64_MAX_MINUS_1, "b": Int64(1)},
        expected=INT64_MAX,
        msg="$sum should produce INT64_MAX from two int64 operands",
    ),
    ExpressionTestCase(
        "intbound_int64_min",
        expression={"$sum": "$a"},
        doc={"a": INT64_MIN},
        expected=INT64_MIN,
        msg="$sum should preserve INT64_MIN as int64",
    ),
    ExpressionTestCase(
        "intbound_int64_min_sum",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": INT64_MIN_PLUS_1, "b": Int64(-1)},
        expected=INT64_MIN,
        msg="$sum should produce INT64_MIN from two int64 operands",
    ),
]

# Property [Integer Overflow]: int32 overflow promotes to int64, and int64
# overflow promotes to double.
SUM_INT_OVERFLOW_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "intover_int32_max_plus_one",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": INT32_MAX, "b": 1},
        expected=Int64(INT32_MAX + 1),
        msg="$sum should promote INT32_MAX + 1 to int64",
    ),
    ExpressionTestCase(
        "intover_int32_min_minus_one",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": INT32_MIN, "b": -1},
        expected=Int64(INT32_MIN - 1),
        msg="$sum should promote INT32_MIN - 1 to int64",
    ),
    ExpressionTestCase(
        "intover_int64_max_plus_one",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": INT64_MAX, "b": Int64(1)},
        expected=DOUBLE_FROM_INT64_MAX,
        msg="$sum should promote INT64_MAX + 1 to double",
    ),
    ExpressionTestCase(
        "intover_int64_min_minus_one",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": INT64_MIN, "b": Int64(-1)},
        expected=-DOUBLE_FROM_INT64_MAX,
        msg="$sum should promote INT64_MIN - 1 to double",
    ),
]

SUM_INT_BOUNDARY_ALL_TESTS = SUM_INT_BOUNDARY_TESTS + SUM_INT_OVERFLOW_TESTS


@pytest.mark.parametrize("test_case", pytest_params(SUM_INT_BOUNDARY_ALL_TESTS))
def test_sum_int_boundaries(collection, test_case: ExpressionTestCase):
    """Test $sum integer boundary and overflow."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
