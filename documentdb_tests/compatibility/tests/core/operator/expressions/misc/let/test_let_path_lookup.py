"""
Path lookup on variable tests for $let.

Covers basic path lookup, array path lookup, and null/missing path lookup.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.parametrize import pytest_params

# ---------------------------------------------------------------------------
# Path lookup success cases
# ---------------------------------------------------------------------------
PATH_SUCCESS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_object",
        expression={"$let": {"vars": {"x": {"a": {"b": 1}}}, "in": "$$x.a"}},
        expected={"b": 1},
        msg="Should return nested object via path",
    ),
    ExpressionTestCase(
        "scalar",
        expression={"$let": {"vars": {"x": {"a": {"b": 42}}}, "in": "$$x.a.b"}},
        expected=42,
        msg="Should return scalar via deep path",
    ),
    ExpressionTestCase(
        "multi_level_scalar",
        expression={"$let": {"vars": {"x": {"a": {"b": {"c": 99}}}}, "in": "$$x.a.b.c"}},
        expected=99,
        msg="Should return scalar via multi-level path",
    ),
    ExpressionTestCase(
        "array_of_objects",
        expression={"$let": {"vars": {"x": [{"b": 1}, {"b": 2}]}, "in": "$$x.b"}},
        expected=[1, 2],
        msg="Should return array of field values",
    ),
    ExpressionTestCase(
        "array_multiple",
        expression={"$let": {"vars": {"x": [{"b": 10}, {"b": 20}, {"b": 30}]}, "in": "$$x.b"}},
        expected=[10, 20, 30],
        msg="Should return all matching values",
    ),
    ExpressionTestCase(
        "array_nonexistent",
        expression={"$let": {"vars": {"x": [{"b": 1}, {"b": 2}]}, "in": "$$x.c"}},
        expected=[],
        msg="Non-existent path on array should return empty array",
    ),
    ExpressionTestCase(
        "array_with_null",
        expression={"$let": {"vars": {"x": [{"b": None}]}, "in": "$$x.b"}},
        expected=[None],
        msg="Should return array with null",
    ),
    ExpressionTestCase(
        "array_mixed_null",
        expression={"$let": {"vars": {"x": [{"b": 1}, {"b": None}, {"b": 3}]}, "in": "$$x.b"}},
        expected=[1, None, 3],
        msg="Should return mixed values and null",
    ),
    ExpressionTestCase(
        "array_null_deeper",
        expression={"$let": {"vars": {"x": [{"b": None}, {"b": None}]}, "in": "$$x.b.c"}},
        expected=[],
        msg="Deeper path on null fields should return empty array",
    ),
    # Special characters in field path names
    ExpressionTestCase(
        "hyphenated_field",
        expression={
            "$let": {
                "vars": {"x": {"good": 10, "bad-val": 20}},
                "in": {"$add": ["$$x.good", "$$x.bad-val"]},
            }
        },
        expected=30,
        msg="Should resolve hyphenated field name in path",
    ),
    ExpressionTestCase(
        "nested_hyphen_and_dollar",
        expression={
            "$let": {
                "vars": {"x": {"a": {"sub-val": 55}, "b-val": {"c$val": 45}}},
                "in": {"$add": ["$$x.a.sub-val", "$$x.b-val.c$val"]},
            }
        },
        expected=100,
        msg="Should resolve nested hyphen and dollar field names",
    ),
    ExpressionTestCase(
        "deep_special_chars",
        expression={
            "$let": {
                "vars": {
                    "x": {
                        "a": {"-a-1": {"@a@2": {"a$3": 5}}},
                        "b": {"%b%1": {"*b*2": {"%b%3": 10}}},
                    }
                },
                "in": {"$add": ["$$x.a.-a-1.@a@2.a$3", "$$x.b.%b%1.*b*2.%b%3"]},
            }
        },
        expected=15,
        msg="Should resolve deep paths with hyphen, at, dollar, percent, asterisk",
    ),
    ExpressionTestCase(
        "deep_extended_special_chars",
        expression={
            "$let": {
                "vars": {
                    "x": {
                        "a": {"-a-1-": {"@a@2@": {"a$3$": 5}}},
                        "b": {"%b%1%": {"*b*2*": {"&b&3&": 10}}},
                        "c": {"~c~1~": {"!c!2!": {"+c+3+": 3}}},
                    }
                },
                "in": {
                    "$add": [
                        "$$x.a.-a-1-.@a@2@.a$3$",
                        "$$x.b.%b%1%.*b*2*.&b&3&",
                        "$$x.c.~c~1~.!c!2!.+c+3+",
                    ]
                },
            }
        },
        expected=18,
        msg="Should resolve deep paths with tilde, exclamation, plus, ampersand",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PATH_SUCCESS_TESTS))
def test_let_path_lookup(collection, test):
    """Test $let path lookup on variable values."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# ---------------------------------------------------------------------------
# Path lookup missing/omitted cases
# ---------------------------------------------------------------------------
PATH_MISSING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nonexistent",
        expression={"$let": {"vars": {"x": {"a": 1}}, "in": "$$x.b"}},
        msg="Non-existent path should omit field",
    ),
    ExpressionTestCase(
        "deep_nonexistent",
        expression={"$let": {"vars": {"x": {"a": {"b": 1}}}, "in": "$$x.a.c.d"}},
        msg="Deep non-existent path should omit field",
    ),
    ExpressionTestCase(
        "null_variable",
        expression={"$let": {"vars": {"x": None}, "in": "$$x.a"}},
        msg="Path on null variable should omit field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PATH_MISSING_TESTS))
def test_let_path_lookup_missing(collection, test):
    """Test $let path lookup that results in missing/omitted field."""
    result = execute_expression(collection, test.expression)
    assertSuccess(result, [{}], msg=test.msg)
