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

# Property [Array Handling]: $min has two modes. With multiple operands,
# arrays are compared as values, not traversed. With a single operand that
# resolves to an array, $min traverses into it and returns the minimum element.
MIN_ARRAY_HANDLING_TESTS: list[ExpressionTestCase] = [
    # Same array [5, 1, 8] through all three expression forms.
    ExpressionTestCase(
        "single_expression_traverses",
        expression={"$min": "$a"},
        doc={"a": [5, 1, 8]},
        expected=1,
        msg="$min with a single expression should traverse the array and return the min element",
    ),
    ExpressionTestCase(
        "single_element_list_traverses",
        expression={"$min": ["$a"]},
        doc={"a": [5, 1, 8]},
        expected=1,
        msg="$min with a single-element list should unwrap and traverse the array",
    ),
    ExpressionTestCase(
        "multi_operand_does_not_traverse",
        expression={"$min": ["$a", "$b"]},
        doc={"a": [5, 1, 8], "b": 3},
        expected=3,
        msg="$min with multiple operands should return the scalar, not traverse the array",
    ),
    # Traversal skips null elements.
    ExpressionTestCase(
        "traversal_skips_null",
        expression={"$min": "$a"},
        doc={"a": [None, 5, None, 3]},
        expected=3,
        msg="$min should skip null elements when traversing an array",
    ),
    ExpressionTestCase(
        "traversal_all_null",
        expression={"$min": "$a"},
        doc={"a": [None, None, None]},
        expected=None,
        msg="$min should return null when all array elements are null",
    ),
    ExpressionTestCase(
        "traversal_empty_array",
        expression={"$min": "$a"},
        doc={"a": []},
        expected=None,
        msg="$min should return null for an empty array",
    ),
    # Only one level of traversal: nested arrays are compared as values.
    ExpressionTestCase(
        "traversal_nested_not_recursive",
        expression={"$min": "$a"},
        doc={"a": [1, [2, 3]]},
        expected=1,
        msg="$min should not recurse into nested arrays during traversal",
    ),
    # Mixed types: BSON ordering applies during traversal.
    ExpressionTestCase(
        "traversal_mixed_bson_types",
        expression={"$min": "$a"},
        doc={"a": [42, "hello", True]},
        expected=42,
        msg="$min should use BSON type ordering when traversing mixed-type arrays",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(MIN_ARRAY_HANDLING_TESTS))
def test_min_array_cases(collection, test_case: ExpressionTestCase):
    """Test $min array handling cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc or {})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
