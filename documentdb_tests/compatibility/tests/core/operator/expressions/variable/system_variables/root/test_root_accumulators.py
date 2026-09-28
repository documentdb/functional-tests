"""
Accumulator input tests for the $$ROOT system variable.

Covers $$ROOT as accumulator input/output in $group, $bucket, and
$setWindowFields — one wiring case per host context (TEST_COVERAGE.md §18).
Per-accumulator coverage lives in each accumulator's own folder
(accumulators/<name>/test_accumulator_<name>_root_input.py); $bucket's own
wiring sample already exists in stages/bucket/test_bucket_output.py
(push_root_returns_full_docs).
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

DOC_1 = {"_id": 1, "g": "A", "v": 10}
DOC_2 = {"_id": 2, "g": "A", "v": 30}
DOC_3 = {"_id": 3, "g": "A", "v": 20}

BUCKET_DOC_1 = {"_id": 1, "v": 5}
BUCKET_DOC_2 = {"_id": 2, "v": 15}
BUCKET_DOC_3 = {"_id": 3, "v": 25}

# Property [Group Accumulator Input]: $group accumulators accept $$ROOT as their
# input or output expression, collecting whole documents rather than a scalar
# field. One case each for output-position and input-position is sufficient to
# prove the wiring; per-accumulator behavior is owned by each accumulator's folder.
GROUP_ACCUMULATOR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        id="group_top",
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": "$g", "r": {"$top": {"sortBy": {"v": -1}, "output": "$$ROOT"}}}},
        ],
        expected=[{"_id": "A", "r": DOC_2}],
        msg="$top with output $$ROOT should return the whole highest-sorted document",
    ),
    AccumulatorTestCase(
        id="group_firstN",
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": "$g", "r": {"$firstN": {"n": 2, "input": "$$ROOT"}}}},
        ],
        expected=[{"_id": "A", "r": [DOC_1, DOC_2]}],
        msg="$firstN with input $$ROOT should return the first whole documents",
    ),
]


@pytest.mark.parametrize("test", pytest_params(GROUP_ACCUMULATOR_TESTS))
def test_root_as_group_accumulator_input(collection, test: AccumulatorTestCase):
    """$group accumulators accept $$ROOT as input/output."""
    collection.insert_many([dict(d) for d in [DOC_1, DOC_2, DOC_3]])
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test.pipeline, "cursor": {}},
    )
    assertSuccess(result, test.expected, msg=test.msg)


# Property [Bucket and Window Accumulator Input]: accumulators in $bucket output
# and $setWindowFields output accept $$ROOT the same way $group does. One case
# each proves the wiring; per-accumulator behavior is owned elsewhere.
BUCKET_AND_WINDOW_ACCUMULATOR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        id="bucket_bottom",
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$bucket": {
                    "groupBy": "$v",
                    "boundaries": [0, 20, 40],
                    "output": {"r": {"$bottom": {"sortBy": {"v": 1}, "output": "$$ROOT"}}},
                }
            },
        ],
        expected=[{"_id": 0, "r": BUCKET_DOC_2}, {"_id": 20, "r": BUCKET_DOC_3}],
        msg="$bottom in $bucket output with $$ROOT should return whole documents",
    ),
    AccumulatorTestCase(
        id="window_first_whole_document",
        pipeline=[
            {
                "$setWindowFields": {
                    "sortBy": {"v": 1},
                    "output": {
                        "r": {
                            "$first": "$$ROOT",
                            "window": {"documents": ["unbounded", "current"]},
                        }
                    },
                }
            },
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {**BUCKET_DOC_1, "r": BUCKET_DOC_1},
            {**BUCKET_DOC_2, "r": BUCKET_DOC_1},
            {**BUCKET_DOC_3, "r": BUCKET_DOC_1},
        ],
        msg="$first with $$ROOT should return the whole first document of each window",
    ),
]


@pytest.mark.parametrize("test", pytest_params(BUCKET_AND_WINDOW_ACCUMULATOR_TESTS))
def test_root_as_bucket_and_window_accumulator_input(collection, test: AccumulatorTestCase):
    """$bucket and $setWindowFields accumulators accept $$ROOT as input/output."""
    collection.insert_many([dict(d) for d in [BUCKET_DOC_1, BUCKET_DOC_2, BUCKET_DOC_3]])
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test.pipeline, "cursor": {}},
    )
    assertSuccess(result, test.expected, msg=test.msg)
