"""$toLong field reference and expression-as-input tests."""

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
from documentdb_tests.framework.test_constants import (
    INT64_MAX,
)

# Property [Field Reference]: $toLong resolves field paths and nested dot-notation paths;
# missing fields and missing nested fields return null.
TOLONG_FIELD_REF_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_field",
        msg="int32 field widens to Int64",
        expression={"$toLong": "$v"},
        doc={"v": 42},
        expected=Int64(42),
    ),
    ExpressionTestCase(
        "int64_field",
        msg="int64 field passes through unchanged",
        expression={"$toLong": "$v"},
        doc={"v": Int64(100)},
        expected=Int64(100),
    ),
    ExpressionTestCase(
        "double_field",
        msg="double field is truncated to Int64",
        expression={"$toLong": "$v"},
        doc={"v": 7.9},
        expected=Int64(7),
    ),
    ExpressionTestCase(
        "string_field",
        msg="numeric string field converts to Int64",
        expression={"$toLong": "$v"},
        doc={"v": "99"},
        expected=Int64(99),
    ),
    ExpressionTestCase(
        "bool_field",
        msg="bool field converts to Int64",
        expression={"$toLong": "$v"},
        doc={"v": True},
        expected=Int64(1),
    ),
    ExpressionTestCase(
        "decimal_field",
        msg="Decimal128 field is truncated to Int64",
        expression={"$toLong": "$v"},
        doc={"v": Decimal128("5.9")},
        expected=Int64(5),
    ),
    ExpressionTestCase(
        "binary_field",
        msg="1-byte binary field converts to Int64",
        expression={"$toLong": "$v"},
        doc={"v": Binary(b"\x0a")},
        expected=Int64(10),
    ),
    ExpressionTestCase(
        "nested_field",
        msg="nested field path converts to Int64",
        expression={"$toLong": "$doc.v"},
        doc={"doc": {"v": 200}},
        expected=Int64(200),
    ),
    ExpressionTestCase(
        "missing_nested",
        msg="missing nested field returns null",
        expression={"$toLong": "$doc.missing"},
        doc={"doc": {"x": 1}},
        expected=None,
    ),
    ExpressionTestCase(
        "missing_field",
        msg="missing top-level field returns null",
        expression={"$toLong": "$v"},
        doc={},
        expected=None,
    ),
    ExpressionTestCase(
        "int64_max_field",
        msg="int64 max field passes through unchanged",
        expression={"$toLong": "$v"},
        doc={"v": INT64_MAX},
        expected=INT64_MAX,
    ),
    ExpressionTestCase(
        "composite_array_path",
        msg="$toLong fails when field path resolves to a composite array",
        expression={"$toLong": "$a.b"},
        doc={"a": [{"b": 1}, {"b": 2}]},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
]

# Property [Expression Input]: $toLong evaluates a nested expression before converting.
TOLONG_EXPRESSION_INPUT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "add",
        msg="$toLong converts an arithmetic expression result",
        expression={"$toLong": {"$add": [10, 20]}},
        expected=Int64(30),
    ),
    ExpressionTestCase(
        "concat",
        msg="$toLong converts a string concatenation expression result",
        expression={"$toLong": {"$concat": ["1", "23"]}},
        expected=Int64(123),
    ),
    ExpressionTestCase(
        "nested_conversion",
        msg="$toLong converts a nested type-conversion expression result",
        expression={"$toLong": {"$toDecimal": 42}},
        expected=Int64(42),
    ),
]


@pytest.mark.parametrize(
    "test", pytest_params(TOLONG_FIELD_REF_TESTS + TOLONG_EXPRESSION_INPUT_TESTS)
)
def test_toLong_field_ref(collection, test: ExpressionTestCase):
    """$toLong resolves field paths and nested paths from inserted documents."""
    if test.doc is not None:
        result = execute_expression_with_insert(collection, test.expression, test.doc)
    else:
        result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
