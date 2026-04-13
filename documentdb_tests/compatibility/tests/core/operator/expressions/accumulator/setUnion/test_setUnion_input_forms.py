from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import SETUNION_TYPE_ERROR
from documentdb_tests.framework.parametrize import pytest_params

# Property [Return Type]: the result is always an array when the operation
# succeeds.
SETUNION_RETURN_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "rettype_disjoint",
        expression={"$type": {"$setUnion": ["$a", "$b"]}},
        doc={"a": [1, 2], "b": [3, 4]},
        expected="array",
        msg="$setUnion of disjoint arrays should return an array",
    ),
    ExpressionTestCase(
        "rettype_empty",
        expression={"$type": {"$setUnion": ["$a", "$b"]}},
        doc={"a": [], "b": []},
        expected="array",
        msg="$setUnion of empty arrays should return an array",
    ),
    ExpressionTestCase(
        "rettype_zero_args",
        expression={"$type": {"$setUnion": []}},
        expected="array",
        msg="$setUnion with zero arguments should return an array",
    ),
]

# Property [Arity]: $setUnion accepts zero, one, or many array arguments,
# including large argument counts and large arrays.
SETUNION_ARITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "arity_zero_args",
        expression={"$setUnion": []},
        expected=[],
        msg="$setUnion should return [] when given zero arguments",
    ),
    ExpressionTestCase(
        "arity_single_array",
        expression={"$setUnion": ["$a"]},
        doc={"a": [3, 1, 2, 1]},
        expected=[1, 2, 3],
        msg="$setUnion should return deduplicated contents of a single array argument",
    ),
    ExpressionTestCase(
        "arity_many_arrays",
        expression={"$setUnion": ["$a", "$b", "$c"]},
        doc={"a": [1, 2], "b": [2, 3], "c": [3, 4]},
        expected=[1, 2, 3, 4],
        msg="$setUnion should accept multiple array arguments",
    ),
    ExpressionTestCase(
        "arity_large_args",
        expression={"$setUnion": ["$a"] * 10_000},
        doc={"a": [1, 2, 3]},
        expected=[1, 2, 3],
        msg="$setUnion should accept 10,000 arguments",
    ),
]

# Property [Input Forms]: $setUnion accepts field paths, literal values,
# and expression operands.
SETUNION_INPUT_FORM_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "input_literal_array",
        expression={"$setUnion": ["$a", [3, 4]]},
        doc={"a": [1, 2]},
        expected=[1, 2, 3, 4],
        msg="$setUnion should accept a literal array alongside a field reference",
    ),
    ExpressionTestCase(
        "input_literal_error",
        expression={"$setUnion": ["$a", "not an array"]},
        doc={"a": [1, 2]},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject a literal non-array value as an operand",
    ),
    ExpressionTestCase(
        "input_expression_operand",
        expression={"$setUnion": [{"$concatArrays": ["$a", "$b"]}, "$c"]},
        doc={"a": [1], "b": [2], "c": [3]},
        expected=[1, 2, 3],
        msg="$setUnion should accept an expression that resolves to an array",
    ),
    ExpressionTestCase(
        "input_expression_error",
        expression={"$setUnion": [{"$add": ["$a", "$b"]}, "$c"]},
        doc={"a": 1, "b": 2, "c": [1, 2]},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject an expression that returns a non-array type",
    ),
    ExpressionTestCase(
        "input_array_index",
        expression={"$setUnion": [{"$arrayElemAt": ["$a", 0]}, "$b"]},
        doc={"a": [[1, 2]], "b": [2, 3]},
        expected=[1, 2, 3],
        msg="$setUnion should accept an array element accessed by index",
    ),
    ExpressionTestCase(
        "input_array_index_error",
        expression={"$setUnion": [{"$arrayElemAt": ["$a", 0]}, "$b"]},
        doc={"a": ["not an array"], "b": [1, 2]},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should reject an array element that is not an array",
    ),
    ExpressionTestCase(
        "input_composite_array",
        expression={"$setUnion": "$a.vals"},
        doc={"a": [{"vals": [1, 2]}, {"vals": [2, 3]}]},
        expected=[[1, 2], [2, 3]],
        msg="$setUnion should traverse a composite array path and collect values",
    ),
    ExpressionTestCase(
        "input_composite_array_scalars",
        expression={"$setUnion": "$a.vals"},
        doc={"a": [{"vals": 1}, {"vals": 2}]},
        expected=[1, 2],
        msg="$setUnion should treat scalar values collected via composite path as array elements",
    ),
    ExpressionTestCase(
        "input_nested_setunion",
        expression={"$setUnion": [{"$setUnion": ["$a", "$b"]}, "$c"]},
        doc={"a": [1, 2], "b": [2, 3], "c": [3, 4]},
        expected=[1, 2, 3, 4],
        msg="$setUnion should accept a nested $setUnion as an operand",
    ),
    ExpressionTestCase(
        "input_nested_setunion_associative",
        expression={"$setUnion": ["$a", {"$setUnion": ["$b", "$c"]}]},
        doc={"a": [1, 2], "b": [2, 3], "c": [3, 4]},
        expected=[1, 2, 3, 4],
        msg="$setUnion should be associative: union(A, union(B, C)) == union(union(A, B), C)",
    ),
]

SETUNION_INPUT_FORMS_TESTS_ALL = (
    SETUNION_RETURN_TYPE_TESTS + SETUNION_ARITY_TESTS + SETUNION_INPUT_FORM_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SETUNION_INPUT_FORMS_TESTS_ALL))
def test_setunion_input_forms(collection, test_case: ExpressionTestCase):
    """Test $setUnion input form and arity cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc or {})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        ignore_order=True,
    )
