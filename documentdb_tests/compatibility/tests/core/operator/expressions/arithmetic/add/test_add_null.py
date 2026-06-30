from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

# Property [Null Propagation]: $add returns null if any operand is null or refers to a missing
# field.
ADD_NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "single_null",
        doc={"a": None},
        expression={"$add": ["$a"]},
        expected=None,
        msg="$add should return null for a single null operand",
    ),
    ExpressionTestCase(
        "null_operand",
        doc={"a": 1, "b": None},
        expression={"$add": ["$a", "$b"]},
        expected=None,
        msg="$add should return null when any operand is null",
    ),
    ExpressionTestCase(
        "missing_field",
        doc={},
        expression={"$add": [1, MISSING]},
        expected=None,
        msg="$add should return null when any operand is a missing field",
    ),
    ExpressionTestCase(
        "null_with_multiple",
        doc={"a": 1, "b": 2, "c": None},
        expression={"$add": ["$a", "$b", "$c"]},
        expected=None,
        msg="$add should return null when null appears among multiple operands",
    ),
    ExpressionTestCase(
        "null_in_middle",
        doc={"a": 1, "b": 2, "c": 3, "e": 5},
        expression={"$add": ["$a", "$b", "$c", None, "$e"]},
        expected=None,
        msg="$add should return null when null appears in the middle of operands",
    ),
    ExpressionTestCase(
        "all_null",
        doc={"a": None, "b": None},
        expression={"$add": ["$a", "$b"]},
        expected=None,
        msg="$add should return null when all operands are null",
    ),
    ExpressionTestCase(
        "all_missing",
        doc={},
        expression={"$add": [MISSING, MISSING]},
        expected=None,
        msg="$add should return null when all operands are missing fields",
    ),
    ExpressionTestCase(
        "date_and_null",
        doc={"a": datetime(2026, 1, 1, tzinfo=timezone.utc), "b": None},
        expression={"$add": ["$a", "$b"]},
        expected=None,
        msg="$add should return null when a date is paired with a null operand",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(ADD_NULL_TESTS))
def test_add_null(collection, test_case: ExpressionTestCase):
    """Test $add null and missing field propagation cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
