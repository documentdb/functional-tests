"""Tests for listCollections nameOnly behavior."""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.compatibility.tests.core.collections.commands.utils.target_collection import (
    CappedCollection,
    TimeseriesCollection,
    ValidatedCollection,
    ViewCollection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Contains, Eq, Exists, IsType, Len, NotExists
from documentdb_tests.framework.test_constants import INT64_ZERO

# Property [nameOnly and Filter Interaction]: when nameOnly is true,
# filtering on name and type works normally, but filtering on options,
# info, or idIndex returns an empty result set because those fields are
# absent.
NAMEONLY_FILTER_INTERACTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "listCollections": 1,
            "nameOnly": True,
            "filter": {"name": ctx.collection},
        },
        expected=lambda ctx: {
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
        msg="nameOnly=true with filter on name should work normally",
        id="nameonly_filter_name",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command={
            "listCollections": 1,
            "nameOnly": True,
            "filter": {"type": "collection"},
        },
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="nameOnly=true with filter on type should work normally",
        id="nameonly_filter_type",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command={
            "listCollections": 1,
            "nameOnly": True,
            "filter": {"options": {}},
        },
        expected={"cursor.firstBatch": Len(0)},
        msg="nameOnly=true with filter on options returns empty because options is absent",
        id="nameonly_filter_options_empty",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command={
            "listCollections": 1,
            "nameOnly": True,
            "filter": {"info.readOnly": False},
        },
        expected={"cursor.firstBatch": Len(0)},
        msg="nameOnly=true with filter on info returns empty because info is absent",
        id="nameonly_filter_info_empty",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command={
            "listCollections": 1,
            "nameOnly": True,
            "filter": {"idIndex.name": "_id_"},
        },
        expected={"cursor.firstBatch": Len(0)},
        msg="nameOnly=true with filter on idIndex returns empty because idIndex is absent",
        id="nameonly_filter_idindex_empty",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "listCollections": 1,
            "nameOnly": True,
            "filter": {
                "$or": [
                    {"name": ctx.collection},
                    {"options.capped": True},
                ],
            },
        },
        expected=lambda ctx: {
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
        msg=(
            "nameOnly=true $or with available-field branch matches;"
            " unavailable-field branch silently fails"
        ),
        id="nameonly_filter_or_mixed_branches",
    ),
]

# Property [Response Structure (nameOnly=true)]: when nameOnly is true,
# each result document contains exactly {name, type} with no options,
# info, or idIndex fields, regardless of collection type.
NAME_ONLY_STRUCTURE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "listCollections": 1,
            "nameOnly": True,
            "filter": {"name": ctx.collection},
        },
        expected={
            "ok": Eq(1.0),
            "cursor.firstBatch.0": {
                "name": Exists(),
                "type": Exists(),
                "options": NotExists(),
                "info": NotExists(),
                "idIndex": NotExists(),
            },
        },
        msg="Regular collection with nameOnly=true should have only name and type",
        id="name_only_regular",
    ),
    CommandTestCase(
        target_collection=CappedCollection(),
        command=lambda ctx: {
            "listCollections": 1,
            "nameOnly": True,
            "filter": {"name": ctx.collection},
        },
        expected={
            "ok": Eq(1.0),
            "cursor.firstBatch.0": {
                "name": Exists(),
                "type": Exists(),
                "options": NotExists(),
                "info": NotExists(),
                "idIndex": NotExists(),
            },
        },
        msg="Capped collection with nameOnly=true should have only name and type",
        id="name_only_capped",
    ),
    CommandTestCase(
        target_collection=ValidatedCollection(),
        command=lambda ctx: {
            "listCollections": 1,
            "nameOnly": True,
            "filter": {"name": ctx.collection},
        },
        expected={
            "ok": Eq(1.0),
            "cursor.firstBatch.0": {
                "name": Exists(),
                "type": Exists(),
                "options": NotExists(),
                "info": NotExists(),
                "idIndex": NotExists(),
            },
        },
        msg="Validated collection with nameOnly=true should have only name and type",
        id="name_only_validated",
    ),
    CommandTestCase(
        target_collection=ViewCollection(),
        command=lambda ctx: {
            "listCollections": 1,
            "nameOnly": True,
            "filter": {"name": ctx.collection},
        },
        expected={
            "ok": Eq(1.0),
            "cursor.firstBatch.0": {
                "name": Exists(),
                "type": Exists(),
                "options": NotExists(),
                "info": NotExists(),
                "idIndex": NotExists(),
            },
        },
        msg="View with nameOnly=true should have only name and type",
        id="name_only_view",
    ),
    CommandTestCase(
        target_collection=TimeseriesCollection(),
        command=lambda ctx: {
            "listCollections": 1,
            "nameOnly": True,
            "filter": {"name": ctx.collection},
        },
        expected={
            "ok": Eq(1.0),
            "cursor.firstBatch.0": {
                "name": Exists(),
                "type": Exists(),
                "options": NotExists(),
                "info": NotExists(),
                "idIndex": NotExists(),
            },
        },
        msg="Timeseries collection with nameOnly=true should have only name and type",
        id="name_only_timeseries",
    ),
    CommandTestCase(
        target_collection=TimeseriesCollection(),
        command=lambda ctx: {
            "listCollections": 1,
            "nameOnly": True,
            "filter": {"name": f"system.buckets.{ctx.collection}"},
        },
        expected={
            "ok": Eq(1.0),
            "cursor.firstBatch.0": {
                "name": Exists(),
                "type": Exists(),
                "options": NotExists(),
                "info": NotExists(),
                "idIndex": NotExists(),
            },
        },
        msg="system.buckets.* with nameOnly=true should have only name and type",
        id="name_only_system_buckets",
    ),
    CommandTestCase(
        target_collection=ViewCollection(),
        command={
            "listCollections": 1,
            "nameOnly": True,
            "filter": {"name": "system.views"},
        },
        expected={
            "ok": Eq(1.0),
            "cursor.firstBatch.0": {
                "name": Exists(),
                "type": Exists(),
                "options": NotExists(),
                "info": NotExists(),
                "idIndex": NotExists(),
            },
        },
        msg="system.views with nameOnly=true should have only name and type",
        id="name_only_system_views",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command={
            "listCollections": 1,
            "nameOnly": True,
            "filter": {"options": {"$exists": False}},
        },
        expected={"cursor.firstBatch": Len(1)},
        msg=(
            "Filtering options.$exists:false with nameOnly=true should match all"
            " collections, confirming fields are truly absent"
        ),
        id="name_only_options_exists_false",
    ),
]

# Property [nameOnly=false Structure]: explicit nameOnly=false produces
# the same full output structure as omitting nameOnly.
NAMEONLY_FALSE_STRUCTURE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "listCollections": 1,
            "nameOnly": False,
            "filter": {"name": ctx.collection},
        },
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.ns": Eq(f"{ctx.database}.$cmd.listCollections"),
            "cursor.id": Eq(INT64_ZERO),
            "cursor.firstBatch.0": {
                "name": IsType("string"),
                "type": IsType("string"),
                "options": IsType("object"),
                "info": IsType("object"),
                "idIndex": IsType("object"),
            },
        },
        msg="Explicit nameOnly=false should behave identically to omitting nameOnly",
        id="explicit_name_only_false_structure",
    ),
]

# Property [nameOnly Type Errors]: when nameOnly is any non-boolean
# BSON type, the command produces a TYPE_MISMATCH_ERROR with no
# numeric-to-bool or string-to-bool coercion.
NAMEONLY_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="nameonly_int32",
        command={"listCollections": 1, "nameOnly": 1},
        msg="nameOnly=int32 should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="nameonly_int64",
        command={"listCollections": 1, "nameOnly": Int64(1)},
        msg="nameOnly=Int64 should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="nameonly_double",
        command={"listCollections": 1, "nameOnly": 1.0},
        msg="nameOnly=double should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="nameonly_decimal128",
        command={"listCollections": 1, "nameOnly": Decimal128("1")},
        msg="nameOnly=Decimal128 should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="nameonly_string",
        command={"listCollections": 1, "nameOnly": "true"},
        msg="nameOnly=string should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="nameonly_array",
        command={"listCollections": 1, "nameOnly": [True]},
        msg="nameOnly=array should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="nameonly_object",
        command={"listCollections": 1, "nameOnly": {}},
        msg="nameOnly=object should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="nameonly_objectid",
        command=lambda _: {"listCollections": 1, "nameOnly": ObjectId()},
        msg="nameOnly=ObjectId should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="nameonly_datetime",
        command={"listCollections": 1, "nameOnly": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        msg="nameOnly=datetime should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="nameonly_timestamp",
        command={"listCollections": 1, "nameOnly": Timestamp(1, 1)},
        msg="nameOnly=Timestamp should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="nameonly_binary",
        command={"listCollections": 1, "nameOnly": Binary(b"hello")},
        msg="nameOnly=Binary should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="nameonly_regex",
        command={"listCollections": 1, "nameOnly": Regex(".*")},
        msg="nameOnly=Regex should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="nameonly_code",
        command={"listCollections": 1, "nameOnly": Code("function(){}")},
        msg="nameOnly=Code should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="nameonly_code_with_scope",
        command={"listCollections": 1, "nameOnly": Code("function(){}", {"x": 1})},
        msg="nameOnly=CodeWithScope should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="nameonly_minkey",
        command={"listCollections": 1, "nameOnly": MinKey()},
        msg="nameOnly=MinKey should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="nameonly_maxkey",
        command={"listCollections": 1, "nameOnly": MaxKey()},
        msg="nameOnly=MaxKey should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
]

NAMEONLY_TESTS: list[CommandTestCase] = (
    NAMEONLY_FILTER_INTERACTION_TESTS
    + NAME_ONLY_STRUCTURE_TESTS
    + NAMEONLY_FALSE_STRUCTURE_TESTS
    + NAMEONLY_TYPE_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(NAMEONLY_TESTS))
def test_listCollections_nameonly(database_client, collection, test):
    """Test listCollections nameOnly behavior."""
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
