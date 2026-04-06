"""Demo: object-input operator argument validation using shared OBJECT_INPUT_INVALID_ARGS."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assertExprResult,
    execute_expression,
)
from documentdb_tests.framework.error_codes import ErrorCode
from documentdb_tests.framework.test_constants import OBJECT_INPUT_INVALID_ARGS

# $filter requires an object argument; error code 28646 for non-object input
FILTER_OBJECT_REQUIRED_ERROR = ErrorCode(28646)


@pytest.mark.parametrize("arg", OBJECT_INPUT_INVALID_ARGS)
def test_filter_rejects_non_object_arg(collection, arg):
    """Test $filter rejects non-object arguments."""
    result = execute_expression(collection, {"$filter": arg})
    assertExprResult(result, FILTER_OBJECT_REQUIRED_ERROR)
