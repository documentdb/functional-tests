"""
Place-argument and field-lookup tests for $round expression.

Covers place types (int64, decimal128, whole-double, negative-zero),
int32-to-int64 promotion, null/missing short-circuiting, error-precedence
success cases, midpoint rounding at a place, nested $round, and field-path
resolution.
"""

import pytest
from bson import (
    Decimal128,
    Int64,
)

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    INT32_MAX,
    MISSING,
)

ROUND_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "place_int64",
        expression={"$round": [1.12345, Int64(2)]},
        expected=1.12,
        msg="int64 place value 2 rounds double 1.12345 to 1.12",
    ),
    ExpressionTestCase(
        "place_decimal",
        expression={"$round": [1.12345, Decimal128("2")]},
        expected=1.12,
        msg="decimal128 place value 2 rounds double 1.12345 to 1.12",
    ),
    ExpressionTestCase(
        "int32_with_place",
        expression={"$round": [5, 3]},
        expected=5,
        msg="int32 5 with place 3 is already integral and unchanged",
    ),
    ExpressionTestCase(
        "int64_with_place",
        expression={"$round": [Int64(5), 3]},
        expected=Int64(5),
        msg="int64 5 with place 3 is already integral and unchanged",
    ),
    ExpressionTestCase(
        "neg_place_int64",
        expression={"$round": [Int64(1234), Int64(-2)]},
        expected=Int64(1200),
        msg="int64 1234 at place -2 rounds to 1200 (int64 type preserved)",
    ),
    ExpressionTestCase(
        "neg_place_decimal",
        expression={"$round": [Decimal128("23.298"), Decimal128("-1")]},
        expected=Decimal128("2E+1"),
        msg="decimal128 23.298 at place -1 rounds to 2E+1 (nearest ten)",
    ),
    ExpressionTestCase(
        "int32_to_int64_promotion",
        expression={"$round": [INT32_MAX, -1]},
        expected=Int64(2147483650),
        msg="rounding INT32_MAX at place -1 overflows int32 and promotes to int64",
    ),
    ExpressionTestCase(
        "place_null",
        expression={"$round": [5.7, None]},
        expected=None,
        msg="null place short-circuits to a null result",
    ),
    ExpressionTestCase(
        "missing_value",
        expression={"$round": MISSING},
        expected=None,
        msg="missing input returns null",
    ),
    ExpressionTestCase(
        "place_whole_double",
        expression={"$round": [1.2345, 2.0]},
        expected=1.23,
        msg="whole-number double 2.0 is accepted as place 2",
    ),
    ExpressionTestCase(
        "place_negative_zero_double",
        expression={"$round": [1.2345, -0.0]},
        expected=1.0,
        msg="double -0.0 place is treated as place 0",
    ),
    ExpressionTestCase(
        "place_negative_zero_decimal",
        expression={"$round": [1.2345, Decimal128("-0")]},
        expected=1.0,
        msg="decimal128 -0 place is treated as place 0",
    ),
    ExpressionTestCase(
        "null_num_short_circuit",
        expression={"$round": [None, 101]},
        expected=None,
        msg="null number short-circuits before place bounds validation",
    ),
    ExpressionTestCase(
        "midpoint_place_2",
        expression={"$round": [1.005, 2]},
        expected=1.0,
        msg="1.005 is not exactly representable as a double and rounds to 1.0 at place 2",
    ),
    ExpressionTestCase(
        "midpoint_place_1",
        expression={"$round": [1.25, 1]},
        expected=1.2,
        msg="1.25 rounds half-to-even to 1.2 at place 1",
    ),
    ExpressionTestCase(
        "decimal_midpoint_place_1_65",
        expression={"$round": [Decimal128("0.65"), 1]},
        expected=Decimal128("0.6"),
        msg="decimal128 0.65 rounds half-to-even down to 0.6 at place 1 (6 is even)",
    ),
    ExpressionTestCase(
        "decimal_midpoint_place_1_75",
        expression={"$round": [Decimal128("0.75"), 1]},
        expected=Decimal128("0.8"),
        msg="decimal128 0.75 rounds half-to-even up to 0.8 at place 1 (8 is even)",
    ),
    ExpressionTestCase(
        "decimal_midpoint_place_1_85",
        expression={"$round": [Decimal128("0.85"), 1]},
        expected=Decimal128("0.8"),
        msg="decimal128 0.85 rounds half-to-even down to 0.8 at place 1 (8 is even)",
    ),
    ExpressionTestCase(
        "decimal_midpoint_place_1_95",
        expression={"$round": [Decimal128("0.95"), 1]},
        expected=Decimal128("1.0"),
        msg="decimal128 0.95 rounds half-to-even up to 1.0 at place 1 (0 is even)",
    ),
    ExpressionTestCase(
        "midpoint_neg_place",
        expression={"$round": [15, -1]},
        expected=20,
        msg="15 rounds half-to-even up to 20 at place -1",
    ),
    ExpressionTestCase(
        "midpoint_neg_place_25",
        expression={"$round": [25, -1]},
        expected=20,
        msg="25 rounds half-to-even down to 20 at place -1 (complements 15 rounding up)",
    ),
    ExpressionTestCase(
        "carry_propagation_neg_place",
        expression={"$round": [4995, -3]},
        expected=5000,
        msg="4995 at place -3 carries across all three digits to 5000",
    ),
    ExpressionTestCase(
        "carry_propagation_neg_place_negative",
        expression={"$round": [-4995, -3]},
        expected=-5000,
        msg="-4995 at place -3 carries across all three digits to -5000",
    ),
    ExpressionTestCase(
        "carry_propagation_positive_place",
        expression={"$round": [3.995, 2]},
        expected=4.0,
        msg="3.995 at place 2 carries out of the fractional part into the integer part, 4.0",
    ),
]

ROUND_INSERT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "place_int64",
        expression={"$round": ["$value", "$place"]},
        doc={"value": 1.12345, "place": Int64(2)},
        expected=1.12,
        msg="int64 place value 2 rounds double 1.12345 to 1.12",
    ),
    ExpressionTestCase(
        "int32_with_place",
        expression={"$round": ["$value", "$place"]},
        doc={"value": 5, "place": 3},
        expected=5,
        msg="int32 5 with place 3 is already integral and unchanged",
    ),
    ExpressionTestCase(
        "int64_with_place",
        expression={"$round": ["$value", "$place"]},
        doc={"value": Int64(5), "place": 3},
        expected=Int64(5),
        msg="int64 5 with place 3 is already integral and unchanged",
    ),
    ExpressionTestCase(
        "neg_place_int64",
        expression={"$round": ["$value", "$place"]},
        doc={"value": Int64(1234), "place": Int64(-2)},
        expected=Int64(1200),
        msg="int64 1234 at place -2 rounds to 1200 (int64 type preserved)",
    ),
    ExpressionTestCase(
        "neg_place_decimal",
        expression={"$round": ["$value", "$place"]},
        doc={"value": Decimal128("23.298"), "place": Decimal128("-1")},
        expected=Decimal128("2E+1"),
        msg="decimal128 23.298 at place -1 rounds to 2E+1 (nearest ten)",
    ),
    ExpressionTestCase(
        "int32_to_int64_promotion",
        expression={"$round": ["$value", "$place"]},
        doc={"value": INT32_MAX, "place": -1},
        expected=Int64(2147483650),
        msg="rounding INT32_MAX at place -1 overflows int32 and promotes to int64",
    ),
    ExpressionTestCase(
        "place_null",
        expression={"$round": ["$value", "$place"]},
        doc={"value": 5.7, "place": None},
        expected=None,
        msg="null place short-circuits to a null result",
    ),
    ExpressionTestCase(
        "place_whole_double",
        expression={"$round": ["$value", "$place"]},
        doc={"value": 1.2345, "place": 2.0},
        expected=1.23,
        msg="whole-number double 2.0 is accepted as place 2",
    ),
    ExpressionTestCase(
        "place_negative_zero_double",
        expression={"$round": ["$value", "$place"]},
        doc={"value": 1.2345, "place": -0.0},
        expected=1.0,
        msg="double -0.0 place is treated as place 0",
    ),
    ExpressionTestCase(
        "place_negative_zero_decimal",
        expression={"$round": ["$value", "$place"]},
        doc={"value": 1.2345, "place": Decimal128("-0")},
        expected=1.0,
        msg="decimal128 -0 place is treated as place 0",
    ),
    ExpressionTestCase(
        "null_num_short_circuit",
        expression={"$round": ["$value", "$place"]},
        doc={"value": None, "place": 101},
        expected=None,
        msg="null number short-circuits before place bounds validation",
    ),
    ExpressionTestCase(
        "midpoint_place_2",
        expression={"$round": ["$value", "$place"]},
        doc={"value": 1.005, "place": 2},
        expected=1.0,
        msg="1.005 is not exactly representable as a double and rounds to 1.0 at place 2",
    ),
    ExpressionTestCase(
        "midpoint_place_1",
        expression={"$round": ["$value", "$place"]},
        doc={"value": 1.25, "place": 1},
        expected=1.2,
        msg="1.25 rounds half-to-even to 1.2 at place 1",
    ),
    ExpressionTestCase(
        "decimal_midpoint_place_1_65",
        expression={"$round": ["$value", "$place"]},
        doc={"value": Decimal128("0.65"), "place": 1},
        expected=Decimal128("0.6"),
        msg="decimal128 0.65 rounds half-to-even down to 0.6 at place 1 (6 is even)",
    ),
    ExpressionTestCase(
        "midpoint_neg_place",
        expression={"$round": ["$value", "$place"]},
        doc={"value": 15, "place": -1},
        expected=20,
        msg="15 rounds half-to-even up to 20 at place -1",
    ),
    ExpressionTestCase(
        "carry_propagation_neg_place",
        expression={"$round": ["$value", "$place"]},
        doc={"value": 4995, "place": -3},
        expected=5000,
        msg="4995 at place -3 carries across all three digits to 5000",
    ),
    ExpressionTestCase(
        "carry_propagation_neg_place_negative",
        expression={"$round": ["$value", "$place"]},
        doc={"value": -4995, "place": -3},
        expected=-5000,
        msg="-4995 at place -3 carries across all three digits to -5000",
    ),
    ExpressionTestCase(
        "carry_propagation_positive_place",
        expression={"$round": ["$value", "$place"]},
        doc={"value": 3.995, "place": 2},
        expected=4.0,
        msg="3.995 at place 2 carries out of the fractional part into the integer part, 4.0",
    ),
]

ROUND_NESTED_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_round_2",
        expression={"$round": {"$round": 4.6}},
        expected=5.0,
        msg="Should evaluate nested $round",
    ),
    ExpressionTestCase(
        "nested_round_2_midpoint",
        expression={"$round": {"$round": 1.55}},
        expected=2.0,
        msg="Should evaluate nested $round at midpoint",
    ),
    ExpressionTestCase(
        "nested_round_3_with_place",
        expression={"$round": [{"$round": [{"$round": [3.456, 2]}, 1]}]},
        expected=4.0,
        msg="Should evaluate triple-nested $round with place",
    ),
]

ROUND_FIELD_LOOKUP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_field",
        expression={"$round": "$a.b"},
        doc={"a": {"b": 4.6}},
        expected=5.0,
        msg="Should resolve nested field path",
    ),
    ExpressionTestCase(
        "nonexistent_field",
        expression={"$round": "$a.nonexistent"},
        doc={"a": {"missing": 1}},
        expected=None,
        msg="Should return null for nonexistent field path",
    ),
]


ROUND_LITERAL_ALL_TESTS: list[ExpressionTestCase] = ROUND_LITERAL_TESTS + ROUND_NESTED_TESTS
ROUND_INSERT_ALL_TESTS: list[ExpressionTestCase] = ROUND_INSERT_TESTS + ROUND_FIELD_LOOKUP_TESTS


@pytest.mark.parametrize("test", pytest_params(ROUND_LITERAL_ALL_TESTS))
def test_round_literal(collection, test):
    """Test $round with literal values and nested expressions."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(ROUND_INSERT_ALL_TESTS))
def test_round_insert(collection, test):
    """Test $round with inserted document values and field-path lookups."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
