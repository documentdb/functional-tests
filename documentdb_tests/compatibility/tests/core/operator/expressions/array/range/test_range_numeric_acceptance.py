"""
Numeric type acceptance tests for $range expression.

Tests Int64, whole doubles, whole Decimal128, single-element results,
negative number ranges, large ranges, and negative zero handling.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Success: numeric type acceptance (int64, whole doubles, whole decimal128)
NUMERIC_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="int64_args",
        doc={"start": Int64(0), "end": Int64(3)},
        expression={"$range": ["$start", "$end"]},
        expected=[0, 1, 2],
        msg="Should accept Int64 arguments",
    ),
    ExpressionTestCase(
        id="whole_double_args",
        doc={"start": 0.0, "end": 3.0},
        expression={"$range": ["$start", "$end"]},
        expected=[0, 1, 2],
        msg="Should accept whole-number double arguments",
    ),
    ExpressionTestCase(
        id="whole_decimal128_args",
        doc={"start": Decimal128("0"), "end": Decimal128("3")},
        expression={"$range": ["$start", "$end"]},
        expected=[0, 1, 2],
        msg="Should accept whole-number Decimal128 arguments",
    ),
    ExpressionTestCase(
        id="int64_step",
        doc={"start": 0, "end": 6, "step": Int64(2)},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[0, 2, 4],
        msg="Should accept Int64 step",
    ),
    ExpressionTestCase(
        id="whole_double_step",
        doc={"start": 0, "end": 6, "step": 2.0},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[0, 2, 4],
        msg="Should accept whole-number double step",
    ),
    ExpressionTestCase(
        id="whole_decimal128_step",
        doc={"start": 0, "end": 6, "step": Decimal128("2")},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[0, 2, 4],
        msg="Should accept whole-number Decimal128 step",
    ),
    ExpressionTestCase(
        id="decimal128_trailing_zero_start",
        doc={"start": Decimal128("0.0"), "end": 3},
        expression={"$range": ["$start", "$end"]},
        expected=[0, 1, 2],
        msg="Should accept Decimal128 0.0 as start",
    ),
    ExpressionTestCase(
        id="decimal128_trailing_zero_end",
        doc={"start": 0, "end": Decimal128("3.0")},
        expression={"$range": ["$start", "$end"]},
        expected=[0, 1, 2],
        msg="Should accept Decimal128 3.0 as end",
    ),
    ExpressionTestCase(
        id="decimal128_trailing_zero_both",
        doc={"start": Decimal128("0.0"), "end": Decimal128("3.0")},
        expression={"$range": ["$start", "$end"]},
        expected=[0, 1, 2],
        msg="Should accept Decimal128 0.0 start and 3.0 end",
    ),
]

# Success: single element result
# Property [Single Element]: $range produces single-element arrays.
SINGLE_ELEMENT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="single_element",
        doc={"start": 0, "end": 1},
        expression={"$range": ["$start", "$end"]},
        expected=[0],
        msg="Should return single element",
    ),
    ExpressionTestCase(
        id="desc_single",
        doc={"start": 1, "end": 0, "step": -1},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[1],
        msg="Descending single element",
    ),
    ExpressionTestCase(
        id="step_eq_range",
        doc={"start": 0, "end": 5, "step": 5},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[0],
        msg="Step equal to range should produce single element",
    ),
    ExpressionTestCase(
        id="step_gt_range",
        doc={"start": 0, "end": 5, "step": 10},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[0],
        msg="Step greater than range should produce single element",
    ),
]

# Success: negative number ranges
NEGATIVE_RANGE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="neg_to_zero",
        doc={"start": -5, "end": 0},
        expression={"$range": ["$start", "$end"]},
        expected=[-5, -4, -3, -2, -1],
        msg="Negative start to zero ascending",
    ),
    ExpressionTestCase(
        id="zero_to_neg",
        doc={"start": 0, "end": -5, "step": -1},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[0, -1, -2, -3, -4],
        msg="Zero to negative descending",
    ),
    ExpressionTestCase(
        id="cross_zero_asc",
        doc={"start": -3, "end": 3},
        expression={"$range": ["$start", "$end"]},
        expected=[-3, -2, -1, 0, 1, 2],
        msg="Crossing zero ascending",
    ),
    ExpressionTestCase(
        id="cross_zero_desc",
        doc={"start": 3, "end": -3, "step": -1},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[3, 2, 1, 0, -1, -2],
        msg="Crossing zero descending",
    ),
    ExpressionTestCase(
        id="neg_desc_step2",
        doc={"start": -10, "end": -20, "step": -2},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[-10, -12, -14, -16, -18],
        msg="Negative descending with step -2",
    ),
    ExpressionTestCase(
        id="neg_asc_step2",
        doc={"start": -10, "end": -1, "step": 2},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[-10, -8, -6, -4, -2],
        msg="Negative ascending with step 2",
    ),
]

# Success: large range
LARGE_RANGE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="large_range",
        doc={"start": 0, "end": 1000},
        expression={"$range": ["$start", "$end"]},
        expected=list(range(1000)),
        msg="Should generate large range",
    ),
]

# Success: negative zero start/end
NEG_ZERO_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="neg_zero_double_start",
        doc={"start": -0.0, "end": 5},
        expression={"$range": ["$start", "$end"]},
        expected=[0, 1, 2, 3, 4],
        msg="Negative zero double start treated as 0",
    ),
    ExpressionTestCase(
        id="neg_zero_decimal_start",
        doc={"start": Decimal128("-0"), "end": 5},
        expression={"$range": ["$start", "$end"]},
        expected=[0, 1, 2, 3, 4],
        msg="Negative zero Decimal128 start treated as 0",
    ),
    ExpressionTestCase(
        id="neg_zero_double_end",
        doc={"start": 0, "end": -0.0},
        expression={"$range": ["$start", "$end"]},
        expected=[],
        msg="Negative zero double end treated as 0",
    ),
    ExpressionTestCase(
        id="neg_zero_decimal_end",
        doc={"start": 0, "end": Decimal128("-0")},
        expression={"$range": ["$start", "$end"]},
        expected=[],
        msg="Negative zero Decimal128 end treated as 0",
    ),
]

ALL_TESTS = (
    NUMERIC_TYPE_TESTS
    + SINGLE_ELEMENT_TESTS
    + NEGATIVE_RANGE_TESTS
    + LARGE_RANGE_TESTS
    + NEG_ZERO_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_range_numeric_acceptance(collection, test):
    """Test $range with various accepted numeric types and value patterns."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
