"""
Tests for $unsetField with special field names: periods, dollars, boundary names,
case sensitivity, empty strings, unicode, and null characters.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import NULL_CHAR_IN_FIELD_NAME_ERROR
from documentdb_tests.framework.parametrize import pytest_params

EXPRESSION_TESTS: list[ExpressionTestCase] = [
    # Fields with periods (non-traversal)
    ExpressionTestCase(
        "dotted_top_level",
        expression={
            "$unsetField": {
                "field": "price.usd",
                "input": {
                    "$setField": {"field": "price.usd", "input": {"item": "shirt"}, "value": 45.99}
                },
            }
        },
        expected={"item": "shirt"},
        msg="Should remove top-level dotted field name",
    ),
    ExpressionTestCase(
        "dotted_not_nested_path",
        expression={"$unsetField": {"field": "a.b", "input": {"a": {"b": 1}, "c": 2}}},
        expected={"a": {"b": 1}, "c": 2},
        msg="Dotted name should NOT traverse nested path",
    ),
    ExpressionTestCase(
        "multi_period",
        expression={
            "$unsetField": {
                "field": "a.b.c",
                "input": {"$setField": {"field": "a.b.c", "input": {"x": 2}, "value": 1}},
            }
        },
        expected={"x": 2},
        msg="Should remove field with multiple periods",
    ),
    ExpressionTestCase(
        "dotted_both_exist",
        expression={
            "$unsetField": {
                "field": "a.b",
                "input": {
                    "$setField": {"field": "a.b", "input": {"a": {"b": 1}, "c": 2}, "value": 10}
                },
            }
        },
        expected={"a": {"b": 1}, "c": 2},
        msg="Should remove top-level a.b, not nested a.b",
    ),
    # Fields with dollar signs
    ExpressionTestCase(
        "dollar_literal",
        expression={
            "$unsetField": {
                "field": {"$literal": "$price"},
                "input": {
                    "$setField": {
                        "field": {"$literal": "$price"},
                        "input": {"item": "shirt"},
                        "value": 45.99,
                    }
                },
            }
        },
        expected={"item": "shirt"},
        msg="Should remove dollar-prefixed field via $literal",
    ),
    ExpressionTestCase(
        "dollar_a",
        expression={
            "$unsetField": {
                "field": {"$literal": "$a"},
                "input": {
                    "$setField": {"field": {"$literal": "$a"}, "input": {"b": 2}, "value": 1}
                },
            }
        },
        expected={"b": 2},
        msg="Should remove $a field via $literal",
    ),
    ExpressionTestCase(
        "dollar_dot_literal",
        expression={
            "$unsetField": {
                "field": {"$literal": "$a.b"},
                "input": {
                    "$setField": {"field": {"$literal": "$a.b"}, "input": {"c": 2}, "value": 1}
                },
            }
        },
        expected={"c": 2},
        msg="Should remove field with both dollar and period",
    ),
    ExpressionTestCase(
        "just_dollar",
        expression={
            "$unsetField": {
                "field": {"$literal": "$"},
                "input": {"$setField": {"field": {"$literal": "$"}, "input": {"a": 2}, "value": 1}},
            }
        },
        expected={"a": 2},
        msg="Should remove field named just $",
    ),
    # Boundary field names
    ExpressionTestCase(
        "empty_string",
        expression={
            "$unsetField": {
                "field": "",
                "input": {"$setField": {"field": "", "input": {"a": 2}, "value": 1}},
            }
        },
        expected={"a": 2},
        msg="Should remove empty string field",
    ),
    ExpressionTestCase(
        "underscore_id",
        expression={"$unsetField": {"field": "_id", "input": {"_id": 1, "a": 2}}},
        expected={"a": 2},
        msg="Should remove _id field",
    ),
    ExpressionTestCase(
        "spaces",
        expression={
            "$unsetField": {
                "field": "a b",
                "input": {"$setField": {"field": "a b", "input": {"c": 2}, "value": 1}},
            }
        },
        expected={"c": 2},
        msg="Should remove field with spaces",
    ),
    ExpressionTestCase(
        "unicode",
        expression={
            "$unsetField": {
                "field": "café",
                "input": {"$setField": {"field": "café", "input": {"a": 2}, "value": 1}},
            }
        },
        expected={"a": 2},
        msg="Should remove unicode field",
    ),
    ExpressionTestCase(
        "just_dot",
        expression={
            "$unsetField": {
                "field": ".",
                "input": {"$setField": {"field": ".", "input": {"a": 2}, "value": 1}},
            }
        },
        expected={"a": 2},
        msg="Should remove field named .",
    ),
    ExpressionTestCase(
        "triple_dot",
        expression={
            "$unsetField": {
                "field": "...",
                "input": {"$setField": {"field": "...", "input": {"a": 2}, "value": 1}},
            }
        },
        expected={"a": 2},
        msg="Should remove field named ...",
    ),
]


@pytest.mark.parametrize("test", pytest_params(EXPRESSION_TESTS))
def test_unsetField_special_names(collection, test):
    """Test $unsetField with special field names."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


def test_unsetField_long_field_name(collection):
    """Test $unsetField with very long field name (1000+ chars)."""
    long_name = "x" * 1024
    result = execute_expression(
        collection,
        {
            "$unsetField": {
                "field": long_name,
                "input": {"$setField": {"field": long_name, "input": {"a": 1}, "value": 99}},
            }
        },
    )
    assert_expression_result(result, expected={"a": 1}, msg="Should remove very long field name")


NULL_CHAR_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_char_start",
        expression={"$unsetField": {"field": "\x00abc", "input": {}}},
        error_code=NULL_CHAR_IN_FIELD_NAME_ERROR,
        msg="Field starting with null char should error with invalid field name",
    ),
    ExpressionTestCase(
        "null_char_end",
        expression={"$unsetField": {"field": "abc\x00", "input": {}}},
        error_code=NULL_CHAR_IN_FIELD_NAME_ERROR,
        msg="Field ending with null char should error with invalid field name",
    ),
    ExpressionTestCase(
        "null_char_only",
        expression={"$unsetField": {"field": "\x00", "input": {}}},
        error_code=NULL_CHAR_IN_FIELD_NAME_ERROR,
        msg="Field of single null char should error with invalid field name",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NULL_CHAR_FIELD_TESTS))
def test_unsetField_null_char_fields(collection, test):
    """Test $unsetField with null character field names."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, error_code=test.error_code, msg=test.msg)
