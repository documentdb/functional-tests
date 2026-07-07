"""
Core behavior tests for $range expression.

Tests generating integer sequences with various start, end, step values,
negative ranges, empty results, and large ranges.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.array.range.utils.range_common import (  # noqa: E501
    RangeTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# ---------------------------------------------------------------------------
# Success: basic ascending ranges (default step=1)
# ---------------------------------------------------------------------------
BASIC_ASC_TESTS: list[RangeTest] = [
    RangeTest(
        id="zero_to_five",
        start=0,
        end=5,
        expected=[0, 1, 2, 3, 4],
        msg="Should generate 0..4",
    ),
    RangeTest(
        id="one_to_four",
        start=1,
        end=4,
        expected=[1, 2, 3],
        msg="Should generate 1..3",
    ),
    RangeTest(
        id="negative_range",
        start=-5,
        end=-1,
        expected=[-5, -4, -3, -2],
        msg="Should generate -5..-2",
    ),
    RangeTest(
        id="start_equals_end",
        start=5,
        end=5,
        expected=[],
        msg="Should return empty when start equals end",
    ),
    RangeTest(
        id="start_greater_than_end",
        start=10,
        end=5,
        expected=[],
        msg="Should return empty when start > end with default step",
    ),
]

# ---------------------------------------------------------------------------
# Success: custom step
# ---------------------------------------------------------------------------
STEP_TESTS: list[RangeTest] = [
    RangeTest(
        id="step_two",
        start=0,
        end=10,
        step=2,
        expected=[0, 2, 4, 6, 8],
        msg="Should generate with step 2",
    ),
    RangeTest(
        id="step_three",
        start=0,
        end=10,
        step=3,
        expected=[0, 3, 6, 9],
        msg="Should generate with step 3",
    ),
    RangeTest(
        id="step_five",
        start=0,
        end=20,
        step=5,
        expected=[0, 5, 10, 15],
        msg="Should generate with step 5",
    ),
    RangeTest(
        id="step_one_explicit",
        start=0,
        end=3,
        step=1,
        expected=[0, 1, 2],
        msg="Explicit step 1 same as default",
    ),
    RangeTest(
        id="step_overshoots",
        start=0,
        end=5,
        step=3,
        expected=[0, 3],
        msg="Should stop when step overshoots end",
    ),
    RangeTest(
        id="step_exactly_reaches",
        start=0,
        end=6,
        step=2,
        expected=[0, 2, 4],
        msg="End is exclusive even when step exactly reaches it",
    ),
    RangeTest(
        id="start_nonzero",
        start=5,
        end=15,
        expected=[5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
        msg="Should work with nonzero start",
    ),
    RangeTest(
        id="step_4",
        start=5,
        end=15,
        step=4,
        expected=[5, 9, 13],
        msg="Should work with step 4",
    ),
]

# ---------------------------------------------------------------------------
# Success: negative step (descending)
# ---------------------------------------------------------------------------
NEGATIVE_STEP_TESTS: list[RangeTest] = [
    RangeTest(
        id="descending_basic",
        start=5,
        end=0,
        step=-1,
        expected=[5, 4, 3, 2, 1],
        msg="Should generate descending 5..1",
    ),
    RangeTest(
        id="descending_step_two",
        start=10,
        end=0,
        step=-2,
        expected=[10, 8, 6, 4, 2],
        msg="Should generate descending with step -2",
    ),
    RangeTest(
        id="descending_negative_range",
        start=-1,
        end=-5,
        step=-1,
        expected=[-1, -2, -3, -4],
        msg="Should generate descending in negative range",
    ),
    RangeTest(
        id="descending_start_equals_end",
        start=5,
        end=5,
        step=-1,
        expected=[],
        msg="Should return empty when start equals end with negative step",
    ),
    RangeTest(
        id="descending_wrong_direction",
        start=0,
        end=5,
        step=-1,
        expected=[],
        msg="Should return empty when step direction mismatches",
    ),
    RangeTest(
        id="descending_step_neg3",
        start=10,
        end=0,
        step=-3,
        expected=[10, 7, 4, 1],
        msg="Should generate descending with step -3",
    ),
    RangeTest(
        id="descending_past_zero",
        start=5,
        end=-1,
        step=-1,
        expected=[5, 4, 3, 2, 1, 0],
        msg="Should descend past zero",
    ),
]

# ---------------------------------------------------------------------------
# Success: empty results
# ---------------------------------------------------------------------------
EMPTY_TESTS: list[RangeTest] = [
    RangeTest(
        id="ascending_wrong_direction",
        start=5,
        end=0,
        step=1,
        expected=[],
        msg="Should return empty when ascending step but start > end",
    ),
    RangeTest(
        id="zero_zero_pos_step",
        start=0,
        end=0,
        step=1,
        expected=[],
        msg="0 to 0 step 1 should be empty",
    ),
    RangeTest(
        id="zero_zero_neg_step",
        start=0,
        end=0,
        step=-1,
        expected=[],
        msg="0 to 0 step -1 should be empty",
    ),
    RangeTest(
        id="neg_equal",
        start=-1,
        end=-1,
        expected=[],
        msg="-1 to -1 should be empty",
    ),
    RangeTest(
        id="large_equal",
        start=1000000,
        end=1000000,
        expected=[],
        msg="Large equal start/end should be empty",
    ),
    RangeTest(
        id="neg_mismatch",
        start=-1,
        end=-5,
        step=1,
        expected=[],
        msg="Negative range with positive step should be empty",
    ),
]

# ---------------------------------------------------------------------------
# Success: numeric type acceptance (int64, whole doubles, whole decimal128)
# ---------------------------------------------------------------------------
NUMERIC_TYPE_TESTS: list[RangeTest] = [
    RangeTest(
        id="int64_args",
        start=Int64(0),
        end=Int64(3),
        expected=[0, 1, 2],
        msg="Should accept Int64 arguments",
    ),
    RangeTest(
        id="whole_double_args",
        start=0.0,
        end=3.0,
        expected=[0, 1, 2],
        msg="Should accept whole-number double arguments",
    ),
    RangeTest(
        id="whole_decimal128_args",
        start=Decimal128("0"),
        end=Decimal128("3"),
        expected=[0, 1, 2],
        msg="Should accept whole-number Decimal128 arguments",
    ),
    RangeTest(
        id="int64_step",
        start=0,
        end=6,
        step=Int64(2),
        expected=[0, 2, 4],
        msg="Should accept Int64 step",
    ),
    RangeTest(
        id="whole_double_step",
        start=0,
        end=6,
        step=2.0,
        expected=[0, 2, 4],
        msg="Should accept whole-number double step",
    ),
    RangeTest(
        id="whole_decimal128_step",
        start=0,
        end=6,
        step=Decimal128("2"),
        expected=[0, 2, 4],
        msg="Should accept whole-number Decimal128 step",
    ),
    RangeTest(
        id="decimal128_trailing_zero_start",
        start=Decimal128("0.0"),
        end=3,
        expected=[0, 1, 2],
        msg="Should accept Decimal128 0.0 as start",
    ),
    RangeTest(
        id="decimal128_trailing_zero_end",
        start=0,
        end=Decimal128("3.0"),
        expected=[0, 1, 2],
        msg="Should accept Decimal128 3.0 as end",
    ),
    RangeTest(
        id="decimal128_trailing_zero_both",
        start=Decimal128("0.0"),
        end=Decimal128("3.0"),
        expected=[0, 1, 2],
        msg="Should accept Decimal128 0.0 start and 3.0 end",
    ),
]

# ---------------------------------------------------------------------------
# Success: single element result
# ---------------------------------------------------------------------------
SINGLE_ELEMENT_TESTS: list[RangeTest] = [
    RangeTest(
        id="single_element",
        start=0,
        end=1,
        expected=[0],
        msg="Should return single element",
    ),
    RangeTest(
        id="desc_single",
        start=1,
        end=0,
        step=-1,
        expected=[1],
        msg="Descending single element",
    ),
    RangeTest(
        id="step_eq_range",
        start=0,
        end=5,
        step=5,
        expected=[0],
        msg="Step equal to range should produce single element",
    ),
    RangeTest(
        id="step_gt_range",
        start=0,
        end=5,
        step=10,
        expected=[0],
        msg="Step greater than range should produce single element",
    ),
]

# ---------------------------------------------------------------------------
# Success: negative number ranges
# ---------------------------------------------------------------------------
NEGATIVE_RANGE_TESTS: list[RangeTest] = [
    RangeTest(
        id="neg_to_zero",
        start=-5,
        end=0,
        expected=[-5, -4, -3, -2, -1],
        msg="Negative start to zero ascending",
    ),
    RangeTest(
        id="zero_to_neg",
        start=0,
        end=-5,
        step=-1,
        expected=[0, -1, -2, -3, -4],
        msg="Zero to negative descending",
    ),
    RangeTest(
        id="cross_zero_asc",
        start=-3,
        end=3,
        expected=[-3, -2, -1, 0, 1, 2],
        msg="Crossing zero ascending",
    ),
    RangeTest(
        id="cross_zero_desc",
        start=3,
        end=-3,
        step=-1,
        expected=[3, 2, 1, 0, -1, -2],
        msg="Crossing zero descending",
    ),
    RangeTest(
        id="neg_desc_step2",
        start=-10,
        end=-20,
        step=-2,
        expected=[-10, -12, -14, -16, -18],
        msg="Negative descending with step -2",
    ),
    RangeTest(
        id="neg_asc_step2",
        start=-10,
        end=-1,
        step=2,
        expected=[-10, -8, -6, -4, -2],
        msg="Negative ascending with step 2",
    ),
]

# ---------------------------------------------------------------------------
# Success: large range
# ---------------------------------------------------------------------------
LARGE_RANGE_TESTS: list[RangeTest] = [
    RangeTest(
        id="large_range",
        start=0,
        end=1000,
        expected=list(range(1000)),
        msg="Should generate large range",
    ),
]

# ---------------------------------------------------------------------------
# Success: negative zero start/end
# ---------------------------------------------------------------------------
NEG_ZERO_TESTS: list[RangeTest] = [
    RangeTest(
        id="neg_zero_double_start",
        start=-0.0,
        end=5,
        expected=[0, 1, 2, 3, 4],
        msg="Negative zero double start treated as 0",
    ),
    RangeTest(
        id="neg_zero_decimal_start",
        start=Decimal128("-0"),
        end=5,
        expected=[0, 1, 2, 3, 4],
        msg="Negative zero Decimal128 start treated as 0",
    ),
    RangeTest(
        id="neg_zero_double_end",
        start=0,
        end=-0.0,
        expected=[],
        msg="Negative zero double end treated as 0",
    ),
    RangeTest(
        id="neg_zero_decimal_end",
        start=0,
        end=Decimal128("-0"),
        expected=[],
        msg="Negative zero Decimal128 end treated as 0",
    ),
]

# ---------------------------------------------------------------------------
# Aggregate and test
# ---------------------------------------------------------------------------
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
    doc = {"start": test.start, "end": test.end}
    args = ["$start", "$end"]
    if test.step is not None:
        args.append("$step")
        doc["step"] = test.step
    result = execute_expression_with_insert(collection, {"$range": args}, doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


TEST_SUBSET_FOR_LITERAL = [
    BASIC_ASC_TESTS[0],  # zero_to_five
    STEP_TESTS[0],  # step_two
    NEGATIVE_STEP_TESTS[0],  # descending_basic
    EMPTY_TESTS[0],  # ascending_wrong_direction
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_range_literal(collection, test):
    """Test $range with literal values."""
    args = [test.start, test.end]
    if test.step is not None:
        args.append(test.step)
    result = execute_expression(collection, {"$range": args})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
