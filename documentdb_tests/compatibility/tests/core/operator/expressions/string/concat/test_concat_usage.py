from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
    execute_project_with_insert,
)


# Property [Document Field References]: $concat works with field references from inserted documents.
def test_concat_document_fields(collection):
    """Test $concat reads values from document fields."""
    result = execute_project_with_insert(
        collection,
        {"a": "hello", "b": " ", "c": "world"},
        {"result": {"$concat": ["$a", "$b", "$c"]}},
    )
    assertSuccess(
        result, [{"result": "hello world"}], msg="$concat should resolve field references"
    )


# Property [Bare Argument]: bare string or null (non-array) is accepted by $concat.
_SYNTAX_BARE_VALID = [
    pytest.param("hello", "hello", id="bare_string"),
    pytest.param(None, None, id="bare_null"),
]


@pytest.mark.parametrize("value, expected", _SYNTAX_BARE_VALID)
def test_concat_bare_argument(collection, value, expected):
    """Test $concat accepts a bare string or null without an array wrapper."""
    result = execute_expression(collection, {"$concat": value})
    assertSuccess(
        result,
        [{"result": expected}],
        msg=f"$concat bare argument {value!r} should return {expected!r}",
    )
