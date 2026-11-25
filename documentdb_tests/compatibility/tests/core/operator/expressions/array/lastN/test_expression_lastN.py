"""Tests for the $lastN array expression: n-vs-length behavior, n typing,
element preservation, and invalid n / input handling.

The form ``{"$lastN": {"n": <int>, "input": <array>}}`` (used inside $project)
returns the last ``n`` elements of ``input``.

Differences from the $lastN accumulator: ``input`` must resolve to a real array
(null, missing, or scalar raises 5788200 rather than being included), and invalid
``n`` gets granular codes 5787902/5787903/5787908 instead of the generic 7548606.
The exception is an ``n`` that is numeric but not int64-coercible (NaN, infinity,
overflow), where both forms report 31109."""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    N_ACCUMULATOR_MISSING_INPUT_FIRSTN_FAMILY_ERROR,
    N_ACCUMULATOR_MISSING_N_FIRSTN_FAMILY_ERROR,
    N_ACCUMULATOR_N_NOT_INTEGRAL_ERROR,
    N_ACCUMULATOR_N_NOT_NUMERIC_ERROR,
    N_ACCUMULATOR_N_NOT_POSITIVE_ERROR,
    N_ACCUMULATOR_SPEC_NOT_OBJECT_ERROR,
    N_ACCUMULATOR_UNKNOWN_ARGUMENT_ERROR,
    N_EXPRESSION_INPUT_NOT_ARRAY_ERROR,
    OUT_OF_RANGE_CONVERSION_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NAN,
    FLOAT_INFINITY,
    FLOAT_NAN,
)

pytestmark = pytest.mark.aggregate

# Property [n vs Array Length]: $lastN returns min(n, len) elements from the end.
# n == 1 returns a single-element list, not a scalar; an empty input returns [].
LASTN_N_VS_LENGTH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "n_less_than_length",
        expression={"$lastN": {"n": 2, "input": [10, 20, 30, 40]}},
        expected=[30, 40],
        msg="$lastN should return the last n elements when n is less than the array length",
    ),
    ExpressionTestCase(
        "n_equal_to_length",
        expression={"$lastN": {"n": 4, "input": [10, 20, 30, 40]}},
        expected=[10, 20, 30, 40],
        msg="$lastN should return the whole array when n equals the array length",
    ),
    ExpressionTestCase(
        "n_greater_than_length",
        expression={"$lastN": {"n": 9, "input": [10, 20, 30, 40]}},
        expected=[10, 20, 30, 40],
        msg="$lastN should return all elements when n exceeds the array length",
    ),
    ExpressionTestCase(
        "n_equals_one",
        expression={"$lastN": {"n": 1, "input": [10, 20, 30, 40]}},
        expected=[40],
        msg="$lastN with n=1 should return a single-element list, not a scalar",
    ),
    ExpressionTestCase(
        "empty_input_array",
        expression={"$lastN": {"n": 2, "input": []}},
        expected=[],
        msg="$lastN should return an empty list for an empty input array",
    ),
]

# Property [n Type Handling]: n may be any integral-valued numeric (int, long,
# integral double) or an expression that resolves to one.
LASTN_N_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "n_as_long",
        expression={"$lastN": {"n": Int64(2), "input": [10, 20, 30]}},
        expected=[20, 30],
        msg="$lastN should accept a long-typed n",
    ),
    ExpressionTestCase(
        "n_as_expression",
        expression={"$lastN": {"n": {"$toLong": 2}, "input": [10, 20, 30]}},
        expected=[20, 30],
        msg="$lastN should accept an expression that resolves to n",
    ),
    ExpressionTestCase(
        "n_as_integral_double",
        expression={"$lastN": {"n": 2.0, "input": [10, 20, 30]}},
        expected=[20, 30],
        msg="$lastN should accept an integral-valued double n",
    ),
]

# Property [Element Preservation]: $lastN does no traversal or type checking; it
# returns the trailing elements exactly as they appear, whatever they hold.
LASTN_ELEMENT_PRESERVATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_arrays_preserved",
        expression={"$lastN": {"n": 2, "input": [[1, 2], [3, 4], [5, 6]]}},
        expected=[[3, 4], [5, 6]],
        msg="$lastN should return nested array elements without traversal",
    ),
    ExpressionTestCase(
        "mixed_types_preserved",
        expression={"$lastN": {"n": 2, "input": [1, "two", None, True]}},
        expected=[None, True],
        msg="$lastN should preserve mixed BSON types in the returned slice",
    ),
    ExpressionTestCase(
        "null_element_preserved",
        expression={"$lastN": {"n": 2, "input": [10, 20, None]}},
        expected=[20, None],
        msg="$lastN should preserve a null element present in the last n",
    ),
    ExpressionTestCase(
        "objects_preserved",
        expression={"$lastN": {"n": 2, "input": [{"a": 1}, {"b": 2}, {"c": 3}]}},
        expected=[{"b": 2}, {"c": 3}],
        msg="$lastN should return object elements unchanged",
    ),
    ExpressionTestCase(
        "special_numerics_preserved",
        expression={"$lastN": {"n": 2, "input": [FLOAT_NAN, FLOAT_INFINITY, DECIMAL128_NAN]}},
        expected=[FLOAT_INFINITY, DECIMAL128_NAN],
        msg="$lastN should pass through special numeric elements unchanged",
    ),
]

LASTN_SUCCESS_TESTS = (
    LASTN_N_VS_LENGTH_TESTS + LASTN_N_TYPE_TESTS + LASTN_ELEMENT_PRESERVATION_TESTS
)

# Property [Field References]: n and input may be field paths resolved from the
# document rather than literals.
LASTN_INSERT_SUCCESS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "input_field_ref",
        expression={"$lastN": {"n": 2, "input": "$values"}},
        doc={"values": [10, 20, 30, 40]},
        expected=[30, 40],
        msg="$lastN should resolve input from a field reference",
    ),
    ExpressionTestCase(
        "n_field_ref",
        expression={"$lastN": {"n": "$k", "input": "$values"}},
        doc={"values": [10, 20, 30, 40], "k": 3},
        expected=[20, 30, 40],
        msg="$lastN should resolve n from a field reference",
    ),
    ExpressionTestCase(
        "n_long_field_ref",
        expression={"$lastN": {"n": Int64(2), "input": "$values"}},
        doc={"values": [1, 2, 3]},
        expected=[2, 3],
        msg="$lastN should resolve a long n against a referenced array",
    ),
    ExpressionTestCase(
        "empty_input_field_ref",
        expression={"$lastN": {"n": 2, "input": "$values"}},
        doc={"values": []},
        expected=[],
        msg="$lastN should return an empty list for a referenced empty array",
    ),
]

# Property [Invalid n]: n must resolve to a positive integral value. The array
# expression uses granular codes for each failure mode (unlike the accumulator).
LASTN_INVALID_N_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_n",
        expression={"$lastN": {"input": [1, 2, 3]}},
        error_code=N_ACCUMULATOR_MISSING_N_FIRSTN_FAMILY_ERROR,
        msg="$lastN should reject an argument object that omits n",
    ),
    ExpressionTestCase(
        "n_zero",
        expression={"$lastN": {"n": 0, "input": [1, 2, 3]}},
        error_code=N_ACCUMULATOR_N_NOT_POSITIVE_ERROR,
        msg="$lastN should reject n = 0",
    ),
    ExpressionTestCase(
        "n_negative",
        expression={"$lastN": {"n": -1, "input": [1, 2, 3]}},
        error_code=N_ACCUMULATOR_N_NOT_POSITIVE_ERROR,
        msg="$lastN should reject a negative n",
    ),
    ExpressionTestCase(
        "n_non_integer_double",
        expression={"$lastN": {"n": 2.5, "input": [1, 2, 3]}},
        error_code=N_ACCUMULATOR_N_NOT_INTEGRAL_ERROR,
        msg="$lastN should reject a non-integer double n",
    ),
    ExpressionTestCase(
        "n_non_integer_decimal128",
        expression={"$lastN": {"n": Decimal128("1.5"), "input": [1, 2, 3]}},
        error_code=N_ACCUMULATOR_N_NOT_INTEGRAL_ERROR,
        msg="$lastN should reject a non-integer Decimal128 n",
    ),
    ExpressionTestCase(
        "n_string",
        expression={"$lastN": {"n": "2", "input": [1, 2, 3]}},
        error_code=N_ACCUMULATOR_N_NOT_NUMERIC_ERROR,
        msg="$lastN should reject a non-numeric string n",
    ),
    ExpressionTestCase(
        "n_null",
        expression={"$lastN": {"n": None, "input": [1, 2, 3]}},
        error_code=N_ACCUMULATOR_N_NOT_NUMERIC_ERROR,
        msg="$lastN should reject a null n",
    ),
]

# Property [Non-Coercible n]: NaN, infinity, and out-of-range doubles are numeric
# (so they clear the check that rejects null) but fail int64 conversion. An
# overflowing expression reaches this path without an explicit infinity.
LASTN_NON_COERCIBLE_N_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "n_nan",
        expression={"$lastN": {"n": FLOAT_NAN, "input": [1, 2, 3]}},
        error_code=OUT_OF_RANGE_CONVERSION_ERROR,
        msg="$lastN should reject NaN as n",
    ),
    ExpressionTestCase(
        "n_infinity",
        expression={"$lastN": {"n": FLOAT_INFINITY, "input": [1, 2, 3]}},
        error_code=OUT_OF_RANGE_CONVERSION_ERROR,
        msg="$lastN should reject infinity as n",
    ),
    ExpressionTestCase(
        "n_out_of_range_double",
        expression={"$lastN": {"n": 1e19, "input": [1, 2, 3]}},
        error_code=OUT_OF_RANGE_CONVERSION_ERROR,
        msg="$lastN should reject an n too large to coerce to a 64-bit integer",
    ),
]

# Property [Invalid input]: input must be present and resolve to an array. A
# missing, null, or non-array input is rejected (not coerced to an empty list).
LASTN_INVALID_INPUT_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_input",
        expression={"$lastN": {"n": 2}},
        error_code=N_ACCUMULATOR_MISSING_INPUT_FIRSTN_FAMILY_ERROR,
        msg="$lastN should reject an argument object that omits input",
    ),
    ExpressionTestCase(
        "input_null_literal",
        expression={"$lastN": {"n": 2, "input": None}},
        error_code=N_EXPRESSION_INPUT_NOT_ARRAY_ERROR,
        msg="$lastN should reject a null input literal",
    ),
    ExpressionTestCase(
        "input_missing_via_remove",
        expression={"$lastN": {"n": 2, "input": "$$REMOVE"}},
        error_code=N_EXPRESSION_INPUT_NOT_ARRAY_ERROR,
        msg="$lastN should reject a missing input ($$REMOVE)",
    ),
    ExpressionTestCase(
        "input_scalar_literal",
        expression={"$lastN": {"n": 2, "input": 5}},
        error_code=N_EXPRESSION_INPUT_NOT_ARRAY_ERROR,
        msg="$lastN should reject a non-array (scalar) input",
    ),
]

# Property [Malformed Specification]: the operator argument must be an object
# containing only the known n / input fields.
LASTN_MALFORMED_SPEC_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "spec_array",
        expression={"$lastN": [1, 2]},
        error_code=N_ACCUMULATOR_SPEC_NOT_OBJECT_ERROR,
        msg="$lastN should reject an array specification",
    ),
    ExpressionTestCase(
        "spec_scalar",
        expression={"$lastN": 5},
        error_code=N_ACCUMULATOR_SPEC_NOT_OBJECT_ERROR,
        msg="$lastN should reject a scalar specification",
    ),
    ExpressionTestCase(
        "unknown_argument",
        expression={"$lastN": {"n": 2, "input": [1, 2, 3], "extra": 1}},
        error_code=N_ACCUMULATOR_UNKNOWN_ARGUMENT_ERROR,
        msg="$lastN should reject an unknown argument field",
    ),
]

LASTN_ERROR_TESTS = (
    LASTN_INVALID_N_ERROR_TESTS
    + LASTN_NON_COERCIBLE_N_ERROR_TESTS
    + LASTN_INVALID_INPUT_ERROR_TESTS
    + LASTN_MALFORMED_SPEC_ERROR_TESTS
)

# Property [Invalid input, from documents]: a referenced field that is null,
# missing, or non-array is rejected at runtime, mirroring the literal cases.
LASTN_INSERT_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "input_null_field",
        expression={"$lastN": {"n": 2, "input": "$values"}},
        doc={"values": None},
        error_code=N_EXPRESSION_INPUT_NOT_ARRAY_ERROR,
        msg="$lastN should reject a null input resolved from a field",
    ),
    ExpressionTestCase(
        "input_missing_field",
        expression={"$lastN": {"n": 2, "input": "$values"}},
        doc={"other": 1},
        error_code=N_EXPRESSION_INPUT_NOT_ARRAY_ERROR,
        msg="$lastN should reject a missing input field",
    ),
    ExpressionTestCase(
        "input_int_field",
        expression={"$lastN": {"n": 2, "input": "$values"}},
        doc={"values": 5},
        error_code=N_EXPRESSION_INPUT_NOT_ARRAY_ERROR,
        msg="$lastN should reject an int input resolved from a field",
    ),
    ExpressionTestCase(
        "input_string_field",
        expression={"$lastN": {"n": 2, "input": "$values"}},
        doc={"values": "hello"},
        error_code=N_EXPRESSION_INPUT_NOT_ARRAY_ERROR,
        msg="$lastN should reject a string input resolved from a field",
    ),
    ExpressionTestCase(
        "input_object_field",
        expression={"$lastN": {"n": 2, "input": "$values"}},
        doc={"values": {"a": 1}},
        error_code=N_EXPRESSION_INPUT_NOT_ARRAY_ERROR,
        msg="$lastN should reject an object input resolved from a field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LASTN_SUCCESS_TESTS))
def test_expression_lastN(collection, test):
    """Test $lastN array-expression success cases with literal inputs."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(LASTN_INSERT_SUCCESS_TESTS))
def test_expression_lastN_insert(collection, test):
    """Test $lastN array-expression success cases with field references."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(LASTN_ERROR_TESTS))
def test_expression_lastN_errors(collection, test):
    """Test $lastN array-expression error cases with literal inputs."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, error_code=test.error_code, msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(LASTN_INSERT_ERROR_TESTS))
def test_expression_lastN_insert_errors(collection, test):
    """Test $lastN array-expression error cases with field references."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, error_code=test.error_code, msg=test.msg)
