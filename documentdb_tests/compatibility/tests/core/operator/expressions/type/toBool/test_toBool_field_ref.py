"""$toBool field reference and expression-as-input tests."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.type.utils.convert_variants import (  # noqa: E501
    with_convert_variants,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import INT32_ZERO

# Property [Field Reference]: $toBool resolves field paths and nested dot-notation paths;
# missing fields return null.
TOBOOL_FIELD_REF_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "truthy_string_field",
        msg="String field value converts to true",
        expression={"$toBool": "$v"},
        doc={"v": "hello"},
        expected=True,
    ),
    ExpressionTestCase(
        "falsy_int_field",
        msg="Zero integer field value converts to false",
        expression={"$toBool": "$v"},
        doc={"v": INT32_ZERO},
        expected=False,
    ),
    ExpressionTestCase(
        "truthy_int_field",
        msg="Non-zero integer field value converts to true",
        expression={"$toBool": "$v"},
        doc={"v": 1},
        expected=True,
    ),
    ExpressionTestCase(
        "bool_true_field",
        msg="true boolean field passes through unchanged",
        expression={"$toBool": "$v"},
        doc={"v": True},
        expected=True,
    ),
    ExpressionTestCase(
        "bool_false_field",
        msg="false boolean field passes through unchanged",
        expression={"$toBool": "$v"},
        doc={"v": False},
        expected=False,
    ),
    ExpressionTestCase(
        "null_field",
        msg="Null document field returns null",
        expression={"$toBool": "$v"},
        doc={"v": None},
        expected=None,
    ),
    ExpressionTestCase(
        "missing_field",
        msg="Missing top-level field returns null",
        expression={"$toBool": "$v"},
        doc={},
        expected=None,
    ),
    ExpressionTestCase(
        "nested_field",
        msg="Nested dot-notation field path resolves and converts",
        expression={"$toBool": "$doc.v"},
        doc={"doc": {"v": "hello"}},
        expected=True,
    ),
    ExpressionTestCase(
        "missing_nested_field",
        msg="Missing nested field returns null",
        expression={"$toBool": "$doc.missing"},
        doc={"doc": {"x": 1}},
        expected=None,
    ),
    ExpressionTestCase(
        "composite_array_path",
        msg="Field path resolving to a composite array (array-of-objects) is truthy",
        expression={"$toBool": "$a.b"},
        doc={"a": [{"b": 1}, {"b": 2}]},
        expected=True,
    ),
]

# Property [Expression Input]: $toBool evaluates a nested expression before converting.
TOBOOL_EXPRESSION_INPUT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "add_result",
        msg="$toBool converts an arithmetic expression result",
        expression={"$toBool": {"$add": [1, 2]}},
        expected=True,
    ),
    ExpressionTestCase(
        "empty_object_argument",
        msg="An empty object argument evaluates to an empty document, which is truthy",
        expression={"$toBool": {}},
        expected=True,
    ),
    ExpressionTestCase(
        "tostring_zero",
        msg="$toBool converts $toString(0) to true because the string '0' is truthy",
        expression={"$toBool": {"$toString": INT32_ZERO}},
        expected=True,
    ),
    ExpressionTestCase(
        "todouble_zero_string",
        msg="$toBool converts $toDouble('0.0') to false because double 0.0 is falsy",
        expression={"$toBool": {"$toDouble": "0.0"}},
        expected=False,
    ),
]


@pytest.mark.parametrize(
    "test",
    pytest_params(
        with_convert_variants(
            TOBOOL_FIELD_REF_TESTS + TOBOOL_EXPRESSION_INPUT_TESTS, "$toBool", "bool"
        )
    ),
)
def test_toBool_field_ref(collection, test: ExpressionTestCase):
    """$toBool resolves field paths from inserted documents and evaluates nested expressions."""
    if test.doc is not None:
        result = execute_expression_with_insert(collection, test.expression, test.doc)
    else:
        result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
