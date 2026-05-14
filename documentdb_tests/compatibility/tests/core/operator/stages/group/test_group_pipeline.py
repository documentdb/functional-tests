"""Aggregation $group stage tests - pipeline behavior and integration."""

from __future__ import annotations

import math
from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import (
    assertResult,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    TS_MAX_SIGNED32,
    TS_MAX_UNSIGNED32,
)

# Property [Empty and Non-Existent Input]: $group on an empty or non-existent
# collection produces zero output documents regardless of the _id expression.
GROUP_EMPTY_INPUT_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="empty_collection_field_ref",
        docs=[],
        pipeline=[{"$group": {"_id": "$v"}}],
        expected=[],
        msg="Empty collection should produce zero output documents",
    ),
    StageTestCase(
        id="nonexistent_collection_field_ref",
        docs=None,
        pipeline=[{"$group": {"_id": "$v"}}],
        expected=[],
        msg="Non-existent collection should produce zero output documents",
    ),
    StageTestCase(
        id="empty_collection_null_id",
        docs=[],
        pipeline=[{"$group": {"_id": None}}],
        expected=[],
        msg="_id: null on empty collection should produce zero output documents",
    ),
    StageTestCase(
        id="empty_collection_constant_id",
        docs=[],
        pipeline=[{"$group": {"_id": 1}}],
        expected=[],
        msg="_id: <constant> on empty collection should produce zero output documents",
    ),
]

# Property [Re-Grouping]: $group output can be consumed by subsequent $group
# stages, including triple-$group pipelines.
GROUP_RE_GROUPING_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="double_group",
        docs=[
            {"_id": 1, "dept": "eng", "x": 10},
            {"_id": 2, "dept": "eng", "x": 20},
            {"_id": 3, "dept": "sales", "x": 30},
            {"_id": 4, "dept": "sales", "x": 40},
        ],
        pipeline=[
            {"$group": {"_id": "$dept", "total": {"$sum": "$x"}}},
            {"$group": {"_id": None, "grand_total": {"$sum": "$total"}}},
        ],
        expected=[{"_id": None, "grand_total": 100}],
        msg="$group output should be consumable by a subsequent $group stage",
    ),
    StageTestCase(
        id="triple_group",
        docs=[
            {"_id": 1, "dept": "eng", "team": "a", "x": 5},
            {"_id": 2, "dept": "eng", "team": "a", "x": 15},
            {"_id": 3, "dept": "eng", "team": "b", "x": 10},
            {"_id": 4, "dept": "sales", "team": "c", "x": 20},
        ],
        pipeline=[
            {"$group": {"_id": {"dept": "$dept", "team": "$team"}, "team_total": {"$sum": "$x"}}},
            {"$group": {"_id": "$_id.dept", "dept_total": {"$sum": "$team_total"}}},
            {"$group": {"_id": None, "grand_total": {"$sum": "$dept_total"}}},
        ],
        expected=[{"_id": None, "grand_total": 50}],
        msg="Triple $group pipeline should work correctly",
    ),
]

# Property [$push Preserves Document Order]: $push preserves document order
# within groups when preceded by $sort.
GROUP_PUSH_ORDER_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="push_preserves_order_after_sort",
        docs=[
            {"_id": 1, "g": "a", "v": 3},
            {"_id": 2, "g": "a", "v": 1},
            {"_id": 3, "g": "a", "v": 2},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": "$g", "vals": {"$push": "$v"}}},
        ],
        expected=[{"_id": "a", "vals": [1, 2, 3]}],
        msg="$push should preserve document order within groups when preceded by $sort",
    ),
]

# Property [Timestamp Literal _id Not Replaced]: Timestamp(0, 0) used as a
# literal _id value is not replaced by the server, and Timestamp boundary
# values are accepted.
GROUP_TIMESTAMP_ID_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="timestamp_zero_zero_not_replaced",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[{"$group": {"_id": Timestamp(0, 0), "count": {"$sum": 1}}}],
        expected=[{"_id": Timestamp(0, 0), "count": 2}],
        msg=(
            "Timestamp(0, 0) as literal _id should not be replaced by the"
            " server (server-side replacement only occurs on insert)"
        ),
    ),
    StageTestCase(
        id="timestamp_max_time_component",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[{"$group": {"_id": TS_MAX_UNSIGNED32, "count": {"$sum": 1}}}],
        expected=[{"_id": TS_MAX_UNSIGNED32, "count": 2}],
        msg="Timestamp with max unsigned 32-bit time component should be accepted as _id",
    ),
    StageTestCase(
        id="timestamp_max_inc_component",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[{"$group": {"_id": Timestamp(1, 4_294_967_295), "count": {"$sum": 1}}}],
        expected=[{"_id": Timestamp(1, 4_294_967_295), "count": 2}],
        msg="Timestamp with max increment component should be accepted as _id",
    ),
    StageTestCase(
        id="timestamp_max_signed32_time",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[{"$group": {"_id": TS_MAX_SIGNED32, "count": {"$sum": 1}}}],
        expected=[{"_id": TS_MAX_SIGNED32, "count": 2}],
        msg="Timestamp with max signed 32-bit time component should be accepted as _id",
    ),
]

# Property [Compound _id Field Name Acceptance]: _id is accepted as a field
# name within a compound _id key, and Unicode, emoji, spaces, tabs, and long
# names are accepted as compound _id field names.
GROUP_COMPOUND_ID_FIELD_NAME_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="compound_id_with_id_field_name",
        docs=[{"_id": 1, "v": "a"}, {"_id": 2, "v": "b"}],
        pipeline=[{"$group": {"_id": {"_id": "$v"}, "count": {"$sum": 1}}}],
        expected=[
            {"_id": {"_id": "a"}, "count": 1},
            {"_id": {"_id": "b"}, "count": 1},
        ],
        msg="_id as a field name within a compound _id key should be allowed",
    ),
    StageTestCase(
        id="compound_id_unicode_field_name",
        docs=[{"_id": 1, "v": 10}],
        pipeline=[{"$group": {"_id": {"\u00e9": "$v"}, "count": {"$sum": 1}}}],
        expected=[{"_id": {"\u00e9": 10}, "count": 1}],
        msg="Unicode characters should be accepted as compound _id field names",
    ),
    StageTestCase(
        id="compound_id_emoji_field_name",
        docs=[{"_id": 1, "v": 10}],
        pipeline=[{"$group": {"_id": {"\U0001f600": "$v"}, "count": {"$sum": 1}}}],
        expected=[{"_id": {"\U0001f600": 10}, "count": 1}],
        msg="Emoji should be accepted as compound _id field names",
    ),
    StageTestCase(
        id="compound_id_space_field_name",
        docs=[{"_id": 1, "v": 10}],
        pipeline=[{"$group": {"_id": {" ": "$v"}, "count": {"$sum": 1}}}],
        expected=[{"_id": {" ": 10}, "count": 1}],
        msg="Space should be accepted as a compound _id field name",
    ),
    StageTestCase(
        id="compound_id_tab_field_name",
        docs=[{"_id": 1, "v": 10}],
        pipeline=[{"$group": {"_id": {"\t": "$v"}, "count": {"$sum": 1}}}],
        expected=[{"_id": {"\t": 10}, "count": 1}],
        msg="Tab should be accepted as a compound _id field name",
    ),
    StageTestCase(
        id="compound_id_long_field_name",
        docs=[{"_id": 1, "v": 10}],
        pipeline=[{"$group": {"_id": {"a" * 200: "$v"}, "count": {"$sum": 1}}}],
        expected=[{"_id": {"a" * 200: 10}, "count": 1}],
        msg="Long field names (200 chars) should be accepted as compound _id field names",
    ),
]

# Property [Inclusion-Style Detection Bypass]: nested objects with numeric
# values do not trigger the inclusion-style check, and $literal wrapping
# bypasses it.
GROUP_INCLUSION_STYLE_BYPASS_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="inclusion_nested_numeric_ok",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": {"a": {"b": 1}}, "count": {"$sum": 1}}}],
        expected=[{"_id": {"a": {"b": 1}}, "count": 1}],
        msg="Nested object with numeric value should not trigger inclusion-style error",
    ),
    StageTestCase(
        id="inclusion_literal_bypass",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": {"a": {"$literal": 1}}, "count": {"$sum": 1}}}],
        expected=[{"_id": {"a": 1}, "count": 1}],
        msg="$literal wrapping should bypass the inclusion-style check",
    ),
]


GROUP_PIPELINE_UNORDERED_TESTS = (
    GROUP_EMPTY_INPUT_TESTS
    + GROUP_RE_GROUPING_TESTS
    + GROUP_PUSH_ORDER_TESTS
    + GROUP_TIMESTAMP_ID_TESTS
    + GROUP_COMPOUND_ID_FIELD_NAME_TESTS
    + GROUP_INCLUSION_STYLE_BYPASS_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(GROUP_PIPELINE_UNORDERED_TESTS))
def test_group_pipeline(collection, test_case: StageTestCase):
    """Test $group stage - pipeline behavior."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        ignore_doc_order=True,
    )


# Property [Output Field Order]: output field order matches the specification
# order, not alphabetical order.
GROUP_OUTPUT_FIELD_ORDER_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="output_field_order_matches_spec",
        docs=[{"_id": 1, "v": "a", "x": 10}],
        pipeline=[
            {
                "$group": {
                    "_id": "$v",
                    "z_field": {"$sum": 1},
                    "a_field": {"$sum": "$x"},
                }
            }
        ],
        expected=[{"_id": "a", "z_field": 1, "a_field": 10}],
        msg="Output field order should match specification order",
    ),
]

# Property [_id Type Preservation]: the _id type is preserved for all BSON
# types in the output.
GROUP_ID_TYPE_PRESERVATION_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="id_type_preserved_all_bson_types",
        docs=[
            {"_id": 1, "v": Int64(42)},
            {"_id": 2, "v": 3.14},
            {"_id": 3, "v": Decimal128("9.99")},
            {"_id": 4, "v": True},
            {"_id": 5, "v": ObjectId("507f1f77bcf86cd799439011")},
            {"_id": 6, "v": datetime(2024, 1, 1, tzinfo=timezone.utc)},
            {"_id": 7, "v": Timestamp(1, 1)},
            {"_id": 8, "v": Binary(b"data")},
            {"_id": 9, "v": Regex("abc", "i")},
            {"_id": 10, "v": Code("function(){}")},
            {"_id": 11, "v": MinKey()},
            {"_id": 12, "v": MaxKey()},
            {"_id": 13, "v": "hello"},
            {"_id": 14, "v": 99},
            {"_id": 15, "v": None},
        ],
        pipeline=[
            {"$group": {"_id": "$v", "count": {"$sum": 1}}},
            {"$project": {"type": {"$type": "$_id"}, "count": 1}},
            {"$sort": {"type": 1, "_id": 1}},
        ],
        expected=[
            {"_id": b"data", "type": "binData", "count": 1},
            {"_id": True, "type": "bool", "count": 1},
            {"_id": datetime(2024, 1, 1, tzinfo=timezone.utc), "type": "date", "count": 1},
            {"_id": Decimal128("9.99"), "type": "decimal", "count": 1},
            {"_id": 3.14, "type": "double", "count": 1},
            {"_id": 99, "type": "int", "count": 1},
            {"_id": Int64(42), "type": "long", "count": 1},
            {"_id": None, "type": "null", "count": 1},
            {"_id": {"": MinKey()}, "type": "object", "count": 1},
            {"_id": {"": MaxKey()}, "type": "object", "count": 1},
            {"_id": ObjectId("507f1f77bcf86cd799439011"), "type": "objectId", "count": 1},
            {"_id": Regex("abc", "i"), "type": "regex", "count": 1},
            {"_id": "function(){}", "type": "string", "count": 1},
            {"_id": "hello", "type": "string", "count": 1},
            {"_id": Timestamp(1, 1), "type": "timestamp", "count": 1},
        ],
        msg="_id type should be preserved for all BSON types in the output",
    ),
]

# Property [Blocking Stage]: $group is a blocking stage that waits for all
# input before producing output.
GROUP_BLOCKING_STAGE_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="blocking_stage",
        docs=[{"_id": i, "v": i % 3} for i in range(9)],
        pipeline=[
            {"$group": {"_id": "$v", "total": {"$sum": 1}}},
            {
                "$group": {
                    "_id": None,
                    "group_count": {"$sum": 1},
                    "doc_sum": {"$sum": "$total"},
                }
            },
        ],
        expected=[{"_id": None, "group_count": 3, "doc_sum": 9}],
        msg=(
            "$group should consume all input before producing output;"
            " a subsequent $group should see all groups"
        ),
    ),
]


GROUP_PIPELINE_ORDERED_TESTS = (
    GROUP_OUTPUT_FIELD_ORDER_TESTS + GROUP_ID_TYPE_PRESERVATION_TESTS + GROUP_BLOCKING_STAGE_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(GROUP_PIPELINE_ORDERED_TESTS))
def test_group_pipeline_ordered(collection, test_case: StageTestCase):
    """Test $group stage - output ordering and type preservation."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        msg=test_case.msg,
    )


NAN = pytest.approx(math.nan, nan_ok=True)

# Property [NaN Behavior]: NaN contaminates $sum, inf + (-inf) produces NaN,
# float NaN and Decimal128 NaN group together, and $addToSet deduplicates
# NaN variants to one entry.
GROUP_NAN_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="sum_nan_contaminates",
        docs=[{"_id": 1, "v": FLOAT_NAN}, {"_id": 2, "v": 10}],
        pipeline=[{"$group": {"_id": None, "r": {"$sum": "$v"}}}],
        expected=[{"_id": None, "r": NAN}],
        msg="NaN input should contaminate the $sum result",
    ),
    StageTestCase(
        id="sum_inf_plus_neg_inf_produces_nan",
        docs=[
            {"_id": 1, "v": FLOAT_INFINITY},
            {"_id": 2, "v": FLOAT_NEGATIVE_INFINITY},
        ],
        pipeline=[{"$group": {"_id": None, "r": {"$sum": "$v"}}}],
        expected=[{"_id": None, "r": NAN}],
        msg="inf + (-inf) should produce NaN",
    ),
    StageTestCase(
        id="nan_variants_group_together",
        docs=[
            {"_id": 1, "v": FLOAT_NAN},
            {"_id": 2, "v": Decimal128("NaN")},
        ],
        pipeline=[{"$group": {"_id": "$v", "ids": {"$push": "$_id"}}}],
        expected=[{"_id": NAN, "ids": [1, 2]}],
        msg="float NaN and Decimal128 NaN should group together",
    ),
    StageTestCase(
        id="addtoset_nan_dedup",
        docs=[
            {"_id": 1, "v": FLOAT_NAN},
            {"_id": 2, "v": Decimal128("NaN")},
            {"_id": 3, "v": FLOAT_NAN},
        ],
        pipeline=[
            {"$group": {"_id": None, "r": {"$addToSet": "$v"}}},
        ],
        expected=[{"_id": None, "r": [NAN]}],
        msg="NaN variants (float NaN and Decimal128 NaN) should deduplicate to one entry",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(GROUP_NAN_TESTS))
def test_group_nan(collection, test_case: StageTestCase):
    """Test $group NaN behavior."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        msg=test_case.msg,
        ignore_doc_order=True,
    )


# Property [Collation Affects Grouping]: collation settings (e.g.,
# case-insensitive) affect which values are considered equivalent for grouping.
GROUP_COLLATION_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="collation_case_insensitive_merges_groups",
        docs=[
            {"_id": 1, "v": "hello"},
            {"_id": 2, "v": "Hello"},
        ],
        pipeline=[{"$group": {"_id": "$v", "ids": {"$push": "$_id"}}}],
        expected=[{"_id": "hello", "ids": [1, 2]}],
        msg="Case-insensitive collation should merge differently-cased strings into one group",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(GROUP_COLLATION_TESTS))
def test_group_collation_affects_grouping(collection, test_case: StageTestCase):
    """Test collation affects grouping equivalence."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        msg=test_case.msg,
    )


# Property [Large Input]: 1000 distinct group key values produce 1000 output
# groups without issues.
GROUP_LARGE_INPUT_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="large_input_1000_groups",
        docs=[{"_id": i, "v": i} for i in range(1_000)],
        pipeline=[
            {"$group": {"_id": "$v", "count": {"$sum": 1}}},
            {"$group": {"_id": None, "num_groups": {"$sum": 1}}},
        ],
        expected=[{"_id": None, "num_groups": 1_000}],
        msg="1000 distinct group keys should produce 1000 output groups",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(GROUP_LARGE_INPUT_TESTS))
def test_group_large_input(collection, test_case: StageTestCase):
    """Test 1000 distinct group keys produce 1000 output groups."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {"batchSize": 10_000},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        msg=test_case.msg,
    )


# Property [$$NOW in _id]: $$NOW returns the same datetime for the entire
# pipeline, so all documents group together under a single datetime key.
GROUP_NOW_IN_ID_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="now_in_id_groups_all",
        docs=[{"_id": 1, "x": 10}, {"_id": 2, "x": 20}],
        pipeline=[
            {"$group": {"_id": "$$NOW", "count": {"$sum": 1}}},
            {"$project": {"_id": 0, "type": {"$type": "$_id"}, "count": 1}},
        ],
        expected=[{"type": "date", "count": 2}],
        msg="$$NOW in _id should group all documents together under a single datetime",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(GROUP_NOW_IN_ID_TESTS))
def test_group_now_in_id(collection, test_case: StageTestCase):
    """Test $$NOW in _id groups all documents together."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        msg=test_case.msg,
    )
