"""Tests for dbStats accuracy and state changes.

Covers count fields (collections, objects, indexes) reflecting database
state.
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


COUNT_ACCURACY_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="collections_count_reflects_created",
        setup=[{"create": "c1"}, {"create": "c2"}, {"create": "c3"}],
        command={"dbStats": 1},
        use_admin=False,
        checks={"collections": Eq(Int64(3))},
        msg="collections should equal the number of created collections",
    ),
    DiagnosticTestCase(
        id="objects_sum_across_collections",
        setup=[
            {"insert": "c1", "documents": [{"_id": i} for i in range(4)]},
            {"insert": "c2", "documents": [{"_id": i} for i in range(6)]},
        ],
        command={"dbStats": 1},
        use_admin=False,
        checks={"objects": Eq(Int64(10))},
        msg="objects should equal the total documents across all collections",
    ),
    DiagnosticTestCase(
        id="indexes_default_plus_created",
        setup=[
            {"insert": "c1", "documents": [{"_id": i, "a": i, "b": i} for i in range(5)]},
            {
                "createIndexes": "c1",
                "indexes": [
                    {"key": {"a": 1}, "name": "a_1"},
                    {"key": {"b": 1}, "name": "b_1"},
                ],
            },
        ],
        command={"dbStats": 1},
        use_admin=False,
        checks={"indexes": Eq(Int64(3))},
        msg="indexes should count the default _id index plus created indexes",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COUNT_ACCURACY_TESTS))
def test_dbStats_count_accuracy(collection, test):
    """Test dbStats count fields accurately reflect created collections, documents, and indexes."""
    for setup_command in test.setup:
        setup_result = execute_command(collection, setup_command)
        if isinstance(setup_result, Exception):
            raise setup_result
    result = execute_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
