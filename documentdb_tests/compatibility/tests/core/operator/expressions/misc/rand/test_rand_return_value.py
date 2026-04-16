"""
Tests for $rand return value properties.

Validates return type (double), range [0, 1), and per-invocation independence.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)


def test_rand_basic(collection):
    """Test {$rand: {}} is >= 0.0 and < 1.0."""
    result = execute_expression(collection, {"$rand": {}})
    assert_expression_result(
        result, expected=pytest.approx(0.5, abs=0.5), msg="Should return value in [0, 1)"
    )


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
