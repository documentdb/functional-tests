"""Tests for hostInfo command argument handling.

hostInfo takes no arguments: the command value is ignored and any BSON type
is accepted, always returning ok:1.
"""

import pytest

from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.bson_type_validator import (
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.test_constants import BsonType

pytestmark = pytest.mark.admin


BSON_TYPE_PARAMS = [
    BsonTypeTestCase(
        id="hostInfo_command_value",
        msg="hostInfo should accept any BSON type as command value",
        keyword="hostInfo",
        valid_types=list(BsonType),
    ),
]

ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(BSON_TYPE_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_hostInfo_argument_types(collection, bson_type, sample_value, spec):
    """Test that hostInfo accepts any BSON type as its command value."""
    result = execute_admin_command(collection, {"hostInfo": sample_value})
    assertProperties(result, {"ok": Eq(1.0)}, msg=spec.msg, raw_res=True)
