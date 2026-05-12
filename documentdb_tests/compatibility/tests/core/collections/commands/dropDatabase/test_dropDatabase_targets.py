from __future__ import annotations

import datetime

import pytest
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import ILLEGAL_OPERATION_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import (
    CappedCollection,
    ExistingDatabase,
    NamedCollection,
    TargetDatabase,
    TimeseriesCollection,
    ViewCollection,
)

# Property [Collection Type Acceptance]: dropDatabase succeeds with
# ok:1.0 regardless of the collection types present in the database,
# including capped, empty, timeseries, view, and indexed collections.
COLLECTION_TYPE_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        target_collection=CappedCollection(size=4096),
        docs=[{"_id": 1}],
        command={"dropDatabase": 1},
        expected={"ok": 1.0},
        msg="dropDatabase should succeed with capped collection present",
        id="coll_type_capped",
    ),
    CommandTestCase(
        target_collection=NamedCollection(),
        command={"dropDatabase": 1},
        expected={"ok": 1.0},
        msg="dropDatabase should succeed with empty collection present",
        id="coll_type_empty",
    ),
    CommandTestCase(
        target_collection=TimeseriesCollection(),
        docs=[{"ts": datetime.datetime.now(), "meta": "a", "val": 1}],
        command={"dropDatabase": 1},
        expected={"ok": 1.0},
        msg="dropDatabase should succeed with timeseries collection present",
        id="coll_type_timeseries",
    ),
    CommandTestCase(
        target_collection=ViewCollection(),
        command={"dropDatabase": 1},
        expected={"ok": 1.0},
        msg="dropDatabase should succeed with view present",
        id="coll_type_view",
    ),
    CommandTestCase(
        indexes=[IndexModel([("a", 1)], unique=True)],
        docs=[{"_id": 1, "a": 1}],
        command={"dropDatabase": 1},
        expected={"ok": 1.0},
        msg="dropDatabase should succeed with indexed collection present",
        id="coll_type_indexed",
    ),
]

# Property [Database State Acceptance]: dropDatabase succeeds regardless
# of whether the target database exists or contains data.
DB_STATE_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        # TargetDatabase is used here only to avoid dropping the fixture
        # database. No docs are provided so the database will not exist.
        target_collection=TargetDatabase(suffix="nonexistent"),
        docs=None,
        command={"dropDatabase": 1},
        expected={"ok": 1.0},
        msg="dropDatabase should succeed on a database that does not exist",
        id="db_state_nonexistent",
    ),
    CommandTestCase(
        target_collection=TargetDatabase(suffix="empty_coll"),
        docs=[],
        command={"dropDatabase": 1},
        expected={"ok": 1.0},
        msg="dropDatabase should succeed on a database with an empty collection",
        id="db_state_empty_collection",
    ),
]

# Property [Database Name Accepted]: database names containing
# non-ASCII characters, punctuation, and varying lengths up to the
# 63-character limit are accepted.
DB_NAME_ACCEPTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        target_collection=TargetDatabase(suffix="ünïcödé"),
        docs=[{"_id": 1}],
        command={"dropDatabase": 1},
        expected={"ok": 1.0},
        id="db_name_unicode",
        msg="Unicode database name should be accepted",
    ),
    CommandTestCase(
        target_collection=TargetDatabase(suffix="dashed-db"),
        docs=[{"_id": 1}],
        command={"dropDatabase": 1},
        expected={"ok": 1.0},
        id="db_name_dashes",
        msg="Dashed database name should be accepted",
    ),
    CommandTestCase(
        target_collection=TargetDatabase(suffix="_under"),
        docs=[{"_id": 1}],
        command={"dropDatabase": 1},
        expected={"ok": 1.0},
        id="db_name_underscore",
        msg="Database name with underscore should be accepted",
    ),
    CommandTestCase(
        target_collection=TargetDatabase(suffix="1234"),
        docs=[{"_id": 1}],
        command={"dropDatabase": 1},
        expected={"ok": 1.0},
        id="db_name_digit",
        msg="Database name with digit should be accepted",
    ),
]

# Property [System Database Restrictions]: dropping the admin database
# produces an IllegalOperation error.
SYSTEM_DATABASE_RESTRICTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        target_collection=ExistingDatabase(db_name="admin"),
        command={"dropDatabase": 1},
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="Dropping admin should produce IllegalOperation error",
        id="drop_admin",
    ),
]

DROP_DATABASE_TARGET_TESTS: list[CommandTestCase] = (
    COLLECTION_TYPE_ACCEPTANCE_TESTS
    + DB_STATE_ACCEPTANCE_TESTS
    + DB_NAME_ACCEPTED_TESTS
    + SYSTEM_DATABASE_RESTRICTION_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(DROP_DATABASE_TARGET_TESTS))
def test_dropDatabase_targets(database_client, collection, register_db_cleanup, test):
    """Test dropDatabase command inputs and error handling."""
    coll = test.prepare(database_client, collection)
    if isinstance(test.target_collection, TargetDatabase):
        register_db_cleanup(coll.database.name)
    result = execute_command(coll, test.command)
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
