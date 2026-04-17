"""
Tests for $mergeObjects with special field names.

Covers dotted fields, dollar-prefixed fields, unicode, empty string keys,
numeric string keys, and long field names.
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

LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "numeric_key_overwrite",
        expression={"$mergeObjects": [{"0": 1}, {"0": 2}]},
        expected={"0": 2},
        msg="Numeric string key overlap should succeed with last value winning",
    ),
    ExpressionTestCase(
        "string_key_overwrite",
        expression={"$mergeObjects": [{"key": 1}, {"key": 2}]},
        expected={"key": 2},
        msg="String key overlap should succeed with last value winning",
    ),
    ExpressionTestCase(
        "unicode_fields",
        expression={"$mergeObjects": [{"日本語": 1}, {"中文": 2}]},
        expected={"日本語": 1, "中文": 2},
        msg="Unicode field names should succeed and be preserved",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LITERAL_TESTS))
def test_mergeObjects_literal(collection, test):
    """Test $mergeObjects with literal special field names."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


FIELD_REF_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "dollar_fields",
        expression={"$mergeObjects": ["$obj1", "$obj2"]},
        doc={"obj1": {"$a": 1, "b": 2}, "obj2": {"$c": 3}},
        expected={"$a": 1, "b": 2, "$c": 3},
        msg="Dollar-prefixed fields should succeed and be preserved",
    ),
    ExpressionTestCase(
        "dollar_middle_fields",
        expression={"$mergeObjects": ["$obj1", "$obj2"]},
        doc={"obj1": {"a$b": 1}, "obj2": {"c$d": 2}},
        expected={"a$b": 1, "c$d": 2},
        msg="Dollar-in-middle fields should succeed and be preserved",
    ),
    ExpressionTestCase(
        "dollar_overlap",
        expression={"$mergeObjects": ["$obj1", "$obj2"]},
        doc={"obj1": {"$a": 1, "$b": 2}, "obj2": {"$a": 99, "$c": 3}},
        expected={"$a": 99, "$b": 2, "$c": 3},
        msg="Dollar-prefixed overlap should succeed with last value winning",
    ),
    ExpressionTestCase(
        "consecutive_dots",
        expression={"$mergeObjects": ["$obj1", "$obj2"]},
        doc={"obj1": {"a..b": 1}, "obj2": {"c..d": 2}},
        expected={"a..b": 1, "c..d": 2},
        msg="Consecutive dots in field names should succeed and be preserved",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIELD_REF_TESTS))
def test_mergeObjects_field_ref(collection, test):
    """Test $mergeObjects with special field names via inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


def test_mergeObjects_long_field_name(collection):
    """Test $mergeObjects with very long field name."""
    long_key = "a" * 1000
    result = execute_expression(collection, {"$mergeObjects": [{long_key: 1}, {"b": 2}]})
    assert_expression_result(
        result,
        expected={long_key: 1, "b": 2},
        msg="Very long field name should succeed and be preserved",
    )
