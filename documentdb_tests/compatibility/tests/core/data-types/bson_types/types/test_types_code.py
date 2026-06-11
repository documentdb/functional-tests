import pytest
from bson import Code

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

from ..utils.round_trip_test_case import RoundTripTestCase

# Property [Code Ordering]: Code values compare by their code string
# lexicographically, and Code without scope is distinct from Code with scope.
CODE_COMPARISON_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "lexicographic_order",
        expression={"$lt": [Code("function a() {}"), Code("function b() {}")]},
        expected=True,
        msg="Code ordering should compare code strings lexicographically",
    ),
    ExpressionTestCase(
        "same_code_equal",
        expression={"$eq": [Code("function a() {}"), Code("function a() {}")]},
        expected=True,
        msg="Code equality should hold for identical code strings",
    ),
    ExpressionTestCase(
        "different_code_not_equal",
        expression={"$eq": [Code("function a() {}"), Code("function b() {}")]},
        expected=False,
        msg="Code equality should distinguish different code strings",
    ),
    ExpressionTestCase(
        "empty_code_equal",
        expression={"$eq": [Code(""), Code("")]},
        expected=True,
        msg="Code equality should hold for two empty code strings",
    ),
    ExpressionTestCase(
        "code_without_scope_ne_code_with_scope",
        expression={"$eq": [Code("x"), Code("x", {})]},
        expected=False,
        msg="Code without scope should not equal Code with scope even if code matches",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CODE_COMPARISON_TESTS))
def test_code_comparison(collection, test):
    """Test Code BSON type comparison semantics."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# Property [Code Round-Trip Fidelity]: Code values survive insert and retrieval
# unchanged, including the deprecated Code with scope variant.
CODE_ROUND_TRIP_TESTS: list[RoundTripTestCase] = [
    RoundTripTestCase(
        "empty_code",
        value=Code(""),
        expected=Code(""),
        msg="Empty Code should survive round-trip",
    ),
    RoundTripTestCase(
        "simple_code",
        value=Code("function() { return 1; }"),
        expected=Code("function() { return 1; }"),
        msg="Simple Code should survive round-trip",
    ),
    RoundTripTestCase(
        "code_with_scope",
        value=Code("function() { return x; }", {"x": 1}),
        expected=Code("function() { return x; }", {"x": 1}),
        msg="Code with scope should survive round-trip",
    ),
    RoundTripTestCase(
        "code_with_empty_scope",
        value=Code("return 1", {}),
        expected=Code("return 1", {}),
        msg="Code with empty scope should survive round-trip",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CODE_ROUND_TRIP_TESTS))
def test_code_round_trip(collection, test):
    """Test Code values survive storage and retrieval unchanged."""
    collection.insert_one({"_id": test.id, "v": test.value})
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": test.id}})
    assertSuccess(result, [{"_id": test.id, "v": test.expected}], msg=test.msg)
