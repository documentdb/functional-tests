"""Tests for dbStats across collection variants and data scenarios.

Covers empty collections (with and without a secondary index), avgObjSize
when there are no objects, positive storage/index sizes when data and
indexes exist, total index counts across multiple collections, capped
collections, and object counts across a range of collection sizes and
document shapes.
"""

from dataclasses import dataclass, field

import pytest
from bson import Decimal128, Int64

from documentdb_tests.framework.assertions import assertProperties, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Gt
from documentdb_tests.framework.target_collection import CappedCollection
from documentdb_tests.framework.test_case import BaseTestCase

pytestmark = pytest.mark.admin


def test_dbStats_empty_collection_index_count(collection):
    """Test an empty collection with a secondary index reports two indexes."""
    collection.create_index("a")
    result = execute_command(collection, {"dbStats": 1})
    assertSuccessPartial(
        result,
        {"indexes": Int64(2)},
        msg="Empty collection with one secondary index should report indexes:2",
    )


def test_dbStats_empty_collection_sizes_positive(collection):
    """Test an empty collection with an index reports positive storage and index sizes."""
    collection.create_index("a")
    result = execute_command(collection, {"dbStats": 1})
    assertProperties(
        result,
        {"storageSize": Gt(0.0), "indexSize": Gt(0.0)},
        raw_res=True,
        msg="Empty collection should still allocate storage and index space",
    )


def test_dbStats_avg_obj_size_zero_when_no_objects(collection):
    """Test an empty collection reports zero objects and zero avgObjSize."""
    result = execute_command(collection, {"dbStats": 1})
    assertSuccessPartial(
        result,
        {"objects": Int64(0), "avgObjSize": 0.0},
        msg="Empty collection should report objects:0 and avgObjSize:0",
    )


def test_dbStats_index_size_positive_with_indexes(collection):
    """Test indexSize is positive when secondary indexes exist."""
    collection.insert_many([{"_id": i, "a": i} for i in range(10)])
    collection.create_index("a")
    result = execute_command(collection, {"dbStats": 1})
    assertProperties(
        result,
        {"indexSize": Gt(0.0)},
        raw_res=True,
        msg="indexSize should be positive with indexes",
    )


def test_dbStats_total_index_count_across_collections(collection):
    """Test indexes counts the default and secondary indexes across all collections."""
    collection.insert_many([{"_id": i, "a": i} for i in range(5)])
    collection.create_index("a")
    c2 = collection.database[f"{collection.name}_c2"]
    c2.insert_many([{"_id": i, "b": i} for i in range(5)])
    c2.create_index("b")
    result = execute_command(collection, {"dbStats": 1})
    assertSuccessPartial(
        result,
        {"indexes": Int64(4)},
        msg="indexes should total default plus secondary indexes across collections",
    )


def test_dbStats_capped_collection_counted(collection):
    """Test dbStats counts a capped collection and its documents."""
    capped = CappedCollection(size=4096).resolve(collection.database, collection)
    capped.insert_many([{"_id": i} for i in range(3)])
    result = execute_command(capped, {"dbStats": 1})
    assertSuccessPartial(
        result,
        {"collections": Int64(1), "objects": Int64(3)},
        msg="Capped collection should be counted with its documents",
    )


@dataclass(frozen=True)
class ScenarioTestCase(BaseTestCase):
    """A dbStats data scenario: documents to insert plus response checks."""

    docs: list = field(default_factory=list)
    checks: dict = field(default_factory=dict)


# Document scenarios covering varied collection sizes and shapes
# (stats_unified scenarios #32-#39).
SCENARIO_TESTS: list[ScenarioTestCase] = [
    ScenarioTestCase(
        id="small",
        docs=[{"_id": i, "a": i} for i in range(5)],
        checks={"objects": Eq(Int64(5)), "storageSize": Gt(0.0)},
        msg="small collection should report objects:5 and positive storageSize",
    ),
    ScenarioTestCase(
        id="medium_mixed_types",
        docs=[{"_id": i, "a": Int64(i), "b": float(i), "c": Decimal128(str(i))} for i in range(50)],
        checks={"objects": Eq(Int64(50)), "storageSize": Gt(0.0)},
        msg="mixed-type collection should report objects:50 and positive storageSize",
    ),
    ScenarioTestCase(
        id="large",
        docs=[{"_id": i, "a": i} for i in range(500)],
        checks={"objects": Eq(Int64(500)), "storageSize": Gt(0.0)},
        msg="large collection should report objects:500 and positive storageSize",
    ),
    ScenarioTestCase(
        id="toast_small",
        docs=[{"_id": i, "blob": "x" * 4096} for i in range(5)],
        checks={"objects": Eq(Int64(5)), "storageSize": Gt(0.0)},
        msg="toast small collection should report objects:5 and positive storageSize",
    ),
    ScenarioTestCase(
        id="toast_large",
        docs=[{"_id": i, "blob": "x" * 4096} for i in range(50)],
        checks={"objects": Eq(Int64(50)), "storageSize": Gt(0.0)},
        msg="toast large collection should report objects:50 and positive storageSize",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SCENARIO_TESTS))
def test_dbStats_object_count_and_storage_across_scenarios(collection, test):
    """Test objects and storageSize for varied collection sizes and document shapes."""
    collection.insert_many(test.docs)
    result = execute_command(collection, {"dbStats": 1})
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
