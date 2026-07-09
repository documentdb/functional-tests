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
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    INT64_ZERO,
)

# Property [Numeric Type Acceptance]: $range accepts Int64, whole doubles, and whole Decimal128.
NUMERIC_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int64_args",
        doc={"start": INT64_ZERO, "end": Int64(3)},
        expression={"$range": ["$start", "$end"]},
        expected=[0, 1, 2],
        msg="$range should accept Int64 arguments",
    ),
    ExpressionTestCase(
        "whole_double_args",
        doc={"start": DOUBLE_ZERO, "end": 3.0},
        expression={"$range": ["$start", "$end"]},
        expected=[0, 1, 2],
        msg="$range should accept whole-number double arguments",
    ),
    ExpressionTestCase(
        "whole_decimal128_args",
        doc={"start": DECIMAL128_ZERO, "end": Decimal128("3")},
        expression={"$range": ["$start", "$end"]},
        expected=[0, 1, 2],
        msg="$range should accept whole-number Decimal128 arguments",
    ),
    ExpressionTestCase(
        "int64_step",
        doc={"start": 0, "end": 6, "step": Int64(2)},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[0, 2, 4],
        msg="$range should accept Int64 step",
    ),
    ExpressionTestCase(
        "whole_double_step",
        doc={"start": 0, "end": 6, "step": 2.0},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[0, 2, 4],
        msg="$range should accept whole-number double step",
    ),
    ExpressionTestCase(
        "whole_decimal128_step",
        doc={"start": 0, "end": 6, "step": Decimal128("2")},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[0, 2, 4],
        msg="$range should accept whole-number Decimal128 step",
    ),
    ExpressionTestCase(
        "decimal128_trailing_zero_start",
        doc={"start": Decimal128("0.0"), "end": 3},
        expression={"$range": ["$start", "$end"]},
        expected=[0, 1, 2],
        msg="$range should accept Decimal128 0.0 as start",
    ),
    ExpressionTestCase(
        "decimal128_trailing_zero_end",
        doc={"start": 0, "end": Decimal128("3.0")},
        expression={"$range": ["$start", "$end"]},
        expected=[0, 1, 2],
        msg="$range should accept Decimal128 3.0 as end",
    ),
    ExpressionTestCase(
        "decimal128_trailing_zero_both",
        doc={"start": Decimal128("0.0"), "end": Decimal128("3.0")},
        expression={"$range": ["$start", "$end"]},
        expected=[0, 1, 2],
        msg="$range should accept Decimal128 0.0 start and 3.0 end",
    ),
]

# Property [Single Element]: $range produces single-element arrays at boundaries.
# Property [Single Element]: $range produces single-element arrays.
SINGLE_ELEMENT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "single_element",
        doc={"start": 0, "end": 1},
        expression={"$range": ["$start", "$end"]},
        expected=[0],
        msg="$range should return single element",
    ),
    ExpressionTestCase(
        "desc_single",
        doc={"start": 1, "end": 0, "step": -1},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[1],
        msg="$range descending single element",
    ),
    ExpressionTestCase(
        "step_eq_range",
        doc={"start": 0, "end": 5, "step": 5},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[0],
        msg="$range step equal to range should produce single element",
    ),
    ExpressionTestCase(
        "step_gt_range",
        doc={"start": 0, "end": 5, "step": 10},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[0],
        msg="$range step greater than range should produce single element",
    ),
]

# Property [Negative Numbers]: $range handles negative start, end, and crossing zero.
NEGATIVE_RANGE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "neg_to_zero",
        doc={"start": -5, "end": 0},
        expression={"$range": ["$start", "$end"]},
        expected=[-5, -4, -3, -2, -1],
        msg="$range negative start to zero ascending",
    ),
    ExpressionTestCase(
        "zero_to_neg",
        doc={"start": 0, "end": -5, "step": -1},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[0, -1, -2, -3, -4],
        msg="$range zero to negative descending",
    ),
    ExpressionTestCase(
        "cross_zero_asc",
        doc={"start": -3, "end": 3},
        expression={"$range": ["$start", "$end"]},
        expected=[-3, -2, -1, 0, 1, 2],
        msg="$range crossing zero ascending",
    ),
    ExpressionTestCase(
        "cross_zero_desc",
        doc={"start": 3, "end": -3, "step": -1},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[3, 2, 1, 0, -1, -2],
        msg="$range crossing zero descending",
    ),
    ExpressionTestCase(
        "neg_desc_step2",
        doc={"start": -10, "end": -20, "step": -2},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[-10, -12, -14, -16, -18],
        msg="$range negative descending with step -2",
    ),
    ExpressionTestCase(
        "neg_asc_step2",
        doc={"start": -10, "end": -1, "step": 2},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[-10, -8, -6, -4, -2],
        msg="$range negative ascending with step 2",
    ),
]

# Property [Large Range]: $range generates large sequences.
LARGE_RANGE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "large_range",
        doc={"start": 0, "end": 1000},
        expression={"$range": ["$start", "$end"]},
        expected=list(range(1000)),
        msg="$range should generate large range",
    ),
]

# Property [Negative Zero]: $range treats negative zero as zero.
NEG_ZERO_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "neg_zero_double_start",
        doc={"start": DOUBLE_NEGATIVE_ZERO, "end": 5},
        expression={"$range": ["$start", "$end"]},
        expected=[0, 1, 2, 3, 4],
        msg="$range negative zero double start treated as 0",
    ),
    ExpressionTestCase(
        "neg_zero_decimal_start",
        doc={"start": DECIMAL128_NEGATIVE_ZERO, "end": 5},
        expression={"$range": ["$start", "$end"]},
        expected=[0, 1, 2, 3, 4],
        msg="$range negative zero Decimal128 start treated as 0",
    ),
    ExpressionTestCase(
        "neg_zero_double_end",
        doc={"start": 0, "end": DOUBLE_NEGATIVE_ZERO},
        expression={"$range": ["$start", "$end"]},
        expected=[],
        msg="$range negative zero double end treated as 0",
    ),
    ExpressionTestCase(
        "neg_zero_decimal_end",
        doc={"start": 0, "end": DECIMAL128_NEGATIVE_ZERO},
        expression={"$range": ["$start", "$end"]},
        expected=[],
        msg="$range negative zero Decimal128 end treated as 0",
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
    """Test $range accepts Int64, whole doubles, whole Decimal128, and negative zero."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
