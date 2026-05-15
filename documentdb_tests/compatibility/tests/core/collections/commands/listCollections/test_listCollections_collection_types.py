"""Tests for listCollections command."""

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists, IsType, NotExists
from documentdb_tests.framework.target_collection import (
    CappedCollection,
    ChangeStreamPreAndPostImagesCollection,
    ClusteredCollection,
    CollatedCollection,
    GridFSCollection,
    StorageEngineCollection,
    TimeseriesCollection,
    TimeseriesCustomBucketCollection,
    TimeseriesTTLCollection,
    ValidatedCollection,
    ViewCollection,
    ViewWithPipelineCollection,
)

# Property [Regular Collection Output]: regular collections have type
# "collection", empty options, info with readOnly=false and uuid
# (Binary subtype 4), and idIndex with {v: 2, key: {_id: 1}, name:
# '_id_'}.
REGULAR_COLLECTION_OUTPUT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        docs=[{"_id": 1}],
        command=lambda ctx: {"listCollections": 1, "filter": {"name": ctx.collection}},
        expected={
            "cursor.firstBatch.0": {
                "type": Eq("collection"),
                "options": Eq({}),
                "info.readOnly": Eq(False),
                "info.uuid": IsType("binData"),
                "idIndex": Eq({"v": 2, "key": {"_id": 1}, "name": "_id_"}),
            },
        },
        msg="Regular collection should have standard output fields",
        id="regular_collection_output",
    ),
]

# Property [Capped Collection Output]: capped collections include
# capped, size, and max fields in options.
CAPPED_COLLECTION_OUTPUT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        target_collection=CappedCollection(size=4096, max=100),
        command=lambda ctx: {"listCollections": 1, "filter": {"name": ctx.collection}},
        expected={
            "cursor.firstBatch.0": {
                "type": Eq("collection"),
                "options.capped": Eq(True),
                "options.size": Eq(4096),
                "options.max": Eq(100),
            },
        },
        msg="Capped collection options should include capped, size, and max",
        id="capped_collection_output",
    ),
]

# Property [Validated Collection Output]: validated collections include
# validator, validationLevel, and validationAction in options.
VALIDATED_COLLECTION_OUTPUT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        target_collection=ValidatedCollection(),
        command=lambda ctx: {"listCollections": 1, "filter": {"name": ctx.collection}},
        expected={
            "cursor.firstBatch.0": {
                "type": Eq("collection"),
                "options.validator": Exists(),
                "options.validationLevel": Exists(),
                "options.validationAction": Exists(),
            },
        },
        msg="Validated collection options should include validator fields",
        id="validated_collection_output",
    ),
]

# Property [Collated Collection Output]: collated collections include
# collation in options with at least the requested locale.
COLLATED_COLLECTION_OUTPUT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        target_collection=CollatedCollection(),
        command=lambda ctx: {"listCollections": 1, "filter": {"name": ctx.collection}},
        expected={
            "cursor.firstBatch.0": {
                "type": Eq("collection"),
                "options.collation": Exists(),
                "options.collation.locale": Eq("en"),
            },
        },
        msg="Collated collection should include collation with requested locale",
        id="collated_collection_output",
    ),
]

# Property [View Output]: views have type "view", options with viewOn
# and pipeline, info with readOnly=true and no uuid, and no idIndex.
VIEW_OUTPUT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        target_collection=ViewCollection(),
        command=lambda ctx: {"listCollections": 1, "filter": {"name": ctx.collection}},
        expected={
            "cursor.firstBatch.0": {
                "type": Eq("view"),
                "options.viewOn": IsType("string"),
                "options.pipeline": Eq([]),
                "info.readOnly": Eq(True),
                "info.uuid": NotExists(),
                "idIndex": NotExists(),
            },
        },
        msg="View should have type=view, readOnly=true, no uuid, no idIndex",
        id="view_output",
    ),
    CommandTestCase(
        target_collection=ViewWithPipelineCollection(),
        command=lambda ctx: {"listCollections": 1, "filter": {"name": ctx.collection}},
        expected={
            "cursor.firstBatch.0": {
                "type": Eq("view"),
                "options.pipeline": Eq([{"$match": {"x": 1}}]),
                "options.viewOn": IsType("string"),
            },
        },
        msg="View with pipeline should include pipeline content and viewOn",
        id="view_with_pipeline_output",
    ),
]

# Property [Timeseries Output]: timeseries collections have type
# "timeseries", info with no uuid, and no idIndex.
TIMESERIES_OUTPUT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        target_collection=TimeseriesCollection(),
        command=lambda ctx: {"listCollections": 1, "filter": {"name": ctx.collection}},
        expected={
            "cursor.firstBatch.0": {
                "type": Eq("timeseries"),
                "options.timeseries.granularity": Eq("seconds"),
                "info.uuid": NotExists(),
                "idIndex": NotExists(),
            },
        },
        msg="Timeseries collection should have type=timeseries, no uuid, no idIndex",
        id="timeseries_output",
    ),
]

# Property [System Buckets Output]: system.buckets.* backing collections
# have type "collection", options with validator, clusteredIndex=true,
# and timeseries sub-document, and info with uuid.
SYSTEM_BUCKETS_OUTPUT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        target_collection=TimeseriesCollection(),
        command=lambda ctx: {
            "listCollections": 1,
            "filter": {"name": f"system.buckets.{ctx.collection}"},
        },
        expected={
            "cursor.firstBatch.0": {
                "type": Eq("collection"),
                "options.validator": Exists(),
                "options.clusteredIndex": Eq(True),
                "options.timeseries": Exists(),
                "info.uuid": Exists(),
            },
        },
        msg="system.buckets.* should have validator, clusteredIndex, timeseries, uuid",
        id="system_buckets_output",
    ),
]

# Property [Clustered Collection Output]: user-created clustered
# collections have no idIndex, and the server expands clusteredIndex
# with v=2 and name='_id_'.
CLUSTERED_COLLECTION_OUTPUT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        target_collection=ClusteredCollection(),
        command=lambda ctx: {"listCollections": 1, "filter": {"name": ctx.collection}},
        expected={
            "cursor.firstBatch.0": {
                "type": Eq("collection"),
                "idIndex": NotExists(),
                "options.clusteredIndex.v": Eq(2),
                "options.clusteredIndex.name": Eq("_id_"),
            },
        },
        msg="Clustered collection should have no idIndex, expanded clusteredIndex",
        id="clustered_collection_output",
    ),
]

# Property [Timeseries TTL Output]: timeseries with TTL has
# expireAfterSeconds as a top-level option alongside timeseries.
TIMESERIES_TTL_OUTPUT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        target_collection=TimeseriesTTLCollection(expire_after_seconds=3600),
        command=lambda ctx: {"listCollections": 1, "filter": {"name": ctx.collection}},
        expected={
            "cursor.firstBatch.0": {
                "type": Eq("timeseries"),
                "options.timeseries": Exists(),
                "options.expireAfterSeconds": Eq(Int64(3600)),
            },
        },
        msg="Timeseries with TTL should have expireAfterSeconds alongside timeseries",
        id="timeseries_ttl_output",
    ),
]

# Property [Timeseries Custom Bucket Output]: timeseries with custom
# bucket span has bucketRoundingSeconds and bucketMaxSpanSeconds inside
# the timeseries sub-document, and granularity is absent.
TIMESERIES_CUSTOM_BUCKET_OUTPUT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        target_collection=TimeseriesCustomBucketCollection(bucket_seconds=300),
        command=lambda ctx: {"listCollections": 1, "filter": {"name": ctx.collection}},
        expected={
            "cursor.firstBatch.0": {
                "type": Eq("timeseries"),
                "options.timeseries.bucketRoundingSeconds": Eq(300),
                "options.timeseries.bucketMaxSpanSeconds": Eq(300),
                "options.timeseries.granularity": NotExists(),
            },
        },
        msg="Custom bucket timeseries should have bucket fields, no granularity",
        id="timeseries_custom_bucket_output",
    ),
]

# Property [ChangeStreamPreAndPostImages Output]: changeStreamPreAndPostImages appears as a
# top-level option with {enabled: true}.
CSPI_OUTPUT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        target_collection=ChangeStreamPreAndPostImagesCollection(),
        command=lambda ctx: {"listCollections": 1, "filter": {"name": ctx.collection}},
        expected={
            "cursor.firstBatch.0": {
                "type": Eq("collection"),
                "options.changeStreamPreAndPostImages": Eq({"enabled": True}),
            },
        },
        msg="changeStreamPreAndPostImages should appear as top-level option",
        id="cspi_output",
    ),
]

# Property [StorageEngine and IndexOptionDefaults Output]: storageEngine
# and indexOptionDefaults are preserved in output as provided at
# creation time.
STORAGE_ENGINE_OUTPUT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        target_collection=StorageEngineCollection(),
        command=lambda ctx: {"listCollections": 1, "filter": {"name": ctx.collection}},
        expected={
            "cursor.firstBatch.0": {
                "type": Eq("collection"),
                "options.storageEngine": Eq({"wiredTiger": {"configString": ""}}),
                "options.indexOptionDefaults": Eq(
                    {"storageEngine": {"wiredTiger": {"configString": ""}}}
                ),
            },
        },
        msg="storageEngine and indexOptionDefaults should be preserved",
        id="storage_engine_output",
    ),
]

# Property [System Views Output]: the system.views collection has type
# "collection", not "view".
SYSTEM_VIEWS_OUTPUT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        target_collection=ViewCollection(),
        command={
            "listCollections": 1,
            "filter": {"name": "system.views"},
        },
        expected={"cursor.firstBatch.0.type": Eq("collection")},
        msg="system.views should have type=collection, not view",
        id="system_views_output",
    ),
]

# Property [GridFS Output]: GridFS collections (e.g. fs.files,
# fs.chunks) have type "collection" and are listed normally.
GRIDFS_OUTPUT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        target_collection=GridFSCollection(),
        command=lambda ctx: {"listCollections": 1, "filter": {"name": ctx.collection}},
        expected={"cursor.firstBatch.0.type": Eq("collection")},
        msg="GridFS collection should have type=collection",
        id="gridfs_output",
    ),
]

COLLECTION_TYPE_OUTPUT_TESTS: list[CommandTestCase] = (
    REGULAR_COLLECTION_OUTPUT_TESTS
    + CAPPED_COLLECTION_OUTPUT_TESTS
    + VALIDATED_COLLECTION_OUTPUT_TESTS
    + COLLATED_COLLECTION_OUTPUT_TESTS
    + VIEW_OUTPUT_TESTS
    + TIMESERIES_OUTPUT_TESTS
    + SYSTEM_BUCKETS_OUTPUT_TESTS
    + CLUSTERED_COLLECTION_OUTPUT_TESTS
    + TIMESERIES_TTL_OUTPUT_TESTS
    + TIMESERIES_CUSTOM_BUCKET_OUTPUT_TESTS
    + CSPI_OUTPUT_TESTS
    + STORAGE_ENGINE_OUTPUT_TESTS
    + SYSTEM_VIEWS_OUTPUT_TESTS
    + GRIDFS_OUTPUT_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COLLECTION_TYPE_OUTPUT_TESTS))
def test_listCollections_collection_types(database_client, collection, test):
    """Test listCollections command input acceptance and output structure."""
    target = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(target)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
