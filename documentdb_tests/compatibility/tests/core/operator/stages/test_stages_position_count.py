"""Tests for $count composing with other stages at different pipeline positions."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Pipeline Position]: $count produces the correct count when
# composed with other stage types at different pipeline positions.
COUNT_PIPELINE_POSITION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "pipeline_after_match",
        docs=[
            {"_id": 1, "status": "active"},
            {"_id": 2, "status": "inactive"},
            {"_id": 3, "status": "active"},
            {"_id": 4, "status": "active"},
        ],
        pipeline=[{"$match": {"status": "active"}}, {"$count": "n"}],
        expected=[{"n": 3}],
        msg="$count should reflect documents remaining after $match",
    ),
    StageTestCase(
        "pipeline_after_skip",
        docs=[{"_id": 1}, {"_id": 2}, {"_id": 3}, {"_id": 4}, {"_id": 5}],
        pipeline=[{"$skip": 2}, {"$count": "remaining"}],
        expected=[{"remaining": 3}],
        msg="$count should reflect documents remaining after $skip",
    ),
    StageTestCase(
        "pipeline_after_limit",
        docs=[{"_id": 1}, {"_id": 2}, {"_id": 3}, {"_id": 4}, {"_id": 5}],
        pipeline=[{"$limit": 3}, {"$count": "limited"}],
        expected=[{"limited": 3}],
        msg="$count should reflect documents remaining after $limit",
    ),
    StageTestCase(
        "pipeline_after_unwind",
        docs=[
            {"_id": 1, "tags": ["a", "b", "c"]},
            {"_id": 2, "tags": ["d"]},
        ],
        pipeline=[{"$unwind": "$tags"}, {"$count": "unwound"}],
        expected=[{"unwound": 4}],
        msg="$count should reflect documents produced by $unwind",
    ),
    StageTestCase(
        "pipeline_after_group",
        docs=[
            {"_id": 1, "cat": "a"},
            {"_id": 2, "cat": "b"},
            {"_id": 3, "cat": "a"},
            {"_id": 4, "cat": "c"},
        ],
        pipeline=[{"$group": {"_id": "$cat"}}, {"$count": "groups"}],
        expected=[{"groups": 3}],
        msg="$count should return the number of groups produced by $group",
    ),
    StageTestCase(
        "pipeline_after_project",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}, {"_id": 3, "x": 3}],
        pipeline=[{"$project": {"x": 1}}, {"$count": "total"}],
        expected=[{"total": 3}],
        msg="$count should count documents reshaped by $project",
    ),
    StageTestCase(
        "pipeline_after_unset",
        docs=[{"_id": 1, "x": 1, "y": 2}, {"_id": 2, "x": 3, "y": 4}],
        pipeline=[{"$unset": "y"}, {"$count": "total"}],
        expected=[{"total": 2}],
        msg="$count should count documents after $unset removes a field",
    ),
    StageTestCase(
        "pipeline_after_addFields",
        docs=[{"_id": 1, "x": 5}, {"_id": 2, "x": 10}],
        pipeline=[
            {"$addFields": {"doubled": {"$multiply": ["$x", 2]}}},
            {"$count": "total"},
        ],
        expected=[{"total": 2}],
        msg="$count should count documents enriched by $addFields",
    ),
    StageTestCase(
        "pipeline_after_replaceRoot",
        docs=[
            {"_id": 1, "inner": {"a": 1}},
            {"_id": 2, "inner": {"a": 2}},
            {"_id": 3, "inner": {"a": 3}},
        ],
        pipeline=[{"$replaceRoot": {"newRoot": "$inner"}}, {"$count": "total"}],
        expected=[{"total": 3}],
        msg="$count should count documents reshaped by $replaceRoot",
    ),
    StageTestCase(
        "pipeline_after_sort_limit",
        docs=[{"_id": i, "score": i} for i in range(10)],
        pipeline=[
            {"$sort": {"score": -1}},
            {"$limit": 5},
            {"$count": "top_n"},
        ],
        expected=[{"top_n": 5}],
        msg="$count should return the number of top-N documents after $sort and $limit",
    ),
    StageTestCase(
        "pipeline_after_lookup",
        docs=[{"_id": 1, "code": "a"}, {"_id": 2, "code": "b"}],
        setup=lambda c: c.database["items"].insert_one({"_id": 1, "code": "a", "v": 10}),
        pipeline=[
            {
                "$lookup": {
                    "from": "items",
                    "localField": "code",
                    "foreignField": "code",
                    "as": "matched",
                }
            },
            {"$count": "total"},
        ],
        expected=[{"total": 2}],
        msg="$count should count documents after $lookup join",
    ),
]

# Property [Unicode Normalization]: precomposed and decomposed forms of the
# same character produce distinct field names in the $count output document
# when composed with $addFields.
COUNT_UNICODE_NORMALIZATION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "normalization_precomposed_vs_decomposed",
        docs=[{"_id": 1}],
        # U+00E9 (precomposed) used as $count field, then U+0065 U+0301
        # (decomposed) added via $addFields. Both should coexist.
        pipeline=[
            {"$count": "\u00e9"},
            {"$addFields": {"e\u0301": "decomposed"}},
        ],
        expected=[{"\u00e9": 1, "e\u0301": "decomposed"}],
        msg="$count should treat precomposed and decomposed forms as distinct field names",
    ),
    StageTestCase(
        "normalization_decomposed_as_count_field",
        docs=[{"_id": 1}],
        # U+0065 U+0301 (decomposed) used as $count field, then U+00E9
        # (precomposed) added via $addFields. Both should coexist.
        pipeline=[
            {"$count": "e\u0301"},
            {"$addFields": {"\u00e9": "precomposed"}},
        ],
        expected=[{"e\u0301": 1, "\u00e9": "precomposed"}],
        msg="$count should treat decomposed and precomposed forms as distinct field names",
    ),
    StageTestCase(
        "normalization_hangul_precomposed_vs_decomposed",
        docs=[{"_id": 1}],
        # U+AC00 (precomposed Hangul syllable) vs U+1100 U+1161 (decomposed).
        pipeline=[
            {"$count": "\uac00"},
            {"$addFields": {"\u1100\u1161": "decomposed"}},
        ],
        expected=[{"\uac00": 1, "\u1100\u1161": "decomposed"}],
        msg="$count should treat precomposed and decomposed Hangul as distinct field names",
    ),
]

COUNT_INTEGRATION_TESTS = COUNT_PIPELINE_POSITION_TESTS + COUNT_UNICODE_NORMALIZATION_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(COUNT_INTEGRATION_TESTS))
def test_stages_position_count_cases(collection, test_case: StageTestCase):
    """Test $count composing with other stages at different pipeline positions."""
    populate_collection(collection, test_case)
    if test_case.setup:
        test_case.setup(collection)
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
    )
