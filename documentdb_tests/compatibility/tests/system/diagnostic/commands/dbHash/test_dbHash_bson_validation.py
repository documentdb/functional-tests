"""Tests for dbHash command BSON type validation."""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
)
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.admin

# dbHash ignores the command field value — all BSON types should succeed
DBHASH_VALUE_PARAMS = [
    BsonTypeTestCase(
        id="dbHash_value",
        msg="dbHash should accept all BSON types for command value",
        keyword="dbHash",
        valid_types=list(BsonType),
    ),
]

# dbHash ignores the collections field value type — all BSON types succeed
COLLECTIONS_PARAMS = [
    BsonTypeTestCase(
        id="collections",
        msg="collections should accept all BSON types",
        keyword="collections",
        valid_types=list(BsonType),
    ),
]

DBHASH_VALUE_ACCEPTANCE = generate_bson_acceptance_test_cases(DBHASH_VALUE_PARAMS)
COLLECTIONS_ACCEPTANCE = generate_bson_acceptance_test_cases(COLLECTIONS_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", DBHASH_VALUE_ACCEPTANCE)
def test_dbHash_value_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Test dbHash accepts all BSON types for command field value."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, {"dbHash": sample_value})
    assertSuccessPartial(result, {"ok": 1.0}, msg=f"dbHash should accept {bson_type.value}")


@pytest.mark.parametrize("bson_type,sample_value,spec", COLLECTIONS_ACCEPTANCE)
def test_dbHash_collections_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Test dbHash accepts all BSON types for collections parameter."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, {"dbHash": 1, "collections": sample_value})
    assertSuccessPartial(result, {"ok": 1.0}, msg=f"collections should accept {bson_type.value}")


def test_dbHash_unrecognized_field(collection):
    """Test dbHash with unrecognized extra field succeeds."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, {"dbHash": 1, "foo": 1})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Unrecognized field should be ignored")
