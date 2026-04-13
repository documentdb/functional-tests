from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [Zero and Negative Zero Deduplication]: all zero representations
# across numeric types including negative zero are treated as duplicates,
# retaining the first-seen value and type.
SETUNION_ZERO_DEDUP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "zero_all_representations",
        expression={"$setUnion": ["$a"]},
        doc={
            "a": [0, DOUBLE_ZERO, DOUBLE_NEGATIVE_ZERO, DECIMAL128_ZERO, DECIMAL128_NEGATIVE_ZERO]
        },
        expected=[0],
        msg="$setUnion should collapse all zero representations, retaining first-seen int32",
    ),
    ExpressionTestCase(
        "zero_cross_array_pos_int32_neg_double",
        expression={"$setUnion": ["$a", "$b"]},
        doc={"a": [0], "b": [DOUBLE_NEGATIVE_ZERO]},
        expected=[0],
        msg="$setUnion should collapse int32 0 and double -0.0, retaining first-seen int32",
    ),
    ExpressionTestCase(
        "zero_cross_array_neg_double_pos_int32",
        expression={"$setUnion": ["$a", "$b"]},
        doc={"a": [DOUBLE_NEGATIVE_ZERO], "b": [0]},
        expected=[DOUBLE_NEGATIVE_ZERO],
        msg="$setUnion should collapse double -0.0 and int32 0, retaining first-seen double -0.0",
    ),
    ExpressionTestCase(
        "zero_double_pos_then_neg",
        expression={"$setUnion": ["$a"]},
        doc={"a": [DOUBLE_ZERO, DOUBLE_NEGATIVE_ZERO]},
        expected=[DOUBLE_ZERO],
        msg="$setUnion should collapse double 0.0 and -0.0, retaining first-seen 0.0",
    ),
    ExpressionTestCase(
        "zero_double_neg_then_pos",
        expression={"$setUnion": ["$a"]},
        doc={"a": [DOUBLE_NEGATIVE_ZERO, DOUBLE_ZERO]},
        expected=[DOUBLE_NEGATIVE_ZERO],
        msg="$setUnion should collapse double -0.0 and 0.0, retaining first-seen -0.0",
    ),
    ExpressionTestCase(
        "zero_decimal_pos_then_neg",
        expression={"$setUnion": ["$a"]},
        doc={"a": [DECIMAL128_ZERO, DECIMAL128_NEGATIVE_ZERO]},
        expected=[DECIMAL128_ZERO],
        msg="$setUnion should collapse Decimal128 0 and -0, retaining first-seen 0",
    ),
    ExpressionTestCase(
        "zero_decimal_neg_then_pos",
        expression={"$setUnion": ["$a"]},
        doc={"a": [DECIMAL128_NEGATIVE_ZERO, DECIMAL128_ZERO]},
        expected=[DECIMAL128_NEGATIVE_ZERO],
        msg="$setUnion should collapse Decimal128 -0 and 0, retaining first-seen -0",
    ),
]

# Property [NaN Deduplication]: NaN values are deduplicated despite NaN != NaN
# in IEEE 754, and cross-type NaN values collapse to one element.
SETUNION_NAN_DEDUP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nan_double_dedup",
        expression={"$setUnion": ["$a"]},
        doc={"a": [FLOAT_NAN, FLOAT_NAN]},
        expected=[pytest.approx(FLOAT_NAN, nan_ok=True)],
        msg="$setUnion should deduplicate double NaN values",
    ),
    ExpressionTestCase(
        "nan_decimal_dedup",
        expression={"$setUnion": ["$a"]},
        doc={"a": [DECIMAL128_NAN, DECIMAL128_NAN]},
        expected=[DECIMAL128_NAN],
        msg="$setUnion should deduplicate Decimal128 NaN values",
    ),
    ExpressionTestCase(
        "nan_cross_type_dedup_double_first",
        expression={"$setUnion": ["$a"]},
        doc={"a": [FLOAT_NAN, DECIMAL128_NAN]},
        expected=[pytest.approx(FLOAT_NAN, nan_ok=True)],
        msg="$setUnion should collapse NaN types, retaining first-seen double",
    ),
    ExpressionTestCase(
        "nan_cross_type_dedup_decimal_first",
        expression={"$setUnion": ["$a"]},
        doc={"a": [DECIMAL128_NAN, FLOAT_NAN]},
        expected=[DECIMAL128_NAN],
        msg="$setUnion should collapse NaN types, retaining first-seen Decimal128",
    ),
    ExpressionTestCase(
        "nan_cross_array_dedup",
        expression={"$setUnion": ["$a", "$b"]},
        doc={"a": [FLOAT_NAN], "b": [FLOAT_NAN]},
        expected=[pytest.approx(FLOAT_NAN, nan_ok=True)],
        msg="$setUnion should deduplicate NaN values across arrays",
    ),
    ExpressionTestCase(
        "nan_with_other_values",
        expression={"$setUnion": ["$a"]},
        doc={"a": [FLOAT_NAN, 1, 2]},
        expected=[pytest.approx(FLOAT_NAN, nan_ok=True), 1, 2],
        msg="$setUnion should keep NaN alongside other values",
    ),
]

# Property [Infinity Deduplication]: positive and negative infinity values are
# deduplicated within and across numeric types.
SETUNION_INFINITY_DEDUP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "inf_pos_double_dedup",
        expression={"$setUnion": ["$a"]},
        doc={"a": [FLOAT_INFINITY, FLOAT_INFINITY]},
        expected=[FLOAT_INFINITY],
        msg="$setUnion should deduplicate double positive infinity values",
    ),
    ExpressionTestCase(
        "inf_neg_double_dedup",
        expression={"$setUnion": ["$a"]},
        doc={"a": [FLOAT_NEGATIVE_INFINITY, FLOAT_NEGATIVE_INFINITY]},
        expected=[FLOAT_NEGATIVE_INFINITY],
        msg="$setUnion should deduplicate double negative infinity values",
    ),
    ExpressionTestCase(
        "inf_pos_cross_type_double_first",
        expression={"$setUnion": ["$a"]},
        doc={"a": [FLOAT_INFINITY, DECIMAL128_INFINITY]},
        expected=[FLOAT_INFINITY],
        msg="$setUnion should collapse +inf types, retaining first-seen double",
    ),
    ExpressionTestCase(
        "inf_pos_cross_type_decimal_first",
        expression={"$setUnion": ["$a"]},
        doc={"a": [DECIMAL128_INFINITY, FLOAT_INFINITY]},
        expected=[DECIMAL128_INFINITY],
        msg="$setUnion should collapse +inf types, retaining first-seen Decimal128",
    ),
    ExpressionTestCase(
        "inf_neg_cross_type_double_first",
        expression={"$setUnion": ["$a"]},
        doc={"a": [FLOAT_NEGATIVE_INFINITY, DECIMAL128_NEGATIVE_INFINITY]},
        expected=[FLOAT_NEGATIVE_INFINITY],
        msg="$setUnion should collapse -inf types, retaining first-seen double",
    ),
    ExpressionTestCase(
        "inf_neg_cross_type_decimal_first",
        expression={"$setUnion": ["$a"]},
        doc={"a": [DECIMAL128_NEGATIVE_INFINITY, FLOAT_NEGATIVE_INFINITY]},
        expected=[DECIMAL128_NEGATIVE_INFINITY],
        msg="$setUnion should collapse -inf types, retaining first-seen Decimal128",
    ),
    ExpressionTestCase(
        "inf_pos_cross_array_dedup",
        expression={"$setUnion": ["$a", "$b"]},
        doc={"a": [FLOAT_INFINITY], "b": [DECIMAL128_INFINITY]},
        expected=[FLOAT_INFINITY],
        msg="$setUnion should deduplicate positive infinity across arrays",
    ),
    ExpressionTestCase(
        "inf_pos_and_neg_distinct",
        expression={"$setUnion": ["$a"]},
        doc={"a": [FLOAT_INFINITY, FLOAT_NEGATIVE_INFINITY]},
        expected=[FLOAT_INFINITY, FLOAT_NEGATIVE_INFINITY],
        msg="$setUnion should treat positive and negative infinity as distinct",
    ),
]

SETUNION_NUMERIC_EDGE_TESTS_ALL = (
    SETUNION_ZERO_DEDUP_TESTS + SETUNION_NAN_DEDUP_TESTS + SETUNION_INFINITY_DEDUP_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SETUNION_NUMERIC_EDGE_TESTS_ALL))
def test_setunion_numeric_edge_cases(collection, test_case: ExpressionTestCase):
    """Test $setUnion numeric edge case deduplication."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc or {})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        ignore_order=True,
    )
