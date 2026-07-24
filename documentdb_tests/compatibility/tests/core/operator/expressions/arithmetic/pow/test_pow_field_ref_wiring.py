"""
Field-reference wiring tests for $pow expression.

Confirms field-path resolution feeds correctly into $pow (one type-combo,
one boundary, one null); full matrices are covered as literals elsewhere.
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
from documentdb_tests.framework.test_constants import (
    INT32_MAX,
    MISSING,
)

POW_INSERT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "same_type_int32",
        expression={"$pow": ["$base", "$power"]},
        doc={"base": 2, "power": 3},
        expected=8,
        msg="Should handle same type int32",
    ),
    ExpressionTestCase(
        "int32_max_base",
        expression={"$pow": ["$base", "$power"]},
        doc={"base": INT32_MAX, "power": 1},
        expected=INT32_MAX,
        msg="Should handle int32 max base",
    ),
    ExpressionTestCase(
        "null_base",
        expression={"$pow": ["$base", "$power"]},
        doc={"base": None, "power": 2},
        expected=None,
        msg="Should return null for null base",
    ),
    ExpressionTestCase(
        "missing_base",
        expression={"$pow": ["$base", "$power"]},
        doc={"power": 2},
        expected=None,
        msg="Should return null for missing base",
    ),
    ExpressionTestCase(
        "missing_exponent",
        expression={"$pow": ["$base", "$power"]},
        doc={"base": 2},
        expected=None,
        msg="Should return null for missing exponent",
    ),
]


POW_MIXED_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "same_type_int32",
        expression={"$pow": ["$base", 3]},
        doc={"base": 2},
        expected=8,
        msg="Should handle same type int32",
    ),
    ExpressionTestCase(
        "int32_max_base",
        expression={"$pow": ["$base", 1]},
        doc={"base": INT32_MAX},
        expected=INT32_MAX,
        msg="Should handle int32 max base",
    ),
    ExpressionTestCase(
        "null_base",
        expression={"$pow": ["$base", 2]},
        doc={"base": None},
        expected=None,
        msg="Should return null for null base",
    ),
    ExpressionTestCase(
        "missing_base",
        expression={"$pow": ["$base", 2]},
        doc={},
        expected=None,
        msg="Should return null for missing base",
    ),
    ExpressionTestCase(
        "missing_exponent",
        expression={"$pow": ["$base", MISSING]},
        doc={"base": 2},
        expected=None,
        msg="Should return null for missing exponent",
    ),
]


@pytest.mark.parametrize("test", pytest_params(POW_INSERT_TESTS))
def test_pow_insert(collection, test):
    """Test $pow from documents"""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(POW_MIXED_TESTS))
def test_pow_mixed(collection, test):
    """Test $pow from mixed documents and literals"""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
