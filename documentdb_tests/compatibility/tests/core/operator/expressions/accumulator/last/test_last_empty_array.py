from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.accumulator.last.utils.last_common import (  # noqa: E501
    LastTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression_with_insert,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.parametrize import pytest_params

# Property [Empty Array]: when the argument resolves to an empty array,
# the result is missing (key absent), not null.
LAST_EMPTY_ARRAY_TESTS: list[LastTest] = [
    LastTest(
        "empty_array_literal",
        value={"$literal": []},
        msg="$last of empty array should produce missing (key absent), not null",
    ),
    LastTest(
        "empty_array_field_reference",
        value="$arr",
        document={"arr": []},
        msg="$last of empty array via field reference should produce missing, not null",
    ),
    LastTest(
        "empty_array_literal_unwrap",
        value=[[]],
        msg="$last of [[]] should unwrap to $last: [] and produce missing (key absent)",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(LAST_EMPTY_ARRAY_TESTS))
def test_last_empty_array(collection, test_case: LastTest):
    """Test $last of empty array produces MISSING."""
    result = execute_expression_with_insert(
        collection,
        {"$last": test_case.value},
        test_case.document or {},
    )
    assertSuccess(result, [{}], msg=test_case.msg)
