"""
Expression and field path tests for $reverseArray expression.

Tests field path lookups (including composite array-of-objects paths),
$let and system variables ($$ROOT/$$CURRENT/$$REMOVE), null/missing field
handling, self-composition (nested $reverseArray), expression-operator
operands (Rule 3), algebraic invariants (length and multiset preservation,
Rule 17), the array return-type assertion (Rule 1), and float NaN element
preservation.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import FLOAT_NAN

# Property [Field-path operand]: the operand may be a (possibly nested) field
# path rather than a literal array; a path segment that doesn't resolve to a
# value returns null instead of erroring.
FIELD_LOOKUP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="nested_field_path",
        expression={"$reverseArray": "$a.b"},
        doc={"a": {"b": [1, 2, 3]}},
        expected=[3, 2, 1],
        msg="Should resolve nested field path",
    ),
    ExpressionTestCase(
        id="deeply_nested_field",
        expression={"$reverseArray": "$a.b.c"},
        doc={"a": {"b": {"c": [10, 20, 30]}}},
        expected=[30, 20, 10],
        msg="Should resolve deeply nested field path",
    ),
    ExpressionTestCase(
        id="nonexistent_field_null",
        expression={"$reverseArray": "$a.nonexistent"},
        doc={"a": {"missing": 1}},
        expected=None,
        msg="Non-existent field should return null",
    ),
]

# Property [Composite/positional path resolution]: field paths that traverse
# array-of-objects (composite paths) or numeric-looking path segments resolve
# per the engine's path semantics (object key vs. array index vs. no match)
# before being reversed, distinct from actual indexing via $arrayElemAt.
COMPOSITE_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="composite_array",
        expression={"$reverseArray": "$x.y"},
        doc={"x": [{"y": 10}, {"y": 20}, {"y": 30}]},
        expected=[30, 20, 10],
        msg="Composite array path from array-of-objects",
    ),
    ExpressionTestCase(
        id="composite_array_path_nested",
        expression={"$reverseArray": "$a.b"},
        doc={"a": [{"b": [1, 2]}, {"b": [3, 4]}]},
        expected=[[3, 4], [1, 2]],
        msg="Composite array path reverses",
    ),
    ExpressionTestCase(
        id="array_index_on_object_key",
        expression={"$reverseArray": "$a.0.b"},
        doc={"a": {"0": {"b": [1, 2, 3]}}},
        expected=[3, 2, 1],
        msg="Numeric key on object resolves correctly",
    ),
    ExpressionTestCase(
        id="object_key_zero",
        expression={"$reverseArray": "$a.0"},
        doc={"a": {"0": [1, 2, 3]}},
        expected=[3, 2, 1],
        msg="$a.0 resolves as field named '0' on object",
    ),
    ExpressionTestCase(
        id="numeric_index_on_array",
        expression={"$reverseArray": "$a.0"},
        doc={"a": [[3, 2, 1], [6, 5, 4]]},
        expected=[],
        msg="Numeric index $a.0 on array-of-arrays resolves to empty",
    ),
    ExpressionTestCase(
        id="arrayElemAt_index_on_array",
        expression={"$reverseArray": {"$arrayElemAt": ["$arr", 0]}},
        doc={"arr": [[1, 2], [3, 4]]},
        expected=[2, 1],
        msg="Contrast with numeric_index_on_array: $arrayElemAt actually indexes"
        " (unlike the $a.0 path segment) and returns the element to reverse",
    ),
]

# Property [$let and system-variable operand]: the operand may be a
# $let-bound variable or a system variable ($$ROOT/$$CURRENT), resolved to its
# underlying array the same way a plain field path would be.
LET_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="let_field_ref",
        expression={"$let": {"vars": {"myArr": "$arr"}, "in": {"$reverseArray": "$$myArr"}}},
        doc={"arr": [1, 2]},
        expected=[2, 1],
        msg="$let with field reference",
    ),
    ExpressionTestCase(
        id="root_variable",
        expression={"$reverseArray": "$$ROOT.values"},
        doc={"_id": 1, "values": [1, 2, 3]},
        expected=[3, 2, 1],
        msg="Should work with $$ROOT",
    ),
    ExpressionTestCase(
        id="current_variable",
        expression={"$reverseArray": "$$CURRENT.values"},
        doc={"_id": 2, "values": [1, 2, 3]},
        expected=[3, 2, 1],
        msg="$$CURRENT should be equivalent to field path",
    ),
]

# Property [Null/missing operand via expression resolution]: a missing field,
# $$REMOVE, or an array literal built from field references (rather than a
# plain field path) each resolve correctly before reversal — null propagates,
# and constructed array literals are reversed like any other array.
NULL_MISSING_EXPR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="missing_field",
        expression={"$reverseArray": "$nonexistent"},
        doc={"other": 1},
        expected=None,
        msg="Missing field should return null",
    ),
    ExpressionTestCase(
        id="missing_input_type_is_null",
        expression={"$type": {"$reverseArray": "$nonexistent"}},
        doc={"x": 1},
        expected="null",
        msg="Missing field should produce null type",
    ),
    ExpressionTestCase(
        id="remove_variable",
        expression={"$reverseArray": "$$REMOVE"},
        doc={"x": 1},
        expected=None,
        msg="$$REMOVE returns null",
    ),
    ExpressionTestCase(
        id="field_ref_wrapped_array",
        expression={"$reverseArray": ["$arr"]},
        doc={"arr": [1, 2, 3]},
        expected=[3, 2, 1],
        msg="[$arr] where arr is array resolves correctly",
    ),
    ExpressionTestCase(
        id="array_of_field_refs",
        expression={"$reverseArray": [["$x", "$y"]]},
        doc={"x": 1, "y": 2},
        expected=[2, 1],
        msg="Array literal built from multiple field refs, then reversed",
    ),
]

# Property [Self-composition]: $reverseArray may be nested inside itself;
# applying it twice is the identity transform (reverse undoes reverse).
SELF_COMPOSITION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="double_reverse",
        expression={"$reverseArray": {"$reverseArray": "$arr"}},
        doc={"arr": [1, 2, 3]},
        expected=[1, 2, 3],
        msg="Double reverse = identity",
    ),
]

# Property [Expression-operator operand] (Rule 3): the operand may be the
# output of another expression operator, not just a literal or field
# reference.
EXPRESSION_OPERAND_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="operand_from_slice",
        expression={"$reverseArray": {"$slice": [[1, 2, 3, 4], 2]}},
        doc={"x": 0},
        expected=[2, 1],
        msg="Should reverse an operand produced by $slice",
    ),
]

# Property [Algebraic invariants] (Rule 17):
#   - Length invariant: reversing never changes the array length. Includes an
#     even-length case (length_invariant_six) alongside the odd-length case
#     (length_invariant_five) to exercise the swap-loop boundary in both
#     parities — an off-by-one in an in-place swap-based reverse is more
#     likely to surface on one parity than the other.
#   - Multiset preservation: the reversed array has the same elements, with the
#     same per-value counts, as the input (compared order-independently by
#     sorting both sides). Uses an input with an element repeated 3x
#     (multiset_preservation_duplicate_counts) so an implementation bug that
#     preserves the *set* of distinct values but drops/duplicates individual
#     occurrences (e.g. a faulty swap that overwrites one duplicate with
#     another) would be caught; a simple set-equality check would not catch it.
ALGEBRAIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="length_invariant_empty",
        expression={"$eq": [{"$size": {"$reverseArray": "$arr"}}, {"$size": "$arr"}]},
        doc={"arr": []},
        expected=True,
        msg="Reversed length equals input length (size 0)",
    ),
    ExpressionTestCase(
        id="length_invariant_single",
        expression={"$eq": [{"$size": {"$reverseArray": "$arr"}}, {"$size": "$arr"}]},
        doc={"arr": [42]},
        expected=True,
        msg="Reversed length equals input length (size 1)",
    ),
    ExpressionTestCase(
        id="length_invariant_five",
        expression={"$eq": [{"$size": {"$reverseArray": "$arr"}}, {"$size": "$arr"}]},
        doc={"arr": [1, 2, 3, 4, 5]},
        expected=True,
        msg="Reversed length equals input length (size 5, odd — exercises a"
        " middle-element swap boundary)",
    ),
    ExpressionTestCase(
        id="length_invariant_six",
        expression={"$eq": [{"$size": {"$reverseArray": "$arr"}}, {"$size": "$arr"}]},
        doc={"arr": [1, 2, 3, 4, 5, 6]},
        expected=True,
        msg="Reversed length equals input length (size 6, even — exercises the"
        " opposite swap-loop parity from size 5)",
    ),
    ExpressionTestCase(
        id="multiset_preservation",
        expression={
            "$eq": [
                {"$sortArray": {"input": {"$reverseArray": "$arr"}, "sortBy": 1}},
                {"$sortArray": {"input": "$arr", "sortBy": 1}},
            ]
        },
        doc={"arr": [3, 1, 2, 3, 5]},
        expected=True,
        msg="Reversed array preserves the same multiset of elements",
    ),
    ExpressionTestCase(
        id="multiset_preservation_duplicate_counts",
        expression={
            "$eq": [
                {"$sortArray": {"input": {"$reverseArray": "$arr"}, "sortBy": 1}},
                {"$sortArray": {"input": "$arr", "sortBy": 1}},
            ]
        },
        doc={"arr": [7, 7, 7, 2, 9]},
        expected=True,
        msg="Reversed array preserves exact per-value counts, not just the set"
        " of distinct values (value 7 appears exactly 3 times either way)",
    ),
]

# Property [NaN element preservation]: float NaN elements (including multiple
# NaNs in the same array) survive reversal unchanged — reversal never
# normalizes or collapses NaN payloads.
FLOAT_NAN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="float_nan_preserved",
        expression={"$arrayElemAt": [{"$reverseArray": "$arr"}, 2]},
        doc={"arr": [FLOAT_NAN, 1, 2]},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="Float NaN element preserved after reversal",
    ),
    ExpressionTestCase(
        id="multiple_float_nan_preserved",
        expression={"$arrayElemAt": [{"$reverseArray": "$arr"}, 1]},
        doc={"arr": [FLOAT_NAN, FLOAT_NAN, 1]},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="Multiple float NaN elements preserved after reversal",
    ),
]

# Property [Return type] (Rule 1): a successful $reverseArray yields BSON
# type "array".
RETURN_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="return_type_is_array",
        expression={"$type": {"$reverseArray": [[1, 2, 3]]}},
        doc={"x": 0},
        expected="array",
        msg="Result of $reverseArray should be BSON type 'array'",
    ),
    ExpressionTestCase(
        id="outer_array_wrap_value",
        expression={"$reverseArray": [[1, 2, 3]]},
        doc={"x": 0},
        expected=[3, 2, 1],
        msg="Outer-array-wrapped operand [[1,2,3]] unwraps to [1,2,3] and reverses"
        " to the exact value, not just BSON type 'array'",
    ),
]

ALL_EXPR_TESTS = (
    FIELD_LOOKUP_TESTS
    + COMPOSITE_PATH_TESTS
    + LET_TESTS
    + NULL_MISSING_EXPR_TESTS
    + SELF_COMPOSITION_TESTS
    + EXPRESSION_OPERAND_TESTS
    + ALGEBRAIC_TESTS
    + RETURN_TYPE_TESTS
    + FLOAT_NAN_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_EXPR_TESTS))
def test_reverseArray_expression(collection, test):
    """Test $reverseArray with field paths and expressions."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
