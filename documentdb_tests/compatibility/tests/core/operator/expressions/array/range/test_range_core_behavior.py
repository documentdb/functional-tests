"""
Core behavior tests for $range expression.

Tests generating integer sequences with various start, end, step values,
negative ranges, empty results, and large ranges.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Success: basic ascending ranges (default step=1)
BASIC_ASC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="zero_to_five",
        doc={"start": 0, "end": 5},
        expression={"$range": ["$start", "$end"]},
        expected=[0, 1, 2, 3, 4],
        msg="Should generate 0..4",
    ),
    ExpressionTestCase(
        id="one_to_four",
        doc={"start": 1, "end": 4},
        expression={"$range": ["$start", "$end"]},
        expected=[1, 2, 3],
        msg="Should generate 1..3",
    ),
    ExpressionTestCase(
        id="negative_range",
        doc={"start": -5, "end": -1},
        expression={"$range": ["$start", "$end"]},
        expected=[-5, -4, -3, -2],
        msg="Should generate -5..-2",
    ),
    ExpressionTestCase(
        id="start_equals_end",
        doc={"start": 5, "end": 5},
        expression={"$range": ["$start", "$end"]},
        expected=[],
        msg="Should return empty when start equals end",
    ),
    ExpressionTestCase(
        id="start_greater_than_end",
        doc={"start": 10, "end": 5},
        expression={"$range": ["$start", "$end"]},
        expected=[],
        msg="Should return empty when start > end with default step",
    ),
]

# Success: custom step
# Property [Step]: $range respects custom step values.
STEP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="step_two",
        doc={"start": 0, "end": 10, "step": 2},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[0, 2, 4, 6, 8],
        msg="Should generate with step 2",
    ),
    ExpressionTestCase(
        id="step_three",
        doc={"start": 0, "end": 10, "step": 3},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[0, 3, 6, 9],
        msg="Should generate with step 3",
    ),
    ExpressionTestCase(
        id="step_five",
        doc={"start": 0, "end": 20, "step": 5},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[0, 5, 10, 15],
        msg="Should generate with step 5",
    ),
    ExpressionTestCase(
        id="step_one_explicit",
        doc={"start": 0, "end": 3, "step": 1},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[0, 1, 2],
        msg="Explicit step 1 same as default",
    ),
    ExpressionTestCase(
        id="step_overshoots",
        doc={"start": 0, "end": 5, "step": 3},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[0, 3],
        msg="Should stop when step overshoots end",
    ),
    ExpressionTestCase(
        id="step_exactly_reaches",
        doc={"start": 0, "end": 6, "step": 2},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[0, 2, 4],
        msg="End is exclusive even when step exactly reaches it",
    ),
    ExpressionTestCase(
        id="start_nonzero",
        doc={"start": 5, "end": 15},
        expression={"$range": ["$start", "$end"]},
        expected=[5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
        msg="Should work with nonzero start",
    ),
    ExpressionTestCase(
        id="step_4",
        doc={"start": 5, "end": 15, "step": 4},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[5, 9, 13],
        msg="Should work with step 4",
    ),
]

# Success: negative step (descending)
NEGATIVE_STEP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="descending_basic",
        doc={"start": 5, "end": 0, "step": -1},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[5, 4, 3, 2, 1],
        msg="Should generate descending 5..1",
    ),
    ExpressionTestCase(
        id="descending_step_two",
        doc={"start": 10, "end": 0, "step": -2},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[10, 8, 6, 4, 2],
        msg="Should generate descending with step -2",
    ),
    ExpressionTestCase(
        id="descending_negative_range",
        doc={"start": -1, "end": -5, "step": -1},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[-1, -2, -3, -4],
        msg="Should generate descending in negative range",
    ),
    ExpressionTestCase(
        id="descending_start_equals_end",
        doc={"start": 5, "end": 5, "step": -1},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[],
        msg="Should return empty when start equals end with negative step",
    ),
    ExpressionTestCase(
        id="descending_wrong_direction",
        doc={"start": 0, "end": 5, "step": -1},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[],
        msg="Should return empty when step direction mismatches",
    ),
    ExpressionTestCase(
        id="descending_step_neg3",
        doc={"start": 10, "end": 0, "step": -3},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[10, 7, 4, 1],
        msg="Should generate descending with step -3",
    ),
    ExpressionTestCase(
        id="descending_past_zero",
        doc={"start": 5, "end": -1, "step": -1},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[5, 4, 3, 2, 1, 0],
        msg="Should descend past zero",
    ),
]

# Success: empty results
EMPTY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="ascending_wrong_direction",
        doc={"start": 5, "end": 0, "step": 1},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[],
        msg="Should return empty when ascending step but start > end",
    ),
    ExpressionTestCase(
        id="zero_zero_pos_step",
        doc={"start": 0, "end": 0, "step": 1},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[],
        msg="0 to 0 step 1 should be empty",
    ),
    ExpressionTestCase(
        id="zero_zero_neg_step",
        doc={"start": 0, "end": 0, "step": -1},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[],
        msg="0 to 0 step -1 should be empty",
    ),
    ExpressionTestCase(
        id="neg_equal",
        doc={"start": -1, "end": -1},
        expression={"$range": ["$start", "$end"]},
        expected=[],
        msg="-1 to -1 should be empty",
    ),
    ExpressionTestCase(
        id="large_equal",
        doc={"start": 1000000, "end": 1000000},
        expression={"$range": ["$start", "$end"]},
        expected=[],
        msg="Large equal start/end should be empty",
    ),
    ExpressionTestCase(
        id="neg_mismatch",
        doc={"start": -1, "end": -5, "step": 1},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[],
        msg="Negative range with positive step should be empty",
    ),
]

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

# Aggregate and test
ALL_TESTS = (
    BASIC_ASC_TESTS
    + STEP_TESTS
    + NEGATIVE_STEP_TESTS
    + EMPTY_TESTS
    + NUMERIC_TYPE_TESTS
    + SINGLE_ELEMENT_TESTS
    + NEGATIVE_RANGE_TESTS
    + LARGE_RANGE_TESTS
    + NEG_ZERO_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_range_insert(collection, test):
    """Test $range with values from inserted documents."""
    if test.doc is None:
        result = execute_expression(collection, test.expression)
    else:
        result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
