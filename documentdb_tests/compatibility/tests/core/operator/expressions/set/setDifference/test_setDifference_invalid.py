"""Tests for $setDifference null propagation, argument validation, and non-array errors."""

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    EXPRESSION_TYPE_MISMATCH_ERROR,
    SET_DIFFERENCE_FIRST_NOT_ARRAY_ERROR,
    SET_DIFFERENCE_SECOND_NOT_ARRAY_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    FLOAT_INFINITY,
    FLOAT_NAN,
    MISSING,
)

# Property [Null Propagation]: a null array argument makes the whole result null.
SETDIFFERENCE_NULL_PROP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_first",
        doc={"arr1": None, "arr2": [1, 2]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=None,
        msg="Should return null when first argument is null",
    ),
    ExpressionTestCase(
        "null_second",
        doc={"arr1": [1, 2], "arr2": None},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=None,
        msg="Should return null when second argument is null",
    ),
    ExpressionTestCase(
        "null_both",
        doc={"arr1": None, "arr2": None},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=None,
        msg="Should return null when both arguments are null",
    ),
]

# Property [Null Elements]: a null element inside an array is an ordinary value
# subject to set membership and dedup.
SETDIFFERENCE_NULL_ELEMENT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_elem_in_first",
        doc={"arr1": [None, 1, 2], "arr2": [1]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[None, 2],
        msg="Should preserve null element in result when not in second array",
    ),
    ExpressionTestCase(
        "null_elem_removed",
        doc={"arr1": [None, 1], "arr2": [None]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[1],
        msg="Should remove null element when it appears in second array",
    ),
    ExpressionTestCase(
        "null_elem_both",
        doc={"arr1": [None, 1], "arr2": [None, 2]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[1],
        msg="Should remove null element when present in both arrays",
    ),
    ExpressionTestCase(
        "null_elem_dedup",
        doc={"arr1": [None, None, 1], "arr2": []},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[None, 1],
        msg="Should deduplicate multiple null elements in first array",
    ),
]

# Property [Valid Element Types]: an array of any BSON element type is accepted
# and returned unchanged when the second array is empty.
SETDIFFERENCE_VALID_ELEMENT_TESTS: list[ExpressionTestCase] = [
    *[
        ExpressionTestCase(
            f"{tid}_elements",
            doc={"arr1": arr, "arr2": []},
            expression={"$setDifference": ["$arr1", "$arr2"]},
            expected=arr,
            msg=f"Should handle an array of {tid} elements",
        )
        for tid, arr in [
            ("string", ["x", "y", "z"]),
            ("int32", [1, 2, 3]),
            ("int64", [Int64(1), Int64(2)]),
            ("double", [1.5, 2.5]),
            ("decimal128", [Decimal128("1"), Decimal128("2")]),
            ("boolean", [False, True]),
            ("null", [None]),
            (
                "date",
                [
                    datetime(2024, 1, 1, tzinfo=timezone.utc),
                    datetime(2024, 1, 2, tzinfo=timezone.utc),
                ],
            ),
            (
                "objectid",
                [ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa"), ObjectId("bbbbbbbbbbbbbbbbbbbbbbbb")],
            ),
            ("regex", [Regex("abc", ""), Regex("def", "")]),
            ("timestamp", [Timestamp(1, 1), Timestamp(2, 1)]),
            ("minkey", [MinKey()]),
            ("maxkey", [MaxKey()]),
            ("object", [{"a": 1}, {"b": 2}]),
            ("nested_array", [[1, 2], [3, 4]]),
        ]
    ],
    ExpressionTestCase(
        "binary_elements",
        doc={"arr1": [Binary(b"\x01\x02\x03", 0), Binary(b"\x04\x05\x06", 0)], "arr2": []},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[b"\x01\x02\x03", b"\x04\x05\x06"],
        msg="Should handle an array of binary elements",
    ),
    ExpressionTestCase(
        "mixed_types",
        doc={"arr1": [1, "a", True, None], "arr2": []},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[1, "a", True, None],
        msg="Should handle an array of mixed BSON type elements",
    ),
]

# Property [Null Precedence]: a null operand propagates null before a non-array
# operand in the other position is validated.
SETDIFFERENCE_NULL_PRECEDENCE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_first_non_array_second",
        expression={"$setDifference": [None, 1]},
        expected=None,
        msg="Null first arg should propagate null, not error on non-array second",
    ),
]

# Property [Missing Field]: a field path to an absent field resolves to null and
# propagates null through the operator.
SETDIFFERENCE_MISSING_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_field_first",
        doc={"a": [1, 2]},
        expression={"$setDifference": [MISSING, "$a"]},
        expected=None,
        msg="Should return null when first field is missing",
    ),
    ExpressionTestCase(
        "missing_field_second",
        doc={"a": [1, 2]},
        expression={"$setDifference": ["$a", MISSING]},
        expected=None,
        msg="Should return null when second field is missing",
    ),
    ExpressionTestCase(
        "missing_field_both",
        doc={"z": 1},
        expression={"$setDifference": ["$x", "$y"]},
        expected=None,
        msg="Should return null when both fields are missing",
    ),
]

SETDIFFERENCE_SUCCESS_TESTS: list[ExpressionTestCase] = (
    SETDIFFERENCE_NULL_PROP_TESTS
    + SETDIFFERENCE_NULL_ELEMENT_TESTS
    + SETDIFFERENCE_VALID_ELEMENT_TESTS
    + SETDIFFERENCE_NULL_PRECEDENCE_TESTS
    + SETDIFFERENCE_MISSING_FIELD_TESTS
)

# Property [Non-Array First]: a non-array first argument errors, and every
# non-array BSON type is rejected.
SETDIFFERENCE_NON_ARRAY_FIRST_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"{tid}_first",
        doc={"arr1": val, "arr2": []},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        error_code=SET_DIFFERENCE_FIRST_NOT_ARRAY_ERROR,
        msg=f"Should return error for {tid} as first argument",
    )
    for tid, val in [
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("decimal128", Decimal128("1")),
        ("string", "hello"),
        ("bool", True),
        ("object", {"a": 1}),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("objectid", ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa")),
        ("regex", Regex("abc", "")),
        ("binary", Binary(b"\x01", 0)),
        ("timestamp", Timestamp(1, 1)),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("nan", FLOAT_NAN),
        ("infinity", FLOAT_INFINITY),
        ("decimal_nan", DECIMAL128_NAN),
        ("decimal_infinity", DECIMAL128_INFINITY),
    ]
]

# Property [Non-Array Second]: a non-array second argument errors, and every
# non-array BSON type is rejected.
SETDIFFERENCE_NON_ARRAY_SECOND_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"{tid}_second",
        doc={"arr1": ["a"], "arr2": val},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        error_code=SET_DIFFERENCE_SECOND_NOT_ARRAY_ERROR,
        msg=f"Should return error for {tid} as second argument",
    )
    for tid, val in [
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("decimal128", Decimal128("1")),
        ("string", "hello"),
        ("bool", True),
        ("object", {"a": 1}),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("objectid", ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa")),
        ("regex", Regex("abc", "")),
        ("binary", Binary(b"\x01", 0)),
        ("timestamp", Timestamp(1, 1)),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("nan", FLOAT_NAN),
        ("infinity", FLOAT_INFINITY),
        ("decimal_nan", DECIMAL128_NAN),
        ("decimal_infinity", DECIMAL128_INFINITY),
    ]
]

# Property [Arity]: $setDifference requires exactly two arguments.
SETDIFFERENCE_ARITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "arity_zero",
        expression={"$setDifference": []},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should return error for zero arguments",
    ),
    ExpressionTestCase(
        "arity_one",
        expression={"$setDifference": [[1]]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should return error for one argument",
    ),
    ExpressionTestCase(
        "arity_three",
        expression={"$setDifference": [[1], [2], [3]]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should return error for three arguments",
    ),
]

# Property [Field Resolves To Non-Array]: a field path that resolves to a
# non-array value errors on the position it occupies.
SETDIFFERENCE_FIELD_NON_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "field_resolves_int_first",
        doc={"a": 5},
        expression={"$setDifference": ["$a", [1]]},
        error_code=SET_DIFFERENCE_FIRST_NOT_ARRAY_ERROR,
        msg="Field resolving to int should error on first position",
    ),
    ExpressionTestCase(
        "field_resolves_string_first",
        doc={"a": "hello"},
        expression={"$setDifference": ["$a", [1]]},
        error_code=SET_DIFFERENCE_FIRST_NOT_ARRAY_ERROR,
        msg="Field resolving to string should error on first position",
    ),
    ExpressionTestCase(
        "field_resolves_int_second",
        doc={"a": 5},
        expression={"$setDifference": [[1], "$a"]},
        error_code=SET_DIFFERENCE_SECOND_NOT_ARRAY_ERROR,
        msg="Field resolving to int should error on second position",
    ),
]

SETDIFFERENCE_ERROR_TESTS: list[ExpressionTestCase] = (
    SETDIFFERENCE_NON_ARRAY_FIRST_TESTS
    + SETDIFFERENCE_NON_ARRAY_SECOND_TESTS
    + SETDIFFERENCE_ARITY_TESTS
    + SETDIFFERENCE_FIELD_NON_ARRAY_TESTS
)

SETDIFFERENCE_INVALID_TESTS: list[ExpressionTestCase] = (
    SETDIFFERENCE_SUCCESS_TESTS + SETDIFFERENCE_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(SETDIFFERENCE_INVALID_TESTS))
def test_setDifference_invalid(collection, test):
    """Test $setDifference null, missing, arity, and non-array handling."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
