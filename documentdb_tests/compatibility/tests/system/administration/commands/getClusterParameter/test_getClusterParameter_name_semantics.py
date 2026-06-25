"""Tests for how getClusterParameter interprets parameter names.

Parameter names are exact-match literals: there is no field-path traversal,
operator interpretation, globbing, or case folding. Any name that is not an
exact match for an existing cluster parameter is reported as unknown, and the
single-name and array forms report an unknown name identically.

(The empty-string name case is covered in test_getClusterParameter_argument_handling.py.)
"""

from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.compatibility.tests.system.administration.commands.getClusterParameter.utils import (  # noqa: E501
    valid_parameter_names,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import NO_SUCH_KEY_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase

pytestmark = pytest.mark.admin

_UNKNOWN_NAME = "definitelyNotAClusterParameterXYZ"


@dataclass(frozen=True)
class NameCase(BaseTestCase):
    """A parameter-name argument expected to be reported as unknown."""

    argument: Any = None


# ---------------------------------------------------------------------------
# Category #8: argument boundary probing — every odd name is a literal,
# unknown parameter name (no traversal/operator/glob interpretation).
# Category #9: wildcard edges — '*' is only special as the whole-string
# argument; inside an array or combined with other characters it is literal.
# Category #11: an unknown name reports identically as a string or in an array.
# ---------------------------------------------------------------------------

_UNKNOWN_NAME_CASES: list[NameCase] = [
    # #8 boundary probing
    NameCase(
        "whitespace_only",
        argument="   ",
        error_code=NO_SUCH_KEY_ERROR,
        msg="Whitespace-only name should be an unknown parameter.",
    ),
    NameCase(
        "very_long_10k",
        argument="x" * 10000,
        error_code=NO_SUCH_KEY_ERROR,
        msg="A 10k-character name should be an unknown parameter (no crash).",
    ),
    NameCase(
        "dotted_name",
        argument="a.b.c",
        error_code=NO_SUCH_KEY_ERROR,
        msg="Dotted name should be literal, not a field path -> unknown parameter.",
    ),
    NameCase(
        "dollar_prefixed",
        argument="$foo",
        error_code=NO_SUCH_KEY_ERROR,
        msg="$-prefixed name should be literal, not an operator -> unknown parameter.",
    ),
    NameCase(
        "unicode_name",
        argument="paramètre_café_\u6d4b\u8bd5",
        error_code=NO_SUCH_KEY_ERROR,
        msg="Unicode name should be an unknown parameter.",
    ),
    # #9 wildcard edges
    NameCase(
        "star_in_array",
        argument=["*"],
        error_code=NO_SUCH_KEY_ERROR,
        msg="'*' inside an array should be a literal name, not expand-all.",
    ),
    NameCase(
        "double_star",
        argument="**",
        error_code=NO_SUCH_KEY_ERROR,
        msg="'**' should be a literal name (no globbing).",
    ),
    NameCase(
        "star_prefix",
        argument="*foo",
        error_code=NO_SUCH_KEY_ERROR,
        msg="'*foo' should be a literal name (no globbing).",
    ),
    # #11 unknown-name contract
    NameCase(
        "unknown_single_string",
        argument=_UNKNOWN_NAME,
        error_code=NO_SUCH_KEY_ERROR,
        msg="An unknown single name should report NoSuchKey.",
    ),
    NameCase(
        "unknown_in_array",
        argument=[_UNKNOWN_NAME],
        error_code=NO_SUCH_KEY_ERROR,
        msg="An unknown name inside an array should report NoSuchKey.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(_UNKNOWN_NAME_CASES))
def test_getClusterParameter_unknown_name(collection, test):
    """Test odd/unknown parameter names are reported as unknown."""
    result = execute_admin_command(collection, {"getClusterParameter": test.argument})
    assertFailureCode(result, test.error_code, msg=test.msg)


# ---------------------------------------------------------------------------
# Cases needing a deployment-derived valid name (built at runtime).
# ---------------------------------------------------------------------------


def test_getClusterParameter_name_is_case_sensitive(collection):
    """Test a known name with altered case is treated as unknown (exact match)."""
    (name,) = valid_parameter_names(collection, 1)
    altered = name.upper() if name != name.upper() else name.lower()
    result = execute_admin_command(collection, {"getClusterParameter": altered})
    assertFailureCode(
        result,
        NO_SUCH_KEY_ERROR,
        msg=f"Case-altered name '{altered}' should not match known name '{name}'.",
    )


def test_getClusterParameter_star_with_valid_name_in_array(collection):
    """Test '*' combined with a valid name in an array treats '*' literally."""
    (name,) = valid_parameter_names(collection, 1)
    result = execute_admin_command(collection, {"getClusterParameter": ["*", name]})
    assertFailureCode(
        result,
        NO_SUCH_KEY_ERROR,
        msg="'*' alongside a valid name in an array should be a literal unknown name.",
    )


def test_getClusterParameter_unknown_name_contract_consistent(collection):
    """Test single-string and array forms report an unknown name identically."""
    single = execute_admin_command(collection, {"getClusterParameter": _UNKNOWN_NAME})
    array = execute_admin_command(collection, {"getClusterParameter": [_UNKNOWN_NAME]})
    single_code = getattr(single, "code", None)
    array_code = getattr(array, "code", None)
    assertFailureCode(
        array,
        single_code,
        msg=f"Array unknown-name code ({array_code}) should match single "
        f"unknown-name code ({single_code}).",
    )
