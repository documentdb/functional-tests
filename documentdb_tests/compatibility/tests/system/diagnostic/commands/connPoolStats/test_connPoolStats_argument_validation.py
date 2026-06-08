"""Tests for connPoolStats command argument validation.

Verifies that connPoolStats accepts all BSON types for the command field
value and ignores unrecognized fields.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.bson_type_validator import (
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.test_constants import BsonType

pytestmark = pytest.mark.admin

# connPoolStats ignores the command field value — all types should succeed
CONNPOOLSTATS_PARAMS = [
    BsonTypeTestCase(
        id="connPoolStats_value",
        msg="connPoolStats should accept all BSON types",
        keyword="connPoolStats",
        valid_types=list(BsonType),
    ),
]

ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(CONNPOOLSTATS_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_connPoolStats_accepts_any_type(collection, bson_type, sample_value, spec):
    """Test connPoolStats accepts all BSON types for command field value."""
    result = execute_admin_command(collection, {"connPoolStats": sample_value})
    assertSuccessPartial(result, {"ok": 1.0}, msg=f"connPoolStats should accept {bson_type.value}")


def test_connPoolStats_unrecognized_field(collection):
    """Test connPoolStats with unrecognized extra field succeeds."""
    result = execute_admin_command(collection, {"connPoolStats": 1, "foo": 1})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Unrecognized field should be ignored")


def test_connPoolStats_multiple_unrecognized_fields(collection):
    """Test connPoolStats with multiple unrecognized fields succeeds."""
    result = execute_admin_command(
        collection, {"connPoolStats": 1, "foo": 1, "bar": "baz", "qux": []}
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="Multiple unrecognized fields should be ignored")
