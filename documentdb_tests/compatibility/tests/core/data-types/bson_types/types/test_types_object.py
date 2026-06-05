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

# Property [Document Ordering]: documents compare field by field in stored
# order, comparing the field name before the value within each pair, and a
# document that is a prefix of another sorts before the longer document.
OBJECT_COMPARISON_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "empty_equality",
        expression={"$eq": [{}, {}]},
        expected=True,
        msg="Document equality should hold for two empty documents",
    ),
    ExpressionTestCase(
        "value_when_keys_equal",
        expression={"$lt": [{"a": 1, "b": 1}, {"a": 1, "b": 2}]},
        expected=True,
        msg="Document ordering should compare values when field names are equal",
    ),
    ExpressionTestCase(
        "key_before_value",
        expression={"$lt": [{"a": 2}, {"b": 1}]},
        expected=True,
        msg="Document ordering should compare field names before values within each pair",
    ),
    ExpressionTestCase(
        "key_diff_value_equal",
        expression={"$lt": [{"a": 1}, {"b": 1}]},
        expected=True,
        msg="Document ordering should compare field names when values are equal",
    ),
    ExpressionTestCase(
        "prefix_shorter_first",
        expression={"$lt": [{"a": 1}, {"a": 1, "b": 1}]},
        expected=True,
        msg="Document ordering should place a prefix document before a longer document",
    ),
    ExpressionTestCase(
        "empty_before_nonempty",
        expression={"$lt": [{}, {"a": 1}]},
        expected=True,
        msg="Document ordering should place the empty document before a non-empty document",
    ),
    ExpressionTestCase(
        "nested_value_recurse",
        expression={"$lt": [{"a": {"b": 1}}, {"a": {"b": 2}}]},
        expected=True,
        msg="Document ordering should recurse into nested document values",
    ),
    ExpressionTestCase(
        "numeric_equivalence_in_value",
        expression={"$eq": [{"x": 1}, {"x": Int64(1)}]},
        expected=True,
        msg="Document equality should apply numeric equivalence to field values",
    ),
]


@pytest.mark.parametrize("test", pytest_params(OBJECT_COMPARISON_TESTS))
def test_object_comparison(collection, test):
    """Test embedded document BSON type comparison semantics."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# Property [Document Round-Trip Fidelity]: embedded documents survive insert
# and retrieval unchanged, preserving field order.
OBJECT_ROUND_TRIP_TESTS: list[RoundTripTestCase] = [
    RoundTripTestCase(
        "empty_doc",
        value={},
        expected={},
        msg="Empty document should survive round-trip",
    ),
    RoundTripTestCase(
        "nested_doc",
        value={"a": {"b": {"c": 1}}},
        expected={"a": {"b": {"c": 1}}},
        msg="Nested document should survive round-trip",
    ),
    RoundTripTestCase(
        "mixed_value_types",
        value={"s": "hello", "n": 42, "b": True, "null": None, "arr": [1, 2]},
        expected={"s": "hello", "n": 42, "b": True, "null": None, "arr": [1, 2]},
        msg="Document with mixed value types should survive round-trip",
    ),
]


@pytest.mark.parametrize("test", pytest_params(OBJECT_ROUND_TRIP_TESTS))
def test_object_round_trip(collection, test):
    """Test embedded document values survive storage and retrieval unchanged."""
    collection.insert_one({"_id": test.id, "v": test.value})
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": test.id}})
    assertSuccess(result, [{"_id": test.id, "v": test.expected}], msg=test.msg)
