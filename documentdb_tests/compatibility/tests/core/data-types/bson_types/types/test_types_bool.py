import pytest

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

# Property [Bool Ordering]: false sorts before true, and true is not equal to
# false.
BOOL_COMPARISON_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "false_lt_true",
        expression={"$lt": [False, True]},
        expected=True,
        msg="Bool ordering should place false before true",
    ),
    ExpressionTestCase(
        "true_ne_false",
        expression={"$eq": [True, False]},
        expected=False,
        msg="Bool equality should distinguish true from false",
    ),
]


@pytest.mark.parametrize("test", pytest_params(BOOL_COMPARISON_TESTS))
def test_bool_comparison(collection, test):
    """Test bool BSON type comparison semantics."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# Property [Bool Round-Trip Fidelity]: bool values survive insert and retrieval
# unchanged.
BOOL_ROUND_TRIP_TESTS: list[RoundTripTestCase] = [
    RoundTripTestCase(
        "true_value",
        value=True,
        expected=True,
        msg="True should survive round-trip",
    ),
    RoundTripTestCase(
        "false_value",
        value=False,
        expected=False,
        msg="False should survive round-trip",
    ),
]


@pytest.mark.parametrize("test", pytest_params(BOOL_ROUND_TRIP_TESTS))
def test_bool_round_trip(collection, test):
    """Test bool values survive storage and retrieval unchanged."""
    collection.insert_one({"_id": test.id, "v": test.value})
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": test.id}})
    assertSuccess(result, [{"_id": test.id, "v": test.expected}], msg=test.msg)
