"""Tests for errors in the contents of $rankFusion input sub-pipelines."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    LIMIT_NOT_POSITIVE_ERROR,
    PIPELINE_STAGE_EXTRA_FIELD_ERROR,
    RANK_FUSION_NESTED_HYBRID_STAGE_ERROR,
    RANK_FUSION_NO_RANKED_STAGE_OR_SORT_ERROR,
    RANK_FUSION_NON_SELECTION_STAGE_ERROR,
    RANK_FUSION_NOT_FIRST_STAGE_ERROR,
    SORT_EMPTY_SPEC_ERROR,
    UNKNOWN_PIPELINE_STAGE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Input Pipeline Ranked Or Sort Requirement]: an input pipeline that
# neither begins with a ranked stage nor contains an explicit $sort anywhere is
# rejected, even when it consists only of otherwise-allowed selection stages.
RANKFUSION_CONTENT_NO_RANK_OR_SORT_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"content_no_rank_or_sort_{tid}",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$rankFusion": {"input": {"pipelines": {"p1": stages}}}}],
        error_code=RANK_FUSION_NO_RANKED_STAGE_OR_SORT_ERROR,
        msg=f"$rankFusion should reject an input pipeline with {tid} and no ranked stage or sort",
    )
    for tid, stages in [
        ("match_only", [{"$match": {"a": 1}}]),
        ("limit_only", [{"$limit": 1}]),
        ("match_then_limit", [{"$match": {"a": 1}}, {"$limit": 1}]),
        ("sample_only", [{"$sample": {"size": 1}}]),
    ]
]

# Property [Input Pipeline Non-Selection Stage]: a stage that modifies or
# transforms documents is not a selection stage and is rejected, including
# $geoNear when distanceField or includeLocs is set because those options modify
# documents.
RANKFUSION_CONTENT_NON_SELECTION_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"content_non_selection_{tid}",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$rankFusion": {"input": {"pipelines": {"p1": [{"$sort": {"a": -1}}, stage]}}}}],
        error_code=RANK_FUSION_NON_SELECTION_STAGE_ERROR,
        msg=f"$rankFusion should reject the non-selection stage {tid} in an input pipeline",
    )
    for tid, stage in [
        ("project", {"$project": {"a": 1}}),
        ("add_fields", {"$addFields": {"x": 1}}),
        ("set", {"$set": {"x": 1}}),
        ("unset", {"$unset": "a"}),
        ("group", {"$group": {"_id": "$a"}}),
        ("unwind", {"$unwind": "$a"}),
        ("count", {"$count": "c"}),
        ("replace_root", {"$replaceRoot": {"newRoot": {"x": 1}}}),
        # $replaceWith is an alias of $replaceRoot and is exercised separately.
        ("replace_with", {"$replaceWith": {"x": 1}}),
        ("bucket", {"$bucket": {"groupBy": "$a", "boundaries": [0, 5, 10], "default": "o"}}),
        ("bucket_auto", {"$bucketAuto": {"groupBy": "$a", "buckets": 2}}),
        ("lookup", {"$lookup": {"from": "c", "localField": "a", "foreignField": "a", "as": "x"}}),
        (
            "graph_lookup",
            {
                "$graphLookup": {
                    "from": "c",
                    "startWith": "$a",
                    "connectFromField": "a",
                    "connectToField": "a",
                    "as": "x",
                }
            },
        ),
        ("out", {"$out": "out_c"}),
        ("merge", {"$merge": {"into": "merge_c"}}),
        ("facet", {"$facet": {"f": [{"$match": {"a": 1}}]}}),
        ("documents", {"$documents": [{"x": 1}]}),
        ("union_with", {"$unionWith": "c"}),
        ("redact", {"$redact": "$$KEEP"}),
        ("sort_by_count", {"$sortByCount": "$a"}),
        (
            "set_window_fields",
            {"$setWindowFields": {"sortBy": {"a": 1}, "output": {"w": {"$sum": 1}}}},
        ),
        ("densify", {"$densify": {"field": "a", "range": {"step": 1, "bounds": "full"}}}),
        ("fill", {"$fill": {"sortBy": {"a": 1}, "output": {"a": {"method": "linear"}}}}),
        (
            "geo_near_distance_field",
            {"$geoNear": {"near": {"type": "Point", "coordinates": [0, 0]}, "distanceField": "d"}},
        ),
        (
            "geo_near_include_locs",
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "includeLocs": "loc",
                }
            },
        ),
    ]
]

# Property [Input Pipeline Nested Hybrid First Stage]: a nested $rankFusion or
# $scoreFusion that is the first stage of an input pipeline is rejected with the
# disallowed-nested-hybrid error.
RANKFUSION_CONTENT_NESTED_HYBRID_FIRST_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "content_nested_rank_fusion_first",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {
                        "pipelines": {
                            "p1": [
                                {
                                    "$rankFusion": {
                                        "input": {"pipelines": {"q": [{"$sort": {"a": -1}}]}}
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        ],
        error_code=RANK_FUSION_NESTED_HYBRID_STAGE_ERROR,
        msg="$rankFusion should reject a nested $rankFusion as an input pipeline's first stage",
    ),
    StageTestCase(
        "content_nested_score_fusion_first",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {
                        "pipelines": {
                            "p1": [
                                {
                                    "$scoreFusion": {
                                        "input": {
                                            "pipelines": {"q": [{"$sort": {"a": -1}}]},
                                            "normalization": "none",
                                        }
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        ],
        error_code=RANK_FUSION_NESTED_HYBRID_STAGE_ERROR,
        msg="$rankFusion should reject a nested $scoreFusion as an input pipeline's first stage",
    ),
]

# Property [Input Pipeline Nested Hybrid Not First Stage]: a nested $rankFusion
# or $scoreFusion that follows another stage in an input pipeline is rejected
# with the must-be-first-stage error.
RANKFUSION_CONTENT_NESTED_HYBRID_NOT_FIRST_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "content_nested_rank_fusion_not_first",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {
                        "pipelines": {
                            "p1": [
                                {"$sort": {"a": -1}},
                                {
                                    "$rankFusion": {
                                        "input": {"pipelines": {"q": [{"$sort": {"a": -1}}]}}
                                    }
                                },
                            ]
                        }
                    }
                }
            }
        ],
        error_code=RANK_FUSION_NOT_FIRST_STAGE_ERROR,
        msg="$rankFusion should reject a nested $rankFusion that is not the first stage",
    ),
    StageTestCase(
        "content_nested_score_fusion_not_first",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {
                        "pipelines": {
                            "p1": [
                                {"$sort": {"a": -1}},
                                {
                                    "$scoreFusion": {
                                        "input": {
                                            "pipelines": {"q": [{"$sort": {"a": -1}}]},
                                            "normalization": "none",
                                        }
                                    }
                                },
                            ]
                        }
                    }
                }
            }
        ],
        error_code=RANK_FUSION_NOT_FIRST_STAGE_ERROR,
        msg="$rankFusion should reject a nested $scoreFusion that is not the first stage",
    ),
]

# Property [Input Pipeline Malformed Stage Object]: a stage object that is not a
# single recognized pipeline stage is rejected, whether its name is unrecognized
# or it does not contain exactly one field.
RANKFUSION_CONTENT_MALFORMED_STAGE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "content_unrecognized_stage",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}, {"notAStage": 1}]}}
                }
            }
        ],
        error_code=UNKNOWN_PIPELINE_STAGE_ERROR,
        msg="$rankFusion should reject an unrecognized stage in an input pipeline",
    ),
    StageTestCase(
        "content_empty_stage",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$rankFusion": {"input": {"pipelines": {"p1": [{"$sort": {"a": -1}}, {}]}}}}],
        error_code=PIPELINE_STAGE_EXTRA_FIELD_ERROR,
        msg="$rankFusion should reject an empty stage object in an input pipeline",
    ),
    StageTestCase(
        "content_two_field_stage",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {
                        "pipelines": {
                            "p1": [{"$sort": {"a": -1}}, {"$match": {"a": 1}, "$limit": 1}]
                        }
                    }
                }
            }
        ],
        error_code=PIPELINE_STAGE_EXTRA_FIELD_ERROR,
        msg="$rankFusion should reject a two-field stage object in an input pipeline",
    ),
]

# Property [Input Pipeline Selection Stage Argument]: a selection stage admitted
# into an input pipeline still enforces its own argument validation, so a
# non-positive $limit and an empty $sort specification are each rejected with
# that stage's own error.
RANKFUSION_CONTENT_SELECTION_ARG_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "content_limit_zero",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {"$rankFusion": {"input": {"pipelines": {"p1": [{"$sort": {"a": -1}}, {"$limit": 0}]}}}}
        ],
        error_code=LIMIT_NOT_POSITIVE_ERROR,
        msg="$rankFusion should reject a $limit of 0 in an input pipeline",
    ),
    StageTestCase(
        "content_sort_empty",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$rankFusion": {"input": {"pipelines": {"p1": [{"$sort": {}}]}}}}],
        error_code=SORT_EMPTY_SPEC_ERROR,
        msg="$rankFusion should reject an empty $sort specification in an input pipeline",
    ),
]

RANKFUSION_PIPELINE_CONTENT_ERROR_TESTS = (
    RANKFUSION_CONTENT_NO_RANK_OR_SORT_ERROR_TESTS
    + RANKFUSION_CONTENT_NON_SELECTION_ERROR_TESTS
    + RANKFUSION_CONTENT_NESTED_HYBRID_FIRST_ERROR_TESTS
    + RANKFUSION_CONTENT_NESTED_HYBRID_NOT_FIRST_ERROR_TESTS
    + RANKFUSION_CONTENT_MALFORMED_STAGE_ERROR_TESTS
    + RANKFUSION_CONTENT_SELECTION_ARG_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(RANKFUSION_PIPELINE_CONTENT_ERROR_TESTS))
def test_rankFusion_pipeline_content_errors(collection, test_case: StageTestCase):
    """Test errors in the contents of $rankFusion input sub-pipelines."""
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
    )
