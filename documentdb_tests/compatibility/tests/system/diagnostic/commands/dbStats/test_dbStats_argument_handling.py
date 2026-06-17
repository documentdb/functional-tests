"""Tests for dbStats command argument handling.

The value of the ``dbStats`` field is ignored by the server: any value
selects the current database, so every BSON type should be accepted,
including numeric edge cases such as 0, -1, and Infinity.
"""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties, assertSuccessPartial
from documentdb_tests.framework.bson_type_validator import (
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.test_constants import FLOAT_INFINITY, BsonType

pytestmark = pytest.mark.admin


# dbStats ignores the command field value — all BSON types should succeed.
DBSTATS_VALUE_PARAMS: list[BsonTypeTestCase] = [
    BsonTypeTestCase(
        id="dbStats_value",
        msg="dbStats should accept all BSON types for the command field value",
        keyword="dbStats",
        valid_types=list(BsonType),
    ),
]

ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(DBSTATS_VALUE_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_dbStats_accepts_any_value_type(collection, bson_type, sample_value, spec):
    """Test dbStats accepts all BSON types for the command field value."""
    result = execute_command(collection, {"dbStats": sample_value})
    assertSuccessPartial(
        result,
        {"ok": 1.0, "db": collection.database.name},
        msg=f"dbStats should accept {bson_type.value} for the command field value",
    )


# Specific numeric edge-case values for the command field.
EDGE_CASE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="value_zero",
        command={"dbStats": 0},
        checks={"ok": Eq(1.0)},
        msg="dbStats:0 should succeed",
    ),
    DiagnosticTestCase(
        id="value_negative_one",
        command={"dbStats": -1},
        checks={"ok": Eq(1.0)},
        msg="dbStats:-1 should succeed",
    ),
    DiagnosticTestCase(
        id="value_infinity",
        command={"dbStats": FLOAT_INFINITY},
        checks={"ok": Eq(1.0)},
        msg="dbStats:Infinity should succeed",
    ),
]


@pytest.mark.parametrize("test", pytest_params(EDGE_CASE_TESTS))
def test_dbStats_accepts_value_edge_cases(collection, test):
    """Test dbStats succeeds for specific numeric edge-case command values."""
    result = execute_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
