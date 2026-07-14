"""$toInt field reference and expression-as-input tests."""

import pytest
from bson import Binary, Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import CONVERSION_FAILURE_ERROR
from documentdb_tests.framework.parametrize import pytest_params

# Property [Field Reference]: $toInt resolves field paths and nested dot-notation paths;
# missing fields and missing nested fields return null.
TOINT_FIELD_REF_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int_field",
        msg="int32 field passes through unchanged",
        expression={"$toInt": "$v"},
        doc={"v": 42},
        expected=42,
    ),
    ExpressionTestCase(
        "int64_field",
        msg="int64 field (within int32 range) converts to int32",
        expression={"$toInt": "$v"},
        doc={"v": Int64(99)},
        expected=99,
    ),
    ExpressionTestCase(
        "double_field",
        msg="double field is truncated toward zero",
        expression={"$toInt": "$v"},
        doc={"v": 3.7},
        expected=3,
    ),
    ExpressionTestCase(
        "string_field",
        msg="numeric string field converts to int32",
        expression={"$toInt": "$v"},
        doc={"v": "42"},
        expected=42,
    ),
    ExpressionTestCase(
        "bool_field",
        msg="bool field converts to int32",
        expression={"$toInt": "$v"},
        doc={"v": True},
        expected=1,
    ),
    ExpressionTestCase(
        "decimal128_field",
        msg="Decimal128 field converts to int32 (truncated)",
        expression={"$toInt": "$v"},
        doc={"v": Decimal128("7.9")},
        expected=7,
    ),
    ExpressionTestCase(
        "binary_field",
        msg="4-byte binary field converts to int32",
        expression={"$toInt": "$v"},
        doc={"v": Binary(b"\x2a\x00\x00\x00", 0)},
        expected=42,
    ),
    ExpressionTestCase(
        "nested_field",
        msg="nested field path converts to int32",
        expression={"$toInt": "$doc.v"},
        doc={"doc": {"v": 100}},
        expected=100,
    ),
    ExpressionTestCase(
        "missing_nested",
        msg="missing nested field returns null",
        expression={"$toInt": "$doc.missing"},
        doc={"doc": {"x": 1}},
        expected=None,
    ),
    ExpressionTestCase(
        "missing_field",
        msg="missing top-level field returns null",
        expression={"$toInt": "$v"},
        doc={},
        expected=None,
    ),
    ExpressionTestCase(
        "composite_array_path",
        msg="$toInt fails when field path resolves to a composite array",
        expression={"$toInt": "$a.b"},
        doc={"a": [{"b": 1}, {"b": 2}]},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
]


@pytest.mark.parametrize("test", pytest_params(TOINT_FIELD_REF_TESTS))
def test_toInt_field_ref(collection, test: ExpressionTestCase):
    """$toInt resolves field paths and nested paths from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


# Property [Expression Input]: $toInt evaluates a nested expression before converting.
TOINT_EXPRESSION_INPUT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "add",
        msg="$toInt converts an arithmetic expression result",
        expression={"$toInt": {"$add": [10, 20]}},
        expected=30,
    ),
    ExpressionTestCase(
        "concat",
        msg="$toInt converts a string concatenation expression result",
        expression={"$toInt": {"$concat": ["3", "0"]}},
        expected=30,
    ),
    ExpressionTestCase(
        "nested_conversion",
        msg="$toInt converts a nested type-conversion expression result",
        expression={"$toInt": {"$toDecimal": 42}},
        expected=42,
    ),
]


@pytest.mark.parametrize("test", pytest_params(TOINT_EXPRESSION_INPUT_TESTS))
def test_toInt_expression_as_input(collection, test: ExpressionTestCase):
    """$toInt accepts any expression as its argument."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
