"""Tests for getCmdLineOpts command argument handling.

Validates that getCmdLineOpts accepts any BSON type as its argument value.
"""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.bson_type_validator import (
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.test_constants import FLOAT_INFINITY, BsonType

pytestmark = pytest.mark.admin


BSON_TYPE_SPEC = BsonTypeTestCase(
    id="getCmdLineOpts_arg",
    msg="getCmdLineOpts should accept any BSON type as argument value",
    keyword="getCmdLineOpts",
    valid_types=list(BsonType),
)

ACCEPTANCE_CASES = generate_bson_acceptance_test_cases([BSON_TYPE_SPEC])

EDGE_CASES: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "int_0",
        command={"getCmdLineOpts": 0},
        checks={"ok": Eq(1.0)},
        msg="Should accept int 0",
    ),
    DiagnosticTestCase(
        "int_neg1",
        command={"getCmdLineOpts": -1},
        checks={"ok": Eq(1.0)},
        msg="Should accept int -1",
    ),
    DiagnosticTestCase(
        "infinity",
        command={"getCmdLineOpts": FLOAT_INFINITY},
        checks={"ok": Eq(1.0)},
        msg="Should accept infinity",
    ),
]


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_getCmdLineOpts_argument_types(collection, bson_type, sample_value, spec):
    """Test that getCmdLineOpts accepts various BSON types as argument value."""
    result = execute_admin_command(collection, {spec.keyword: sample_value})
    assertProperties(result, {"ok": Eq(1.0)}, msg=spec.msg, raw_res=True)


@pytest.mark.parametrize("test", pytest_params(EDGE_CASES))
def test_getCmdLineOpts_argument_edge_cases(collection, test):
    """Test that getCmdLineOpts accepts numeric edge case values."""
    result = execute_admin_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
