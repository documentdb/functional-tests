"""
Tests for $eq null and missing field handling.

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

EQ_MISSING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_vs_null",
        expression={"$eq": ["$missing_field", None]},
        doc={"a": 1},
        expected=False,
        msg="Missing field not equal to null literal",
    ),
    ExpressionTestCase(
        "null_vs_missing",
        expression={"$eq": [None, "$missing_field"]},
        doc={"a": 1},
        expected=False,
        msg="Null literal not equal to missing field",
    ),
    ExpressionTestCase(
        "both_missing",
        expression={"$eq": ["$missing1", "$missing2"]},
        doc={"a": 1},
        expected=True,
        msg="Both missing fields are equal",
    ),
    ExpressionTestCase(
        "missing_vs_int",
        expression={"$eq": ["$missing_field", 1]},
        doc={"a": 1},
        expected=False,
        msg="Missing field not equal to int",
    ),
    ExpressionTestCase(
        "int_vs_missing",
        expression={"$eq": [1, "$missing_field"]},
        doc={"a": 1},
        expected=False,
        msg="Int not equal to missing field",
    ),
]


EQ_NULL_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "explicit_null_vs_null_literal",
        expression={"$eq": ["$a", None]},
        doc={"a": None},
        expected=True,
        msg="Explicit null field equals null literal",
    ),
    ExpressionTestCase(
        "null_literal_vs_explicit_null",
        expression={"$eq": [None, "$a"]},
        doc={"a": None},
        expected=True,
        msg="Null literal equals explicit null field",
    ),
    ExpressionTestCase(
        "explicit_null_vs_missing",
        expression={"$eq": ["$a", "$missing_field"]},
        doc={"a": None},
        expected=False,
        msg="Explicit null field not equal to missing field",
    ),
    ExpressionTestCase(
        "missing_vs_explicit_null",
        expression={"$eq": ["$missing_field", "$a"]},
        doc={"a": None},
        expected=False,
        msg="Missing field not equal to explicit null field",
    ),
    ExpressionTestCase(
        "both_explicit_null",
        expression={"$eq": ["$a", "$b"]},
        doc={"a": None, "b": None},
        expected=True,
        msg="Both explicit null fields are equal",
    ),
    ExpressionTestCase(
        "explicit_null_vs_int",
        expression={"$eq": ["$a", 1]},
        doc={"a": None},
        expected=False,
        msg="Explicit null field not equal to int",
    ),
]


EQ_SELF_REF_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "self_ref_int",
        expression={"$eq": ["$a", "$a"]},
        doc={"a": 1},
        expected=True,
        msg="Field compared to itself should be equal",
    ),
    ExpressionTestCase(
        "self_ref_null",
        expression={"$eq": ["$a", "$a"]},
        doc={"a": None},
        expected=True,
        msg="Null field compared to itself should be equal",
    ),
    ExpressionTestCase(
        "self_ref_nan",
        expression={"$eq": ["$a", "$a"]},
        doc={"a": FLOAT_NAN},
        expected=True,
        msg="NaN field compared to itself should be equal (BSON equality)",
    ),
    ExpressionTestCase(
        "self_ref_missing",
        expression={"$eq": ["$missing", "$missing"]},
        doc={"a": 1},
        expected=True,
        msg="Missing field compared to itself should be equal",
    ),
]

ALL_TESTS = EQ_MISSING_TESTS + EQ_NULL_FIELD_TESTS + EQ_SELF_REF_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_eq_null_missing(collection, test):
    """Test $eq null, missing, and self-referential field handling."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
