"""Tests for dbHash command core behavior, response structure, and UUID consistency."""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties, assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Gte, IsType, Ne
from documentdb_tests.framework.target_collection import NamedCollection

pytestmark = pytest.mark.admin

RESPONSE_PROPERTY_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="host_is_string",
        command={"dbHash": 1},
        use_admin=False,
        checks={"host": IsType("string")},
        msg="'host' should be a string",
    ),
    DiagnosticTestCase(
        id="collections_is_object",
        command={"dbHash": 1},
        use_admin=False,
        checks={"collections": IsType("object")},
        msg="'collections' should be an object",
    ),
    DiagnosticTestCase(
        id="md5_is_string",
        command={"dbHash": 1},
        use_admin=False,
        checks={"md5": IsType("string")},
        msg="'md5' should be a string",
    ),
    DiagnosticTestCase(
        id="timeMillis_gte_0",
        command={"dbHash": 1},
        use_admin=False,
        checks={"timeMillis": Gte(0)},
        msg="'timeMillis' should be >= 0",
    ),
    DiagnosticTestCase(
        id="capped_is_array",
        command={"dbHash": 1},
        use_admin=False,
        checks={"capped": IsType("array")},
        msg="'capped' should be an array",
    ),
    DiagnosticTestCase(
        id="uuids_is_object",
        command={"dbHash": 1},
        use_admin=False,
        checks={"uuids": IsType("object")},
        msg="'uuids' should be an object",
    ),
    DiagnosticTestCase(
        id="empty_database",
        command={"dbHash": 1, "collections": ["nonexistent_xyz_abc"]},
        use_admin=False,
        checks={"ok": Eq(1.0)},
        msg="Should succeed on filtered empty",
    ),
]


@pytest.mark.parametrize("test", pytest_params(RESPONSE_PROPERTY_TESTS))
def test_dbHash_response_properties(collection, test):
    """Verifies dbHash response fields have expected types and values."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


def test_dbHash_uuid_stable_across_calls(collection):
    """Test UUID for a collection remains stable across dbHash calls."""
    collection.insert_one({"_id": 1})
    r1 = execute_command(collection, {"dbHash": 1})
    uuid1 = r1["uuids"][collection.name]
    r2 = execute_command(collection, {"dbHash": 1})
    assertResult(
        r2,
        expected={"uuids": {collection.name: Eq(uuid1)}},
        raw_res=True,
        msg="UUID should be stable",
    )


def test_dbHash_uuid_changes_after_recreate(database_client, collection):
    """Test UUID changes after dropping and recreating a collection with same name."""
    coll = NamedCollection(suffix="_uuid").resolve(database_client, collection)
    coll.insert_one({"_id": 1})
    r1 = execute_command(coll, {"dbHash": 1})
    uuid1 = r1["uuids"][coll.name]
    database_client.drop_collection(coll.name)
    database_client.create_collection(coll.name)
    coll.insert_one({"_id": 2})
    r2 = execute_command(coll, {"dbHash": 1})
    assertResult(
        r2,
        expected={"uuids": {coll.name: Ne(uuid1)}},
        raw_res=True,
        msg="UUID should change after recreate",
    )
