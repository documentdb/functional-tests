"""Tests for listCollections command."""

import pytest
from bson import Regex

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.compatibility.tests.core.collections.commands.utils.target_collection import (
    CappedCollection,
    CollatedCollection,
    TimeseriesCollection,
    ValidatedCollection,
    ViewCollection,
    ViewWithPipelineCollection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Contains, Eq, Len, NotContains

# Property [Filter Basic Predicate]: the filter field accepts a query
# predicate document that restricts the result set to matching
# collections.
FILTER_BASIC_PREDICATE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "listCollections": 1,
            "filter": {"name": ctx.collection},
        },
        expected=lambda ctx: {
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
        msg="Implicit $eq on name should return only the matching collection",
        id="filter_eq_name",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "listCollections": 1,
            "filter": {"name": {"$eq": ctx.collection}},
        },
        expected=lambda ctx: {
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
        msg="Explicit $eq on name should return only the matching collection",
        id="filter_explicit_eq_name",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "listCollections": 1,
            "filter": {"name": {"$ne": ctx.collection}},
        },
        expected=lambda ctx: {"cursor.firstBatch": NotContains("name", ctx.collection)},
        msg="$ne should exclude the named collection",
        id="filter_ne_name",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "listCollections": 1,
            "filter": {"name": {"$in": [ctx.collection]}},
        },
        expected=lambda ctx: {
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
        msg="$in should return exactly the matching set",
        id="filter_in_name",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "listCollections": 1,
            "filter": {"name": {"$nin": [ctx.collection]}},
        },
        expected=lambda ctx: {"cursor.firstBatch": NotContains("name", ctx.collection)},
        msg="$nin should exclude the specified collection",
        id="filter_nin_name",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "listCollections": 1,
            "filter": {"$and": [{"name": ctx.collection}, {"type": "collection"}]},
        },
        expected=lambda ctx: {
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
        msg="$and should require both conditions to match",
        id="filter_and",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "listCollections": 1,
            "filter": {
                "$or": [{"name": ctx.collection}, {"name": "nonexistent"}],
            },
        },
        expected=lambda ctx: {
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
        msg="$or should match when either branch matches",
        id="filter_or",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "listCollections": 1,
            "filter": {"$nor": [{"name": ctx.collection}]},
        },
        expected=lambda ctx: {"cursor.firstBatch": NotContains("name", ctx.collection)},
        msg="$nor should exclude matching collections",
        id="filter_nor",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "listCollections": 1,
            "filter": {"name": {"$not": {"$eq": ctx.collection}}},
        },
        expected=lambda ctx: {"cursor.firstBatch": NotContains("name", ctx.collection)},
        msg="$not with $eq should invert the match",
        id="filter_not_eq",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "listCollections": 1,
            "filter": {"name": {"$not": Regex(f"^{ctx.collection}$")}},
        },
        expected=lambda ctx: {"cursor.firstBatch": NotContains("name", ctx.collection)},
        msg="$not with $regex should invert the match",
        id="filter_not_regex",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "listCollections": 1,
            "filter": {"name": {"$exists": True}},
        },
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$exists: true on name should match all collections",
        id="filter_exists_true",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "listCollections": 1,
            "filter": {"name": {"$type": 2}},
        },
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$type with numeric BSON type code for string should match name field",
        id="filter_type_numeric",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "listCollections": 1,
            "filter": {"name": {"$type": "string"}},
        },
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$type with string alias should match name field",
        id="filter_type_string_alias",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "listCollections": 1,
            "filter": {"$comment": "test", "name": ctx.collection},
        },
        expected=lambda ctx: {
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
        msg="$comment should not affect query results",
        id="filter_comment",
    ),
    CommandTestCase(
        target_collection=ViewCollection(),
        command={"listCollections": 1, "filter": {"type": "view"}},
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="filter type=view should match views",
        id="filter_type_view",
    ),
    CommandTestCase(
        target_collection=TimeseriesCollection(),
        command={"listCollections": 1, "filter": {"type": "timeseries"}},
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="filter type=timeseries should match timeseries collections",
        id="filter_type_timeseries",
    ),
]

# Property [Filter Regex]: regex filtering on the name field works with
# prefix, suffix, case-insensitive options, and Python Regex objects.
FILTER_REGEX_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "listCollections": 1,
            "filter": {"name": {"$regex": f"^{ctx.collection}"}},
        },
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$regex with prefix should match",
        id="filter_regex_prefix",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "listCollections": 1,
            "filter": {"name": {"$regex": f"{ctx.collection}$"}},
        },
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$regex with suffix should match",
        id="filter_regex_suffix",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "listCollections": 1,
            "filter": {
                "name": {"$regex": ctx.collection.upper(), "$options": "i"},
            },
        },
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$regex with case-insensitive option should match",
        id="filter_regex_case_insensitive",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "listCollections": 1,
            "filter": {"name": Regex(f"^{ctx.collection}$")},
        },
        expected=lambda ctx: {
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
        msg="Python Regex object should work as filter",
        id="filter_regex_object",
    ),
]

# Property [Filter Comparison Operators]: comparison operators ($gt,
# $gte, $lt, $lte) work on string, numeric, and boolean output fields.
FILTER_COMPARISON_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "listCollections": 1,
            "filter": {"name": {"$gt": ctx.collection}},
        },
        expected=lambda ctx: {"cursor.firstBatch": NotContains("name", ctx.collection)},
        msg="$gt on name should exclude the exact match",
        id="filter_gt_name_excludes_exact",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "listCollections": 1,
            "filter": {"name": {"$gte": ctx.collection}},
        },
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$gte on name should include the exact match",
        id="filter_gte_name_includes_exact",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "listCollections": 1,
            "filter": {"name": {"$lt": ctx.collection}},
        },
        expected=lambda ctx: {"cursor.firstBatch": NotContains("name", ctx.collection)},
        msg="$lt on name should exclude the exact match",
        id="filter_lt_name_excludes_exact",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "listCollections": 1,
            "filter": {"name": {"$lte": ctx.collection}},
        },
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$lte on name should include the exact match",
        id="filter_lte_name_includes_exact",
    ),
    CommandTestCase(
        target_collection=CappedCollection(size=4096, max=100),
        command={"listCollections": 1, "filter": {"options.size": {"$gte": 4096}}},
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$gte on numeric options.size should match",
        id="filter_gte_numeric_size",
    ),
    CommandTestCase(
        target_collection=CappedCollection(size=4096, max=100),
        command={"listCollections": 1, "filter": {"options.max": {"$lt": 200}}},
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$lt on numeric options.max should match",
        id="filter_lt_numeric_max",
    ),
    CommandTestCase(
        target_collection=ViewCollection(),
        command={"listCollections": 1, "filter": {"info.readOnly": {"$gt": False}}},
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$gt on boolean info.readOnly should match true > false",
        id="filter_gt_boolean_readonly",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command={"listCollections": 1, "filter": {"type": {"$lte": "collection"}}},
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$lte on type string should include exact match",
        id="filter_lte_type",
    ),
]

# Property [Filter Type Operator]: $type matches output fields by BSON
# type, including numeric codes and arrays of type names.
FILTER_TYPE_OPERATOR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        docs=[{"_id": 1}],
        command={"listCollections": 1, "filter": {"options": {"$type": "object"}}},
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$type 'object' should match options field",
        id="filter_type_options_object",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command={"listCollections": 1, "filter": {"info": {"$type": 3}}},
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$type numeric code 3 (object) should match info field",
        id="filter_type_info_numeric",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command={
            "listCollections": 1,
            "filter": {"idIndex": {"$type": ["object", "null"]}},
        },
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$type with array of types should match any listed type",
        id="filter_type_array_of_types",
    ),
]

# Property [Filter Dot Notation]: dot notation into sub-documents works
# for filtering on nested output fields.
FILTER_DOT_NOTATION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        target_collection=CappedCollection(size=4096, max=100),
        command={"listCollections": 1, "filter": {"options.capped": True}},
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="Dot notation options.capped should match capped collection",
        id="filter_dot_options_capped",
    ),
    CommandTestCase(
        target_collection=ViewCollection(),
        command={"listCollections": 1, "filter": {"info.readOnly": True}},
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="Dot notation info.readOnly should match view",
        id="filter_dot_info_readonly",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command={"listCollections": 1, "filter": {"idIndex.name": "_id_"}},
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="Dot notation idIndex.name should match regular collection",
        id="filter_dot_idindex_name",
    ),
    CommandTestCase(
        target_collection=TimeseriesCollection(),
        command={
            "listCollections": 1,
            "filter": {"options.timeseries.timeField": "ts"},
        },
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="Dot notation into timeseries sub-document should match",
        id="filter_dot_timeseries_timefield",
    ),
    CommandTestCase(
        target_collection=CollatedCollection(),
        command={
            "listCollections": 1,
            "filter": {"options.collation.locale": "en"},
        },
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="Dot notation into collation sub-document should match",
        id="filter_dot_collation_locale",
    ),
    CommandTestCase(
        target_collection=ValidatedCollection(),
        command={
            "listCollections": 1,
            "filter": {"options.validator.$jsonSchema.required": ["x"]},
        },
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="Dot notation into validator.$jsonSchema.required should match",
        id="filter_dot_validator_jsonschema",
    ),
]

# Property [Filter Positional Dot Notation]: positional dot notation
# works on array fields in output documents.
FILTER_POSITIONAL_DOT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        target_collection=ViewWithPipelineCollection(),
        command=lambda ctx: {
            "listCollections": 1,
            "filter": {"options.pipeline.0.$match.x": 1},
        },
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="Positional dot notation options.pipeline.0 should match view",
        id="filter_positional_dot_pipeline",
    ),
]

# Property [Filter Nonexistent Field]: filtering on a nonexistent
# output field with equality returns empty, with $exists: false returns
# all, and with null returns all.
FILTER_NONEXISTENT_FIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        docs=[{"_id": 1}],
        command={"listCollections": 1, "filter": {"nonexistent": "value"}},
        expected={"cursor.firstBatch": Len(0)},
        msg="Equality on nonexistent field should return empty",
        id="filter_nonexistent_eq_empty",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command={
            "listCollections": 1,
            "filter": {"nonexistent": {"$exists": False}},
        },
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$exists: false on nonexistent field should return all",
        id="filter_nonexistent_exists_false",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command={"listCollections": 1, "filter": {"nonexistent": None}},
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="null on nonexistent field should return all (null matches missing)",
        id="filter_nonexistent_null",
    ),
]

# Property [Filter Array Operators on Non-Array]: $size and $elemMatch
# on non-array output fields silently return empty results.
FILTER_ARRAY_OPS_NON_ARRAY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        docs=[{"_id": 1}],
        command={"listCollections": 1, "filter": {"name": {"$size": 1}}},
        expected={"cursor.firstBatch": Len(0)},
        msg="$size on non-array name field should return empty",
        id="filter_size_on_non_array",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        command={
            "listCollections": 1,
            "filter": {"type": {"$elemMatch": {"$eq": "collection"}}},
        },
        expected={"cursor.firstBatch": Len(0)},
        msg="$elemMatch on non-array type field should return empty",
        id="filter_elemmatch_on_non_array",
    ),
]

# Property [Filter Array Operators on Array]: $size and $elemMatch on
# actual array output fields (e.g. options.pipeline on views) match
# correctly.
FILTER_ARRAY_OPS_ARRAY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        target_collection=ViewWithPipelineCollection(),
        command={
            "listCollections": 1,
            "filter": {"options.pipeline": {"$size": 1}},
        },
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$size on pipeline array should match view with one stage",
        id="filter_size_on_array",
    ),
    CommandTestCase(
        target_collection=ViewWithPipelineCollection(),
        command={
            "listCollections": 1,
            "filter": {
                "options.pipeline": {
                    "$elemMatch": {"$eq": {"$match": {"x": 1}}},
                },
            },
        },
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$elemMatch on pipeline array should match stage by equality",
        id="filter_elemmatch_on_array",
    ),
]

# Property [Filter $all Scalar]: $all matches scalar values by
# equality.
FILTER_ALL_SCALAR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "listCollections": 1,
            "filter": {"name": {"$all": [ctx.collection]}},
        },
        expected=lambda ctx: {
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
        msg="$all should match scalar name by equality",
        id="filter_all_scalar_name",
    ),
]

# Property [Filter $all Pipeline Stages]: $all matches pipeline stages
# by exact document equality.
FILTER_ALL_PIPELINE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        target_collection=ViewWithPipelineCollection(),
        command={
            "listCollections": 1,
            "filter": {
                "options.pipeline": {"$all": [{"$match": {"x": 1}}]},
            },
        },
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$all should match pipeline stages by exact document equality",
        id="filter_all_pipeline_stage",
    ),
]

# Property [Filter $mod and Bitwise Operators]: $mod and bitwise
# operators work on numeric output fields.
FILTER_BITWISE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        target_collection=CappedCollection(size=4096, max=100),
        command={"listCollections": 1, "filter": {"options.max": {"$mod": [50, 0]}}},
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$mod on numeric options.max should match",
        id="filter_mod_numeric",
    ),
    CommandTestCase(
        target_collection=CappedCollection(size=4096, max=100),
        command={
            "listCollections": 1,
            "filter": {"options.max": {"$bitsAllSet": [5, 6]}},
        },
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$bitsAllSet on numeric options.max should match (100 has bits 5,6)",
        id="filter_bitsallset_numeric",
    ),
    CommandTestCase(
        target_collection=CappedCollection(size=4096, max=100),
        command={
            "listCollections": 1,
            "filter": {"options.max": {"$bitsAllClear": [0, 1]}},
        },
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$bitsAllClear on numeric options.max should match (100 has bits 0,1 clear)",
        id="filter_bitsallclear_numeric",
    ),
    CommandTestCase(
        target_collection=CappedCollection(size=4096, max=100),
        command={
            "listCollections": 1,
            "filter": {"options.max": {"$bitsAnySet": [2, 3]}},
        },
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$bitsAnySet on numeric options.max should match (100 has bit 2 set)",
        id="filter_bitsanyset_numeric",
    ),
    CommandTestCase(
        target_collection=CappedCollection(size=4096, max=100),
        command={
            "listCollections": 1,
            "filter": {"options.max": {"$bitsAnyClear": [0, 2]}},
        },
        expected=lambda ctx: {"cursor.firstBatch": Contains("name", ctx.collection)},
        msg="$bitsAnyClear on numeric options.max should match (100 has bit 0 clear)",
        id="filter_bitsanyclear_numeric",
    ),
]

FILTER_PREDICATE_TESTS: list[CommandTestCase] = (
    FILTER_BASIC_PREDICATE_TESTS
    + FILTER_REGEX_TESTS
    + FILTER_COMPARISON_TESTS
    + FILTER_TYPE_OPERATOR_TESTS
    + FILTER_DOT_NOTATION_TESTS
    + FILTER_POSITIONAL_DOT_TESTS
    + FILTER_NONEXISTENT_FIELD_TESTS
    + FILTER_ARRAY_OPS_NON_ARRAY_TESTS
    + FILTER_ARRAY_OPS_ARRAY_TESTS
    + FILTER_ALL_SCALAR_TESTS
    + FILTER_ALL_PIPELINE_TESTS
    + FILTER_BITWISE_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(FILTER_PREDICATE_TESTS))
def test_listCollections_filter_predicates(database_client, collection, test):
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
