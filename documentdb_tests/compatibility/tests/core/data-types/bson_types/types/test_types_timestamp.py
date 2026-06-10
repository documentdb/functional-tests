import pytest
from bson import Timestamp

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

# Property [Timestamp Ordering]: Timestamps order by their seconds component
# first and by their increment component second, both treated as unsigned
# 32-bit values.
TIMESTAMP_ORDERING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "increment_when_seconds_equal",
        expression={"$lt": [Timestamp(100, 1), Timestamp(100, 2)]},
        expected=True,
        msg="Timestamp ordering should compare increment when seconds are equal",
    ),
    ExpressionTestCase(
        "seconds_before_increment",
        expression={"$lt": [Timestamp(100, 2), Timestamp(200, 1)]},
        expected=True,
        msg="Timestamp ordering should compare seconds before increment",
    ),
    ExpressionTestCase(
        "zero_timestamp_lowest",
        expression={"$lt": [Timestamp(0, 0), Timestamp(0, 1)]},
        expected=True,
        msg="Timestamp ordering should place the zero timestamp lowest",
    ),
    ExpressionTestCase(
        "increment_unsigned_high",
        expression={"$lt": [Timestamp(1, 1), Timestamp(1, 4_294_967_295)]},
        expected=True,
        msg="Timestamp ordering should treat the increment as an unsigned 32-bit value",
    ),
    ExpressionTestCase(
        "seconds_unsigned_high",
        expression={"$lt": [Timestamp(1, 1), Timestamp(4_294_967_295, 1)]},
        expected=True,
        msg="Timestamp ordering should treat the seconds as an unsigned 32-bit value",
    ),
    ExpressionTestCase(
        "near_max_lt_max_timestamp",
        expression={
            "$lt": [
                Timestamp(4_294_967_295, 4_294_967_294),
                Timestamp(4_294_967_295, 4_294_967_295),
            ]
        },
        expected=True,
        msg=(
            "Timestamp ordering should distinguish the maximum possible"
            " timestamp from one below it"
        ),
    ),
]

# Property [Timestamp Equality]: Timestamps are equal when both their seconds
# and increment components match.
TIMESTAMP_EQUALITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "same_components_equal",
        expression={"$eq": [Timestamp(100, 5), Timestamp(100, 5)]},
        expected=True,
        msg="Timestamp equality should hold when both components match",
    ),
    ExpressionTestCase(
        "different_increment_not_equal",
        expression={"$eq": [Timestamp(100, 5), Timestamp(100, 6)]},
        expected=False,
        msg="Timestamp equality should distinguish different increment components",
    ),
    ExpressionTestCase(
        "different_seconds_not_equal",
        expression={"$eq": [Timestamp(100, 5), Timestamp(101, 5)]},
        expected=False,
        msg="Timestamp equality should distinguish different seconds components",
    ),
]

TIMESTAMP_COMPARISON_TESTS = TIMESTAMP_ORDERING_TESTS + TIMESTAMP_EQUALITY_TESTS


@pytest.mark.parametrize("test", pytest_params(TIMESTAMP_COMPARISON_TESTS))
def test_timestamp_comparison(collection, test):
    """Test Timestamp BSON type comparison semantics."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# Property [Timestamp Round-Trip Fidelity]: Timestamp values survive insert and
# retrieval unchanged.
TIMESTAMP_ROUND_TRIP_TESTS: list[RoundTripTestCase] = [
    RoundTripTestCase(
        "small_timestamp",
        value=Timestamp(1, 1),
        expected=Timestamp(1, 1),
        msg="Small non-zero timestamp should survive round-trip",
    ),
    RoundTripTestCase(
        "max_seconds",
        value=Timestamp(4_294_967_295, 1),
        expected=Timestamp(4_294_967_295, 1),
        msg="Maximum seconds component should survive round-trip",
    ),
    RoundTripTestCase(
        "max_increment",
        value=Timestamp(1, 4_294_967_295),
        expected=Timestamp(1, 4_294_967_295),
        msg="Maximum increment component should survive round-trip",
    ),
    RoundTripTestCase(
        "max_timestamp",
        value=Timestamp(4_294_967_295, 4_294_967_295),
        expected=Timestamp(4_294_967_295, 4_294_967_295),
        msg="Maximum possible timestamp should survive round-trip",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TIMESTAMP_ROUND_TRIP_TESTS))
def test_timestamp_round_trip(collection, test):
    """Test Timestamp values survive storage and retrieval unchanged."""
    collection.insert_one({"_id": test.id, "v": test.value})
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": test.id}})
    assertSuccess(result, [{"_id": test.id, "v": test.expected}], msg=test.msg)
