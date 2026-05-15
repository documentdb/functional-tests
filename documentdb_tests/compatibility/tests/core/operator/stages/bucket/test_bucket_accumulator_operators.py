"""Tests for $bucket accumulator operator support."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Accumulator Operator Support]: each accumulator operator
# functions correctly inside $bucket output as a container.
BUCKET_ACCUMULATOR_OPERATOR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "acc_sum",
        docs=[
            {"_id": 1, "x": 1, "v": 10},
            {"_id": 2, "x": 1, "v": 20},
            {"_id": 3, "x": 1, "v": 30},
        ],
        pipeline=[
            {"$bucket": {"groupBy": "$x", "boundaries": [0, 10], "output": {"r": {"$sum": "$v"}}}}
        ],
        expected=[{"_id": 0, "r": 60}],
        msg="$bucket output should support $sum",
    ),
    StageTestCase(
        "acc_avg",
        docs=[
            {"_id": 1, "x": 1, "v": 10},
            {"_id": 2, "x": 1, "v": 20},
            {"_id": 3, "x": 1, "v": 30},
        ],
        pipeline=[
            {"$bucket": {"groupBy": "$x", "boundaries": [0, 10], "output": {"r": {"$avg": "$v"}}}}
        ],
        expected=[{"_id": 0, "r": 20.0}],
        msg="$bucket output should support $avg",
    ),
    StageTestCase(
        "acc_min",
        docs=[
            {"_id": 1, "x": 1, "v": 10},
            {"_id": 2, "x": 1, "v": 20},
            {"_id": 3, "x": 1, "v": 30},
        ],
        pipeline=[
            {"$bucket": {"groupBy": "$x", "boundaries": [0, 10], "output": {"r": {"$min": "$v"}}}}
        ],
        expected=[{"_id": 0, "r": 10}],
        msg="$bucket output should support $min",
    ),
    StageTestCase(
        "acc_max",
        docs=[
            {"_id": 1, "x": 1, "v": 10},
            {"_id": 2, "x": 1, "v": 20},
            {"_id": 3, "x": 1, "v": 30},
        ],
        pipeline=[
            {"$bucket": {"groupBy": "$x", "boundaries": [0, 10], "output": {"r": {"$max": "$v"}}}}
        ],
        expected=[{"_id": 0, "r": 30}],
        msg="$bucket output should support $max",
    ),
    StageTestCase(
        "acc_first",
        docs=[
            {"_id": 1, "x": 1, "v": 10},
            {"_id": 2, "x": 1, "v": 20},
            {"_id": 3, "x": 1, "v": 30},
        ],
        pipeline=[
            {"$bucket": {"groupBy": "$x", "boundaries": [0, 10], "output": {"r": {"$first": "$v"}}}}
        ],
        expected=[{"_id": 0, "r": 10}],
        msg="$bucket output should support $first",
    ),
    StageTestCase(
        "acc_last",
        docs=[
            {"_id": 1, "x": 1, "v": 10},
            {"_id": 2, "x": 1, "v": 20},
            {"_id": 3, "x": 1, "v": 30},
        ],
        pipeline=[
            {"$bucket": {"groupBy": "$x", "boundaries": [0, 10], "output": {"r": {"$last": "$v"}}}}
        ],
        expected=[{"_id": 0, "r": 30}],
        msg="$bucket output should support $last",
    ),
    StageTestCase(
        "acc_push",
        docs=[
            {"_id": 1, "x": 1, "v": 10},
            {"_id": 2, "x": 1, "v": 20},
            {"_id": 3, "x": 1, "v": 30},
        ],
        pipeline=[
            {"$bucket": {"groupBy": "$x", "boundaries": [0, 10], "output": {"r": {"$push": "$v"}}}}
        ],
        expected=[{"_id": 0, "r": [10, 20, 30]}],
        msg="$bucket output should support $push",
    ),
    StageTestCase(
        "acc_count",
        docs=[
            {"_id": 1, "x": 1, "v": 10},
            {"_id": 2, "x": 1, "v": 20},
            {"_id": 3, "x": 1, "v": 30},
        ],
        pipeline=[
            {"$bucket": {"groupBy": "$x", "boundaries": [0, 10], "output": {"r": {"$count": {}}}}}
        ],
        expected=[{"_id": 0, "r": 3}],
        msg="$bucket output should support $count",
    ),
    StageTestCase(
        "acc_stdDevPop",
        docs=[
            {"_id": 1, "x": 1, "v": 10},
            {"_id": 2, "x": 1, "v": 20},
            {"_id": 3, "x": 1, "v": 30},
        ],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": {"r": {"$stdDevPop": "$v"}},
                }
            }
        ],
        expected=[{"_id": 0, "r": 8.16496580927726}],
        msg="$bucket output should support $stdDevPop",
    ),
    StageTestCase(
        "acc_stdDevSamp",
        docs=[
            {"_id": 1, "x": 1, "v": 10},
            {"_id": 2, "x": 1, "v": 20},
            {"_id": 3, "x": 1, "v": 30},
        ],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": {"r": {"$stdDevSamp": "$v"}},
                }
            }
        ],
        expected=[{"_id": 0, "r": 10.0}],
        msg="$bucket output should support $stdDevSamp",
    ),
    StageTestCase(
        "acc_mergeObjects",
        docs=[
            {"_id": 1, "x": 1, "v": 10},
            {"_id": 2, "x": 1, "v": 20},
            {"_id": 3, "x": 1, "v": 30},
        ],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": {"r": {"$mergeObjects": {"$cond": [True, {"val": "$v"}, {}]}}},
                }
            }
        ],
        expected=[{"_id": 0, "r": {"val": 30}}],
        msg="$bucket output should support $mergeObjects",
    ),
    StageTestCase(
        "acc_top",
        docs=[
            {"_id": 1, "x": 1, "v": 10},
            {"_id": 2, "x": 1, "v": 20},
            {"_id": 3, "x": 1, "v": 30},
        ],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": {"r": {"$top": {"sortBy": {"v": 1}, "output": "$v"}}},
                }
            }
        ],
        expected=[{"_id": 0, "r": 10}],
        msg="$bucket output should support $top",
    ),
    StageTestCase(
        "acc_bottom",
        docs=[
            {"_id": 1, "x": 1, "v": 10},
            {"_id": 2, "x": 1, "v": 20},
            {"_id": 3, "x": 1, "v": 30},
        ],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": {"r": {"$bottom": {"sortBy": {"v": 1}, "output": "$v"}}},
                }
            }
        ],
        expected=[{"_id": 0, "r": 30}],
        msg="$bucket output should support $bottom",
    ),
    StageTestCase(
        "acc_topN",
        docs=[
            {"_id": 1, "x": 1, "v": 10},
            {"_id": 2, "x": 1, "v": 20},
            {"_id": 3, "x": 1, "v": 30},
        ],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": {"r": {"$topN": {"n": 2, "sortBy": {"v": 1}, "output": "$v"}}},
                }
            }
        ],
        expected=[{"_id": 0, "r": [10, 20]}],
        msg="$bucket output should support $topN",
    ),
    StageTestCase(
        "acc_bottomN",
        docs=[
            {"_id": 1, "x": 1, "v": 10},
            {"_id": 2, "x": 1, "v": 20},
            {"_id": 3, "x": 1, "v": 30},
        ],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": {"r": {"$bottomN": {"n": 2, "sortBy": {"v": 1}, "output": "$v"}}},
                }
            }
        ],
        expected=[{"_id": 0, "r": [20, 30]}],
        msg="$bucket output should support $bottomN",
    ),
    StageTestCase(
        "acc_firstN",
        docs=[
            {"_id": 1, "x": 1, "v": 10},
            {"_id": 2, "x": 1, "v": 20},
            {"_id": 3, "x": 1, "v": 30},
        ],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": {"r": {"$firstN": {"n": 2, "input": "$v"}}},
                }
            }
        ],
        expected=[{"_id": 0, "r": [10, 20]}],
        msg="$bucket output should support $firstN",
    ),
    StageTestCase(
        "acc_lastN",
        docs=[
            {"_id": 1, "x": 1, "v": 10},
            {"_id": 2, "x": 1, "v": 20},
            {"_id": 3, "x": 1, "v": 30},
        ],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": {"r": {"$lastN": {"n": 2, "input": "$v"}}},
                }
            }
        ],
        expected=[{"_id": 0, "r": [20, 30]}],
        msg="$bucket output should support $lastN",
    ),
    StageTestCase(
        "acc_maxN",
        docs=[
            {"_id": 1, "x": 1, "v": 10},
            {"_id": 2, "x": 1, "v": 20},
            {"_id": 3, "x": 1, "v": 30},
        ],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": {"r": {"$maxN": {"n": 2, "input": "$v"}}},
                }
            }
        ],
        expected=[{"_id": 0, "r": [30, 20]}],
        msg="$bucket output should support $maxN",
    ),
    StageTestCase(
        "acc_minN",
        docs=[
            {"_id": 1, "x": 1, "v": 10},
            {"_id": 2, "x": 1, "v": 20},
            {"_id": 3, "x": 1, "v": 30},
        ],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": {"r": {"$minN": {"n": 2, "input": "$v"}}},
                }
            }
        ],
        expected=[{"_id": 0, "r": [10, 20]}],
        msg="$bucket output should support $minN",
    ),
    StageTestCase(
        "acc_median",
        docs=[
            {"_id": 1, "x": 1, "v": 10},
            {"_id": 2, "x": 1, "v": 20},
            {"_id": 3, "x": 1, "v": 30},
        ],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": {"r": {"$median": {"input": "$v", "method": "approximate"}}},
                }
            }
        ],
        expected=[{"_id": 0, "r": 20.0}],
        msg="$bucket output should support $median",
    ),
    StageTestCase(
        "acc_percentile",
        docs=[
            {"_id": 1, "x": 1, "v": 10},
            {"_id": 2, "x": 1, "v": 20},
            {"_id": 3, "x": 1, "v": 30},
        ],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": {
                        "r": {
                            "$percentile": {
                                "input": "$v",
                                "p": [0.5, 0.9],
                                "method": "approximate",
                            }
                        }
                    },
                }
            }
        ],
        expected=[{"_id": 0, "r": [20.0, 30.0]}],
        msg="$bucket output should support $percentile",
    ),
    StageTestCase(
        "acc_accumulator",
        docs=[
            {"_id": 1, "x": 1, "v": 10},
            {"_id": 2, "x": 1, "v": 20},
            {"_id": 3, "x": 1, "v": 30},
        ],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": {
                        "r": {
                            "$accumulator": {
                                "init": "function() { return 0; }",
                                "accumulate": "function(state, val) { return state + val; }",
                                "accumulateArgs": ["$v"],
                                "merge": "function(s1, s2) { return s1 + s2; }",
                                "finalize": "function(state) { return state; }",
                                "lang": "js",
                            }
                        }
                    },
                }
            }
        ],
        expected=[{"_id": 0, "r": 60.0}],
        msg="$bucket output should support $accumulator",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(BUCKET_ACCUMULATOR_OPERATOR_TESTS))
def test_bucket_accumulator_operators(collection, test_case: StageTestCase):
    """Test $bucket accumulator operator support."""
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


# Property [AddToSet Operator Support]: $addToSet functions correctly inside
# $bucket output; result order is non-deterministic.
BUCKET_ADDTOSET_OPERATOR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "acc_addToSet",
        docs=[
            {"_id": 1, "x": 1, "v": 10},
            {"_id": 2, "x": 1, "v": 20},
            {"_id": 3, "x": 1, "v": 30},
        ],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": {"r": {"$addToSet": "$v"}},
                }
            }
        ],
        expected=[{"_id": 0, "r": [10, 20, 30]}],
        msg="$bucket output should support $addToSet",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(BUCKET_ADDTOSET_OPERATOR_TESTS))
def test_bucket_addtoset_operator(collection, test_case: StageTestCase):
    """Test $bucket $addToSet accumulator with unordered comparison."""
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
        ignore_order_in=["r"],
        msg=test_case.msg,
    )
