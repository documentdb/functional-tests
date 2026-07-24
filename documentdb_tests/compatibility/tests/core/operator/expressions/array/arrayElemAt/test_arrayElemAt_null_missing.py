"""
Null and missing field behavior tests for $arrayElemAt expression.

Tests null propagation and missing field handling for array and index arguments.
"""

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.framework.test_constants import MISSING

# Property [Null Propagation]: $arrayElemAt returns null when the array or index argument is null.
NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="null_array",
        doc={"arr": None, "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=None,
        msg="$arrayElemAt should return null for null array",
    ),
    ExpressionTestCase(
        id="null_array_neg_idx",
        doc={"arr": None, "idx": -1},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=None,
        msg="$arrayElemAt should return null for null array with negative index",
    ),
    ExpressionTestCase(
        id="null_index",
        doc={"arr": [1, 2], "idx": None},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=None,
        msg="$arrayElemAt should return null for null index",
    ),
    ExpressionTestCase(
        id="both_null",
        doc={"arr": None, "idx": None},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=None,
        msg="$arrayElemAt should return null when both null",
    ),
]

# Property [Missing Propagation]: $arrayElemAt returns null when the array or index is missing.
LITERAL_ONLY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="missing_array",
        doc={"arr": MISSING, "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=None,
        msg="$arrayElemAt should return null for missing array",
    ),
    ExpressionTestCase(
        id="missing_index",
        doc={"arr": [1, 2, 3], "idx": MISSING},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=None,
        msg="$arrayElemAt should return null for missing index",
    ),
]
