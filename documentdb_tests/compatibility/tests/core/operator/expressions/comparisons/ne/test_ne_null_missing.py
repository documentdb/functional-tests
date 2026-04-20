"""
Tests for $ne null and missing field handling.

Covers missing field behavior, explicit null field values, null vs missing distinctions,
and self-referential comparisons.
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
from documentdb_tests.framework.test_constants import FLOAT_NAN

NE_MISSING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_vs_null",
        expression={"$ne": ["$missing_field", None]},
        doc={"a": 1},
        expected=True,
        msg="Missing field not equal to null literal",
    ),
    ExpressionTestCase(
        "null_vs_missing",
        expression={"$ne": [None, "$missing_field"]},
        doc={"a": 1},
        expected=True,
        msg="Null literal not equal to missing field",
    ),
    ExpressionTestCase(
        "both_missing",
        expression={"$ne": ["$missing1", "$missing2"]},
        doc={"a": 1},
        expected=False,
        msg="Both missing fields are equal",
    ),
    ExpressionTestCase(
        "missing_vs_int",
        expression={"$ne": ["$missing_field", 1]},
        doc={"a": 1},
        expected=True,
        msg="Missing field not equal to int",
    ),
    ExpressionTestCase(
        "int_vs_missing",
        expression={"$ne": [1, "$missing_field"]},
        doc={"a": 1},
        expected=True,
        msg="Int not equal to missing field",
    ),
]


NE_NULL_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "explicit_null_vs_null_literal",
        expression={"$ne": ["$a", None]},
        doc={"a": None},
        expected=False,
        msg="Explicit null field equals null literal",
    ),
    ExpressionTestCase(
        "null_literal_vs_explicit_null",
        expression={"$ne": [None, "$a"]},
        doc={"a": None},
        expected=False,
        msg="Null literal equals explicit null field",
    ),
    ExpressionTestCase(
        "explicit_null_vs_missing",
        expression={"$ne": ["$a", "$missing_field"]},
        doc={"a": None},
        expected=True,
        msg="Explicit null field not equal to missing field",
    ),
    ExpressionTestCase(
        "missing_vs_explicit_null",
        expression={"$ne": ["$missing_field", "$a"]},
        doc={"a": None},
        expected=True,
        msg="Missing field not equal to explicit null field",
    ),
    ExpressionTestCase(
        "both_explicit_null",
        expression={"$ne": ["$a", "$b"]},
        doc={"a": None, "b": None},
        expected=False,
        msg="Both explicit null fields are equal",
    ),
    ExpressionTestCase(
        "explicit_null_vs_int",
        expression={"$ne": ["$a", 1]},
        doc={"a": None},
        expected=True,
        msg="Explicit null field not equal to int",
    ),
]


NE_SELF_REF_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "self_ref_int",
        expression={"$ne": ["$a", "$a"]},
        doc={"a": 1},
        expected=False,
        msg="Field compared to itself should be equal",
    ),
    ExpressionTestCase(
        "self_ref_null",
        expression={"$ne": ["$a", "$a"]},
        doc={"a": None},
        expected=False,
        msg="Null field compared to itself should be equal",
    ),
    ExpressionTestCase(
        "self_ref_nan",
        expression={"$ne": ["$a", "$a"]},
        doc={"a": FLOAT_NAN},
        expected=False,
        msg="NaN field compared to itself should be equal (BSON equality)",
    ),
    ExpressionTestCase(
        "self_ref_missing",
        expression={"$ne": ["$missing", "$missing"]},
        doc={"a": 1},
        expected=False,
        msg="Missing field compared to itself should be equal",
    ),
]

ALL_TESTS = NE_MISSING_TESTS + NE_NULL_FIELD_TESTS + NE_SELF_REF_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_ne_null_missing(collection, test):
    """Test $ne null, missing, and self-referential field handling."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
