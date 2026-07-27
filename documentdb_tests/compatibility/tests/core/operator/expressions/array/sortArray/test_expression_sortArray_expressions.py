"""
Expression and field path tests for $sortArray expression.

Tests field path lookups (including composite array-of-objects paths),
$let and system variables ($$ROOT/$$CURRENT/$$REMOVE), null/missing field
handling, and float NaN sort ordering.
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

# Property [Field-path operand]: the input may be a (possibly nested) field
# path rather than a literal array; a path segment that doesn't resolve to a
# value returns null instead of erroring.
FIELD_LOOKUP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="nested_field_path",
        expression={"$sortArray": {"input": "$a.b", "sortBy": 1}},
        doc={"a": {"b": [3, 1, 2]}},
        expected=[1, 2, 3],
        msg="Should resolve nested field path",
    ),
    ExpressionTestCase(
        id="deeply_nested_field",
        expression={"$sortArray": {"input": "$a.b.c", "sortBy": -1}},
        doc={"a": {"b": {"c": [30, 10, 20]}}},
        expected=[30, 20, 10],
        msg="Should resolve deeply nested field path",
    ),
    ExpressionTestCase(
        id="nonexistent_field_null",
        expression={"$sortArray": {"input": "$a.nonexistent", "sortBy": 1}},
        doc={"a": {"missing": 1}},
        expected=None,
        msg="Non-existent field should return null",
    ),
]

# Property [Composite/positional path resolution]: field paths that traverse
# array-of-objects (composite paths) or numeric-looking path segments resolve
# per the engine's path semantics (object key vs. array index vs. no match)
# before being sorted.
COMPOSITE_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="composite_array",
        expression={"$sortArray": {"input": "$x.y", "sortBy": 1}},
        doc={"x": [{"y": 30}, {"y": 10}, {"y": 20}]},
        expected=[10, 20, 30],
        msg="Composite array path from array-of-objects",
    ),
    ExpressionTestCase(
        id="object_key_zero",
        expression={"$sortArray": {"input": "$a.0", "sortBy": 1}},
        doc={"a": {"0": [3, 1, 2]}},
        expected=[1, 2, 3],
        msg="$a.0 resolves as field named '0' on object",
    ),
    ExpressionTestCase(
        id="numeric_index_on_array",
        expression={"$sortArray": {"input": "$a.0", "sortBy": 1}},
        doc={"a": [[3, 1, 2], [6, 4, 5]]},
        expected=[],
        msg="Numeric index $a.0 on array-of-arrays resolves to empty",
    ),
]

# Property [$let and system-variable operand]: the input may be a $let-bound
# variable or a system variable ($$ROOT/$$CURRENT), resolved to its
# underlying array the same way a plain field path would be.
SYSTEM_VAR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="let_variable",
        expression={
            "$let": {"vars": {"arr": "$arr"}, "in": {"$sortArray": {"input": "$$arr", "sortBy": 1}}}
        },
        doc={"arr": [3, 1, 2]},
        expected=[1, 2, 3],
        msg="Should work with $let variable",
    ),
    ExpressionTestCase(
        id="root_variable",
        expression={"$sortArray": {"input": "$$ROOT.values", "sortBy": 1}},
        doc={"_id": 1, "values": [3, 1, 2]},
        expected=[1, 2, 3],
        msg="Should work with $$ROOT",
    ),
    ExpressionTestCase(
        id="current_variable",
        expression={"$sortArray": {"input": "$$CURRENT.values", "sortBy": 1}},
        doc={"_id": 2, "values": [3, 1, 2]},
        expected=[1, 2, 3],
        msg="$$CURRENT should be equivalent to field path",
    ),
]

# Property [Null/missing input via expression resolution]: a missing field or
# $$REMOVE resolves to null and propagates as null rather than erroring.
NULL_MISSING_EXPR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="missing_field",
        expression={"$sortArray": {"input": "$nonexistent", "sortBy": 1}},
        doc={"other": 1},
        expected=None,
        msg="Missing field should return null",
    ),
    ExpressionTestCase(
        id="missing_input_type_is_null",
        expression={"$type": {"$sortArray": {"input": "$nonexistent", "sortBy": 1}}},
        doc={"x": 1},
        expected="null",
        msg="Missing field should produce null type",
    ),
    ExpressionTestCase(
        id="remove_variable",
        expression={"$sortArray": {"input": "$$REMOVE", "sortBy": 1}},
        doc={"x": 1},
        expected=None,
        msg="$$REMOVE returns null",
    ),
]

# Property [NaN sort ordering]: float NaN elements sort before all numbers
# (including other NaNs, which retain their relative positions among
# themselves), asserted via $arrayElemAt + pytest.approx since NaN can't be
# equality-compared inside a list.
FLOAT_NAN_SORT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="float_nan_sorts_first",
        expression={"$arrayElemAt": [{"$sortArray": {"input": "$arr", "sortBy": 1}}, 0]},
        doc={"arr": [1, FLOAT_NAN, 3, FLOAT_NAN, 2]},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="Float NaN should sort before numbers",
    ),
    ExpressionTestCase(
        id="float_nan_second_position",
        expression={"$arrayElemAt": [{"$sortArray": {"input": "$arr", "sortBy": 1}}, 1]},
        doc={"arr": [1, FLOAT_NAN, 3, FLOAT_NAN, 2]},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="Second NaN should also sort before numbers",
    ),
    ExpressionTestCase(
        id="non_nan_after_nan",
        expression={"$arrayElemAt": [{"$sortArray": {"input": "$arr", "sortBy": 1}}, 2]},
        doc={"arr": [1, FLOAT_NAN, 3, FLOAT_NAN, 2]},
        expected=1,
        msg="First non-NaN value after NaN sorting",
    ),
]

# Property [Expression-operator input] (Rule 3): `input` may be produced by
# an expression operator or an array expression of field refs, not just a
# literal/field path.
EXPRESSION_INPUT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="input_from_concatArrays",
        expression={"$sortArray": {"input": {"$concatArrays": [[3], [1, 2]]}, "sortBy": 1}},
        doc={"x": 0},
        expected=[1, 2, 3],
        msg="Should sort input produced by $concatArrays",
    ),
    ExpressionTestCase(
        id="input_array_of_field_refs",
        expression={"$sortArray": {"input": ["$x", "$y"], "sortBy": 1}},
        doc={"x": 3, "y": 1},
        expected=[1, 3],
        msg="Should sort an array expression built from field references",
    ),
]

# Property [Algebraic invariants] (Rule 17): idempotency, the sortBy-direction
# relationship, and length / multiset (permutation) invariants. (Stability is
# covered elsewhere.)
ALGEBRAIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="idempotent_sort",
        expression={
            "$eq": [
                {
                    "$sortArray": {
                        "input": {"$sortArray": {"input": "$arr", "sortBy": 1}},
                        "sortBy": 1,
                    }
                },
                {"$sortArray": {"input": "$arr", "sortBy": 1}},
            ]
        },
        doc={"arr": [3, 1, 2]},
        expected=True,
        msg="Idempotency: sorting an already-sorted array yields the same result",
    ),
    ExpressionTestCase(
        id="direction_reverse_of_asc_equals_desc",
        expression={
            "$eq": [
                {"$reverseArray": {"$sortArray": {"input": "$arr", "sortBy": 1}}},
                {"$sortArray": {"input": "$arr", "sortBy": -1}},
            ]
        },
        doc={"arr": [3, 1, 2, 5, 4]},
        expected=True,
        msg="Direction relationship: reverse of asc-sort equals desc-sort (no cross-type ties)",
    ),
    ExpressionTestCase(
        id="length_invariant_empty",
        expression={
            "$eq": [{"$size": {"$sortArray": {"input": "$arr", "sortBy": 1}}}, {"$size": "$arr"}]
        },
        doc={"arr": []},
        expected=True,
        msg="Length invariant (size 0)",
    ),
    ExpressionTestCase(
        id="length_invariant_single",
        expression={
            "$eq": [{"$size": {"$sortArray": {"input": "$arr", "sortBy": 1}}}, {"$size": "$arr"}]
        },
        doc={"arr": [9]},
        expected=True,
        msg="Length invariant (size 1)",
    ),
    ExpressionTestCase(
        id="length_invariant_five",
        expression={
            "$eq": [{"$size": {"$sortArray": {"input": "$arr", "sortBy": 1}}}, {"$size": "$arr"}]
        },
        doc={"arr": [5, 4, 3, 2, 1]},
        expected=True,
        msg="Length invariant (size 5)",
    ),
    ExpressionTestCase(
        id="multiset_permutation_invariant",
        expression={
            "$eq": [
                {"$sortArray": {"input": "$a", "sortBy": 1}},
                {"$sortArray": {"input": "$b", "sortBy": 1}},
            ]
        },
        doc={"a": [3, 1, 2, 3], "b": [2, 3, 1, 3]},
        expected=True,
        msg="Multiset/permutation invariant: two permutations of a multiset sort identically",
    ),
]

ALL_EXPR_TESTS = (
    FIELD_LOOKUP_TESTS
    + COMPOSITE_PATH_TESTS
    + SYSTEM_VAR_TESTS
    + NULL_MISSING_EXPR_TESTS
    + EXPRESSION_INPUT_TESTS
    + ALGEBRAIC_TESTS
    + FLOAT_NAN_SORT_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_EXPR_TESTS))
def test_sortArray_expression(collection, test):
    """Test $sortArray with field paths and expressions."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
