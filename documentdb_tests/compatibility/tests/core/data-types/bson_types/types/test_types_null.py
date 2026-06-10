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

# Property [Null Equality]: null is equal to null but distinct from other types.
NULL_COMPARISON_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_eq_null",
        expression={"$eq": [None, None]},
        expected=True,
        msg="Null should equal null",
    ),
    ExpressionTestCase(
        "null_ne_zero",
        expression={"$eq": [None, 0]},
        expected=False,
        msg="Null should not equal zero",
    ),
    ExpressionTestCase(
        "null_ne_empty_string",
        expression={"$eq": [None, ""]},
        expected=False,
        msg="Null should not equal empty string",
    ),
    ExpressionTestCase(
        "null_ne_false",
        expression={"$eq": [None, False]},
        expected=False,
        msg="Null should not equal false",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NULL_COMPARISON_TESTS))
def test_null_comparison(collection, test):
    """Test null BSON type comparison semantics."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# Property [Null Round-Trip Fidelity]: an explicit null field value survives
# insert and retrieval unchanged.
NULL_ROUND_TRIP_TESTS: list[RoundTripTestCase] = [
    RoundTripTestCase(
        "explicit_null",
        value=None,
        expected=None,
        msg="Explicit null field should survive round-trip",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NULL_ROUND_TRIP_TESTS))
def test_null_round_trip(collection, test):
    """Test null values survive storage and retrieval unchanged."""
    collection.insert_one({"_id": test.id, "v": test.value})
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": test.id}})
    assertSuccess(result, [{"_id": test.id, "v": test.expected}], msg=test.msg)
