"""Tests for the dbStats response structure.

Covers the presence and BSON type of every documented response field, the
totalSize relationship, dataSize positivity after inserts, the avgObjSize
relationship, and collection/view counts.
"""

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties, assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Gt, IsType

pytestmark = pytest.mark.admin


RESPONSE_PROPERTY_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="db_is_string",
        checks={"db": IsType("string")},
        msg="'db' field should be a string",
    ),
    DiagnosticTestCase(
        id="collections_is_long",
        checks={"collections": IsType("long")},
        msg="'collections' field should be a long",
    ),
    DiagnosticTestCase(
        id="views_is_long",
        checks={"views": IsType("long")},
        msg="'views' field should be a long",
    ),
    DiagnosticTestCase(
        id="objects_is_long",
        checks={"objects": IsType("long")},
        msg="'objects' field should be a long",
    ),
    DiagnosticTestCase(
        id="avgObjSize_is_double",
        checks={"avgObjSize": IsType("double")},
        msg="'avgObjSize' field should be a double",
    ),
    DiagnosticTestCase(
        id="dataSize_is_double",
        checks={"dataSize": IsType("double")},
        msg="'dataSize' field should be a double",
    ),
    DiagnosticTestCase(
        id="storageSize_is_double",
        checks={"storageSize": IsType("double")},
        msg="'storageSize' field should be a double",
    ),
    DiagnosticTestCase(
        id="indexes_is_long",
        checks={"indexes": IsType("long")},
        msg="'indexes' field should be a long",
    ),
    DiagnosticTestCase(
        id="indexSize_is_double",
        checks={"indexSize": IsType("double")},
        msg="'indexSize' field should be a double",
    ),
    DiagnosticTestCase(
        id="totalSize_is_double",
        checks={"totalSize": IsType("double")},
        msg="'totalSize' field should be a double",
    ),
    DiagnosticTestCase(
        id="scaleFactor_is_long",
        checks={"scaleFactor": IsType("long")},
        msg="'scaleFactor' field should be a long",
    ),
    DiagnosticTestCase(
        id="fsUsedSize_is_double",
        checks={"fsUsedSize": IsType("double")},
        msg="'fsUsedSize' field should be a double",
    ),
    DiagnosticTestCase(
        id="fsTotalSize_is_double",
        checks={"fsTotalSize": IsType("double")},
        msg="'fsTotalSize' field should be a double",
    ),
    DiagnosticTestCase(
        id="ok_is_double",
        checks={"ok": IsType("double")},
        msg="'ok' field should be a double",
    ),
]


@pytest.mark.parametrize("test", pytest_params(RESPONSE_PROPERTY_TESTS))
def test_dbStats_response_properties(collection, test):
    """Verifies each documented dbStats response field has the expected BSON type."""
    collection.insert_many([{"_id": i, "a": i} for i in range(5)])
    collection.create_index("a")
    result = execute_command(collection, {"dbStats": 1})
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


def test_dbStats_total_size_relationship(collection):
    """Test totalSize equals storageSize plus indexSize."""
    collection.insert_many([{"_id": i, "a": i} for i in range(20)])
    collection.create_index("a")
    result = execute_command(collection, {"dbStats": 1})
    assertSuccess(
        result.get("totalSize"),
        expected=result.get("storageSize") + result.get("indexSize"),
        raw_res=True,
        msg="totalSize should equal storageSize + indexSize",
    )


def test_dbStats_avg_obj_size_equals_data_size_over_objects(collection):
    """Test avgObjSize equals dataSize divided by objects."""
    collection.insert_many([{"_id": i, "data": "x" * (i + 1)} for i in range(10)])
    result = execute_command(collection, {"dbStats": 1})
    assertSuccess(
        result.get("avgObjSize"),
        expected=result.get("dataSize") / result.get("objects"),
        raw_res=True,
        msg="avgObjSize should equal dataSize / objects",
    )


RESPONSE_STATE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="data_size_positive_after_insert",
        setup=[{"insert": "c1", "documents": [{"_id": i, "data": "x" * 50} for i in range(10)]}],
        command={"dbStats": 1},
        checks={"dataSize": Gt(0.0)},
        msg="dataSize should be positive after inserts",
    ),
    DiagnosticTestCase(
        id="collections_count_includes_system_views",
        setup=[
            {"insert": "c1", "documents": [{"_id": i} for i in range(3)]},
            {"create": "c1_view", "viewOn": "c1", "pipeline": []},
        ],
        command={"dbStats": 1},
        checks={"collections": Eq(Int64(2))},
        msg="collections should include the base collection and system.views",
    ),
    DiagnosticTestCase(
        id="views_count",
        setup=[
            {"insert": "c1", "documents": [{"_id": i} for i in range(3)]},
            {"create": "c1_view", "viewOn": "c1", "pipeline": []},
        ],
        command={"dbStats": 1},
        checks={"views": Eq(Int64(1))},
        msg="views should count the created view",
    ),
]


@pytest.mark.parametrize("test", pytest_params(RESPONSE_STATE_TESTS))
def test_dbStats_response_reflects_state(collection, test):
    """Test dbStats response fields reflect database state from setup commands."""
    for setup_command in test.setup:
        setup_result = execute_command(collection, setup_command)
        if isinstance(setup_result, Exception):
            raise setup_result
    result = execute_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
