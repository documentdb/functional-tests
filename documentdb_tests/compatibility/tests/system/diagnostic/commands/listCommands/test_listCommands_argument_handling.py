"""Tests for listCommands command argument handling.

Validates that listCommands accepts any BSON type as its argument value
and rejects unrecognized fields.
"""

import pytest

from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.property_checks import Eq

pytestmark = pytest.mark.admin


# listCommands accepts all BSON types as its argument value
LISTCOMMANDS_BSON_TYPE_PARAMS = [
    BsonTypeTestCase(
        id="argument",
        msg="listCommands should accept any BSON type as argument",
        keyword="listCommands",
        valid_types=[
            BsonType.DOUBLE,
            BsonType.STRING,
            BsonType.OBJECT,
            BsonType.ARRAY,
            BsonType.BIN_DATA,
            BsonType.OBJECT_ID,
            BsonType.BOOL,
            BsonType.DATE,
            BsonType.NULL,
            BsonType.REGEX,
            BsonType.JAVASCRIPT,
            BsonType.INT,
            BsonType.TIMESTAMP,
            BsonType.LONG,
            BsonType.DECIMAL,
            BsonType.MIN_KEY,
            BsonType.MAX_KEY,
        ],
    ),
]

ACCEPTANCE_TESTS = generate_bson_acceptance_test_cases(LISTCOMMANDS_BSON_TYPE_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_TESTS)
def test_listCommands_argument_types(collection, bson_type, sample_value, spec):
    """Test that listCommands accepts any BSON type as argument value."""
    result = execute_admin_command(collection, {"listCommands": sample_value})
    assertProperties(result, {"ok": Eq(1.0)}, msg=f"{spec.msg} - {bson_type.value}", raw_res=True)


def test_listCommands_extra_fields_ignored(collection):
    """Test that listCommands ignores extra unrecognized fields."""
    result = execute_admin_command(collection, {"listCommands": 1, "unknownField": 1})
    assertProperties(
        result, {"ok": Eq(1.0)}, msg="Should succeed even with extra fields", raw_res=True
    )
