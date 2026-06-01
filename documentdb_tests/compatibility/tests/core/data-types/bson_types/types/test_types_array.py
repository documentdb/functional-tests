import pytest
from bson import Int64

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

# Property [Array Ordering]: arrays compare element by element, with a prefix
# array sorting before a longer one.
ARRAY_COMPARISON_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "empty_equality",
        expression={"$eq": [[], []]},
        expected=True,
        msg="Array equality should hold for two empty arrays",
    ),
    ExpressionTestCase(
        "element_by_element",
        expression={"$lt": [[1, 2], [2]]},
        expected=True,
        msg="Array ordering should compare the first differing element",
    ),
    ExpressionTestCase(
        "prefix_shorter_first",
        expression={"$lt": [[1], [1, 2]]},
        expected=True,
        msg="Array ordering should place a prefix before the longer array",
    ),
    ExpressionTestCase(
        "empty_before_nonempty",
        expression={"$lt": [[], [1]]},
        expected=True,
        msg="Array ordering should place the empty array before a non-empty array",
    ),
    ExpressionTestCase(
        "numeric_equivalence",
        expression={"$eq": [[1], [Int64(1)]]},
        expected=True,
        msg="Array equality should apply numeric equivalence to elements",
    ),
    ExpressionTestCase(
        "bool_vs_number_distinct",
        expression={"$eq": [[True], [1]]},
        expected=False,
        msg="Array equality should not coerce a bool element to a number",
    ),
    ExpressionTestCase(
        "nested_recursion",
        expression={"$lt": [[[1]], [[2]]]},
        expected=True,
        msg="Array ordering should recurse into nested arrays",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ARRAY_COMPARISON_TESTS))
def test_array_comparison(collection, test):
    """Test array BSON type comparison semantics."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# Property [Array Round-Trip Fidelity]: array values survive insert and
# retrieval unchanged.
ARRAY_ROUND_TRIP_TESTS: list[RoundTripTestCase] = [
    RoundTripTestCase(
        "empty_array",
        value=[],
        expected=[],
        msg="Empty array should survive round-trip",
    ),
    RoundTripTestCase(
        "nested_array",
        value=[[1, 2], [3, [4, 5]]],
        expected=[[1, 2], [3, [4, 5]]],
        msg="Nested array should survive round-trip",
    ),
    RoundTripTestCase(
        "mixed_types",
        value=[1, "two", True, None, [3]],
        expected=[1, "two", True, None, [3]],
        msg="Array with mixed types should survive round-trip",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ARRAY_ROUND_TRIP_TESTS))
def test_array_round_trip(collection, test):
    """Test array values survive storage and retrieval unchanged."""
    collection.insert_one({"_id": test.id, "v": test.value})
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": test.id}})
    assertSuccess(result, [{"_id": test.id, "v": test.expected}], msg=test.msg)
