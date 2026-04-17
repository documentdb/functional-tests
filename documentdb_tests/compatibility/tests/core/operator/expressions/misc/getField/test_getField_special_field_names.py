"""
Special field name tests for $getField expression.

Tests dotted fields, dollar-prefixed fields, field name edge cases,
operator name collisions, and system variable names as literal field keys.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# ---------------------------------------------------------------------------
# Non-dollar special field names — shorthand $getField
# ---------------------------------------------------------------------------
SHORTHAND_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "dotted_field",
        expression={"$getField": "a.b"},
        doc={"a.b": 42},
        expected=42,
        msg="Should access literal dotted field",
    ),
    ExpressionTestCase(
        "multi_dotted",
        expression={"$getField": "a.b.c"},
        doc={"a.b.c": "found"},
        expected="found",
        msg="Should access multi-dotted field",
    ),
    ExpressionTestCase(
        "array_index_key",
        expression={"$getField": "a.0"},
        doc={"a.0": 5},
        expected=5,
        msg="Should access literal 'a.0' field",
    ),
    ExpressionTestCase(
        "empty_string",
        expression={"$getField": ""},
        doc={"": 42},
        expected=42,
        msg="Should access empty string field",
    ),
    ExpressionTestCase(
        "spaces",
        expression={"$getField": "field name"},
        doc={"field name": 1},
        expected=1,
        msg="Should access field with spaces",
    ),
    ExpressionTestCase(
        "special_chars",
        expression={"$getField": "a@b#c"},
        doc={"a@b#c": 5},
        expected=5,
        msg="Should access field with special characters",
    ),
    ExpressionTestCase(
        "just_period",
        expression={"$getField": "."},
        doc={".": 1},
        expected=1,
        msg="Should access field named '.'",
    ),
    ExpressionTestCase(
        "double_period",
        expression={"$getField": "a..b"},
        doc={"a..b": 1},
        expected=1,
        msg="Should access field with consecutive periods",
    ),
    ExpressionTestCase(
        "leading_dot",
        expression={"$getField": ".a"},
        doc={".a": 1},
        expected=1,
        msg="Should access field starting with dot",
    ),
    ExpressionTestCase(
        "trailing_dot",
        expression={"$getField": "a."},
        doc={"a.": 1},
        expected=1,
        msg="Should access field ending with dot",
    ),
    ExpressionTestCase(
        "unicode",
        expression={"$getField": "café"},
        doc={"café": 1},
        expected=1,
        msg="Should access field with Unicode characters",
    ),
    ExpressionTestCase(
        "unicode_cjk",
        expression={"$getField": "日本語"},
        doc={"日本語": 2},
        expected=2,
        msg="Should access field with CJK characters",
    ),
    ExpressionTestCase(
        "duplicate_like",
        expression={"$getField": "a.b"},
        doc={"a.b": 2, "a": {"b": 99}},
        expected=2,
        msg="Should return literal 'a.b' field, not nested a.b",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SHORTHAND_TESTS))
def test_getField_shorthand_special_fields(collection, test):
    """Test $getField shorthand accesses special field names from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# ---------------------------------------------------------------------------
# Dollar-prefixed field names — require $literal in field param
# ---------------------------------------------------------------------------
DOLLAR_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "dollar_prefixed",
        expression={"$getField": {"field": {"$literal": "$price"}, "input": "$$ROOT"}},
        doc={"$price": 99},
        expected=99,
        msg="Should access $-prefixed field",
    ),
    ExpressionTestCase(
        "dollar_dot",
        expression={"$getField": {"field": {"$literal": "$a.b"}, "input": "$$ROOT"}},
        doc={"$a.b": 42},
        expected=42,
        msg="Should access $-and-dot field",
    ),
    ExpressionTestCase(
        "just_dollar",
        expression={"$getField": {"field": {"$literal": "$"}, "input": "$$ROOT"}},
        doc={"$": 1},
        expected=1,
        msg="Should access field named '$'",
    ),
    ExpressionTestCase(
        "double_dollar",
        expression={"$getField": {"field": {"$literal": "$$"}, "input": "$$ROOT"}},
        doc={"$$": 1},
        expected=1,
        msg="Should access field named '$$'",
    ),
    ExpressionTestCase(
        "operator_name_add",
        expression={"$getField": {"field": {"$literal": "$add"}, "input": "$$ROOT"}},
        doc={"$add": 1},
        expected=1,
        msg="Should access field literally named '$add'",
    ),
    ExpressionTestCase(
        "operator_name_getField",
        expression={"$getField": {"field": {"$literal": "$getField"}, "input": "$$ROOT"}},
        doc={"$getField": "meta"},
        expected="meta",
        msg="Should access field literally named '$getField'",
    ),
    ExpressionTestCase(
        "operator_name_match",
        expression={"$getField": {"field": {"$literal": "$match"}, "input": "$$ROOT"}},
        doc={"$match": 1},
        expected=1,
        msg="Should access field literally named '$match'",
    ),
    ExpressionTestCase(
        "sysvar_root_as_key",
        expression={"$getField": {"field": {"$literal": "$$ROOT"}, "input": "$$ROOT"}},
        doc={"$$ROOT": "found"},
        expected="found",
        msg="Should access field literally named '$$ROOT'",
    ),
    ExpressionTestCase(
        "sysvar_current_as_key",
        expression={"$getField": {"field": {"$literal": "$$CURRENT"}, "input": "$$ROOT"}},
        doc={"$$CURRENT": "found"},
        expected="found",
        msg="Should access field literally named '$$CURRENT'",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DOLLAR_FIELD_TESTS))
def test_getField_dollar_special_fields(collection, test):
    """Test $getField accesses dollar-prefixed field names from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
