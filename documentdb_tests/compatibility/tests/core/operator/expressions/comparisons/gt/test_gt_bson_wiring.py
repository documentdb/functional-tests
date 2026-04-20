"""
Representative BSON comparison engine wiring tests for $gt.

A small sample of cross-type and special value comparisons to confirm $gt
delegates to the BSON comparison engine correctly. Not an exhaustive matrix —
full BSON ordering coverage lives in /core/data_types/bson_types/.
"""

from datetime import datetime, timezone

import pytest
from bson import Decimal128, Int64, MaxKey, MinKey

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DOUBLE_NEGATIVE_ZERO, FLOAT_NAN

BSON_WIRING_TESTS: list[ExpressionTestCase] = [
    # Cross-type ordering: number < string < object < array
    ExpressionTestCase(
        "string_gt_number", expression={"$gt": ["a", 1]}, expected=True, msg="string > number"
    ),
    ExpressionTestCase(
        "number_not_gt_string",
        expression={"$gt": [1, "a"]},
        expected=False,
        msg="number not > string",
    ),
    ExpressionTestCase(
        "object_gt_string",
        expression={"$gt": [{"a": 1}, "a"]},
        expected=True,
        msg="object > string",
    ),
    ExpressionTestCase(
        "string_not_gt_object",
        expression={"$gt": ["a", {"a": 1}]},
        expected=False,
        msg="string not > object",
    ),
    ExpressionTestCase(
        "array_gt_object",
        expression={"$gt": [[1], {"a": 1}]},
        expected=True,
        msg="array > object",
    ),
    ExpressionTestCase(
        "object_not_gt_array",
        expression={"$gt": [{"a": 1}, [1]]},
        expected=False,
        msg="object not > array",
    ),
    # bool vs number (bool > number in BSON ordering)
    ExpressionTestCase(
        "bool_gt_number",
        expression={"$gt": [True, 1]},
        expected=True,
        msg="bool > number",
    ),
    ExpressionTestCase(
        "number_not_gt_bool",
        expression={"$gt": [1, True]},
        expected=False,
        msg="number not > bool",
    ),
    # date vs string (date > string in BSON ordering)
    ExpressionTestCase(
        "date_gt_string",
        expression={"$gt": [datetime(2024, 1, 1, tzinfo=timezone.utc), "z"]},
        expected=True,
        msg="date > string",
    ),
    ExpressionTestCase(
        "string_not_gt_date",
        expression={"$gt": ["z", datetime(2024, 1, 1, tzinfo=timezone.utc)]},
        expected=False,
        msg="string not > date",
    ),
    # MinKey / MaxKey extremes
    ExpressionTestCase(
        "maxkey_gt_number", expression={"$gt": [MaxKey(), 1]}, expected=True, msg="MaxKey > number"
    ),
    ExpressionTestCase(
        "minkey_not_gt_number",
        expression={"$gt": [MinKey(), 1]},
        expected=False,
        msg="MinKey not > number",
    ),
    # Numeric equivalence across types
    ExpressionTestCase(
        "int_not_gt_equivalent_long",
        expression={"$gt": [1, Int64(1)]},
        expected=False,
        msg="int(1) not > long(1)",
    ),
    ExpressionTestCase(
        "int_not_gt_equivalent_decimal",
        expression={"$gt": [1, Decimal128("1")]},
        expected=False,
        msg="int(1) not > decimal(1)",
    ),
    # Negative zero == positive zero
    ExpressionTestCase(
        "zero_not_gt_neg_zero",
        expression={"$gt": [0.0, DOUBLE_NEGATIVE_ZERO]},
        expected=False,
        msg="0.0 not > -0.0",
    ),
    # NaN ordering
    ExpressionTestCase(
        "nan_not_gt_nan",
        expression={"$gt": [FLOAT_NAN, FLOAT_NAN]},
        expected=False,
        msg="NaN not > NaN",
    ),
    ExpressionTestCase(
        "zero_gt_nan", expression={"$gt": [0, FLOAT_NAN]}, expected=True, msg="0 > NaN"
    ),
]


@pytest.mark.parametrize("test", pytest_params(BSON_WIRING_TESTS))
def test_gt_bson_wiring(collection, test):
    """Smoke test: confirm $gt is wired to the BSON comparison engine."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
