from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_project,
    execute_project_with_insert,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.parametrize import pytest_params

from .utils.regexMatch_common import (
    RegexMatchTest,
    _expr,
)


# Property [Document Field References]: $regexMatch works with field references
# from inserted documents, not just inline literals.
def test_regexmatch_document_fields(collection):
    """Test $regexMatch reads values from document fields."""
    result = execute_project_with_insert(
        collection,
        {"s": "hello world"},
        {"result": {"$regexMatch": {"input": "$s", "regex": "world"}}},
    )
    assertSuccess(
        result, [{"result": True}], msg="$regexMatch should match from document field references"
    )


# Property [Return Type]: result is always a boolean.
REGEXMATCH_RETURN_TYPE_TESTS: list[RegexMatchTest] = [
    RegexMatchTest(
        "return_type_match",
        input="hello",
        regex="hello",
        expected=True,
        msg="$regexMatch should return bool type on match",
    ),
    RegexMatchTest(
        "return_type_no_match",
        input="hello",
        regex="xyz",
        expected=False,
        msg="$regexMatch should return bool type on no match",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(REGEXMATCH_RETURN_TYPE_TESTS))
def test_regexmatch_return_type(collection, test_case: RegexMatchTest):
    """Test $regexMatch result is always a boolean."""
    expr = _expr(test_case)
    result = execute_project(collection, {"resultType": {"$type": expr}, "result": expr})
    assertSuccess(result, [{"resultType": "bool", "result": test_case.expected}], msg=test_case.msg)
