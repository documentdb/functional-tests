"""
Tests for $ifNull null, missing, and undefined handling.

Covers null propagation, missing field behavior, null as replacement,
null/missing combinations, constant/literal arguments, falsy-but-not-null
values, and mixed fallback scenarios.
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
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

NULL_PROPAGATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_returns_default",
        doc={"a": None},
        expression={"$ifNull": ["$a", "default"]},
        expected="default",
        msg="Should return default when input is null",
    ),
    ExpressionTestCase(
        "both_null_returns_default",
        doc={"a": None, "b": None},
        expression={"$ifNull": ["$a", "$b", "default"]},
        expected="default",
        msg="Should return default when all inputs are null",
    ),
    ExpressionTestCase(
        "first_non_null_second_null",
        doc={"a": 1, "b": None},
        expression={"$ifNull": ["$a", "$b", "default"]},
        expected=1,
        msg="Should return first input when non-null",
    ),
]

MISSING_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_returns_default",
        doc={},
        expression={"$ifNull": ["$missing", "default"]},
        expected="default",
        msg="Should return default when field is missing",
    ),
    ExpressionTestCase(
        "both_missing_returns_default",
        doc={},
        expression={"$ifNull": ["$missing1", "$missing2", "default"]},
        expected="default",
        msg="Should return default when all fields are missing",
    ),
    ExpressionTestCase(
        "missing_then_existing",
        doc={"b": 10},
        expression={"$ifNull": ["$missing", "$b", "default"]},
        expected=10,
        msg="Should return first existing non-null field",
    ),
]

NULL_REPLACEMENT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_replace_null",
        doc={"a": None},
        expression={"$ifNull": ["$a", None]},
        expected=None,
        msg="Should return null when replacement is null",
    ),
    ExpressionTestCase(
        "missing_replace_null",
        doc={},
        expression={"$ifNull": ["$missing", None]},
        expected=None,
        msg="Should return null when missing field and replacement is null",
    ),
]

ALL_NULL_MISSING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_then_missing",
        doc={"a": None},
        expression={"$ifNull": ["$a", "$missing", "fallback"]},
        expected="fallback",
        msg="Should return fallback when null then missing",
    ),
    ExpressionTestCase(
        "null_null_missing",
        doc={"a": None, "b": None},
        expression={"$ifNull": ["$a", "$b", "$missing", "fallback"]},
        expected="fallback",
        msg="Should return fallback when mix of null and missing",
    ),
]

CONSTANT_ARG_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal_null_then_field",
        doc={"a": 42},
        expression={"$ifNull": [None, "$a"]},
        expected=42,
        msg="Should return field value when first arg is literal null",
    ),
    ExpressionTestCase(
        "two_literal_nulls_then_field",
        doc={"a": 42},
        expression={"$ifNull": [None, None, "$a"]},
        expected=42,
        msg="Should return field value when first two args are literal null",
    ),
    ExpressionTestCase(
        "both_literal_null",
        expression={"$ifNull": [None, None]},
        expected=None,
        msg="Should return null when both args are literal null",
    ),
    ExpressionTestCase(
        "literal_null_then_literal_int",
        expression={"$ifNull": [None, 99]},
        expected=99,
        msg="Should return literal int when first is literal null",
    ),
    ExpressionTestCase(
        "both_literal_non_null",
        expression={"$ifNull": [10, 20]},
        expected=10,
        msg="Should return first literal when both are non-null",
    ),
]

FALSY_NOT_NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "false_not_null",
        expression={"$ifNull": [False, "replaced"]},
        expected=False,
        msg="false is not null, should be returned as-is",
    ),
    ExpressionTestCase(
        "zero_int_not_null",
        expression={"$ifNull": [0, "replaced"]},
        expected=0,
        msg="int 0 is not null, should be returned as-is",
    ),
    ExpressionTestCase(
        "zero_double_not_null",
        expression={"$ifNull": [0.0, "replaced"]},
        expected=0.0,
        msg="double 0.0 is not null, should be returned as-is",
    ),
    ExpressionTestCase(
        "empty_string_not_null",
        expression={"$ifNull": ["", "replaced"]},
        expected="",
        msg="empty string is not null, should be returned as-is",
    ),
    ExpressionTestCase(
        "empty_array_not_null",
        expression={"$ifNull": [[], "replaced"]},
        expected=[],
        msg="empty array is not null, should be returned as-is",
    ),
    ExpressionTestCase(
        "empty_object_not_null",
        expression={"$ifNull": [{}, "replaced"]},
        expected={},
        msg="empty object is not null, should be returned as-is",
    ),
]

MIXED_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_field_literal_null_non_null_field",
        doc={"a": None, "b": 77},
        expression={"$ifNull": ["$a", None, "$b"]},
        expected=77,
        msg="Should skip null field and literal null, return non-null field",
    ),
    ExpressionTestCase(
        "doc_example_non_null",
        doc={"desc": "toy car"},
        expression={"$ifNull": ["$desc", "Unspecified"]},
        expected="toy car",
        msg="Should return existing description",
    ),
    ExpressionTestCase(
        "six_inputs_all_missing",
        doc={},
        expression={"$ifNull": ["$a", "$b", "$c", "$d", "$e", "default"]},
        expected="default",
        msg="Should return default when all fields missing",
    ),
    ExpressionTestCase(
        "chaining_fallbacks",
        doc={"nickname": None, "firstName": None, "email": "user@example.com"},
        expression={"$ifNull": ["$nickname", "$firstName", "$email", "anonymous"]},
        expected="user@example.com",
        msg="Should fall through to email",
    ),
    ExpressionTestCase(
        "null_safe_nested_access",
        doc={"address": None},
        expression={"$ifNull": ["$address.city", "Unknown"]},
        expected="Unknown",
        msg="Should return Unknown when address is null",
    ),
]

ALL_INSERT_TESTS = (
    NULL_PROPAGATION_TESTS
    + MISSING_FIELD_TESTS
    + NULL_REPLACEMENT_TESTS
    + ALL_NULL_MISSING_TESTS
    + [t for t in CONSTANT_ARG_TESTS if t.doc is not None]
    + MIXED_TESTS
)

ALL_LITERAL_TESTS = [t for t in CONSTANT_ARG_TESTS if t.doc is None] + FALSY_NOT_NULL_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_INSERT_TESTS))
def test_ifNull_null_missing_insert(collection, test):
    """Test $ifNull null/missing with document insert."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(ALL_LITERAL_TESTS))
def test_ifNull_null_missing_literal(collection, test):
    """Test $ifNull null/missing with literal expressions."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


def test_ifNull_replacement_is_missing_field(collection):
    """Test $ifNull where replacement resolves to a missing field — field omitted from output."""
    collection.insert_one({"a": None})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"_id": 0, "result": {"$ifNull": ["$a", "$nonexistent"]}}}],
            "cursor": {},
        },
    )
    assertSuccess(result, [{}], "Should omit field when replacement resolves to missing")
