"""Tests for $indexStats output document structure."""

from __future__ import annotations

import pytest
from pymongo.collection import Collection
from pymongo.operations import IndexModel

from documentdb_tests.compatibility.tests.core.operator.stages.indexStats.utils.indexStats_test_case import (  # noqa: E501
    IndexStatsTestCase,
    prepare_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists, IsType, NotExists
from documentdb_tests.framework.test_constants import INT64_ZERO

# Property [Top-Level Fields]: each output document contains the documented
# top-level fields with correct types and no _id.
OUTPUT_TOP_LEVEL_FIELDS_TESTS: list[IndexStatsTestCase] = [
    IndexStatsTestCase(
        id="default_index_field_types",
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "_id_"}}],
        expected={
            "name": Eq("_id_"),
            "key": Eq({"_id": 1}),
            "host": IsType("string"),
            "accesses": {"ops": Eq(INT64_ZERO), "since": IsType("date")},
            "spec": IsType("object"),
            "_id": NotExists(),
        },
        msg="Default index output should have correct top-level field types and no _id",
    ),
    IndexStatsTestCase(
        id="user_index_field_types",
        indexes=[IndexModel([("a", 1)])],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "a_1"}}],
        expected={
            "name": Eq("a_1"),
            "key": Eq({"a": 1}),
            "host": IsType("string"),
            "accesses": {"ops": Eq(INT64_ZERO), "since": IsType("date")},
            "spec": {"key": Eq({"a": 1}), "name": Eq("a_1"), "v": IsType("int")},
            "_id": NotExists(),
        },
        msg="User index output should have correct top-level field types and no _id",
    ),
]

# Property [Key Direction Type]: index key direction values are int32, not
# int64.
OUTPUT_KEY_DIRECTION_TYPE_TESTS: list[IndexStatsTestCase] = [
    IndexStatsTestCase(
        id="single_key_direction_is_int",
        indexes=[IndexModel([("a", 1)])],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "a_1"}}],
        expected={"key.a": Eq(1)},
        msg="Single index key direction should be int, not long",
    ),
    IndexStatsTestCase(
        id="compound_key_directions_are_int",
        indexes=[IndexModel([("a", 1), ("b", -1)])],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "a_1_b_-1"}}],
        expected={"key.a": Eq(1), "key.b": Eq(-1)},
        msg="Compound index key directions should be int, not long",
    ),
    IndexStatsTestCase(
        id="id_key_direction_is_int",
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "_id_"}}],
        expected={"key._id": Eq(1)},
        msg="Default _id index key direction should be int, not long",
    ),
]

# Property [Absent Fields]: conditional fields are absent when their
# conditions are not met and present when they are.
OUTPUT_ABSENT_FIELDS_TESTS: list[IndexStatsTestCase] = [
    IndexStatsTestCase(
        id="shard_absent_non_sharded",
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "_id_"}}],
        expected={"shard": NotExists()},
        msg="shard field should be absent on non-sharded topology",
    ),
    IndexStatsTestCase(
        id="building_absent_completed_index",
        indexes=[IndexModel([("a", 1)])],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "a_1"}}],
        expected={"building": NotExists()},
        msg="building field should be absent for completed indexes",
    ),
    IndexStatsTestCase(
        id="hidden_absent_when_not_hidden",
        indexes=[IndexModel([("a", 1)])],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "a_1"}}],
        expected={"spec.hidden": NotExists()},
        msg="spec.hidden should be absent when index is not hidden",
    ),
]

# Property [Default Index Names]: each index type produces the expected
# auto-generated name.
DEFAULT_INDEX_NAME_TESTS: list[IndexStatsTestCase] = [
    IndexStatsTestCase(
        id="single_field_default_name",
        indexes=[IndexModel([("a", 1)])],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "a_1"}}],
        expected={"name": Eq("a_1")},
        msg="Single-field index should have default name",
    ),
    IndexStatsTestCase(
        id="compound_default_name",
        indexes=[IndexModel([("a", 1), ("b", -1)])],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "a_1_b_-1"}}],
        expected={"name": Eq("a_1_b_-1")},
        msg="Compound index should have default name",
    ),
    IndexStatsTestCase(
        id="text_default_name",
        indexes=[IndexModel([("a", "text")])],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "a_text"}}],
        expected={"name": Eq("a_text")},
        msg="Text index should have default name",
    ),
    IndexStatsTestCase(
        id="2d_default_name",
        indexes=[IndexModel([("loc", "2d")])],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "loc_2d"}}],
        expected={"name": Eq("loc_2d")},
        msg="2d index should have default name",
    ),
    IndexStatsTestCase(
        id="2dsphere_default_name",
        indexes=[IndexModel([("geo", "2dsphere")])],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "geo_2dsphere"}}],
        expected={"name": Eq("geo_2dsphere")},
        msg="2dsphere index should have default name",
    ),
    IndexStatsTestCase(
        id="wildcard_default_name",
        indexes=[IndexModel([("$**", 1)])],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "$**_1"}}],
        expected={"name": Eq("$**_1")},
        msg="Wildcard index should have default name",
    ),
    IndexStatsTestCase(
        id="hashed_default_name",
        indexes=[IndexModel([("a", "hashed")])],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "a_hashed"}}],
        expected={"name": Eq("a_hashed")},
        msg="Hashed index should have default name",
    ),
    IndexStatsTestCase(
        id="unique_default_name",
        indexes=[IndexModel([("a", 1)], unique=True)],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "a_1"}}],
        expected={"name": Eq("a_1")},
        msg="Unique index should have default name",
    ),
    IndexStatsTestCase(
        id="sparse_default_name",
        indexes=[IndexModel([("a", 1)], sparse=True)],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "a_1"}}],
        expected={"name": Eq("a_1")},
        msg="Sparse index should have default name",
    ),
    IndexStatsTestCase(
        id="ttl_default_name",
        indexes=[IndexModel([("ts", 1)], expireAfterSeconds=3600)],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "ts_1"}}],
        expected={"name": Eq("ts_1")},
        msg="TTL index should have default name",
    ),
    IndexStatsTestCase(
        id="partial_filter_default_name",
        indexes=[IndexModel([("a", 1)], partialFilterExpression={"a": {"$gt": 0}})],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "a_1"}}],
        expected={"name": Eq("a_1")},
        msg="Partial filter index should have default name",
    ),
    IndexStatsTestCase(
        id="collation_default_name",
        indexes=[IndexModel([("a", 1)], collation={"locale": "en", "strength": 2})],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "a_1"}}],
        expected={"name": Eq("a_1")},
        msg="Collation index should have default name",
    ),
    IndexStatsTestCase(
        id="hidden_default_name",
        indexes=[IndexModel([("a", 1)], hidden=True)],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "a_1"}}],
        expected={"name": Eq("a_1")},
        msg="Hidden index should have default name",
    ),
]

# Property [Custom Index Names]: indexes with custom names including
# special characters are reported correctly.
CUSTOM_INDEX_NAME_TESTS: list[IndexStatsTestCase] = [
    IndexStatsTestCase(
        id="custom_name",
        indexes=[IndexModel([("a", 1)], name="my_custom_name")],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "my_custom_name"}}],
        expected={"name": Eq("my_custom_name")},
        msg="Custom-named index should be reported",
    ),
    IndexStatsTestCase(
        id="unicode_name",
        indexes=[IndexModel([("a", 1)], name="\u00edndice_\u65e5\u672c\u8a9e")],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "\u00edndice_\u65e5\u672c\u8a9e"}}],
        expected={"name": Eq("\u00edndice_\u65e5\u672c\u8a9e")},
        msg="Unicode-named index should be reported",
    ),
    IndexStatsTestCase(
        id="long_name",
        indexes=[IndexModel([("a", 1)], name="x" * 100)],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "x" * 100}}],
        expected={"name": Eq("x" * 100)},
        msg="Long-named index should be reported",
    ),
    IndexStatsTestCase(
        id="name_with_spaces",
        indexes=[IndexModel([("a", 1)], name="my index name")],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "my index name"}}],
        expected={"name": Eq("my index name")},
        msg="Index name with spaces should be reported",
    ),
    IndexStatsTestCase(
        id="name_with_dots",
        indexes=[IndexModel([("a", 1)], name="a.b.c")],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "a.b.c"}}],
        expected={"name": Eq("a.b.c")},
        msg="Index name with dots should be reported",
    ),
    IndexStatsTestCase(
        id="name_with_dollar",
        indexes=[IndexModel([("a", 1)], name="$special")],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "$special"}}],
        expected={"name": Eq("$special")},
        msg="Index name with dollar sign should be reported",
    ),
    IndexStatsTestCase(
        id="name_with_emoji",
        indexes=[IndexModel([("a", 1)], name="\U0001f600\U0001f680")],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "\U0001f600\U0001f680"}}],
        expected={"name": Eq("\U0001f600\U0001f680")},
        msg="Index name with emoji should be reported",
    ),
]

# Property [Key Representation]: the key field correctly represents the
# index key specification for each index type.
KEY_REPRESENTATION_TESTS: list[IndexStatsTestCase] = [
    IndexStatsTestCase(
        id="compound_key",
        indexes=[IndexModel([("a", 1), ("b", -1)])],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "a_1_b_-1"}}],
        expected={"key": Eq({"a": 1, "b": -1})},
        msg="Compound index key should reflect all fields and directions",
    ),
    IndexStatsTestCase(
        id="text_key",
        indexes=[IndexModel([("a", "text")])],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "a_text"}}],
        expected={"key": Eq({"_fts": "text", "_ftsx": 1})},
        msg="Text index key should use _fts/_ftsx representation",
    ),
    IndexStatsTestCase(
        id="2d_key",
        indexes=[IndexModel([("loc", "2d")])],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "loc_2d"}}],
        expected={"key": Eq({"loc": "2d"})},
        msg="2d index key should use string value",
    ),
    IndexStatsTestCase(
        id="2dsphere_key",
        indexes=[IndexModel([("geo", "2dsphere")])],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "geo_2dsphere"}}],
        expected={"key": Eq({"geo": "2dsphere"})},
        msg="2dsphere index key should use string value",
    ),
    IndexStatsTestCase(
        id="hashed_key",
        indexes=[IndexModel([("a", "hashed")])],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "a_hashed"}}],
        expected={"key": Eq({"a": "hashed"})},
        msg="Hashed index key should use string value",
    ),
    IndexStatsTestCase(
        id="wildcard_key",
        indexes=[IndexModel([("$**", 1)])],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "$**_1"}}],
        expected={"key": Eq({"$**": 1})},
        msg="Wildcard index key should use $** field path",
    ),
]

# Property [Index Options in Spec]: index options are reflected in the
# spec document.
INDEX_OPTIONS_IN_SPEC_TESTS: list[IndexStatsTestCase] = [
    IndexStatsTestCase(
        id="2d_options_in_spec",
        indexes=[IndexModel([("loc", "2d")], bits=20, min=-100, max=100, name="loc_2d_opts")],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "loc_2d_opts"}}],
        expected={
            "spec.bits": Eq(20),
            "spec.min": Eq(-100),
            "spec.max": Eq(100),
        },
        msg="2d explicit options (bits, min, max) should appear in spec",
    ),
    IndexStatsTestCase(
        id="wildcard_projection_in_spec",
        indexes=[IndexModel([("$**", 1)], wildcardProjection={"a": 1}, name="wc_proj")],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "wc_proj"}}],
        expected={"spec.wildcardProjection": Eq({"a": 1})},
        msg="Wildcard index with wildcardProjection should include it in spec",
    ),
    IndexStatsTestCase(
        id="field_path_wildcard_no_projection",
        indexes=[IndexModel([("a.$**", 1)], name="fp_wc")],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "fp_wc"}}],
        expected={"spec.wildcardProjection": NotExists()},
        msg="Field-path wildcard should not include wildcardProjection in spec",
    ),
    IndexStatsTestCase(
        id="unique_option_in_spec",
        indexes=[IndexModel([("a", 1)], unique=True, name="a_unique")],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "a_unique"}}],
        expected={"spec.unique": Eq(True)},
        msg="Unique option should be in spec",
    ),
    IndexStatsTestCase(
        id="sparse_option_in_spec",
        indexes=[IndexModel([("a", 1)], sparse=True, name="a_sparse")],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "a_sparse"}}],
        expected={"spec.sparse": Eq(True)},
        msg="Sparse option should be in spec",
    ),
    IndexStatsTestCase(
        id="ttl_expire_in_spec",
        indexes=[IndexModel([("ts", 1)], expireAfterSeconds=3600, name="ts_ttl")],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "ts_ttl"}}],
        expected={"spec.expireAfterSeconds": Eq(3600)},
        msg="TTL expireAfterSeconds should be in spec",
    ),
    IndexStatsTestCase(
        id="collation_in_spec",
        indexes=[
            IndexModel([("a", 1)], collation={"locale": "en", "strength": 2}, name="a_collation")
        ],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "a_collation"}}],
        expected={"spec.collation": Exists()},
        msg="Collation option should be in spec",
    ),
    IndexStatsTestCase(
        id="partial_filter_in_spec",
        indexes=[
            IndexModel([("a", 1)], partialFilterExpression={"a": {"$gt": 0}}, name="a_partial")
        ],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "a_partial"}}],
        expected={"spec.partialFilterExpression": Eq({"a": {"$gt": 0}})},
        msg="partialFilterExpression should be in spec",
    ),
    IndexStatsTestCase(
        id="hidden_option_in_spec",
        indexes=[IndexModel([("a", 1)], hidden=True)],
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "a_1"}}],
        expected={"spec.hidden": Eq(True)},
        msg="Hidden option should be in spec",
    ),
]

OUTPUT_STRUCTURE_TESTS = (
    OUTPUT_TOP_LEVEL_FIELDS_TESTS
    + OUTPUT_KEY_DIRECTION_TYPE_TESTS
    + OUTPUT_ABSENT_FIELDS_TESTS
    + DEFAULT_INDEX_NAME_TESTS
    + CUSTOM_INDEX_NAME_TESTS
    + KEY_REPRESENTATION_TESTS
    + INDEX_OPTIONS_IN_SPEC_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUTPUT_STRUCTURE_TESTS))
def test_indexStats_output_structure(collection: Collection, test_case: IndexStatsTestCase):
    """Test $indexStats output document structure."""
    coll = prepare_collection(collection, test_case)
    result = execute_command(
        coll,
        {
            "aggregate": coll.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
