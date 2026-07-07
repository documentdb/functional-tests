"""
Error tests for $zip expression.

Tests non-array inputs, invalid useLongestLength, invalid defaults,
defaults without useLongestLength, and defaults length mismatch.
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.array.zip.utils.zip_common import (  # noqa: E501
    ZipTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    ZIP_DEFAULTS_LENGTH_MISMATCH_ERROR,
    ZIP_DEFAULTS_NOT_ARRAY_ERROR,
    ZIP_DEFAULTS_WITHOUT_LONGEST_ERROR,
    ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
    ZIP_USE_LONGEST_NOT_BOOL_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)

# ---------------------------------------------------------------------------
# Error: non-array input element — standard BSON types
# ---------------------------------------------------------------------------
NOT_ARRAY_ELEMENT_TESTS: list[ZipTest] = [
    ZipTest(
        id="string_input",
        inputs=["hello", [1]],
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject string input element",
    ),
    ZipTest(
        id="int_input",
        inputs=[42, [1]],
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject int input element",
    ),
    ZipTest(
        id="negative_int_input",
        inputs=[-42, [1]],
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject negative int input element",
    ),
    ZipTest(
        id="bool_input",
        inputs=[True, [1]],
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject bool input element",
    ),
    ZipTest(
        id="object_input",
        inputs=[{"a": 1}, [1]],
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject object input element",
    ),
    ZipTest(
        id="double_input",
        inputs=[3.14, [1]],
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject double input element",
    ),
    ZipTest(
        id="negative_double_input",
        inputs=[-3.14, [1]],
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject negative double input element",
    ),
    ZipTest(
        id="decimal128_input",
        inputs=[Decimal128("1"), [1]],
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject decimal128 input element",
    ),
    ZipTest(
        id="int64_input",
        inputs=[Int64(1), [1]],
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject int64 input element",
    ),
    ZipTest(
        id="objectid_input",
        inputs=[ObjectId(), [1]],
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject objectid input element",
    ),
    ZipTest(
        id="datetime_input",
        inputs=[datetime(2024, 1, 1, tzinfo=timezone.utc), [1]],
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject datetime input element",
    ),
    ZipTest(
        id="binary_input",
        inputs=[Binary(b"x", 0), [1]],
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject binary input element",
    ),
    ZipTest(
        id="regex_input",
        inputs=[Regex("x"), [1]],
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject regex input element",
    ),
    ZipTest(
        id="maxkey_input",
        inputs=[MaxKey(), [1]],
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject maxkey input element",
    ),
    ZipTest(
        id="minkey_input",
        inputs=[MinKey(), [1]],
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject minkey input element",
    ),
    ZipTest(
        id="timestamp_input",
        inputs=[Timestamp(0, 0), [1]],
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject timestamp input element",
    ),
    ZipTest(
        id="non_array_second_position",
        inputs=[[1], 42],
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject non-array in second position",
    ),
    ZipTest(
        id="non_array_middle_position",
        inputs=[[1], "bad", [2]],
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject non-array in middle position",
    ),
]

# ---------------------------------------------------------------------------
# Error: special float/Decimal128 values as input element
# ---------------------------------------------------------------------------
SPECIAL_NUMERIC_ERROR_TESTS: list[ZipTest] = [
    ZipTest(
        id="nan_input",
        inputs=[FLOAT_NAN, [1]],
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject NaN input element",
    ),
    ZipTest(
        id="inf_input",
        inputs=[FLOAT_INFINITY, [1]],
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject Infinity input element",
    ),
    ZipTest(
        id="neg_inf_input",
        inputs=[FLOAT_NEGATIVE_INFINITY, [1]],
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject -Infinity input element",
    ),
    ZipTest(
        id="neg_zero_input",
        inputs=[DOUBLE_NEGATIVE_ZERO, [1]],
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject negative zero input element",
    ),
    ZipTest(
        id="decimal128_nan_input",
        inputs=[DECIMAL128_NAN, [1]],
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject Decimal128 NaN input element",
    ),
    ZipTest(
        id="decimal128_inf_input",
        inputs=[DECIMAL128_INFINITY, [1]],
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject Decimal128 Infinity input element",
    ),
    ZipTest(
        id="decimal128_neg_inf_input",
        inputs=[DECIMAL128_NEGATIVE_INFINITY, [1]],
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject Decimal128 -Infinity input element",
    ),
    ZipTest(
        id="decimal128_neg_zero_input",
        inputs=[DECIMAL128_NEGATIVE_ZERO, [1]],
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject Decimal128 -0 input element",
    ),
]

# ---------------------------------------------------------------------------
# Error: numeric boundary values as input element
# ---------------------------------------------------------------------------
BOUNDARY_ERROR_TESTS: list[ZipTest] = [
    ZipTest(
        id="int32_max_input",
        inputs=[INT32_MAX, [1]],
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject INT32_MAX input element",
    ),
    ZipTest(
        id="int32_min_input",
        inputs=[INT32_MIN, [1]],
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject INT32_MIN input element",
    ),
    ZipTest(
        id="int64_max_input",
        inputs=[INT64_MAX, [1]],
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject INT64_MAX input element",
    ),
    ZipTest(
        id="int64_min_input",
        inputs=[INT64_MIN, [1]],
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject INT64_MIN input element",
    ),
    ZipTest(
        id="decimal128_max_input",
        inputs=[DECIMAL128_MAX, [1]],
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject DECIMAL128_MAX input element",
    ),
    ZipTest(
        id="decimal128_min_input",
        inputs=[DECIMAL128_MIN, [1]],
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject DECIMAL128_MIN input element",
    ),
]

# ---------------------------------------------------------------------------
# Error: string edge cases as input element
# ---------------------------------------------------------------------------
STRING_EDGE_ERROR_TESTS: list[ZipTest] = [
    ZipTest(
        id="comma_separated_string_input",
        inputs=["1, 2, 3", [1]],
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject comma-separated string",
    ),
    ZipTest(
        id="json_like_string_input",
        inputs=["[1, 2, 3]", [1]],
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject JSON-like string",
    ),
]

# ---------------------------------------------------------------------------
# Error: invalid useLongestLength
# ---------------------------------------------------------------------------
USE_LONGEST_ERROR_TESTS: list[ZipTest] = [
    ZipTest(
        id="use_longest_string",
        inputs=[[1], [2]],
        use_longest_length="true",
        error_code=ZIP_USE_LONGEST_NOT_BOOL_ERROR,
        msg="Should reject string useLongestLength",
    ),
    ZipTest(
        id="use_longest_int",
        inputs=[[1], [2]],
        use_longest_length=1,
        error_code=ZIP_USE_LONGEST_NOT_BOOL_ERROR,
        msg="Should reject int useLongestLength",
    ),
    ZipTest(
        id="use_longest_int_0",
        inputs=[[1, 2]],
        use_longest_length=0,
        error_code=ZIP_USE_LONGEST_NOT_BOOL_ERROR,
        msg="Int 0 should error (not bool)",
    ),
    ZipTest(
        id="use_longest_empty_string",
        inputs=[[1, 2]],
        use_longest_length="",
        error_code=ZIP_USE_LONGEST_NOT_BOOL_ERROR,
        msg="Empty string should error (not bool)",
    ),
    ZipTest(
        id="use_longest_array",
        inputs=[[1, 2]],
        use_longest_length=[],
        error_code=ZIP_USE_LONGEST_NOT_BOOL_ERROR,
        msg="Empty array should error (not bool)",
    ),
    ZipTest(
        id="use_longest_object",
        inputs=[[1, 2]],
        use_longest_length={"a": 1},
        error_code=ZIP_USE_LONGEST_NOT_BOOL_ERROR,
        msg="Object should error (not bool)",
    ),
    ZipTest(
        id="use_longest_nan",
        inputs=[[1, 2]],
        use_longest_length=float("nan"),
        error_code=ZIP_USE_LONGEST_NOT_BOOL_ERROR,
        msg="NaN should error (not bool)",
    ),
    ZipTest(
        id="use_longest_infinity",
        inputs=[[1, 2]],
        use_longest_length=float("inf"),
        error_code=ZIP_USE_LONGEST_NOT_BOOL_ERROR,
        msg="Infinity should error (not bool)",
    ),
]

# ---------------------------------------------------------------------------
# Error: invalid defaults
# ---------------------------------------------------------------------------
DEFAULTS_ERROR_TESTS: list[ZipTest] = [
    ZipTest(
        id="defaults_without_use_longest",
        inputs=[[1, 2], [3]],
        defaults=[0, 0],
        error_code=ZIP_DEFAULTS_WITHOUT_LONGEST_ERROR,
        msg="Should reject defaults without useLongestLength",
    ),
    ZipTest(
        id="defaults_without_longest_false",
        inputs=[[1], [2]],
        use_longest_length=False,
        defaults=[0, 0],
        error_code=ZIP_DEFAULTS_WITHOUT_LONGEST_ERROR,
        msg="defaults with useLongestLength false should error",
    ),
    ZipTest(
        id="defaults_length_mismatch",
        inputs=[[1, 2], [3]],
        use_longest_length=True,
        defaults=[0],
        error_code=ZIP_DEFAULTS_LENGTH_MISMATCH_ERROR,
        msg="Should reject defaults with wrong length",
    ),
    ZipTest(
        id="defaults_too_many",
        inputs=[[1], [2]],
        use_longest_length=True,
        defaults=[0, 0, 0],
        error_code=ZIP_DEFAULTS_LENGTH_MISMATCH_ERROR,
        msg="Should reject defaults longer than inputs",
    ),
    ZipTest(
        id="defaults_not_array",
        inputs=[[1], [2]],
        use_longest_length=True,
        defaults="bad",
        error_code=ZIP_DEFAULTS_NOT_ARRAY_ERROR,
        msg="Should reject non-array defaults",
    ),
    ZipTest(
        id="defaults_not_array_object",
        inputs=[[1]],
        use_longest_length=True,
        defaults={"a": 1},
        error_code=ZIP_DEFAULTS_NOT_ARRAY_ERROR,
        msg="defaults as object should error",
    ),
    ZipTest(
        id="defaults_not_array_int",
        inputs=[[1]],
        use_longest_length=True,
        defaults=1,
        error_code=ZIP_DEFAULTS_NOT_ARRAY_ERROR,
        msg="defaults as int should error",
    ),
]

# ---------------------------------------------------------------------------
# Aggregate and test
# ---------------------------------------------------------------------------
ALL_INPUT_ELEMENT_TESTS = (
    NOT_ARRAY_ELEMENT_TESTS
    + SPECIAL_NUMERIC_ERROR_TESTS
    + BOUNDARY_ERROR_TESTS
    + STRING_EDGE_ERROR_TESTS
    + USE_LONGEST_ERROR_TESTS
    + DEFAULTS_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_INPUT_ELEMENT_TESTS))
def test_zip_not_array_insert(collection, test):
    """Test $zip error with non-array input element from inserted documents."""
    expr = {"inputs": [f"$arr{i}" for i in range(len(test.inputs))]}
    if test.use_longest_length is not None:
        expr["useLongestLength"] = test.use_longest_length
    if test.defaults is not None:
        expr["defaults"] = test.defaults
    doc = {f"arr{i}": arr for i, arr in enumerate(test.inputs)}
    result = execute_expression_with_insert(collection, {"$zip": expr}, doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


TEST_SUBSET_FOR_LITERAL = [
    NOT_ARRAY_ELEMENT_TESTS[0],  # string_input
    NOT_ARRAY_ELEMENT_TESTS[-2],  # non_array_second_position
    SPECIAL_NUMERIC_ERROR_TESTS[0],  # nan_input
    BOUNDARY_ERROR_TESTS[0],  # int32_max_input
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_zip_not_array_literal(collection, test):
    """Test $zip error with non-array literal input element."""
    expr = {"inputs": [{"$literal": a} if isinstance(a, list) else a for a in test.inputs]}
    if test.use_longest_length is not None:
        expr["useLongestLength"] = test.use_longest_length
    if test.defaults is not None:
        expr["defaults"] = test.defaults
    result = execute_expression(collection, {"$zip": expr})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
