"""Tests for how getClusterParameter interprets parameter names.

Parameter names are exact-match literals: there is no field-path traversal,
operator interpretation, globbing, or case folding. Any name that is not an
exact match for an existing cluster parameter is reported as unknown, and the
single-name and array forms report an unknown name identically.
"""

from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import NO_SUCH_KEY_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase

pytestmark = pytest.mark.admin

_VALID_PARAM = "changeStreamOptions"


# ---------------------------------------------------------------------------
# §8  Argument boundary probing — name strings are exact literals
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NameCase(BaseTestCase):
    """Test case for literal name semantics."""

    name: Any = None


_BOUNDARY_NAMES: list[NameCase] = [
    NameCase(
        "whitespace_only",
        name="   ",
        error_code=NO_SUCH_KEY_ERROR,
        msg="Whitespace-only string should be treated as a literal no-match",
    ),
    NameCase(
        "dotted_name",
        name="a.b.c",
        error_code=NO_SUCH_KEY_ERROR,
        msg="Dotted name should not be traversed as a field path",
    ),
    NameCase(
        "dollar_prefix",
        name="$foo",
        error_code=NO_SUCH_KEY_ERROR,
        msg="Dollar-prefixed name should not be interpreted as an operator",
    ),
    NameCase(
        "unicode_name",
        name="paramétré",
        error_code=NO_SUCH_KEY_ERROR,
        msg="Unicode name should be treated as a literal no-match",
    ),
    NameCase(
        "very_long_name",
        name="x" * 10000,
        error_code=NO_SUCH_KEY_ERROR,
        msg="Very long name should not crash or timeout",
    ),
    NameCase(
        "case_altered",
        name="ChangeStreamOptions",
        error_code=NO_SUCH_KEY_ERROR,
        msg="Altered-case known name should not match (case-sensitive)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(_BOUNDARY_NAMES))
def test_getClusterParameter_name_is_literal_string(collection, test):
    """Test that parameter names are treated as exact literal strings."""
    result = execute_admin_command(collection, {"getClusterParameter": test.name})
    assertFailureCode(result, test.error_code, msg=test.msg)


# ---------------------------------------------------------------------------
# §9  Wildcard edge interactions
# ---------------------------------------------------------------------------


def test_getClusterParameter_star_in_array_is_literal_name(collection):
    """Test ['*'] treats '*' as a literal name (not expand-all) and errors."""
    result = execute_admin_command(collection, {"getClusterParameter": ["*"]})
    assertFailureCode(
        result, NO_SUCH_KEY_ERROR, msg="'*' inside an array is a literal name, not a wildcard"
    )


def test_getClusterParameter_double_star_no_glob(collection):
    """Test '**' is treated as a literal name, not a pattern."""
    result = execute_admin_command(collection, {"getClusterParameter": "**"})
    assertFailureCode(result, NO_SUCH_KEY_ERROR, msg="'**' should not be treated as a glob")


def test_getClusterParameter_star_prefix_no_glob(collection):
    """Test '*foo' is treated as a literal name, not a pattern."""
    result = execute_admin_command(collection, {"getClusterParameter": "*foo"})
    assertFailureCode(result, NO_SUCH_KEY_ERROR, msg="'*foo' should not be treated as a glob")


def test_getClusterParameter_array_star_and_valid_name(collection):
    """Test ['*', validName] treats '*' as a literal no-match and errors."""
    result = execute_admin_command(collection, {"getClusterParameter": ["*", _VALID_PARAM]})
    assertFailureCode(
        result,
        NO_SUCH_KEY_ERROR,
        msg="'*' inside array with valid name should still error on '*' literal",
    )


# ---------------------------------------------------------------------------
# §11  Unknown-name contract consistency
# ---------------------------------------------------------------------------


def test_getClusterParameter_unknown_single_string_errors(collection):
    """Test single unknown string fails with NO_SUCH_KEY_ERROR."""
    result = execute_admin_command(collection, {"getClusterParameter": "unknownParam"})
    assertFailureCode(
        result,
        NO_SUCH_KEY_ERROR,
        msg="Single unknown name should fail with no-such-parameter error",
    )


def test_getClusterParameter_unknown_in_array_errors(collection):
    """Test ['unknownParam'] fails with same error as 'unknownParam' string."""
    result = execute_admin_command(collection, {"getClusterParameter": ["unknownParam"]})
    assertFailureCode(
        result,
        NO_SUCH_KEY_ERROR,
        msg="Array containing single unknown name should fail identically to string form",
    )
