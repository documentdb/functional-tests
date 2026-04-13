from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import SETUNION_TYPE_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

# Property [Null Propagation]: if any argument is null or missing, the result
# is null.
SETUNION_NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_sole",
        expression={"$setUnion": ["$null"]},
        doc={"null": None},
        expected=None,
        msg="$setUnion should return null when the sole argument is null",
    ),
    ExpressionTestCase(
        "null_first",
        expression={"$setUnion": ["$null", "$a"]},
        doc={"null": None, "a": [1, 2]},
        expected=None,
        msg="$setUnion should return null when null value is in position: first",
    ),
    ExpressionTestCase(
        "null_last",
        expression={"$setUnion": ["$a", "$null"]},
        doc={"a": [1, 2], "null": None},
        expected=None,
        msg="$setUnion should return null when null value is in position: last",
    ),
    ExpressionTestCase(
        "null_middle",
        expression={"$setUnion": ["$a", "$null", "$b"]},
        doc={"a": [1], "null": None, "b": [2]},
        expected=None,
        msg="$setUnion should return null when null value is in position: middle",
    ),
    ExpressionTestCase(
        "null_all",
        expression={"$setUnion": ["$null", "$null2"]},
        doc={"null": None, "null2": None},
        expected=None,
        msg="$setUnion should return null when null value is in position: all",
    ),
    ExpressionTestCase(
        "null_as_array_element",
        expression={"$setUnion": ["$a"]},
        doc={"a": [None, None, 1]},
        expected=[None, 1],
        msg="$setUnion should deduplicate null elements within an array",
    ),
]

# Property [Null Propagation - Missing]: missing fields also propagate null.
SETUNION_MISSING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_sole",
        expression={"$setUnion": [MISSING]},
        expected=None,
        msg="$setUnion should return null when the sole argument is missing",
    ),
    ExpressionTestCase(
        "missing_first",
        expression={"$setUnion": [MISSING, "$a"]},
        doc={"a": [1, 2]},
        expected=None,
        msg="$setUnion should return null when missing value is in position: first",
    ),
    ExpressionTestCase(
        "missing_last",
        expression={"$setUnion": ["$a", MISSING]},
        doc={"a": [1, 2]},
        expected=None,
        msg="$setUnion should return null when missing value is in position: last",
    ),
    ExpressionTestCase(
        "missing_middle",
        expression={"$setUnion": ["$a", MISSING, "$b"]},
        doc={"a": [1], "b": [2]},
        expected=None,
        msg="$setUnion should return null when missing value is in position: middle",
    ),
    ExpressionTestCase(
        "missing_all",
        expression={"$setUnion": [MISSING, MISSING]},
        expected=None,
        msg="$setUnion should return null when missing value is in position: all",
    ),
]

# Property [Null Propagation - Cross]: null and missing cross-combinations.
SETUNION_NULL_MISSING_CROSS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_and_missing",
        expression={"$setUnion": ["$null", MISSING]},
        doc={"null": None},
        expected=None,
        msg="$setUnion should return null for cross-combination of null and missing",
    ),
    ExpressionTestCase(
        "missing_and_null",
        expression={"$setUnion": [MISSING, "$null"]},
        doc={"null": None},
        expected=None,
        msg="$setUnion should return null for cross-combination of missing and null",
    ),
]

# Property [Null/Missing Short-Circuit]: Null and missing arguments
# short-circuit (return null) when they appear before a non-array
# argument. When they appear after, field references to non-array
# values trigger a type error for both null and missing. However,
# $literal non-array expressions only error for null; missing still
# short-circuits.
SETUNION_SHORT_CIRCUIT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "sc_null_before_field_ref_non_array",
        expression={"$setUnion": ["$null", "$val"]},
        doc={"null": None, "val": "not_an_array"},
        expected=None,
        msg="$setUnion should return null when null field precedes a non-array field",
    ),
    ExpressionTestCase(
        "sc_field_ref_non_array_before_null",
        expression={"$setUnion": ["$val", "$null"]},
        doc={"val": "not_an_array", "null": None},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should error when a non-array field precedes a null field",
    ),
    ExpressionTestCase(
        "sc_missing_before_field_ref_non_array",
        expression={"$setUnion": [MISSING, "$val"]},
        doc={"val": "not_an_array"},
        expected=None,
        msg="$setUnion should return null when missing precedes a non-array field",
    ),
    ExpressionTestCase(
        "sc_field_ref_non_array_before_missing",
        expression={"$setUnion": ["$val", MISSING]},
        doc={"val": "not_an_array"},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should error when a non-array field precedes missing",
    ),
    ExpressionTestCase(
        "sc_literal_non_array_before_null",
        expression={"$setUnion": [{"$literal": "not_an_array"}, None]},
        error_code=SETUNION_TYPE_ERROR,
        msg="$setUnion should error when a $literal non-array precedes null",
    ),
    ExpressionTestCase(
        "sc_literal_non_array_before_missing",
        expression={"$setUnion": [{"$literal": "not_an_array"}, MISSING]},
        expected=None,
        msg="$setUnion should return null when a $literal non-array precedes missing",
    ),
]

SETUNION_NULL_TESTS_ALL = (
    SETUNION_NULL_TESTS
    + SETUNION_MISSING_TESTS
    + SETUNION_NULL_MISSING_CROSS_TESTS
    + SETUNION_SHORT_CIRCUIT_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SETUNION_NULL_TESTS_ALL))
def test_setunion_null(collection, test_case: ExpressionTestCase):
    """Test $setUnion null propagation cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc or {})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        ignore_order=True,
    )
