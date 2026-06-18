"""Tests for dbStats across collection variants and data scenarios.

Covers empty collections (with and without a secondary index), avgObjSize
when there are no objects, index counts across multiple collections, and
capped collections.
"""

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

pytestmark = pytest.mark.admin


# Each case establishes database state via ``setup`` runCommand documents,
# runs dbStats, then checks the database-level response. The per-test database
# is unique (provided by the ``collection`` fixture), so setup collections use
# fixed names; dbStats aggregates the whole database regardless of which
# collection it is issued against.
COLLECTION_SCENARIO_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="empty_collection_index_count",
        setup=[{"createIndexes": "c1", "indexes": [{"key": {"a": 1}, "name": "a_1"}]}],
        command={"dbStats": 1},
        checks={"indexes": Eq(Int64(2))},
        msg="Empty collection with one secondary index should report indexes:2",
    ),
    DiagnosticTestCase(
        id="avg_obj_size_zero_when_no_objects",
        command={"dbStats": 1},
        checks={"objects": Eq(Int64(0)), "avgObjSize": Eq(0.0)},
        msg="Empty database should report objects:0 and avgObjSize:0",
    ),
    DiagnosticTestCase(
        id="indexes_across_collections",
        setup=[
            {"insert": "c1", "documents": [{"_id": i, "a": i} for i in range(5)]},
            {"createIndexes": "c1", "indexes": [{"key": {"a": 1}, "name": "a_1"}]},
            {"insert": "c2", "documents": [{"_id": i, "b": i} for i in range(5)]},
            {"createIndexes": "c2", "indexes": [{"key": {"b": 1}, "name": "b_1"}]},
        ],
        command={"dbStats": 1},
        checks={"indexes": Eq(Int64(4))},
        msg="indexes should total default plus secondary indexes across collections",
    ),
    DiagnosticTestCase(
        id="capped_collection_counted",
        setup=[
            {"create": "c1", "capped": True, "size": 4096},
            {"insert": "c1", "documents": [{"_id": i} for i in range(3)]},
        ],
        command={"dbStats": 1},
        checks={"collections": Eq(Int64(1)), "objects": Eq(Int64(3))},
        msg="Capped collection should be counted with its documents",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COLLECTION_SCENARIO_TESTS))
def test_dbStats_collection_scenarios(collection, test):
    """Test dbStats database-level counts and sizes across collection variants and data shapes."""
    for setup_command in test.setup:
        setup_result = execute_command(collection, setup_command)
        if isinstance(setup_result, Exception):
            raise setup_result
    result = execute_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
