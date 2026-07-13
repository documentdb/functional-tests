"""$toDouble field reference and expression-as-input tests."""

import pytest
from bson import Int64

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
from documentdb_tests.framework.test_constants import (
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_TWO_AND_HALF,
)

# Property [Field Reference]: $toDouble resolves field paths and nested dot-notation paths;
# missing fields and missing nested fields return null.
TODOUBLE_FIELD_REF_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int_field",
        msg="int32 field converts to double",
        expression={"$toDouble": "$v"},
        doc={"v": 42},
        expected=42.0,
    ),
    ExpressionTestCase(
        "int64_field",
        msg="int64 field converts to double",
        expression={"$toDouble": "$v"},
        doc={"v": Int64(86400000)},
        expected=86400000.0,
    ),
    ExpressionTestCase(
        "double_field",
        msg="double field passes through unchanged",
        expression={"$toDouble": "$v"},
        doc={"v": 3.14},
        expected=3.14,
    ),
    ExpressionTestCase(
        "string_field",
        msg="numeric string field converts to double",
        expression={"$toDouble": "$v"},
        doc={"v": "2.5"},
        expected=DOUBLE_TWO_AND_HALF,
    ),
    ExpressionTestCase(
        "bool_field",
        msg="bool field converts to double",
        expression={"$toDouble": "$v"},
        doc={"v": True},
        expected=1.0,
    ),
    ExpressionTestCase(
        "nested_field",
        msg="nested field path converts to double",
        expression={"$toDouble": "$doc.v"},
        doc={"doc": {"v": 100}},
        expected=100.0,
    ),
    ExpressionTestCase(
        "missing_nested",
        msg="missing nested field returns null",
        expression={"$toDouble": "$doc.missing"},
        doc={"doc": {"x": 1}},
        expected=None,
    ),
    ExpressionTestCase(
        "missing_field",
        msg="missing top-level field returns null",
        expression={"$toDouble": "$v"},
        doc={},
        expected=None,
    ),
    ExpressionTestCase(
        "neg_zero",
        msg="$toDouble preserves -0.0 sign when reading from a document field",
        expression={"$toDouble": "$v"},
        doc={"v": DOUBLE_NEGATIVE_ZERO},
        expected=DOUBLE_NEGATIVE_ZERO,
    ),
]

# Property [Expression Input]: $toDouble evaluates a nested expression before converting.
TODOUBLE_EXPRESSION_INPUT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "add",
        msg="$toDouble converts an arithmetic expression result",
        expression={"$toDouble": {"$add": [10, 20]}},
        expected=30.0,
    ),
    ExpressionTestCase(
        "concat",
        msg="$toDouble converts a string concatenation expression result",
        expression={"$toDouble": {"$concat": ["3", ".", "14"]}},
        expected=3.14,
    ),
    ExpressionTestCase(
        "nested_conversion",
        msg="$toDouble converts a nested type-conversion expression result",
        expression={"$toDouble": {"$toDecimal": 42}},
        expected=42.0,
    ),
]


@pytest.mark.parametrize("test", pytest_params(TODOUBLE_FIELD_REF_TESTS))
def test_toDouble_field_ref(collection, test: ExpressionTestCase):
    """$toDouble resolves field paths and nested paths from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


def test_toDouble_composite_array_path(collection):
    """$toDouble on a composite array path (array of objects) is a conversion failure."""
    result = execute_expression_with_insert(
        collection,
        {"$toDouble": "$a.b"},
        {"a": [{"b": 1.0}, {"b": 2.0}]},
    )
    assert_expression_result(result, error_code=CONVERSION_FAILURE_ERROR)


@pytest.mark.parametrize("test", pytest_params(TODOUBLE_EXPRESSION_INPUT_TESTS))
def test_toDouble_expression_as_input(collection, test: ExpressionTestCase):
    """$toDouble accepts any expression as its argument."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
