"""
Tests for $rand return value properties.

Validates return type (double), range [0, 1), and per-invocation independence.
"""

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.test_constants import DOUBLE_ZERO


def test_rand_empty_object_range(collection):
    """Test rand with empty object argument returns value in expected range."""
    result = execute_expression(
        collection,
        {
            "$let": {
                "vars": {"r": {"$rand": {}}},
                "in": {"$and": [{"$gte": ["$$r", DOUBLE_ZERO]}, {"$lt": ["$$r", 1.0]}]},
            }
        },
    )
    assert_expression_result(result, expected=True)


def test_rand_return_type(collection):
    """Test {$type: {$rand: {}}} returns 'double'."""
    result = execute_expression(collection, {"$type": {"$rand": {}}})
    assert_expression_result(result, expected="double", msg="Should return double type")


def test_rand_two_calls_differ(collection):
    """Test two $rand calls in same $project produce different values (high probability)."""
    result = execute_expression(collection, {"$ne": [{"$rand": {}}, {"$rand": {}}]})
    assert_expression_result(
        result, expected=True, msg="Should produce different values per invocation"
    )
