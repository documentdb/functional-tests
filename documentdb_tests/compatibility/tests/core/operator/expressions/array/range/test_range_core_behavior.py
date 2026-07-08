"""
Core behavior tests for $range expression.

Tests generating integer sequences with various start, end, step values,
negative steps (descending), and empty results.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Basic Ascending]: $range generates ascending integer sequences.
BASIC_ASC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "zero_to_five",
        doc={"start": 0, "end": 5},
        expression={"$range": ["$start", "$end"]},
        expected=[0, 1, 2, 3, 4],
        msg="$range should generate 0..4",
    ),
    ExpressionTestCase(
        "one_to_four",
        doc={"start": 1, "end": 4},
        expression={"$range": ["$start", "$end"]},
        expected=[1, 2, 3],
        msg="$range should generate 1..3",
    ),
    ExpressionTestCase(
        "negative_range",
        doc={"start": -5, "end": -1},
        expression={"$range": ["$start", "$end"]},
        expected=[-5, -4, -3, -2],
        msg="$range should generate -5..-2",
    ),
    ExpressionTestCase(
        "start_equals_end",
        doc={"start": 5, "end": 5},
        expression={"$range": ["$start", "$end"]},
        expected=[],
        msg="$range should return empty when start equals end",
    ),
    ExpressionTestCase(
        "start_greater_than_end",
        doc={"start": 10, "end": 5},
        expression={"$range": ["$start", "$end"]},
        expected=[],
        msg="$range should return empty when start > end with default step",
    ),
]

# Property [Custom Step]: $range respects custom step values.
# Property [Step]: $range respects custom step values.
STEP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "step_two",
        doc={"start": 0, "end": 10, "step": 2},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[0, 2, 4, 6, 8],
        msg="$range should generate with step 2",
    ),
    ExpressionTestCase(
        "step_three",
        doc={"start": 0, "end": 10, "step": 3},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[0, 3, 6, 9],
        msg="$range should generate with step 3",
    ),
    ExpressionTestCase(
        "step_five",
        doc={"start": 0, "end": 20, "step": 5},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[0, 5, 10, 15],
        msg="$range should generate with step 5",
    ),
    ExpressionTestCase(
        "step_one_explicit",
        doc={"start": 0, "end": 3, "step": 1},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[0, 1, 2],
        msg="$range explicit step 1 same as default",
    ),
    ExpressionTestCase(
        "step_overshoots",
        doc={"start": 0, "end": 5, "step": 3},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[0, 3],
        msg="$range should stop when step overshoots end",
    ),
    ExpressionTestCase(
        "step_exactly_reaches",
        doc={"start": 0, "end": 6, "step": 2},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[0, 2, 4],
        msg="$range end is exclusive even when step exactly reaches it",
    ),
    ExpressionTestCase(
        "start_nonzero",
        doc={"start": 5, "end": 15},
        expression={"$range": ["$start", "$end"]},
        expected=[5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
        msg="$range should work with nonzero start",
    ),
    ExpressionTestCase(
        "step_4",
        doc={"start": 5, "end": 15, "step": 4},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[5, 9, 13],
        msg="$range should work with step 4",
    ),
]

# Property [Negative Step]: $range generates descending sequences with negative step.
NEGATIVE_STEP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "descending_basic",
        doc={"start": 5, "end": 0, "step": -1},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[5, 4, 3, 2, 1],
        msg="$range should generate descending 5..1",
    ),
    ExpressionTestCase(
        "descending_step_two",
        doc={"start": 10, "end": 0, "step": -2},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[10, 8, 6, 4, 2],
        msg="$range should generate descending with step -2",
    ),
    ExpressionTestCase(
        "descending_negative_range",
        doc={"start": -1, "end": -5, "step": -1},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[-1, -2, -3, -4],
        msg="$range should generate descending in negative range",
    ),
    ExpressionTestCase(
        "descending_start_equals_end",
        doc={"start": 5, "end": 5, "step": -1},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[],
        msg="$range should return empty when start equals end with negative step",
    ),
    ExpressionTestCase(
        "descending_wrong_direction",
        doc={"start": 0, "end": 5, "step": -1},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[],
        msg="$range should return empty when step direction mismatches",
    ),
    ExpressionTestCase(
        "descending_step_neg3",
        doc={"start": 10, "end": 0, "step": -3},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[10, 7, 4, 1],
        msg="$range should generate descending with step -3",
    ),
    ExpressionTestCase(
        "descending_past_zero",
        doc={"start": 5, "end": -1, "step": -1},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[5, 4, 3, 2, 1, 0],
        msg="$range should descend past zero",
    ),
]

# Property [Empty Result]: $range returns empty when start/end/step produce no elements.
EMPTY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "ascending_wrong_direction",
        doc={"start": 5, "end": 0, "step": 1},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[],
        msg="$range should return empty when ascending step but start > end",
    ),
    ExpressionTestCase(
        "zero_zero_pos_step",
        doc={"start": 0, "end": 0, "step": 1},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[],
        msg="$range 0 to 0 step 1 should be empty",
    ),
    ExpressionTestCase(
        "zero_zero_neg_step",
        doc={"start": 0, "end": 0, "step": -1},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[],
        msg="$range 0 to 0 step -1 should be empty",
    ),
    ExpressionTestCase(
        "neg_equal",
        doc={"start": -1, "end": -1},
        expression={"$range": ["$start", "$end"]},
        expected=[],
        msg="$range -1 to -1 should be empty",
    ),
    ExpressionTestCase(
        "large_equal",
        doc={"start": 1000000, "end": 1000000},
        expression={"$range": ["$start", "$end"]},
        expected=[],
        msg="$range large equal start/end should be empty",
    ),
    ExpressionTestCase(
        "neg_mismatch",
        doc={"start": -1, "end": -5, "step": 1},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[],
        msg="$range negative range with positive step should be empty",
    ),
]

ALL_TESTS = BASIC_ASC_TESTS + STEP_TESTS + NEGATIVE_STEP_TESTS + EMPTY_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_range_core_behavior(collection, test):
    """Test $range core behavior: ascending, steps, descending, empty results."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
