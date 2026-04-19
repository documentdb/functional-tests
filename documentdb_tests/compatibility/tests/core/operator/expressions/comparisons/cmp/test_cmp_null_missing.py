"""
Tests for $cmp null and missing field handling.

Covers missing field behavior, explicit null field values, null vs missing distinctions,
and self-referential comparisons.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import FLOAT_NAN

CMP_MISSING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_vs_null",
        expression={"$cmp": ["$missing_field", None]},
        doc={"a": 1},
        expected=-1,
        msg="Missing field < null literal",
    ),
    ExpressionTestCase(
        "null_vs_missing",
        expression={"$cmp": [None, "$missing_field"]},
        doc={"a": 1},
        expected=1,
        msg="Null literal > missing field",
    ),
    ExpressionTestCase(
        "both_missing",
        expression={"$cmp": ["$missing1", "$missing2"]},
        doc={"a": 1},
        expected=0,
        msg="Both missing fields are equal",
    ),
    ExpressionTestCase(
        "missing_vs_int",
        expression={"$cmp": ["$missing_field", 1]},
        doc={"a": 1},
        expected=-1,
        msg="Missing field < int",
    ),
]


CMP_NULL_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "explicit_null_vs_null_literal",
        expression={"$cmp": ["$a", None]},
        doc={"a": None},
        expected=0,
        msg="Explicit null field equals null literal",
    ),
    ExpressionTestCase(
        "explicit_null_vs_missing",
        expression={"$cmp": ["$a", "$missing_field"]},
        doc={"a": None},
        expected=1,
        msg="Explicit null field > missing field",
    ),
    ExpressionTestCase(
        "explicit_null_vs_int",
        expression={"$cmp": ["$a", 1]},
        doc={"a": None},
        expected=-1,
        msg="Explicit null field < int",
    ),
]


CMP_SELF_REF_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "self_ref_int",
        expression={"$cmp": ["$a", "$a"]},
        doc={"a": 1},
        expected=0,
        msg="Field compared to itself should be equal",
    ),
    ExpressionTestCase(
        "self_ref_null",
        expression={"$cmp": ["$a", "$a"]},
        doc={"a": None},
        expected=0,
        msg="Null field compared to itself should be equal",
    ),
    ExpressionTestCase(
        "self_ref_nan",
        expression={"$cmp": ["$a", "$a"]},
        doc={"a": FLOAT_NAN},
        expected=0,
        msg="NaN field compared to itself should be equal",
    ),
]

ALL_TESTS = CMP_MISSING_TESTS + CMP_NULL_FIELD_TESTS + CMP_SELF_REF_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_cmp_null_missing(collection, test):
    """Test $cmp null, missing, and self-referential field handling."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
