"""Tests for lockInfo command argument validation.

Verifies that lockInfo accepts any BSON type for the command field value and
that successive calls succeed (point-in-time snapshot behaviour).
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
from documentdb_tests.framework.test_constants import FLOAT_INFINITY

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


VALUE_EDGE_TESTS: list[DiagnosticTestCase] = [
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
    DiagnosticTestCase(
        id="float_infinity",
        command={"lockInfo": FLOAT_INFINITY},
        checks={"ok": Eq(1.0)},
        msg="lockInfo should accept float infinity as the command field value",
    ),
]


@pytest.mark.parametrize("test", pytest_params(VALUE_EDGE_TESTS))
def test_lockInfo_accepts_value_edge_cases(collection, test):
    """Verify lockInfo accepts int and float edge values for the command field."""
    result = execute_admin_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


def test_lockInfo_point_in_time_snapshot(collection):
    """Test lockInfo result is a point-in-time snapshot (successive calls succeed)."""
    execute_admin_command(collection, {"lockInfo": 1})
    result = execute_admin_command(collection, {"lockInfo": 1})
    assertProperties(result, {"ok": Eq(1.0)}, msg="Successive calls should succeed", raw_res=True)
