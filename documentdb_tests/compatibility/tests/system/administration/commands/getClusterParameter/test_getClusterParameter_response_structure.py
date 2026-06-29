"""Tests for getClusterParameter response structure.

Verifies the top-level shape of the success response: ok is 1,
clusterParameters is an array, and a single-name request returns
exactly one element.
"""

import pytest

from documentdb_tests.compatibility.tests.system.administration.utils.administration_test_case import (  # noqa: E501
    AdministrationTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, IsType, Len

pytestmark = pytest.mark.admin

_VALID_PARAM = "changeStreamOptions"

PROPERTY_TESTS: list[AdministrationTestCase] = [
    AdministrationTestCase(
        id="ok_is_1",
        command={"getClusterParameter": "*"},
        checks={"ok": Eq(1.0)},
        msg="Response ok should be 1.0",
    ),
    AdministrationTestCase(
        id="clusterParameters_is_array",
        command={"getClusterParameter": "*"},
        checks={"clusterParameters": IsType("array")},
        msg="clusterParameters should be an array",
    ),
    AdministrationTestCase(
        id="single_name_length_is_one",
        command={"getClusterParameter": _VALID_PARAM},
        checks={"clusterParameters": Len(1)},
        msg="Single-name request should return exactly one element",
    ),
    AdministrationTestCase(
        id="element_id_matches_request",
        command={"getClusterParameter": _VALID_PARAM},
        checks={"clusterParameters.0._id": Eq(_VALID_PARAM)},
        msg=f"Single-name request should return element with _id equal to '{_VALID_PARAM}'",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PROPERTY_TESTS))
def test_getClusterParameter_response_properties(collection, test):
    """Verifies getClusterParameter response fields have expected types and values."""
    result = execute_admin_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
