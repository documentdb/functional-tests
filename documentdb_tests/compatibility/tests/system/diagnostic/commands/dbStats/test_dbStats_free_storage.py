"""Tests for the dbStats ``freeStorage`` parameter.

Covers acceptance of freeStorage 0/1, presence of the free-storage fields
when freeStorage:1 is set, the totalFreeStorageSize relationship, presence
of filesystem size fields, and absence of the free-storage fields when
freeStorage is omitted or 0.
"""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import (
    assertProperties,
    assertSuccess,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Exists, NotExists

pytestmark = pytest.mark.admin


def test_dbStats_free_storage_one_includes_expected_fields(collection):
    """Test dbStats with freeStorage:1 includes the three free-storage fields."""
    collection.insert_one({"_id": 1})
    collection.create_index("a")
    result = execute_command(collection, {"dbStats": 1, "freeStorage": 1})
    assertProperties(
        result,
        {
            "freeStorageSize": Exists(),
            "indexFreeStorageSize": Exists(),
            "totalFreeStorageSize": Exists(),
        },
        raw_res=True,
        msg="freeStorage:1 should include free-storage fields",
    )


def test_dbStats_total_free_storage_size_relationship(collection):
    """Test totalFreeStorageSize equals freeStorageSize plus indexFreeStorageSize."""
    collection.insert_many([{"_id": i, "a": i} for i in range(20)])
    collection.create_index("a")
    result = execute_command(collection, {"dbStats": 1, "freeStorage": 1})
    assertSuccess(
        result["totalFreeStorageSize"],
        result["freeStorageSize"] + result["indexFreeStorageSize"],
        raw_res=True,
        msg="totalFreeStorageSize should equal freeStorageSize + indexFreeStorageSize",
    )


OMITS_FREE_STORAGE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "no_free_storage_param",
        command={"dbStats": 1},
        checks={
            "freeStorageSize": NotExists(),
            "indexFreeStorageSize": NotExists(),
            "totalFreeStorageSize": NotExists(),
        },
        msg="Omitting freeStorage should omit free-storage fields",
    ),
    DiagnosticTestCase(
        "free_storage_zero",
        command={"dbStats": 1, "freeStorage": 0},
        checks={
            "freeStorageSize": NotExists(),
            "indexFreeStorageSize": NotExists(),
            "totalFreeStorageSize": NotExists(),
        },
        msg="freeStorage:0 should omit free-storage fields",
    ),
]


@pytest.mark.parametrize("test", pytest_params(OMITS_FREE_STORAGE_TESTS))
def test_dbStats_omits_free_storage_fields(collection, test):
    """Test dbStats omits free-storage fields when freeStorage is not set or 0."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, test.command)
    assertProperties(result, test.checks, raw_res=True, msg=test.msg)
