"""Tests for getCmdLineOpts command argument handling.

Validates that getCmdLineOpts accepts any BSON type as its argument value.
The command ignores the value supplied for the ``getCmdLineOpts`` field and
always returns the command-line options, so every type should yield ok:1.
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


BSON_TYPE_SPEC = BsonTypeTestCase(
    id="getCmdLineOpts_arg",
    msg="getCmdLineOpts should accept any BSON type as argument value",
    keyword="getCmdLineOpts",
    valid_types=list(BsonType),
)

ACCEPTANCE_CASES = generate_bson_acceptance_test_cases([BSON_TYPE_SPEC])


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_getCmdLineOpts_argument_types(collection, bson_type, sample_value, spec):
    """Test that getCmdLineOpts accepts various BSON types as argument value."""
    result = execute_admin_command(collection, {spec.keyword: sample_value})
    assertProperties(result, {"ok": Eq(1.0)}, msg=spec.msg, raw_res=True)
