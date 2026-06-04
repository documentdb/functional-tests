import pytest
from bson import MaxKey, MinKey

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

# Property [MinKey/MaxKey Distinction]: MinKey and MaxKey are distinct
# singleton types, each equal only to itself, with MinKey sorting before MaxKey.
MINKEY_MAXKEY_COMPARISON_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "minkey_eq_minkey",
        expression={"$eq": [MinKey(), MinKey()]},
        expected=True,
        msg="MinKey should compare equal to MinKey",
    ),
    ExpressionTestCase(
        "maxkey_eq_maxkey",
        expression={"$eq": [MaxKey(), MaxKey()]},
        expected=True,
        msg="MaxKey should compare equal to MaxKey",
    ),
    ExpressionTestCase(
        "minkey_ne_maxkey",
        expression={"$eq": [MinKey(), MaxKey()]},
        expected=False,
        msg="MinKey should not compare equal to MaxKey",
    ),
    ExpressionTestCase(
        "minkey_lt_maxkey",
        expression={"$lt": [MinKey(), MaxKey()]},
        expected=True,
        msg="MinKey should sort before MaxKey",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MINKEY_MAXKEY_COMPARISON_TESTS))
def test_minkey_maxkey_comparison(collection, test):
    """Test MinKey/MaxKey BSON type comparison semantics."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# Property [MinKey/MaxKey Round-Trip Fidelity]: MinKey and MaxKey values survive
# insert and retrieval unchanged.
MINKEY_MAXKEY_ROUND_TRIP_TESTS: list[RoundTripTestCase] = [
    RoundTripTestCase(
        "minkey",
        value=MinKey(),
        expected=MinKey(),
        msg="MinKey should survive round-trip",
    ),
    RoundTripTestCase(
        "maxkey",
        value=MaxKey(),
        expected=MaxKey(),
        msg="MaxKey should survive round-trip",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MINKEY_MAXKEY_ROUND_TRIP_TESTS))
def test_minkey_maxkey_round_trip(collection, test):
    """Test MinKey/MaxKey values survive storage and retrieval unchanged."""
    collection.insert_one({"_id": test.id, "v": test.value})
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": test.id}})
    assertSuccess(result, [{"_id": test.id, "v": test.expected}], msg=test.msg)
