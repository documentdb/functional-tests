"""
Core behavior tests for $in expression.

Tests value found/not found, mixed types, and large arrays.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Success: value found in array → True
FOUND_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="found_int",
        doc={"val": 2, "arr": [1, 2, 3]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find int in array",
    ),
    ExpressionTestCase(
        id="found_first",
        doc={"val": 1, "arr": [1, 2, 3]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find first element",
    ),
    ExpressionTestCase(
        id="found_last",
        doc={"val": 3, "arr": [1, 2, 3]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find last element",
    ),
    ExpressionTestCase(
        id="found_string",
        doc={"val": "b", "arr": ["a", "b", "c"]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find string in array",
    ),
    ExpressionTestCase(
        id="found_bool_true",
        doc={"val": True, "arr": [True, False]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find true in array",
    ),
    ExpressionTestCase(
        id="found_bool_false",
        doc={"val": False, "arr": [True, False]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find false in array",
    ),
    ExpressionTestCase(
        id="found_null",
        doc={"val": None, "arr": [None, 1, 2]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find null in array",
    ),
    ExpressionTestCase(
        id="found_nested_array",
        doc={"val": [3, 4], "arr": [[1, 2], [3, 4]]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find nested array",
    ),
    ExpressionTestCase(
        id="found_object",
        doc={"val": {"a": 1}, "arr": [{"a": 1}, {"b": 2}]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find object in array",
    ),
    ExpressionTestCase(
        id="found_single_element",
        doc={"val": 42, "arr": [42]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find value in single-element array",
    ),
    ExpressionTestCase(
        id="found_duplicate",
        doc={"val": 5, "arr": [5, 5, 5]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find value in array of duplicates",
    ),
]

# Success: value not found → False
NOT_FOUND_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="not_found_int",
        doc={"val": 4, "arr": [1, 2, 3]},
        expression={"$in": ["$val", "$arr"]},
        expected=False,
        msg="Should not find absent int",
    ),
    ExpressionTestCase(
        id="not_found_string",
        doc={"val": "z", "arr": ["a", "b"]},
        expression={"$in": ["$val", "$arr"]},
        expected=False,
        msg="Should not find absent string",
    ),
    ExpressionTestCase(
        id="not_found_empty_array",
        doc={"val": 1, "arr": []},
        expression={"$in": ["$val", "$arr"]},
        expected=False,
        msg="Should not find value in empty array",
    ),
    ExpressionTestCase(
        id="not_found_type_mismatch",
        doc={"val": "1", "arr": [1, 2, 3]},
        expression={"$in": ["$val", "$arr"]},
        expected=False,
        msg="Should not find string '1' in int array",
    ),
    ExpressionTestCase(
        id="not_found_bool_vs_int",
        doc={"val": True, "arr": [1, 0]},
        expression={"$in": ["$val", "$arr"]},
        expected=False,
        msg="Should not find bool in int array",
    ),
    ExpressionTestCase(
        id="not_found_null",
        doc={"val": None, "arr": [1, 2, 3]},
        expression={"$in": ["$val", "$arr"]},
        expected=False,
        msg="Should not find null in non-null array",
    ),
    ExpressionTestCase(
        id="not_found_partial_array",
        doc={"val": [1], "arr": [[1, 2], [3, 4]]},
        expression={"$in": ["$val", "$arr"]},
        expected=False,
        msg="Should not find partial array match",
    ),
    ExpressionTestCase(
        id="not_found_partial_object",
        doc={"val": {"a": 1}, "arr": [{"a": 1, "b": 2}]},
        expression={"$in": ["$val", "$arr"]},
        expected=False,
        msg="Should not find partial object match",
    ),
]

# Success: mixed types in array
MIXED_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="mixed_find_string",
        doc={"val": "2", "arr": [1, "2", True, None, [1]]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find string in mixed-type array",
    ),
    ExpressionTestCase(
        id="mixed_find_null",
        doc={"val": None, "arr": [1, "2", True, None, [1]]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find null in mixed-type array",
    ),
    ExpressionTestCase(
        id="mixed_find_array",
        doc={"val": [1], "arr": [1, "2", True, None, [1]]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find array in mixed-type array",
    ),
    ExpressionTestCase(
        id="mixed_not_found",
        doc={"val": "x", "arr": [1, "2", True, None, [1]]},
        expression={"$in": ["$val", "$arr"]},
        expected=False,
        msg="Should not find absent value in mixed-type array",
    ),
]

# Success: large array

LARGE_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="large_array_found_first",
        doc={"val": 0, "arr": list(range(20_000))},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find first element in large array",
    ),
    ExpressionTestCase(
        id="large_array_found_last",
        doc={"val": 19_999, "arr": list(range(20_000))},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find last element in large array",
    ),
    ExpressionTestCase(
        id="large_array_found_middle",
        doc={"val": 10_000, "arr": list(range(20_000))},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find middle element in large array",
    ),
    ExpressionTestCase(
        id="large_array_not_found",
        doc={"val": -1, "arr": list(range(20_000))},
        expression={"$in": ["$val", "$arr"]},
        expected=False,
        msg="Should not find absent value in large array",
    ),
]

# Aggregate and test
# Property [Literal Evaluation]: $in evaluates correctly with inline literal values.
TEST_SUBSET_FOR_LITERAL: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal_found_int",
        doc=None,
        expression={"$in": [2, {"$literal": [1, 2, 3]}]},
        expected=True,
        msg="$in should find int in literal array",
    ),
    ExpressionTestCase(
        "literal_not_found_int",
        doc=None,
        expression={"$in": [4, {"$literal": [1, 2, 3]}]},
        expected=False,
        msg="$in should not find absent int in literal array",
    ),
    ExpressionTestCase(
        "literal_large_array_found",
        doc=None,
        expression={"$in": [0, {"$literal": list(range(20_000))}]},
        expected=True,
        msg="$in should find value in large literal array",
    ),
]

ALL_TESTS = (
    FOUND_TESTS + NOT_FOUND_TESTS + MIXED_TYPE_TESTS + LARGE_ARRAY_TESTS + TEST_SUBSET_FOR_LITERAL
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_in_insert(collection, test):
    """Test $in with values from inserted documents."""
    if test.doc is None:
        result = execute_expression(collection, test.expression)
    else:
        result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
