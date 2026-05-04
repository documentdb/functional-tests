"""Tests for listCollections command."""

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.compatibility.tests.core.collections.commands.utils.target_collection import (
    ViewWithPipelineCollection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import SIZE_NOT_ARRAY_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Contains, Eq, Len, NotContains

# Property [Filter $expr]: $expr can access output fields and
# supports aggregation expressions ($eq, $gt, $type, $ifNull, $size,
# $substrCP, $regexMatch, $and), can be combined with regular filter
# predicates, and works with nameOnly=true on the available fields.
FILTER_EXPR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "listCollections": 1,
            "filter": {"$expr": {"$eq": ["$name", ctx.collection]}},
        },
        expected=lambda ctx: {
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
        msg="$expr with $eq should filter by name",
        id="filter_expr_eq_name",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command={
            "listCollections": 1,
            "filter": {"$expr": {"$eq": ["$type", "collection"]}},
        },
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$expr should access $type field",
        id="filter_expr_eq_type",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command={
            "listCollections": 1,
            "filter": {"$expr": {"$eq": ["$info.readOnly", False]}},
        },
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$expr should access nested $info.readOnly field",
        id="filter_expr_info_readonly",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command={
            "listCollections": 1,
            "filter": {"$expr": {"$eq": ["$options", {}]}},
        },
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$expr should access $options field",
        id="filter_expr_options",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "listCollections": 1,
            "filter": {"$expr": {"$gt": ["$name", ctx.collection]}},
        },
        expected=lambda ctx: {"cursor.firstBatch": NotContains("name", ctx.collection)},
        msg="$expr with $gt should exclude exact match",
        id="filter_expr_gt_name",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command={
            "listCollections": 1,
            "filter": {
                "$expr": {"$eq": [{"$type": "$name"}, "string"]},
            },
        },
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$expr with $type aggregation expression should match string fields",
        id="filter_expr_type_agg",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command={
            "listCollections": 1,
            "filter": {
                "$expr": {
                    "$eq": [{"$ifNull": ["$options", "fallback"]}, {}],
                },
            },
        },
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$expr with $ifNull should return field value when present",
        id="filter_expr_ifnull",
    ),
    CommandTestCase(
        target_collection=ViewWithPipelineCollection(),
        command={
            "listCollections": 1,
            "filter": {
                "type": "view",
                "$expr": {"$eq": [{"$size": "$options.pipeline"}, 1]},
            },
        },
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$expr with $size should work on array fields",
        id="filter_expr_size_pipeline",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command={
            "listCollections": 1,
            "filter": {
                "$expr": {
                    "$eq": [{"$substrCP": ["$type", 0, 4]}, "coll"],
                },
            },
        },
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$expr with $substrCP should extract substring for comparison",
        id="filter_expr_substrcp",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "listCollections": 1,
            "filter": {
                "$expr": {
                    "$regexMatch": {
                        "input": "$name",
                        "regex": ctx.collection,
                    },
                },
            },
        },
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$expr with $regexMatch should match collection name",
        id="filter_expr_regexmatch",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "listCollections": 1,
            "filter": {
                "$expr": {
                    "$and": [
                        {"$eq": ["$name", ctx.collection]},
                        {"$eq": ["$type", "collection"]},
                    ],
                },
            },
        },
        expected=lambda ctx: {
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
        msg="$expr with $and should require both conditions",
        id="filter_expr_and",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "listCollections": 1,
            "filter": {
                "type": "collection",
                "$expr": {"$eq": ["$name", ctx.collection]},
            },
        },
        expected=lambda ctx: {
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
        msg="$expr combined with regular predicate should apply both",
        id="filter_expr_combined_regular",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "listCollections": 1,
            "nameOnly": True,
            "filter": {"$expr": {"$eq": ["$name", ctx.collection]}},
        },
        expected=lambda ctx: {
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
        msg="$expr with nameOnly=true should access $name",
        id="filter_expr_nameonly_name",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command={
            "listCollections": 1,
            "nameOnly": True,
            "filter": {"$expr": {"$eq": ["$type", "collection"]}},
        },
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$expr with nameOnly=true should access $type",
        id="filter_expr_nameonly_type",
    ),
]

# Property [$expr nameOnly Type Missing]: when nameOnly is true,
# $expr with $type on unavailable fields ($options, $info, $idIndex)
# resolves to "missing", but resolves to the actual type when nameOnly
# is false.
EXPR_NAMEONLY_TYPE_MISSING_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        docs=[{"_id": 1}],
        command={
            "listCollections": 1,
            "nameOnly": True,
            "filter": {
                "$expr": {"$eq": [{"$type": "$options"}, "missing"]},
            },
        },
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$type of $options should be 'missing' when nameOnly=true",
        id="expr_nameonly_type_missing_options",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command={
            "listCollections": 1,
            "nameOnly": True,
            "filter": {
                "$expr": {"$eq": [{"$type": "$info"}, "missing"]},
            },
        },
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$type of $info should be 'missing' when nameOnly=true",
        id="expr_nameonly_type_missing_info",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command={
            "listCollections": 1,
            "nameOnly": True,
            "filter": {
                "$expr": {"$eq": [{"$type": "$idIndex"}, "missing"]},
            },
        },
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$type of $idIndex should be 'missing' when nameOnly=true",
        id="expr_nameonly_type_missing_idindex",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command={
            "listCollections": 1,
            "nameOnly": False,
            "filter": {
                "$expr": {"$eq": [{"$type": "$options"}, "missing"]},
            },
        },
        expected={"cursor.firstBatch": Len(0)},
        msg="$type of $options should not be 'missing' when nameOnly=false",
        id="expr_nameonly_false_type_not_missing_options",
    ),
]

# Property [$expr nameOnly Unavailable Field Error]: when nameOnly is
# true, $expr accessing unavailable fields ($options, $info, $idIndex)
# with an operator that requires a specific type produces a runtime
# error.
EXPR_NAMEONLY_UNAVAILABLE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={
            "listCollections": 1,
            "nameOnly": True,
            "filter": {"$expr": {"$gt": [{"$size": "$options"}, 0]}},
        },
        msg="$expr $size on unavailable $options should produce SIZE_NOT_ARRAY_ERROR",
        id="expr_nameonly_size_options",
        error_code=SIZE_NOT_ARRAY_ERROR,
        docs=[{"_id": 1}],
    ),
    CommandTestCase(
        command={
            "listCollections": 1,
            "nameOnly": True,
            "filter": {"$expr": {"$gt": [{"$size": "$info"}, 0]}},
        },
        msg="$expr $size on unavailable $info should produce SIZE_NOT_ARRAY_ERROR",
        id="expr_nameonly_size_info",
        error_code=SIZE_NOT_ARRAY_ERROR,
        docs=[{"_id": 1}],
    ),
    CommandTestCase(
        command={
            "listCollections": 1,
            "nameOnly": True,
            "filter": {"$expr": {"$gt": [{"$size": "$idIndex"}, 0]}},
        },
        msg="$expr $size on unavailable $idIndex should produce SIZE_NOT_ARRAY_ERROR",
        id="expr_nameonly_size_idindex",
        error_code=SIZE_NOT_ARRAY_ERROR,
        docs=[{"_id": 1}],
    ),
    CommandTestCase(
        command={
            "listCollections": 1,
            "nameOnly": True,
            "filter": {
                "$expr": {
                    "$gt": [{"$size": {"$objectToArray": "$options"}}, 0],
                },
            },
        },
        msg=(
            "$objectToArray on unavailable $options returns null;"
            " $size on null should produce SIZE_NOT_ARRAY_ERROR"
        ),
        id="expr_nameonly_objecttoarray_options",
        error_code=SIZE_NOT_ARRAY_ERROR,
        docs=[{"_id": 1}],
    ),
]

FILTER_EXPR_ALL_TESTS: list[CommandTestCase] = (
    FILTER_EXPR_TESTS + EXPR_NAMEONLY_TYPE_MISSING_TESTS + EXPR_NAMEONLY_UNAVAILABLE_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(FILTER_EXPR_ALL_TESTS))
def test_listCollections_filter_expr(database_client, collection, test):
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
