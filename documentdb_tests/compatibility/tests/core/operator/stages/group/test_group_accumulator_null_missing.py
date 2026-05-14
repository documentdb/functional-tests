"""Aggregation $group stage tests - accumulator null and missing handling."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import (
    assertResult,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Accumulator Null and Missing - Ignoring Accumulators]: $sum, $avg,
# $min, $max, $first, $last, $push, $addToSet, $mergeObjects, $stdDevPop,
# $stdDevSamp, $firstN, $lastN, $maxN, $minN, $top, $bottom, $topN, $bottomN,
# $median, and $percentile each handle null and missing inputs
# according to their documented semantics without producing an error.
GROUP_ACCUMULATOR_NULL_MISSING_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="sum_null_and_missing_ignored",
        docs=[{"_id": 1, "v": None}, {"_id": 2}, {"_id": 3, "v": 10}],
        pipeline=[{"$group": {"_id": None, "r": {"$sum": "$v"}}}],
        expected=[{"_id": None, "r": 10}],
        msg="$sum should ignore null and missing values",
    ),
    StageTestCase(
        id="sum_all_null_produces_zero",
        docs=[{"_id": 1, "v": None}, {"_id": 2, "v": None}],
        pipeline=[{"$group": {"_id": None, "r": {"$sum": "$v"}}}],
        expected=[{"_id": None, "r": 0}],
        msg="$sum with all-null input should produce 0",
    ),
    StageTestCase(
        id="sum_all_missing_produces_zero",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[{"$group": {"_id": None, "r": {"$sum": "$v"}}}],
        expected=[{"_id": None, "r": 0}],
        msg="$sum with all-missing input should produce 0",
    ),
    StageTestCase(
        id="avg_excludes_null_missing_bool",
        docs=[
            {"_id": 1, "v": None},
            {"_id": 2},
            {"_id": 3, "v": True},
            {"_id": 4, "v": 10},
        ],
        pipeline=[{"$group": {"_id": None, "r": {"$avg": "$v"}}}],
        expected=[{"_id": None, "r": 10.0}],
        msg="$avg should exclude null, missing, and boolean values",
    ),
    StageTestCase(
        id="avg_all_null_produces_null",
        docs=[{"_id": 1, "v": None}, {"_id": 2, "v": None}],
        pipeline=[{"$group": {"_id": None, "r": {"$avg": "$v"}}}],
        expected=[{"_id": None, "r": None}],
        msg="$avg with all-null input should produce null",
    ),
    StageTestCase(
        id="avg_all_missing_produces_null",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[{"$group": {"_id": None, "r": {"$avg": "$v"}}}],
        expected=[{"_id": None, "r": None}],
        msg="$avg with all-missing input should produce null",
    ),
    StageTestCase(
        id="avg_all_bool_produces_null",
        docs=[{"_id": 1, "v": True}, {"_id": 2, "v": False}],
        pipeline=[{"$group": {"_id": None, "r": {"$avg": "$v"}}}],
        expected=[{"_id": None, "r": None}],
        msg="$avg with all-boolean input should produce null",
    ),
    StageTestCase(
        id="min_max_null_and_missing_ignored",
        docs=[{"_id": 1, "v": None}, {"_id": 2}, {"_id": 3, "v": 5}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "mn": {"$min": "$v"},
                    "mx": {"$max": "$v"},
                }
            }
        ],
        expected=[{"_id": None, "mn": 5, "mx": 5}],
        msg="$min and $max should ignore null and missing values",
    ),
    StageTestCase(
        id="min_max_all_null_produces_null",
        docs=[{"_id": 1, "v": None}, {"_id": 2, "v": None}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "mn": {"$min": "$v"},
                    "mx": {"$max": "$v"},
                }
            }
        ],
        expected=[{"_id": None, "mn": None, "mx": None}],
        msg="$min and $max with all-null input should produce null",
    ),
    StageTestCase(
        id="min_max_all_missing_produces_null",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "mn": {"$min": "$v"},
                    "mx": {"$max": "$v"},
                }
            }
        ],
        expected=[{"_id": None, "mn": None, "mx": None}],
        msg="$min and $max with all-missing input should produce null",
    ),
    StageTestCase(
        id="first_missing_produces_null",
        docs=[{"_id": 1}, {"_id": 2, "v": 10}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "r": {"$first": "$v"}}},
        ],
        expected=[{"_id": None, "r": None}],
        msg="$first on a missing field should produce null",
    ),
    StageTestCase(
        id="last_missing_produces_null",
        docs=[{"_id": 1, "v": 10}, {"_id": 2}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "r": {"$last": "$v"}}},
        ],
        expected=[{"_id": None, "r": None}],
        msg="$last on a missing field should produce null",
    ),
    StageTestCase(
        id="push_null_included_missing_excluded",
        docs=[{"_id": 1, "v": None}, {"_id": 2}, {"_id": 3, "v": 5}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "r": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "r": [None, 5]}],
        msg="$push should include null and exclude missing values",
    ),
    StageTestCase(
        id="push_all_missing_produces_empty",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[{"$group": {"_id": None, "r": {"$push": "$v"}}}],
        expected=[{"_id": None, "r": []}],
        msg="$push with all-missing input should produce an empty array",
    ),
    StageTestCase(
        id="addtoset_null_included_missing_excluded",
        docs=[
            {"_id": 1, "v": None},
            {"_id": 2},
            {"_id": 3, "v": None},
            {"_id": 4, "v": 5},
        ],
        pipeline=[
            {"$group": {"_id": None, "r": {"$addToSet": "$v"}}},
            {"$project": {"r": {"$sortArray": {"input": "$r", "sortBy": 1}}}},
        ],
        expected=[{"_id": None, "r": [None, 5]}],
        msg="$addToSet should include null (deduplicated to one) and exclude missing values",
    ),
    StageTestCase(
        id="addtoset_all_missing_produces_empty",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[{"$group": {"_id": None, "r": {"$addToSet": "$v"}}}],
        expected=[{"_id": None, "r": []}],
        msg="$addToSet with all-missing input should produce an empty array",
    ),
    StageTestCase(
        id="mergeobjects_null_skipped",
        docs=[
            {"_id": 1, "v": None},
            {"_id": 2},
            {"_id": 3, "v": {"a": 1}},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "r": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "r": {"a": 1}}],
        msg="$mergeObjects should skip null values",
    ),
    StageTestCase(
        id="mergeobjects_all_null_produces_empty_object",
        docs=[{"_id": 1, "v": None}, {"_id": 2, "v": None}],
        pipeline=[{"$group": {"_id": None, "r": {"$mergeObjects": "$v"}}}],
        expected=[{"_id": None, "r": {}}],
        msg="$mergeObjects with all-null input should produce {}",
    ),
    StageTestCase(
        id="mergeobjects_all_missing_produces_empty_object",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[{"$group": {"_id": None, "r": {"$mergeObjects": "$v"}}}],
        expected=[{"_id": None, "r": {}}],
        msg="$mergeObjects with all-missing input should produce {}",
    ),
    StageTestCase(
        id="setunion_all_missing_produces_empty",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[{"$group": {"_id": None, "r": {"$setUnion": "$v"}}}],
        expected=[{"_id": None, "r": []}],
        msg="$setUnion with all-missing input should produce an empty array",
    ),
    StageTestCase(
        id="concatarrays_all_missing_produces_empty",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[{"$group": {"_id": None, "r": {"$concatArrays": "$v"}}}],
        expected=[{"_id": None, "r": []}],
        msg="$concatArrays with all-missing input should produce an empty array",
    ),
    StageTestCase(
        id="stddevpop_all_null_produces_null",
        docs=[{"_id": 1, "v": None}, {"_id": 2, "v": None}],
        pipeline=[{"$group": {"_id": None, "r": {"$stdDevPop": "$v"}}}],
        expected=[{"_id": None, "r": None}],
        msg="$stdDevPop with all-null input should produce null",
    ),
    StageTestCase(
        id="stddevsamp_all_null_produces_null",
        docs=[{"_id": 1, "v": None}, {"_id": 2, "v": None}],
        pipeline=[{"$group": {"_id": None, "r": {"$stdDevSamp": "$v"}}}],
        expected=[{"_id": None, "r": None}],
        msg="$stdDevSamp with all-null input should produce null",
    ),
    StageTestCase(
        id="top_all_null_output_produces_none",
        docs=[{"_id": 1, "v": None, "s": 1}, {"_id": 2, "v": None, "s": 2}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {"$top": {"sortBy": {"s": 1}, "output": "$v"}},
                }
            }
        ],
        expected=[{"_id": None, "r": None}],
        msg="$top with all-null output field should produce None",
    ),
    StageTestCase(
        id="top_all_missing_output_produces_none",
        docs=[{"_id": 1, "s": 1}, {"_id": 2, "s": 2}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {"$top": {"sortBy": {"s": 1}, "output": "$v"}},
                }
            }
        ],
        expected=[{"_id": None, "r": None}],
        msg="$top with all-missing output field should produce None",
    ),
    StageTestCase(
        id="bottom_all_null_output_produces_none",
        docs=[{"_id": 1, "v": None, "s": 1}, {"_id": 2, "v": None, "s": 2}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {"$bottom": {"sortBy": {"s": 1}, "output": "$v"}},
                }
            }
        ],
        expected=[{"_id": None, "r": None}],
        msg="$bottom with all-null output field should produce None",
    ),
    StageTestCase(
        id="bottom_all_missing_output_produces_none",
        docs=[{"_id": 1, "s": 1}, {"_id": 2, "s": 2}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {"$bottom": {"sortBy": {"s": 1}, "output": "$v"}},
                }
            }
        ],
        expected=[{"_id": None, "r": None}],
        msg="$bottom with all-missing output field should produce None",
    ),
    StageTestCase(
        id="topn_null_and_missing_included",
        docs=[
            {"_id": 1, "v": None, "s": 2},
            {"_id": 2, "s": 1},
            {"_id": 3, "v": "hello", "s": 3},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {
                        "$topN": {
                            "sortBy": {"s": 1},
                            "output": "$v",
                            "n": 3,
                        }
                    },
                }
            }
        ],
        expected=[{"_id": None, "r": [None, None, "hello"]}],
        msg="$topN should include null and missing values as None in the output array",
    ),
    StageTestCase(
        id="bottomn_null_and_missing_included",
        docs=[
            {"_id": 1, "v": None, "s": 2},
            {"_id": 2, "s": 1},
            {"_id": 3, "v": "hello", "s": 3},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {
                        "$bottomN": {
                            "sortBy": {"s": 1},
                            "output": "$v",
                            "n": 3,
                        }
                    },
                }
            }
        ],
        expected=[{"_id": None, "r": [None, None, "hello"]}],
        msg="$bottomN should include null and missing values as None in the output array",
    ),
    StageTestCase(
        id="firstn_null_and_missing_included",
        docs=[{"_id": 1, "v": None}, {"_id": 2}, {"_id": 3, "v": 5}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": None,
                    "r": {"$firstN": {"input": "$v", "n": 3}},
                }
            },
        ],
        expected=[{"_id": None, "r": [None, None, 5]}],
        msg="$firstN should include null and missing values as None in the output array",
    ),
    StageTestCase(
        id="lastn_null_and_missing_included",
        docs=[{"_id": 1, "v": None}, {"_id": 2}, {"_id": 3, "v": 5}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": None,
                    "r": {"$lastN": {"input": "$v", "n": 3}},
                }
            },
        ],
        expected=[{"_id": None, "r": [None, None, 5]}],
        msg="$lastN should include null and missing values as None in the output array",
    ),
    StageTestCase(
        id="maxn_null_and_missing_excluded",
        docs=[
            {"_id": 1, "v": None},
            {"_id": 2},
            {"_id": 3, "v": 5},
            {"_id": 4, "v": 3},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {"$maxN": {"input": "$v", "n": 10}},
                }
            }
        ],
        expected=[{"_id": None, "r": [5, 3]}],
        msg="$maxN should exclude null and missing values from the output",
    ),
    StageTestCase(
        id="minn_null_and_missing_excluded",
        docs=[
            {"_id": 1, "v": None},
            {"_id": 2},
            {"_id": 3, "v": 5},
            {"_id": 4, "v": 3},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {"$minN": {"input": "$v", "n": 10}},
                }
            }
        ],
        expected=[{"_id": None, "r": [3, 5]}],
        msg="$minN should exclude null and missing values from the output",
    ),
    StageTestCase(
        id="maxn_all_null_produces_empty",
        docs=[{"_id": 1, "v": None}, {"_id": 2, "v": None}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {"$maxN": {"input": "$v", "n": 10}},
                }
            }
        ],
        expected=[{"_id": None, "r": []}],
        msg="$maxN with all-null input should produce an empty array",
    ),
    StageTestCase(
        id="maxn_all_missing_produces_empty",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {"$maxN": {"input": "$v", "n": 10}},
                }
            }
        ],
        expected=[{"_id": None, "r": []}],
        msg="$maxN with all-missing input should produce an empty array",
    ),
    StageTestCase(
        id="minn_all_null_produces_empty",
        docs=[{"_id": 1, "v": None}, {"_id": 2, "v": None}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {"$minN": {"input": "$v", "n": 10}},
                }
            }
        ],
        expected=[{"_id": None, "r": []}],
        msg="$minN with all-null input should produce an empty array",
    ),
    StageTestCase(
        id="minn_all_missing_produces_empty",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {"$minN": {"input": "$v", "n": 10}},
                }
            }
        ],
        expected=[{"_id": None, "r": []}],
        msg="$minN with all-missing input should produce an empty array",
    ),
    StageTestCase(
        id="median_ignores_null_missing_nonnumeric",
        docs=[
            {"_id": 1, "v": None},
            {"_id": 2},
            {"_id": 3, "v": "hello"},
            {"_id": 4, "v": 10},
            {"_id": 5, "v": 20},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {
                        "$median": {
                            "input": "$v",
                            "method": "approximate",
                        }
                    },
                }
            }
        ],
        expected=[{"_id": None, "r": 10.0}],
        msg="$median should silently ignore null, missing, and non-numeric values",
    ),
    StageTestCase(
        id="median_all_null_produces_none",
        docs=[{"_id": 1, "v": None}, {"_id": 2, "v": None}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {
                        "$median": {
                            "input": "$v",
                            "method": "approximate",
                        }
                    },
                }
            }
        ],
        expected=[{"_id": None, "r": None}],
        msg="$median with all-null input should produce None",
    ),
    StageTestCase(
        id="median_all_missing_produces_none",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {
                        "$median": {
                            "input": "$v",
                            "method": "approximate",
                        }
                    },
                }
            }
        ],
        expected=[{"_id": None, "r": None}],
        msg="$median with all-missing input should produce None",
    ),
    StageTestCase(
        id="percentile_ignores_null_missing_nonnumeric",
        docs=[
            {"_id": 1, "v": None},
            {"_id": 2},
            {"_id": 3, "v": "hello"},
            {"_id": 4, "v": 10},
            {"_id": 5, "v": 20},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {
                        "$percentile": {
                            "input": "$v",
                            "p": [0.5],
                            "method": "approximate",
                        }
                    },
                }
            }
        ],
        expected=[{"_id": None, "r": [10.0]}],
        msg="$percentile should silently ignore null, missing, and non-numeric values",
    ),
    StageTestCase(
        id="percentile_all_null_produces_list_none",
        docs=[{"_id": 1, "v": None}, {"_id": 2, "v": None}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {
                        "$percentile": {
                            "input": "$v",
                            "p": [0.5],
                            "method": "approximate",
                        }
                    },
                }
            }
        ],
        expected=[{"_id": None, "r": [None]}],
        msg="$percentile with all-null input should produce [None]",
    ),
    StageTestCase(
        id="percentile_all_missing_produces_list_none",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {
                        "$percentile": {
                            "input": "$v",
                            "p": [0.5],
                            "method": "approximate",
                        }
                    },
                }
            }
        ],
        expected=[{"_id": None, "r": [None]}],
        msg="$percentile with all-missing input should produce [None]",
    ),
]

# Property [$top/$bottom Sort Key Null/Missing Ordering]: null and missing
# sort key values are treated as the lowest value in ascending order for
# $top, $bottom, $topN, and $bottomN.
GROUP_TOP_BOTTOM_SORT_KEY_NULL_MISSING_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="top_null_sort_is_lowest",
        docs=[
            {"_id": 1, "v": "a", "s": None},
            {"_id": 2, "v": "b", "s": 1},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {"$top": {"sortBy": {"s": 1}, "output": "$v"}},
                }
            }
        ],
        expected=[{"_id": None, "r": "a"}],
        msg="$top should treat null sort field as lowest in ascending order",
    ),
    StageTestCase(
        id="top_missing_sort_is_lowest",
        docs=[
            {"_id": 1, "v": "a"},
            {"_id": 2, "v": "b", "s": 1},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {"$top": {"sortBy": {"s": 1}, "output": "$v"}},
                }
            }
        ],
        expected=[{"_id": None, "r": "a"}],
        msg="$top should treat missing sort field as lowest in ascending order",
    ),
    StageTestCase(
        id="bottom_null_sort_is_lowest",
        docs=[
            {"_id": 1, "v": "a", "s": None},
            {"_id": 2, "v": "b", "s": 1},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {"$bottom": {"sortBy": {"s": 1}, "output": "$v"}},
                }
            }
        ],
        expected=[{"_id": None, "r": "b"}],
        msg="$bottom should treat null sort field as lowest in ascending order",
    ),
    StageTestCase(
        id="bottom_missing_sort_is_lowest",
        docs=[
            {"_id": 1, "v": "a"},
            {"_id": 2, "v": "b", "s": 1},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {"$bottom": {"sortBy": {"s": 1}, "output": "$v"}},
                }
            }
        ],
        expected=[{"_id": None, "r": "b"}],
        msg="$bottom should treat missing sort field as lowest in ascending order",
    ),
    StageTestCase(
        id="topn_null_sort_is_lowest",
        docs=[
            {"_id": 1, "v": "a", "s": None},
            {"_id": 2, "v": "b", "s": 1},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {
                        "$topN": {
                            "sortBy": {"s": 1},
                            "output": "$v",
                            "n": 1,
                        }
                    },
                }
            }
        ],
        expected=[{"_id": None, "r": ["a"]}],
        msg="$topN should treat null sort field as lowest in ascending order",
    ),
    StageTestCase(
        id="topn_missing_sort_is_lowest",
        docs=[
            {"_id": 1, "v": "a"},
            {"_id": 2, "v": "b", "s": 1},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {
                        "$topN": {
                            "sortBy": {"s": 1},
                            "output": "$v",
                            "n": 1,
                        }
                    },
                }
            }
        ],
        expected=[{"_id": None, "r": ["a"]}],
        msg="$topN should treat missing sort field as lowest in ascending order",
    ),
    StageTestCase(
        id="bottomn_null_sort_is_lowest",
        docs=[
            {"_id": 1, "v": "a", "s": None},
            {"_id": 2, "v": "b", "s": 1},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {
                        "$bottomN": {
                            "sortBy": {"s": 1},
                            "output": "$v",
                            "n": 1,
                        }
                    },
                }
            }
        ],
        expected=[{"_id": None, "r": ["b"]}],
        msg="$bottomN should treat null sort field as lowest in ascending order",
    ),
    StageTestCase(
        id="bottomn_missing_sort_is_lowest",
        docs=[
            {"_id": 1, "v": "a"},
            {"_id": 2, "v": "b", "s": 1},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": {
                        "$bottomN": {
                            "sortBy": {"s": 1},
                            "output": "$v",
                            "n": 1,
                        }
                    },
                }
            }
        ],
        expected=[{"_id": None, "r": ["b"]}],
        msg="$bottomN should treat missing sort field as lowest in ascending order",
    ),
]


GROUP_ACCUMULATOR_NULL_MISSING_SPEC_TESTS = (
    GROUP_ACCUMULATOR_NULL_MISSING_TESTS + GROUP_TOP_BOTTOM_SORT_KEY_NULL_MISSING_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(GROUP_ACCUMULATOR_NULL_MISSING_SPEC_TESTS))
def test_group_accumulator_null_missing(collection, test_case: StageTestCase):
    """Test $group stage - accumulator null and missing handling."""
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
