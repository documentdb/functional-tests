from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_project_with_insert,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.parametrize import pytest_params

from .utils.strcasecmp_common import (
    StrcasecmpTest,
    _expr,
)

# Property [Expression Arguments]: both positions accept expressions that resolve
# to the expected type.
STRCASECMP_EXPR_TESTS: list[StrcasecmpTest] = [
    # Verify expressions are actually evaluated, not just accepted.
    StrcasecmpTest(
        "expr_concat_first_less",
        string1={"$concat": ["hel", "lo"]},
        string2="world",
        expected=-1,
        msg="$strcasecmp should evaluate $concat expression in first position",
    ),
    StrcasecmpTest(
        "expr_concat_second_less",
        string1="world",
        string2={"$concat": ["hel", "lo"]},
        expected=1,
        msg="$strcasecmp should evaluate $concat expression in second position",
    ),
    # Expression returning null in either position.
    StrcasecmpTest(
        "expr_null_result_first",
        string1={"$concat": ["a", None]},
        string2="hello",
        expected=-1,
        msg="$strcasecmp should handle expression returning null in first position",
    ),
    StrcasecmpTest(
        "expr_null_result_second",
        string1="hello",
        string2={"$concat": ["a", None]},
        expected=1,
        msg="$strcasecmp should handle expression returning null in second position",
    ),
    # Expression returning number in either position.
    StrcasecmpTest(
        "expr_number_result_first",
        string1={"$add": [1, 2]},
        string2="hello",
        expected=-1,
        msg="$strcasecmp should handle expression returning number in first position",
    ),
    StrcasecmpTest(
        "expr_number_result_second",
        string1="hello",
        string2={"$add": [1, 2]},
        expected=1,
        msg="$strcasecmp should handle expression returning number in second position",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(STRCASECMP_EXPR_TESTS))
def test_strcasecmp_expr_cases(collection, test_case: StrcasecmpTest):
    """Test $strcasecmp expression argument cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )


def test_strcasecmp_document_fields(collection):
    """Test $strcasecmp reads values from document fields."""
    result = execute_project_with_insert(
        collection,
        {"a": "Hello", "b": "HELLO"},
        {"result": {"$strcasecmp": ["$a", "$b"]}},
    )
    assertSuccess(
        result,
        [{"result": 0}],
        msg="$strcasecmp should compare document field values case-insensitively",
    )
