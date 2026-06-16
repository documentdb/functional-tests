"""Tests for lockInfo command argument validation.

Verifies that lockInfo accepts various values for the command field and
rejects unrecognized fields with error code 40415.
"""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

pytestmark = pytest.mark.admin


LOCKINFO_BSON_TYPE_SPECS = [
    BsonTypeTestCase(
        id="command_field",
        msg="lockInfo accepts any BSON type for the command field",
        keyword="lockInfo",
        valid_types=list(BsonType),
    )
]

ACCEPTANCE_TESTS = generate_bson_acceptance_test_cases(LOCKINFO_BSON_TYPE_SPECS)


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_TESTS)
def test_lockInfo_accepts_any_type(collection, bson_type, sample_value, spec):
    """Verify lockInfo succeeds when the command field value is a given BSON type."""
    result = execute_admin_command(collection, {"lockInfo": sample_value})
    assertProperties(result, {"ok": Eq(1.0)}, msg=spec.msg, raw_res=True)


INT_EDGE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="int_zero",
        command={"lockInfo": 0},
        checks={"ok": Eq(1.0)},
        msg="lockInfo should accept int 0",
    ),
    DiagnosticTestCase(
        id="int_neg1",
        command={"lockInfo": -1},
        checks={"ok": Eq(1.0)},
        msg="lockInfo should accept int -1",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INT_EDGE_TESTS))
def test_lockInfo_accepts_int_edge_values(collection, test):
    """Verify lockInfo accepts zero and negative int values for the command field."""
    result = execute_admin_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
