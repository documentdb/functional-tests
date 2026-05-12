"""Tests for $listClusterCatalog output structure and field values."""

from __future__ import annotations

import pytest
from bson import Int64
from pymongo.collection import Collection

from documentdb_tests.compatibility.tests.core.operator.stages.listClusterCatalog.utils.listClusterCatalog_helpers import (  # noqa: E501
    ListClusterCatalogTestCase,
    StageContext,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists, IsType, NotExists
from documentdb_tests.framework.target_collection import (
    CappedCollection,
    CustomCollection,
    ExistingDatabase,
    NamedCollection,
    TimeseriesCollection,
    ViewCollection,
)

# Property [Default Output Fields]: every output document contains all
# default fields.
DEFAULT_FIELD_TESTS: list[ListClusterCatalogTestCase] = [
    ListClusterCatalogTestCase(
        id="default_fields_regular",
        docs=[],
        pipeline=lambda ctx: [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
        expected={
            "ns": IsType("string"),
            "db": IsType("string"),
            "type": IsType("string"),
            "options": IsType("object"),
            "info": IsType("object"),
            "sharded": IsType("bool"),
        },
        msg="Regular collection should have all default fields",
    ),
]

# Property [Default Output Fields - type]: the type field reflects the
# collection kind.
TYPE_TESTS: list[ListClusterCatalogTestCase] = [
    ListClusterCatalogTestCase(
        id="type_regular_collection",
        docs=[],
        pipeline=lambda ctx: [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
        expected={"type": Eq("collection")},
        msg="Regular collection should have type 'collection'",
    ),
    ListClusterCatalogTestCase(
        id="type_view",
        target_collection=ViewCollection(),
        pipeline=lambda ctx: [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
        expected={"type": Eq("view")},
        msg="View should have type 'view'",
    ),
    ListClusterCatalogTestCase(
        id="type_timeseries",
        target_collection=TimeseriesCollection(),
        pipeline=lambda ctx: [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
        expected={"type": Eq("timeseries")},
        msg="Time series collection should have type 'timeseries'",
    ),
]

# Property [idIndex Field]: idIndex is present for regular collections
# and absent for views.
ID_INDEX_TESTS: list[ListClusterCatalogTestCase] = [
    ListClusterCatalogTestCase(
        id="idIndex_regular",
        docs=[],
        pipeline=lambda ctx: [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
        expected={"idIndex": Eq({"v": 2, "key": {"_id": 1}, "name": "_id_"})},
        msg="Regular collection should have idIndex with v=2, key={_id:1}, name=_id_",
    ),
    ListClusterCatalogTestCase(
        id="idIndex_absent_for_view",
        target_collection=ViewCollection(),
        pipeline=lambda ctx: [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
        expected={"idIndex": NotExists()},
        msg="View should not have idIndex field",
    ),
]

# Property [info Sub-field]: info sub-fields reflect collection mutability
# and identity.
INFO_TESTS: list[ListClusterCatalogTestCase] = [
    ListClusterCatalogTestCase(
        id="info_regular",
        docs=[],
        pipeline=lambda ctx: [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
        expected={"info.readOnly": Eq(False), "info.uuid": Exists()},
        msg="Regular collection should have readOnly=false and uuid present",
    ),
    ListClusterCatalogTestCase(
        id="info_view",
        target_collection=ViewCollection(),
        pipeline=lambda ctx: [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
        expected={"info.readOnly": Eq(True), "info.uuid": NotExists()},
        msg="View should have readOnly=true and no uuid",
    ),
]

# Property [options Sub-field]: options reflects the collection's creation
# parameters.
OPTIONS_TESTS: list[ListClusterCatalogTestCase] = [
    ListClusterCatalogTestCase(
        id="options_regular",
        docs=[],
        pipeline=lambda ctx: [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
        expected={"options": Eq({})},
        msg="Regular collection should have empty options",
    ),
    ListClusterCatalogTestCase(
        id="options_view",
        target_collection=ViewCollection(),
        pipeline=lambda ctx: [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
        expected={"options.viewOn": Exists(), "options.pipeline": Eq([])},
        msg="View should have viewOn and pipeline in options",
    ),
    ListClusterCatalogTestCase(
        id="options_capped",
        target_collection=CappedCollection(),
        pipeline=lambda ctx: [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
        expected={"options.capped": Eq(True), "options.size": Exists()},
        msg="Capped collection should have capped and size in options",
    ),
    ListClusterCatalogTestCase(
        id="options_capped_with_max",
        target_collection=CappedCollection(max=100),
        pipeline=lambda ctx: [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
        expected={"options.capped": Eq(True), "options.max": Eq(100)},
        msg="Capped collection with max should have max in options",
    ),
    ListClusterCatalogTestCase(
        id="options_collation",
        target_collection=CustomCollection(
            options={"collation": {"locale": "en", "strength": 2}},
        ),
        pipeline=lambda ctx: [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
        expected={
            "options.collation.locale": Eq("en"),
            "options.collation.strength": Eq(2),
        },
        msg="Collection with collation should have collation in options",
    ),
    ListClusterCatalogTestCase(
        id="options_validator",
        target_collection=CustomCollection(
            options={"validator": {"$jsonSchema": {"bsonType": "object"}}},
        ),
        pipeline=lambda ctx: [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
        expected={"options.validator": Exists()},
        msg="Collection with validator should have validator in options",
    ),
    ListClusterCatalogTestCase(
        id="options_validation_level_and_action",
        target_collection=CustomCollection(
            options={
                "validator": {"$jsonSchema": {"bsonType": "object"}},
                "validationLevel": "moderate",
                "validationAction": "warn",
            },
        ),
        pipeline=lambda ctx: [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
        expected={
            "options.validationLevel": Eq("moderate"),
            "options.validationAction": Eq("warn"),
        },
        msg="Collection with validation options should have level and action in options",
    ),
    ListClusterCatalogTestCase(
        id="options_clustered_index",
        target_collection=CustomCollection(
            options={"clusteredIndex": {"key": {"_id": 1}, "unique": True}},
        ),
        pipeline=lambda ctx: [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
        expected={"options.clusteredIndex": Exists()},
        msg="Clustered collection should have clusteredIndex in options",
    ),
    ListClusterCatalogTestCase(
        id="options_change_stream_pre_post",
        target_collection=CustomCollection(
            options={"changeStreamPreAndPostImages": {"enabled": True}},
        ),
        pipeline=lambda ctx: [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
        expected={"options.changeStreamPreAndPostImages.enabled": Eq(True)},
        msg="Collection with pre/post images should have option in options",
    ),
    ListClusterCatalogTestCase(
        id="options_timeseries",
        target_collection=TimeseriesCollection(),
        pipeline=lambda ctx: [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
        expected={
            "options.timeseries.timeField": Eq("ts"),
            "options.timeseries.metaField": Eq("meta"),
        },
        msg="Timeseries collection should have timeseries config in options",
    ),
    ListClusterCatalogTestCase(
        id="options_expire_after_seconds",
        target_collection=CustomCollection(
            options={
                "clusteredIndex": {"key": {"_id": 1}, "unique": True},
                "expireAfterSeconds": 3600,
            },
        ),
        pipeline=lambda ctx: [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
        expected={"options.expireAfterSeconds": Eq(Int64(3600))},
        msg="Clustered collection with TTL should have expireAfterSeconds in options",
    ),
    ListClusterCatalogTestCase(
        id="options_storage_engine",
        target_collection=CustomCollection(
            options={"storageEngine": {"wiredTiger": {"configString": "block_compressor=zstd"}}},
        ),
        pipeline=lambda ctx: [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
        expected={"options.storageEngine": Exists()},
        msg="Collection with storageEngine should have storageEngine in options",
    ),
    ListClusterCatalogTestCase(
        id="options_index_option_defaults",
        target_collection=CustomCollection(
            options={
                "indexOptionDefaults": {
                    "storageEngine": {"wiredTiger": {"configString": "block_compressor=zstd"}}
                }
            },
        ),
        pipeline=lambda ctx: [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
        expected={"options.indexOptionDefaults": Exists()},
        msg="Collection with indexOptionDefaults should have it in options",
    ),
]

# Property [Non-Persisted Creation Parameters]: transient parameters passed
# during collection creation do not appear in options.
NON_PERSISTED_OPTION_TESTS: list[ListClusterCatalogTestCase] = [
    ListClusterCatalogTestCase(
        id="options_no_write_concern",
        target_collection=CustomCollection(options={"writeConcern": {"w": 1}}),
        pipeline=lambda ctx: [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
        expected={"options": Eq({})},
        msg="writeConcern should not persist in options",
    ),
    ListClusterCatalogTestCase(
        id="options_no_comment",
        target_collection=CustomCollection(options={"comment": "test comment"}),
        pipeline=lambda ctx: [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
        expected={"options": Eq({})},
        msg="comment should not persist in options",
    ),
    ListClusterCatalogTestCase(
        id="options_no_id_index",
        target_collection=CustomCollection(
            options={"idIndex": {"key": {"_id": 1}, "name": "_id_", "v": 2}},
        ),
        pipeline=lambda ctx: [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
        expected={"options": Eq({})},
        msg="idIndex should not persist in options",
    ),
]

# Property [Stage Parameter Behavior]: the shards and balancingConfiguration
# parameters independently control their respective output fields.
OPTION_BEHAVIOR_TESTS: list[ListClusterCatalogTestCase] = [
    ListClusterCatalogTestCase(
        id="shards_true",
        docs=[],
        pipeline=lambda ctx: [
            {"$listClusterCatalog": {"shards": True}},
            {"$match": {"ns": ctx.ns}},
        ],
        expected={"shards": IsType("array")},
        msg="shards: true should include shards field as array",
    ),
    ListClusterCatalogTestCase(
        id="shards_false",
        docs=[],
        pipeline=lambda ctx: [
            {"$listClusterCatalog": {"shards": False}},
            {"$match": {"ns": ctx.ns}},
        ],
        expected={"shards": NotExists()},
        msg="shards: false should not include shards field",
    ),
    ListClusterCatalogTestCase(
        id="shards_omitted",
        docs=[],
        pipeline=lambda ctx: [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
        expected={"shards": NotExists()},
        msg="Omitting shards should not include shards field",
    ),
]

# Property [Sharded Field Value]: the sharded field reflects whether the
# collection is sharded.
SHARDED_FIELD_TESTS: list[ListClusterCatalogTestCase] = [
    ListClusterCatalogTestCase(
        id="sharded_regular_collection",
        docs=[],
        pipeline=lambda ctx: [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
        expected={"sharded": Eq(False)},
        msg="Unsharded regular collection should have sharded=false",
    ),
    ListClusterCatalogTestCase(
        id="sharded_view",
        target_collection=ViewCollection(),
        pipeline=lambda ctx: [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
        expected={"sharded": Eq(False)},
        msg="View should have sharded=false",
    ),
    ListClusterCatalogTestCase(
        id="sharded_timeseries",
        target_collection=TimeseriesCollection(),
        pipeline=lambda ctx: [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
        expected={"sharded": Eq(False)},
        msg="Unsharded timeseries collection should have sharded=false",
    ),
]

# Property [Special Collection Names]: collections with special characters
# in their names are listed correctly.
SPECIAL_NAME_TESTS: list[ListClusterCatalogTestCase] = [
    ListClusterCatalogTestCase(
        id="name_with_spaces",
        target_collection=NamedCollection(suffix=" with spaces"),
        pipeline=lambda ctx: [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
        expected={"ns": Exists()},
        msg="Collection with spaces in name should be listed",
    ),
    ListClusterCatalogTestCase(
        id="name_with_dashes",
        target_collection=NamedCollection(suffix="-with-dashes"),
        pipeline=lambda ctx: [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
        expected={"ns": Exists()},
        msg="Collection with dashes in name should be listed",
    ),
    ListClusterCatalogTestCase(
        id="name_with_dots",
        target_collection=NamedCollection(suffix=".with.dots"),
        pipeline=lambda ctx: [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
        expected={"ns": Exists()},
        msg="Collection with dots in name should be listed",
    ),
    ListClusterCatalogTestCase(
        id="name_with_unicode",
        target_collection=NamedCollection(suffix="_émojis_🎉"),
        pipeline=lambda ctx: [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
        expected={"ns": Exists()},
        msg="Collection with unicode in name should be listed",
    ),
    ListClusterCatalogTestCase(
        id="name_with_slashes",
        target_collection=NamedCollection(suffix="/with/slashes"),
        pipeline=lambda ctx: [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
        expected={"ns": Exists()},
        msg="Collection with forward slashes in name should be listed",
    ),
    ListClusterCatalogTestCase(
        id="name_long",
        target_collection=NamedCollection(suffix="_" + "a" * 60),
        pipeline=lambda ctx: [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
        expected={"ns": Exists()},
        msg="Collection with a long name should be listed",
    ),
]

# Property [Empty Document Argument]: an empty document {} is a valid
# argument; all fields are optional.
EMPTY_DOC_TESTS: list[ListClusterCatalogTestCase] = [
    ListClusterCatalogTestCase(
        id="empty_document",
        docs=[],
        pipeline=lambda ctx: [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
        expected={"ns": Exists()},
        msg="Empty document should be a valid argument and return results",
    ),
]

# Property [readConcern]: readConcern local is accepted.
READ_CONCERN_TESTS: list[ListClusterCatalogTestCase] = [
    ListClusterCatalogTestCase(
        id="readConcern_local",
        docs=[],
        command=lambda ctx: {
            "aggregate": 1,
            "pipeline": [{"$listClusterCatalog": {}}, {"$match": {"ns": ctx.ns}}],
            "cursor": {},
            "readConcern": {"level": "local"},
        },
        expected={"ns": Exists()},
        msg="readConcern local should be accepted",
    ),
]

# Property [Database Scope]: output is scoped to the database the stage
# runs against, except admin which returns cluster-wide results.
SCOPE_TESTS: list[ListClusterCatalogTestCase] = [
    ListClusterCatalogTestCase(
        id="nonexistent_database",
        pipeline=[{"$listClusterCatalog": {}}],
        expected=[],
        msg="Non-existent database should return zero documents",
    ),
    ListClusterCatalogTestCase(
        id="system_db_scope_local",
        target_collection=ExistingDatabase(db_name="local"),
        pipeline=[{"$listClusterCatalog": {}}],
        expected={"db": Eq("local")},
        msg="All results from 'local' should be scoped to 'local'",
    ),
    ListClusterCatalogTestCase(
        id="system_db_scope_config",
        target_collection=ExistingDatabase(db_name="config"),
        pipeline=[{"$listClusterCatalog": {}}],
        expected={"db": Eq("config")},
        msg="All results from 'config' should be scoped to 'config'",
    ),
    ListClusterCatalogTestCase(
        id="admin_includes_other_dbs",
        docs=[],
        target_collection=ExistingDatabase(db_name="admin"),
        pipeline=[{"$listClusterCatalog": {}}, {"$match": {"db": {"$ne": "admin"}}}],
        expected={"db": Exists()},
        msg="Admin scope should include collections from non-admin databases",
    ),
]

OUTPUT_TESTS: list[ListClusterCatalogTestCase] = (
    DEFAULT_FIELD_TESTS
    + TYPE_TESTS
    + ID_INDEX_TESTS
    + INFO_TESTS
    + OPTIONS_TESTS
    + NON_PERSISTED_OPTION_TESTS
    + OPTION_BEHAVIOR_TESTS
    + SHARDED_FIELD_TESTS
    + SPECIAL_NAME_TESTS
    + SCOPE_TESTS
    + EMPTY_DOC_TESTS
    + READ_CONCERN_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test", pytest_params(OUTPUT_TESTS))
def test_listClusterCatalog_output(collection: Collection, test: ListClusterCatalogTestCase):
    """Test $listClusterCatalog output structure and field values."""
    db = collection.database
    resolved = test.prepare(db, collection)
    ctx = StageContext.from_collection(resolved)
    result = execute_command(resolved, test.build_command(collection, ctx))
    assertResult(result, expected=test.expected, msg=test.msg)
