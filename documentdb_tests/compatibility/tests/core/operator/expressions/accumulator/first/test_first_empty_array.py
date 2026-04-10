from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.accumulator.first.utils.first_common import (  # noqa: E501
    FirstTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression_with_insert,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.parametrize import pytest_params

# Property [Empty Array]: when the argument resolves to an empty array,
# the result is missing (key absent), not null.
FIRST_EMPTY_ARRAY_TESTS: list[FirstTest] = [
    FirstTest(
        "empty_array_literal",
        value={"$literal": []},
        msg="$first of empty array should produce missing (key absent), not null",
    ),
    FirstTest(
        "empty_array_field_reference",
        value="$arr",
        document={"arr": []},
        msg="$first of empty array via field reference should produce missing, not null",
    ),
    FirstTest(
        "empty_array_literal_unwrap",
        value=[[]],
        msg="$first of [[]] should unwrap to $first: [] and produce missing (key absent)",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(FIRST_EMPTY_ARRAY_TESTS))
def test_first_empty_array(collection, test_case: FirstTest):
    """Test $first of empty array produces MISSING."""
    result = execute_expression_with_insert(
        collection,
        {"$first": test_case.value},
        test_case.document or {},
    )
    assertSuccess(result, [{}], msg=test_case.msg)
