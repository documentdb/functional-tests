"""Aggregation $group stage tests - accumulator operators."""

from __future__ import annotations

import pytest
from bson import SON

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
    DOUBLE_ZERO,
)

# Property [Accumulator Field Acceptance]: zero or more accumulator fields
# are accepted alongside _id, and accumulator field names become output field
# names.
GROUP_ACCUMULATOR_FIELD_ACCEPTANCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="zero_accumulators",
        docs=[{"_id": 1, "v": "a"}, {"_id": 2, "v": "b"}, {"_id": 3, "v": "a"}],
        pipeline=[{"$group": {"_id": "$v"}}],
        expected=[{"_id": "a"}, {"_id": "b"}],
        msg="$group with zero accumulators should produce one document per group",
    ),
    StageTestCase(
        id="multiple_accumulators",
        docs=[
            {"_id": 1, "v": "a", "x": 10, "y": 100},
            {"_id": 2, "v": "a", "x": 20, "y": 200},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$v",
                    "sum_x": {"$sum": "$x"},
                    "avg_y": {"$avg": "$y"},
                    "count": {"$sum": 1},
                }
            }
        ],
        expected=[{"_id": "a", "sum_x": 30, "avg_y": 150.0, "count": 2}],
        msg="Multiple accumulators should all be computed and appear in output",
    ),
]

# Property [Valid Accumulator Operators]: the following accumulator operators
# are accepted in $group without error: $sum, $avg, $min, $max, $first, $last,
# $push, $addToSet, $count, $mergeObjects, $stdDevPop, $stdDevSamp,
# $setUnion, $concatArrays, $firstN, $lastN, $maxN, $minN, $top, $bottom,
# $topN, $bottomN, $median, and $percentile.
GROUP_VALID_ACCUMULATOR_OPERATORS_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="accumulator_sum",
        docs=[{"_id": 1, "v": "a", "x": 5}],
        pipeline=[{"$group": {"_id": "$v", "r": {"$sum": "$x"}}}],
        expected=[{"_id": "a", "r": 5}],
        msg="$sum should be a valid accumulator",
    ),
    StageTestCase(
        id="accumulator_avg",
        docs=[{"_id": 1, "v": "a", "x": 5}],
        pipeline=[{"$group": {"_id": "$v", "r": {"$avg": "$x"}}}],
        expected=[{"_id": "a", "r": 5.0}],
        msg="$avg should be a valid accumulator",
    ),
    StageTestCase(
        id="accumulator_min",
        docs=[{"_id": 1, "v": "a", "x": 5}],
        pipeline=[{"$group": {"_id": "$v", "r": {"$min": "$x"}}}],
        expected=[{"_id": "a", "r": 5}],
        msg="$min should be a valid accumulator",
    ),
    StageTestCase(
        id="accumulator_max",
        docs=[{"_id": 1, "v": "a", "x": 5}],
        pipeline=[{"$group": {"_id": "$v", "r": {"$max": "$x"}}}],
        expected=[{"_id": "a", "r": 5}],
        msg="$max should be a valid accumulator",
    ),
    StageTestCase(
        id="accumulator_first",
        docs=[{"_id": 1, "v": "a", "x": 5}],
        pipeline=[{"$group": {"_id": "$v", "r": {"$first": "$x"}}}],
        expected=[{"_id": "a", "r": 5}],
        msg="$first should be a valid accumulator",
    ),
    StageTestCase(
        id="accumulator_last",
        docs=[{"_id": 1, "v": "a", "x": 5}],
        pipeline=[{"$group": {"_id": "$v", "r": {"$last": "$x"}}}],
        expected=[{"_id": "a", "r": 5}],
        msg="$last should be a valid accumulator",
    ),
    StageTestCase(
        id="accumulator_push",
        docs=[{"_id": 1, "v": "a", "x": 5}],
        pipeline=[{"$group": {"_id": "$v", "r": {"$push": "$x"}}}],
        expected=[{"_id": "a", "r": [5]}],
        msg="$push should be a valid accumulator",
    ),
    StageTestCase(
        id="accumulator_addtoset",
        docs=[{"_id": 1, "v": "a", "x": 5}],
        pipeline=[{"$group": {"_id": "$v", "r": {"$addToSet": "$x"}}}],
        expected=[{"_id": "a", "r": [5]}],
        msg="$addToSet should be a valid accumulator",
    ),
    StageTestCase(
        id="accumulator_count",
        docs=[{"_id": 1, "v": "a"}, {"_id": 2, "v": "a"}],
        pipeline=[{"$group": {"_id": "$v", "r": {"$count": {}}}}],
        expected=[{"_id": "a", "r": 2}],
        msg="$count accumulator should be valid and count documents in the group",
    ),
    StageTestCase(
        id="accumulator_mergeobjects",
        docs=[{"_id": 1, "v": "a", "x": {"k": 1}}],
        pipeline=[{"$group": {"_id": "$v", "r": {"$mergeObjects": "$x"}}}],
        expected=[{"_id": "a", "r": {"k": 1}}],
        msg="$mergeObjects should be a valid accumulator",
    ),
    StageTestCase(
        id="accumulator_stddevpop",
        docs=[{"_id": 1, "v": "a", "x": 3}, {"_id": 2, "v": "a", "x": 7}],
        pipeline=[{"$group": {"_id": "$v", "r": {"$stdDevPop": "$x"}}}],
        expected=[{"_id": "a", "r": 2.0}],
        msg="$stdDevPop should be a valid accumulator",
    ),
    StageTestCase(
        id="accumulator_stddevsamp",
        docs=[{"_id": 1, "v": "a", "x": 3}, {"_id": 2, "v": "a", "x": 7}],
        pipeline=[{"$group": {"_id": "$v", "r": {"$stdDevSamp": "$x"}}}],
        expected=[{"_id": "a", "r": 2.8284271247461903}],
        msg="$stdDevSamp should be a valid accumulator",
    ),
    StageTestCase(
        id="accumulator_setunion",
        docs=[{"_id": 1, "v": "a", "x": [1]}],
        pipeline=[{"$group": {"_id": "$v", "r": {"$setUnion": "$x"}}}],
        expected=[{"_id": "a", "r": [1]}],
        msg="$setUnion should be a valid accumulator in $group",
    ),
    StageTestCase(
        id="accumulator_concatarrays",
        docs=[{"_id": 1, "v": "a", "x": [1]}],
        pipeline=[{"$group": {"_id": "$v", "r": {"$concatArrays": "$x"}}}],
        expected=[{"_id": "a", "r": [1]}],
        msg="$concatArrays should be a valid accumulator in $group",
    ),
    StageTestCase(
        id="accumulator_firstn",
        docs=[{"_id": 1, "v": "a", "x": 5}],
        pipeline=[{"$group": {"_id": "$v", "r": {"$firstN": {"input": "$x", "n": 1}}}}],
        expected=[{"_id": "a", "r": [5]}],
        msg="$firstN should be a valid accumulator",
    ),
    StageTestCase(
        id="accumulator_lastn",
        docs=[{"_id": 1, "v": "a", "x": 5}],
        pipeline=[{"$group": {"_id": "$v", "r": {"$lastN": {"input": "$x", "n": 1}}}}],
        expected=[{"_id": "a", "r": [5]}],
        msg="$lastN should be a valid accumulator",
    ),
    StageTestCase(
        id="accumulator_maxn",
        docs=[{"_id": 1, "v": "a", "x": 5}],
        pipeline=[{"$group": {"_id": "$v", "r": {"$maxN": {"input": "$x", "n": 1}}}}],
        expected=[{"_id": "a", "r": [5]}],
        msg="$maxN should be a valid accumulator",
    ),
    StageTestCase(
        id="accumulator_minn",
        docs=[{"_id": 1, "v": "a", "x": 5}],
        pipeline=[{"$group": {"_id": "$v", "r": {"$minN": {"input": "$x", "n": 1}}}}],
        expected=[{"_id": "a", "r": [5]}],
        msg="$minN should be a valid accumulator",
    ),
    StageTestCase(
        id="accumulator_top",
        docs=[{"_id": 1, "v": "a", "x": 5}],
        pipeline=[
            {
                "$group": {
                    "_id": "$v",
                    "r": {"$top": {"sortBy": {"x": 1}, "output": "$x"}},
                }
            }
        ],
        expected=[{"_id": "a", "r": 5}],
        msg="$top should be a valid accumulator",
    ),
    StageTestCase(
        id="accumulator_bottom",
        docs=[{"_id": 1, "v": "a", "x": 5}],
        pipeline=[
            {
                "$group": {
                    "_id": "$v",
                    "r": {"$bottom": {"sortBy": {"x": 1}, "output": "$x"}},
                }
            }
        ],
        expected=[{"_id": "a", "r": 5}],
        msg="$bottom should be a valid accumulator",
    ),
    StageTestCase(
        id="accumulator_topn",
        docs=[{"_id": 1, "v": "a", "x": 5}],
        pipeline=[
            {
                "$group": {
                    "_id": "$v",
                    "r": {"$topN": {"sortBy": {"x": 1}, "output": "$x", "n": 1}},
                }
            }
        ],
        expected=[{"_id": "a", "r": [5]}],
        msg="$topN should be a valid accumulator",
    ),
    StageTestCase(
        id="accumulator_bottomn",
        docs=[{"_id": 1, "v": "a", "x": 5}],
        pipeline=[
            {
                "$group": {
                    "_id": "$v",
                    "r": {
                        "$bottomN": {
                            "sortBy": {"x": 1},
                            "output": "$x",
                            "n": 1,
                        }
                    },
                }
            }
        ],
        expected=[{"_id": "a", "r": [5]}],
        msg="$bottomN should be a valid accumulator",
    ),
    StageTestCase(
        id="accumulator_median",
        docs=[{"_id": 1, "v": "a", "x": 5}],
        pipeline=[
            {
                "$group": {
                    "_id": "$v",
                    "r": {"$median": {"input": "$x", "method": "approximate"}},
                }
            }
        ],
        expected=[{"_id": "a", "r": 5.0}],
        msg="$median should be a valid accumulator",
    ),
    StageTestCase(
        id="accumulator_percentile",
        docs=[{"_id": 1, "v": "a", "x": 5}],
        pipeline=[
            {
                "$group": {
                    "_id": "$v",
                    "r": {
                        "$percentile": {
                            "input": "$x",
                            "p": [0.5],
                            "method": "approximate",
                        }
                    },
                }
            }
        ],
        expected=[{"_id": "a", "r": [5.0]}],
        msg="$percentile should be a valid accumulator",
    ),
]

# Property [$count Equivalence with $sum: 1]: $count produces the same result
# as $sum: 1 for counting documents in a group.
GROUP_COUNT_SUM_EQUIVALENCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="accumulator_count_equals_sum_1",
        docs=[{"_id": 1, "v": "a"}, {"_id": 2, "v": "a"}, {"_id": 3, "v": "b"}],
        pipeline=[
            {
                "$group": {
                    "_id": "$v",
                    "cnt": {"$count": {}},
                    "sum_cnt": {"$sum": 1},
                }
            }
        ],
        expected=[
            {"_id": "a", "cnt": 2, "sum_cnt": 2},
            {"_id": "b", "cnt": 1, "sum_cnt": 1},
        ],
        msg="$count should produce the same result as $sum: 1",
    ),
]

# Property [Array Accumulation Across Documents]: $setUnion unions arrays and
# $concatArrays concatenates arrays across multiple documents within a group.
GROUP_ARRAY_ACCUMULATION_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="setunion_accumulates_across_docs",
        docs=[
            {"_id": 1, "v": "a", "x": [1, 2]},
            {"_id": 2, "v": "a", "x": [2, 3]},
            {"_id": 3, "v": "a", "x": [3, 4]},
        ],
        pipeline=[
            {"$group": {"_id": "$v", "r": {"$setUnion": "$x"}}},
            {"$project": {"r": {"$sortArray": {"input": "$r", "sortBy": 1}}}},
        ],
        expected=[{"_id": "a", "r": [1, 2, 3, 4]}],
        msg="$setUnion should union arrays across multiple documents",
    ),
    StageTestCase(
        id="concatarrays_accumulates_across_docs",
        docs=[
            {"_id": 1, "v": "a", "x": [1, 2]},
            {"_id": 2, "v": "a", "x": [3, 4]},
            {"_id": 3, "v": "a", "x": [5]},
        ],
        pipeline=[{"$group": {"_id": "$v", "r": {"$concatArrays": "$x"}}}],
        expected=[{"_id": "a", "r": [1, 2, 3, 4, 5]}],
        msg="$concatArrays should concatenate arrays across multiple documents",
    ),
]

# Property [Accumulator Field Name Flexibility]: empty string, _id (shadowing
# the group key via SON), duplicate names (last definition wins via SON),
# Unicode, emoji, spaces, tabs, long names, __proto__, constructor, $ in
# non-initial position, control characters, NBSP, zero-width space, and BOM
# are all accepted as accumulator field names.
GROUP_ACCUMULATOR_FIELD_NAME_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="empty_string_field_name",
        docs=[{"_id": 1, "v": "a", "x": 5}],
        pipeline=[{"$group": {"_id": "$v", "": {"$sum": "$x"}}}],
        expected=[{"_id": "a", "": 5}],
        msg="Empty string should be accepted as an accumulator field name",
    ),
    StageTestCase(
        id="id_shadows_group_key",
        docs=[{"_id": 1, "v": "a", "x": 10}, {"_id": 2, "v": "a", "x": 20}],
        pipeline=[{"$group": SON([("_id", "$v"), ("_id", {"$sum": 1})])}],
        expected=[{"_id": 1}],
        msg="_id as accumulator field name shadows the group key (last definition wins via SON)",
    ),
    StageTestCase(
        id="duplicate_field_last_wins",
        docs=[{"_id": 1, "v": "a", "x": 10, "y": 100}],
        pipeline=[
            {
                "$group": SON(
                    [
                        ("_id", "$v"),
                        ("total", {"$sum": "$x"}),
                        ("total", {"$sum": "$y"}),
                    ]
                )
            }
        ],
        expected=[{"_id": "a", "total": 100}],
        msg="Duplicate accumulator field names: last definition wins via SON",
    ),
    StageTestCase(
        id="unicode_field_name",
        docs=[{"_id": 1, "v": "a", "x": 5}],
        pipeline=[{"$group": {"_id": "$v", "\u00e9": {"$sum": "$x"}}}],
        expected=[{"_id": "a", "\u00e9": 5}],
        msg="Unicode characters should be accepted as accumulator field names",
    ),
    StageTestCase(
        id="emoji_field_name",
        docs=[{"_id": 1, "v": "a", "x": 5}],
        pipeline=[{"$group": {"_id": "$v", "\U0001f600": {"$sum": "$x"}}}],
        expected=[{"_id": "a", "\U0001f600": 5}],
        msg="Emoji should be accepted as accumulator field names",
    ),
    StageTestCase(
        id="space_field_name",
        docs=[{"_id": 1, "v": "a", "x": 5}],
        pipeline=[{"$group": {"_id": "$v", " ": {"$sum": "$x"}}}],
        expected=[{"_id": "a", " ": 5}],
        msg="Space should be accepted as an accumulator field name",
    ),
    StageTestCase(
        id="tab_field_name",
        docs=[{"_id": 1, "v": "a", "x": 5}],
        pipeline=[{"$group": {"_id": "$v", "\t": {"$sum": "$x"}}}],
        expected=[{"_id": "a", "\t": 5}],
        msg="Tab should be accepted as an accumulator field name",
    ),
    StageTestCase(
        id="long_field_name",
        docs=[{"_id": 1, "v": "a", "x": 5}],
        pipeline=[{"$group": {"_id": "$v", "a" * 200: {"$sum": "$x"}}}],
        expected=[{"_id": "a", "a" * 200: 5}],
        msg="Long field names (200 chars) should be accepted",
    ),
    StageTestCase(
        id="proto_field_name",
        docs=[{"_id": 1, "v": "a", "x": 5}],
        pipeline=[{"$group": {"_id": "$v", "__proto__": {"$sum": "$x"}}}],
        expected=[{"_id": "a", "__proto__": 5}],
        msg="__proto__ should be accepted as an accumulator field name",
    ),
    StageTestCase(
        id="constructor_field_name",
        docs=[{"_id": 1, "v": "a", "x": 5}],
        pipeline=[{"$group": {"_id": "$v", "constructor": {"$sum": "$x"}}}],
        expected=[{"_id": "a", "constructor": 5}],
        msg="constructor should be accepted as an accumulator field name",
    ),
    StageTestCase(
        id="dollar_non_initial_field_name",
        docs=[{"_id": 1, "v": "a", "x": 5}],
        pipeline=[{"$group": {"_id": "$v", "a$b": {"$sum": "$x"}}}],
        expected=[{"_id": "a", "a$b": 5}],
        msg="$ in non-initial position should be accepted in accumulator field names",
    ),
    StageTestCase(
        id="control_char_field_name",
        docs=[{"_id": 1, "v": "a", "x": 5}],
        pipeline=[{"$group": {"_id": "$v", "\x01": {"$sum": "$x"}}}],
        expected=[{"_id": "a", "\x01": 5}],
        msg="Control characters should be accepted as accumulator field names",
    ),
    StageTestCase(
        id="nbsp_field_name",
        docs=[{"_id": 1, "v": "a", "x": 5}],
        pipeline=[{"$group": {"_id": "$v", "\u00a0": {"$sum": "$x"}}}],
        expected=[{"_id": "a", "\u00a0": 5}],
        msg="NBSP should be accepted as an accumulator field name",
    ),
    StageTestCase(
        id="zero_width_space_field_name",
        docs=[{"_id": 1, "v": "a", "x": 5}],
        pipeline=[{"$group": {"_id": "$v", "\u200b": {"$sum": "$x"}}}],
        expected=[{"_id": "a", "\u200b": 5}],
        msg="Zero-width space should be accepted as an accumulator field name",
    ),
    StageTestCase(
        id="bom_field_name",
        docs=[{"_id": 1, "v": "a", "x": 5}],
        pipeline=[{"$group": {"_id": "$v", "\ufeff": {"$sum": "$x"}}}],
        expected=[{"_id": "a", "\ufeff": 5}],
        msg="BOM should be accepted as an accumulator field name",
    ),
]

# Property [Accumulator References Input Fields]: accumulator expressions
# reference input document fields, not sibling accumulator output fields.
GROUP_ACCUMULATOR_INPUT_REF_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="accumulator_refs_input_not_sibling",
        docs=[
            {"_id": 1, "v": "a", "total": 99, "x": 5},
            {"_id": 2, "v": "a", "total": 88, "x": 3},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$v",
                    "computed_total": {"$sum": "$x"},
                    "ref_total": {"$sum": "$total"},
                }
            }
        ],
        expected=[{"_id": "a", "computed_total": 8, "ref_total": 187}],
        msg=(
            "Accumulator expressions should reference input document fields,"
            " not sibling accumulator output fields"
        ),
    ),
]

# Property [$stdDevPop/$stdDevSamp Behavior]: $stdDevPop and $stdDevSamp with
# all identical values produce zero, and $stdDevSamp with a single value
# produces null (sample standard deviation is undefined for n=1).
GROUP_STDDEV_BEHAVIOR_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="stddevpop_all_same_produces_zero",
        docs=[{"_id": 1, "v": 5}, {"_id": 2, "v": 5}],
        pipeline=[{"$group": {"_id": None, "r": {"$stdDevPop": "$v"}}}],
        expected=[{"_id": None, "r": DOUBLE_ZERO}],
        msg="$stdDevPop with all same values should produce 0.0",
    ),
    StageTestCase(
        id="stddevsamp_all_same_produces_zero",
        docs=[{"_id": 1, "v": 5}, {"_id": 2, "v": 5}],
        pipeline=[{"$group": {"_id": None, "r": {"$stdDevSamp": "$v"}}}],
        expected=[{"_id": None, "r": DOUBLE_ZERO}],
        msg="$stdDevSamp with all same values should produce 0.0",
    ),
    StageTestCase(
        id="stddevsamp_single_value_produces_null",
        docs=[{"_id": 1, "v": 5}],
        pipeline=[{"$group": {"_id": None, "r": {"$stdDevSamp": "$v"}}}],
        expected=[{"_id": None, "r": None}],
        msg="$stdDevSamp with a single value should produce null",
    ),
]


GROUP_ACCUMULATOR_SPEC_TESTS = (
    GROUP_ACCUMULATOR_FIELD_ACCEPTANCE_TESTS
    + GROUP_VALID_ACCUMULATOR_OPERATORS_TESTS
    + GROUP_COUNT_SUM_EQUIVALENCE_TESTS
    + GROUP_ARRAY_ACCUMULATION_TESTS
    + GROUP_ACCUMULATOR_FIELD_NAME_TESTS
    + GROUP_ACCUMULATOR_INPUT_REF_TESTS
    + GROUP_STDDEV_BEHAVIOR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(GROUP_ACCUMULATOR_SPEC_TESTS))
def test_group_accumulators(collection, test_case: StageTestCase):
    """Test $group stage - accumulator operators."""
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
