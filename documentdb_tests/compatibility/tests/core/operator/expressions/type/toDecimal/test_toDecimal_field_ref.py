"""$toDecimal field reference and expression-as-input tests."""

import pytest
from bson import Decimal128, Int64

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
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_TWO_AND_HALF,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_TWO_AND_HALF,
    INT32_ZERO,
)

# Property [Field Reference]: $toDecimal resolves field paths and nested dot-notation paths;
# missing fields and missing nested fields return null.
TODECIMAL_FIELD_REF_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int_field",
        msg="int32 field converts to Decimal128",
        expression={"$toDecimal": "$v"},
        doc={"v": 42},
        expected=Decimal128("42"),
    ),
    ExpressionTestCase(
        "int64_field",
        msg="int64 field converts to Decimal128",
        expression={"$toDecimal": "$v"},
        doc={"v": Int64(86400000)},
        expected=Decimal128("86400000"),
    ),
    ExpressionTestCase(
        "decimal_field",
        msg="Decimal128 field passes through unchanged",
        expression={"$toDecimal": "$v"},
        doc={"v": Decimal128("3.14")},
        expected=Decimal128("3.14"),
    ),
    ExpressionTestCase(
        "string_field",
        msg="Numeric string field converts to Decimal128",
        expression={"$toDecimal": "$v"},
        doc={"v": "2.5"},
        expected=DECIMAL128_TWO_AND_HALF,
    ),
    ExpressionTestCase(
        "bool_field",
        msg="Bool field converts to Decimal128",
        expression={"$toDecimal": "$v"},
        doc={"v": True},
        expected=Decimal128("1"),
    ),
    ExpressionTestCase(
        "double_field",
        msg="Double field converts to Decimal128 with 15 significant digits",
        expression={"$toDecimal": "$v"},
        doc={"v": DOUBLE_TWO_AND_HALF},
        expected=Decimal128("2.50000000000000"),
    ),
    ExpressionTestCase(
        "nested_field",
        msg="Nested field path converts to Decimal128",
        expression={"$toDecimal": "$doc.v"},
        doc={"doc": {"v": 100}},
        expected=Decimal128("100"),
    ),
    ExpressionTestCase(
        "missing_nested",
        msg="Missing nested field returns null",
        expression={"$toDecimal": "$doc.missing"},
        doc={"doc": {"x": 1}},
        expected=None,
    ),
    ExpressionTestCase(
        "missing_field",
        msg="Missing top-level field returns null",
        expression={"$toDecimal": "$v"},
        doc={},
        expected=None,
    ),
    ExpressionTestCase(
        "neg_zero_double_field",
        msg="$toDecimal preserves -0.0 sign when reading double from a document field",
        expression={"$toDecimal": "$v"},
        doc={"v": DOUBLE_NEGATIVE_ZERO},
        expected=DECIMAL128_NEGATIVE_ZERO,
    ),
    ExpressionTestCase(
        "zero_field",
        msg="$toDecimal converts zero from a document field",
        expression={"$toDecimal": "$v"},
        doc={"v": INT32_ZERO},
        expected=DECIMAL128_ZERO,
    ),
]

# Property [Expression Input]: $toDecimal evaluates a nested expression before converting.
TODECIMAL_EXPRESSION_INPUT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "add",
        msg="$toDecimal converts an arithmetic expression result",
        expression={"$toDecimal": {"$add": [10, 20]}},
        expected=Decimal128("30"),
    ),
    ExpressionTestCase(
        "concat",
        msg="$toDecimal converts a string concatenation expression result",
        expression={"$toDecimal": {"$concat": ["3", ".", "14"]}},
        expected=Decimal128("3.14"),
    ),
    ExpressionTestCase(
        "nested_conversion",
        msg="$toDecimal converts a nested type-conversion expression result",
        expression={"$toDecimal": {"$toDouble": 42}},
        expected=Decimal128("4.20000000000000E+1"),
    ),
]


@pytest.mark.parametrize("test", pytest_params(TODECIMAL_FIELD_REF_TESTS))
def test_toDecimal_field_ref(collection, test: ExpressionTestCase):
    """$toDecimal resolves field paths and nested paths from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


def test_toDecimal_composite_array_path(collection):
    """$toDecimal on a composite array path (array of objects) is a conversion failure."""
    result = execute_expression_with_insert(
        collection,
        {"$toDecimal": "$a.b"},
        {"a": [{"b": 1}, {"b": 2}]},
    )
    assert_expression_result(result, error_code=CONVERSION_FAILURE_ERROR)


@pytest.mark.parametrize("test", pytest_params(TODECIMAL_EXPRESSION_INPUT_TESTS))
def test_toDecimal_expression_as_input(collection, test: ExpressionTestCase):
    """$toDecimal accepts any expression as its argument."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
