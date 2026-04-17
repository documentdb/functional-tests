"""
Tests for $ifNull with multiple input expressions (v5.0+).

Covers first-non-null-wins behavior, mixed null/missing inputs,
many inputs, mixed types, and stress/edge cases.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

ALL_LITERAL_NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "three_nulls_then_last",
        expression={"$ifNull": [None, None, None, "last"]},
        expected="last",
        msg="Should return replacement when all literal nulls",
    ),
]

STRESS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "twenty_null_inputs",
        expression={"$ifNull": [None] * 19 + ["found_at_20"]},
        expected="found_at_20",
        msg="Should return replacement after 19 nulls",
    ),
    ExpressionTestCase(
        "many_nulls_last_non_null",
        expression={"$ifNull": [None] * 18 + [42, "default"]},
        expected=42,
        msg="Should return last non-null input before replacement",
    ),
    ExpressionTestCase(
        "hundred_null_inputs",
        expression={"$ifNull": [None] * 99 + ["found_at_100"]},
        expected="found_at_100",
        msg="Should return replacement after 99 nulls",
    ),
    ExpressionTestCase(
        "hundred_inputs_non_null_at_50",
        expression={"$ifNull": [None] * 49 + [50] + [None] * 49 + ["default"]},
        expected=50,
        msg="Should return first non-null at position 50 out of 100",
    ),
]

ALL_LITERAL_TESTS = ALL_LITERAL_NULL_TESTS + STRESS_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_LITERAL_TESTS))
def test_ifNull_multiple_inputs_literal(collection, test):
    """Test $ifNull with multiple literal inputs (no document insert)."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


FIRST_NON_NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "first_non_null",
        doc={"a": 1, "b": 2, "c": 3},
        expression={"$ifNull": ["$a", "$b", "$c", "default"]},
        expected=1,
        msg="Should return first non-null input",
    ),
    ExpressionTestCase(
        "second_non_null",
        doc={"a": None, "b": 2, "c": 3},
        expression={"$ifNull": ["$a", "$b", "$c", "default"]},
        expected=2,
        msg="Should return second when first is null",
    ),
    ExpressionTestCase(
        "third_non_null",
        doc={"a": None, "b": None, "c": 3},
        expression={"$ifNull": ["$a", "$b", "$c", "default"]},
        expected=3,
        msg="Should return third when first two are null",
    ),
    ExpressionTestCase(
        "all_null_returns_default",
        doc={"a": None, "b": None, "c": None},
        expression={"$ifNull": ["$a", "$b", "$c", "default"]},
        expected="default",
        msg="Should return default when all inputs are null",
    ),
]

MIXED_NULL_MISSING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "all_missing_or_null",
        doc={"b": None},
        expression={"$ifNull": ["$a", "$b", "$c", "default"]},
        expected="default",
        msg="Should return default when mix of missing and null",
    ),
    ExpressionTestCase(
        "last_exists",
        doc={"c": 99},
        expression={"$ifNull": ["$a", "$b", "$c", "default"]},
        expected=99,
        msg="Should return last non-null when earlier are missing",
    ),
]

MIXED_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int_wins_over_string",
        doc={"a": None, "b": 42, "c": "hello"},
        expression={"$ifNull": ["$a", "$b", "$c", "default"]},
        expected=42,
        msg="Should return int (first non-null) regardless of later types",
    ),
    ExpressionTestCase(
        "string_wins",
        doc={"a": None, "b": None, "c": "hello"},
        expression={"$ifNull": ["$a", "$b", "$c", "default"]},
        expected="hello",
        msg="Should return string when it is first non-null",
    ),
]

ALL_INSERT_TESTS = FIRST_NON_NULL_TESTS + MIXED_NULL_MISSING_TESTS + MIXED_TYPE_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_INSERT_TESTS))
def test_ifNull_multiple_inputs_insert(collection, test):
    """Test $ifNull with multiple inputs requiring document insert."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
