"""Tests for ping command argument handling.

Validates that ping accepts any BSON type as its command value, as well as
numeric edge cases (negative int, zero, infinity). The command value does
not affect behavior — all inputs should return ok: 1.
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


PING_BSON_TYPE_SPECS = [
    BsonTypeTestCase(
        id="ping_value",
        msg="ping command should accept any BSON type as value",
        valid_types=list(BsonType),
    ),
]

ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(PING_BSON_TYPE_SPECS)


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_ping_argument_types(collection, bson_type, sample_value, spec):
    """Test that ping accepts various BSON types as command value."""
    result = execute_admin_command(collection, {"ping": sample_value})
    assertProperties(result, {"ok": Eq(1.0)}, msg=spec.msg, raw_res=True)


NUMERIC_EDGE_CASES: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="negative_int",
        command={"ping": -1},
        checks={"ok": Eq(1.0)},
        msg="Should accept negative int",
    ),
    DiagnosticTestCase(
        id="int_0",
        command={"ping": 0},
        checks={"ok": Eq(1.0)},
        msg="Should accept int 0",
    ),
    DiagnosticTestCase(
        id="infinity",
        command={"ping": FLOAT_INFINITY},
        checks={"ok": Eq(1.0)},
        msg="Should accept infinity",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NUMERIC_EDGE_CASES))
def test_ping_argument_numeric_edge_cases(collection, test):
    """Test that ping accepts edge-case numeric values as command value."""
    result = execute_admin_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
