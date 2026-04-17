from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import (
    REPLACE_FIND_TYPE_ERROR,
    REPLACE_INPUT_TYPE_ERROR,
    REPLACE_REPLACEMENT_TYPE_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

from .utils.replaceAll_common import (
    ReplaceAllTest,
    _expr,
)

# Property [Type Error Precedence]: type errors take precedence over null propagation. When
# multiple arguments have type errors, input is validated first, then find, then replacement.
REPLACEALL_TYPE_PRECEDENCE_TESTS: list[ReplaceAllTest] = [
    # Type error on find takes precedence over null input.
    ReplaceAllTest(
        "precedence_null_input_type_find",
        input=None,
        find=123,
        replacement="b",
        error_code=REPLACE_FIND_TYPE_ERROR,
        msg="$replaceAll precedence: null input type find",
    ),
    # Type error on replacement takes precedence over null input.
    ReplaceAllTest(
        "precedence_null_input_type_replacement",
        input=None,
        find="a",
        replacement=123,
        error_code=REPLACE_REPLACEMENT_TYPE_ERROR,
        msg="$replaceAll precedence: null input type replacement",
    ),
    # Type error on replacement takes precedence over null find.
    ReplaceAllTest(
        "precedence_null_find_type_replacement",
        input="hello",
        find=None,
        replacement=123,
        error_code=REPLACE_REPLACEMENT_TYPE_ERROR,
        msg="$replaceAll precedence: null find type replacement",
    ),
    # Input type error takes precedence over find type error.
    ReplaceAllTest(
        "precedence_input_before_find",
        input=123,
        find=456,
        replacement="b",
        error_code=REPLACE_INPUT_TYPE_ERROR,
        msg="$replaceAll precedence: input before find",
    ),
    # Input type error takes precedence over replacement type error.
    ReplaceAllTest(
        "precedence_input_before_replacement",
        input=123,
        find="a",
        replacement=456,
        error_code=REPLACE_INPUT_TYPE_ERROR,
        msg="$replaceAll precedence: input before replacement",
    ),
    # Find type error takes precedence over replacement type error.
    ReplaceAllTest(
        "precedence_find_before_replacement",
        input="hello",
        find=123,
        replacement=456,
        error_code=REPLACE_FIND_TYPE_ERROR,
        msg="$replaceAll precedence: find before replacement",
    ),
    # All three have type errors: input wins.
    ReplaceAllTest(
        "precedence_all_type_errors",
        input=123,
        find=456,
        replacement=789,
        error_code=REPLACE_INPUT_TYPE_ERROR,
        msg="$replaceAll precedence: all type errors",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(REPLACEALL_TYPE_PRECEDENCE_TESTS))
def test_replaceall_type_precedence_cases(collection, test_case: ReplaceAllTest):
    """Test $replaceAll type error precedence cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
