"""Tests for getClusterParameter core retrieval behavior.

Verifies that the wildcard returns more than one cluster parameter and
that the result includes known parameters by name.
"""

import pytest

from documentdb_tests.compatibility.tests.system.administration.utils.administration_test_case import (  # noqa: E501
    AdministrationTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Contains, LenGt

pytestmark = pytest.mark.admin

_VALID_PARAM = "changeStreamOptions"

CORE_BEHAVIOR_TESTS: list[AdministrationTestCase] = [
    AdministrationTestCase(
        id="wildcard_returns_multiple_params",
        command={"getClusterParameter": "*"},
        checks={"clusterParameters": LenGt(1)},
        msg="Wildcard should return more than one cluster parameter",
    ),
    AdministrationTestCase(
        id="wildcard_includes_known_param",
        command={"getClusterParameter": "*"},
        checks={"clusterParameters": Contains("_id", _VALID_PARAM)},
        msg=f"Wildcard result should include '{_VALID_PARAM}'",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CORE_BEHAVIOR_TESTS))
def test_getClusterParameter_core_behavior(collection, test):
    """Test core retrieval behavior: wildcard parameter count and inclusion."""
    result = execute_admin_command(collection, test.build_command())
    assertProperties(result, test.build_checks(), msg=test.msg, raw_res=True)
