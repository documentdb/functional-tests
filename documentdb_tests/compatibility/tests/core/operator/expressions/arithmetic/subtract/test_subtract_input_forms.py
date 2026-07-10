import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import EXPRESSION_TYPE_MISMATCH_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import INT32_ZERO

pytestmark = pytest.mark.aggregate

# Property [Nested expressions]: $subtract accepts other expressions as operands.
NESTED_EXPRESSION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_subtract_2",
        doc={},
        expression={"$subtract": [{"$subtract": [10, 3]}, 2]},
        expected=5,
        msg="$subtract should accept a nested $subtract expression as the minuend",
    ),
    ExpressionTestCase(
        "nested_subtract_3",
        doc={},
        expression={"$subtract": [{"$subtract": [{"$subtract": [100, 10]}, 20]}, 30]},
        expected=40,
        msg="$subtract should support three levels of nested $subtract expressions",
    ),
]

# Property [Field path lookups]: $subtract resolves nested and deeply-nested field paths.
FIELD_PATH_LOOKUP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_field",
        doc={"a": {"b": 10}, "c": 3},
        expression={"$subtract": ["$a.b", "$c"]},
        expected=7,
        msg="$subtract should resolve a nested field path such as $a.b",
    ),
    ExpressionTestCase(
        "nonexistent_field",
        doc={"a": {"missing": 1}, "b": 5},
        expression={"$subtract": ["$a.nonexistent", "$b"]},
        expected=None,
        msg="$subtract should return null when a field path resolves to a missing field",
    ),
    ExpressionTestCase(
        "deeply_nested_field",
        doc={"a": {"b": {"c": {"d": 20}}}},
        expression={"$subtract": ["$a.b.c.d", 8]},
        expected=12,
        msg="$subtract should resolve a deeply nested field path",
    ),
]

# Property [Array element access]: $subtract works with $arrayElemAt expressions as operands.
ARRAY_ELEMENT_ACCESS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "array_index",
        doc={"arr": [10, 5, 2]},
        expression={
            "$subtract": [
                {"$arrayElemAt": ["$arr", INT32_ZERO]},
                {"$arrayElemAt": ["$arr", 1]},
            ]
        },
        expected=5,
        msg="$subtract should support $arrayElemAt expressions as operands",
    ),
]

# Property [Composite array rejection]: $subtract rejects a composite array from $x.y on
# an array-of-objects.
COMPOSITE_ARRAY_REJECTION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "composite_array_field",
        doc={"x": [{"y": 10}, {"y": 3}]},
        expression={"$subtract": "$x.y"},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$subtract should reject a composite array produced by $x.y on an array-of-objects",
    ),
]

SUBTRACT_INPUT_FORM_TESTS: list[ExpressionTestCase] = (
    NESTED_EXPRESSION_TESTS
    + FIELD_PATH_LOOKUP_TESTS
    + ARRAY_ELEMENT_ACCESS_TESTS
    + COMPOSITE_ARRAY_REJECTION_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SUBTRACT_INPUT_FORM_TESTS))
def test_subtract_input_forms(collection, test_case: ExpressionTestCase):
    """Test $subtract with various expression input forms and field path lookups."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
