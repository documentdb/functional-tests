"""Tests for the structure of projected $rankFusion scoreDetails output."""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.stages.rankFusion.utils.rankFusion_common import (  # noqa: E501
    rrf_score,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, NonEmptyStr, PerDoc
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_MAX,
    DECIMAL128_MAX_NEGATIVE,
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_PRECISION_LOSS,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
)

# Property [scoreDetails Output Structure]: requesting scoreDetails projects
# per-document scoring metadata that describes how the fused score was computed
# from each contributing pipeline.
RANKFUSION_SCORE_DETAILS_STRUCTURE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "score_details_default_weights",
        docs=[
            {"_id": 1, "a": 30, "b": 10},
            {"_id": 2, "a": 20, "b": 30},
            {"_id": 3, "a": 10, "b": 20},
        ],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {
                        "pipelines": {
                            "p1": [{"$sort": {"a": -1}}],
                            "p2": [{"$sort": {"b": -1}}],
                        }
                    },
                    "scoreDetails": True,
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}, "sd": {"$meta": "scoreDetails"}}},
        ],
        expected=PerDoc(
            {
                "_id": Eq(2),
                "score": Eq(rrf_score(2, 1)),
                "sd": {
                    "value": Eq(rrf_score(2, 1)),
                    "description": NonEmptyStr(),
                    "details": Eq(
                        [
                            {"inputPipelineName": "p1", "rank": 2, "weight": 1.0, "details": []},
                            {"inputPipelineName": "p2", "rank": 1, "weight": 1.0, "details": []},
                        ]
                    ),
                },
            },
            {
                "_id": Eq(1),
                "score": Eq(rrf_score(1, 3)),
                "sd": {
                    "value": Eq(rrf_score(1, 3)),
                    "description": NonEmptyStr(),
                    "details": Eq(
                        [
                            {"inputPipelineName": "p1", "rank": 1, "weight": 1.0, "details": []},
                            {"inputPipelineName": "p2", "rank": 3, "weight": 1.0, "details": []},
                        ]
                    ),
                },
            },
            {
                "_id": Eq(3),
                "score": Eq(rrf_score(3, 2)),
                "sd": {
                    "value": Eq(rrf_score(3, 2)),
                    "description": NonEmptyStr(),
                    "details": Eq(
                        [
                            {"inputPipelineName": "p1", "rank": 3, "weight": 1.0, "details": []},
                            {"inputPipelineName": "p2", "rank": 2, "weight": 1.0, "details": []},
                        ]
                    ),
                },
            },
        ),
        msg="$rankFusion scoreDetails should expose value, description, and per-pipeline details",
    ),
]

# Property [scoreDetails Weight Echo]: each details entry echoes its pipeline's
# weight as a double converted from the input weight's BSON numeric type,
# preserving double-conversion semantics for special values.
RANKFUSION_SCORE_DETAILS_WEIGHT_TESTS: list[StageTestCase] = [
    *[
        StageTestCase(
            f"score_details_weight_{tid}",
            docs=[{"_id": 1, "a": 1}],
            pipeline=[
                {
                    "$rankFusion": {
                        "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}},
                        "combination": {"weights": {"p1": weight}},
                        "scoreDetails": True,
                    }
                },
                {
                    "$project": {
                        "_id": 1,
                        "score": {"$meta": "score"},
                        "sd": {"$meta": "scoreDetails"},
                    }
                },
            ],
            expected=PerDoc(
                {
                    "_id": Eq(1),
                    "score": Eq(rrf_score(1, weights=(echoed,))),
                    "sd": {
                        "value": Eq(rrf_score(1, weights=(echoed,))),
                        "description": NonEmptyStr(),
                        "details": Eq(
                            [
                                {
                                    "inputPipelineName": "p1",
                                    "rank": 1,
                                    "weight": echoed,
                                    "details": [],
                                }
                            ]
                        ),
                    },
                }
            ),
            msg=f"$rankFusion scoreDetails should echo a {tid} weight as a double",
        )
        for tid, weight, echoed in [
            ("int32", 4, 4.0),
            ("double", 2.5, 2.5),
            # An int64 above 2^53 loses precision when converted to a double.
            (
                "int64_precision_loss",
                Int64(DOUBLE_PRECISION_LOSS),
                float(DOUBLE_MAX_SAFE_INTEGER),
            ),
            ("infinity_double", FLOAT_INFINITY, FLOAT_INFINITY),
            ("infinity_decimal", DECIMAL128_INFINITY, FLOAT_INFINITY),
            # A finite Decimal128 beyond the double range overflows to infinity.
            ("decimal_overflow", DECIMAL128_MAX, FLOAT_INFINITY),
        ]
    ],
    StageTestCase(
        "score_details_weight_neg_subnormal_decimal",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}},
                    "combination": {"weights": {"p1": DECIMAL128_MAX_NEGATIVE}},
                    "scoreDetails": True,
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}, "sd": {"$meta": "scoreDetails"}}},
        ],
        expected=PerDoc(
            {
                "_id": Eq(1),
                # A -0.0 echoed weight yields a +0.0 score. The score is asserted
                # with a plain value rather than rrf_score, which wraps results in
                # pytest.approx and would compare equal to both +0.0 and -0.0.
                "score": Eq(DOUBLE_ZERO),
                "sd": {
                    "value": Eq(DOUBLE_ZERO),
                    "description": NonEmptyStr(),
                    "details": Eq(
                        [
                            {
                                "inputPipelineName": "p1",
                                "rank": 1,
                                "weight": DOUBLE_NEGATIVE_ZERO,
                                "details": [],
                            }
                        ]
                    ),
                },
            }
        ),
        msg="$rankFusion scoreDetails should echo a negative-subnormal Decimal128 weight as -0.0",
    ),
    StageTestCase(
        "score_details_weight_decimal_and_int64",
        docs=[{"_id": 1, "a": 1, "b": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {
                        "pipelines": {
                            "p1": [{"$sort": {"a": -1}}],
                            "p2": [{"$sort": {"b": -1}}],
                        }
                    },
                    "combination": {"weights": {"p1": Decimal128("4.5"), "p2": Int64(3)}},
                    "scoreDetails": True,
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}, "sd": {"$meta": "scoreDetails"}}},
        ],
        expected=PerDoc(
            {
                "_id": Eq(1),
                "score": Eq(rrf_score(1, 1, weights=(4.5, 3))),
                "sd": {
                    "value": Eq(rrf_score(1, 1, weights=(4.5, 3))),
                    "description": NonEmptyStr(),
                    "details": Eq(
                        [
                            {"inputPipelineName": "p1", "rank": 1, "weight": 4.5, "details": []},
                            {"inputPipelineName": "p2", "rank": 1, "weight": 3.0, "details": []},
                        ]
                    ),
                },
            },
        ),
        msg="$rankFusion scoreDetails should echo Decimal128 and int64 weights as doubles",
    ),
    StageTestCase(
        "score_details_zero_weight_entry",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {
                        "pipelines": {
                            "p1": [{"$sort": {"a": -1}}],
                            "p2": [{"$sort": {"a": -1}}],
                        }
                    },
                    "combination": {"weights": {"p1": 0}},
                    "scoreDetails": True,
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}, "sd": {"$meta": "scoreDetails"}}},
        ],
        expected=PerDoc(
            {
                "_id": Eq(1),
                "score": Eq(rrf_score(1, 1, weights=(0, 1))),
                "sd": {
                    "value": Eq(rrf_score(1, 1, weights=(0, 1))),
                    "description": NonEmptyStr(),
                    "details": Eq(
                        [
                            {
                                "inputPipelineName": "p1",
                                "rank": 1,
                                "weight": DOUBLE_ZERO,
                                "details": [],
                            },
                            {"inputPipelineName": "p2", "rank": 1, "weight": 1.0, "details": []},
                        ]
                    ),
                },
            },
        ),
        msg="$rankFusion scoreDetails should list a zero-weight pipeline with weight 0.0 and rank",
    ),
]

# Property [scoreDetails Missing-Pipeline Entry]: a pipeline that did not return
# the document contributes a details entry whose rank is the string "NA" with
# the weight and nested details subfields omitted.
RANKFUSION_SCORE_DETAILS_NA_TESTS: list[StageTestCase] = [
    StageTestCase(
        "score_details_missing_pipeline_na",
        docs=[{"_id": 1, "a": 1}, {"_id": 2, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {
                        "pipelines": {
                            "p1": [{"$match": {"_id": 1}}, {"$sort": {"a": -1}}],
                            "p2": [{"$match": {"_id": 2}}, {"$sort": {"a": -1}}],
                        }
                    },
                    "scoreDetails": True,
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}, "sd": {"$meta": "scoreDetails"}}},
        ],
        expected=PerDoc(
            {
                "_id": Eq(1),
                "score": Eq(rrf_score(1)),
                "sd": {
                    "value": Eq(rrf_score(1)),
                    "description": NonEmptyStr(),
                    "details": Eq(
                        [
                            {"inputPipelineName": "p1", "rank": 1, "weight": 1.0, "details": []},
                            {"inputPipelineName": "p2", "rank": "NA"},
                        ]
                    ),
                },
            },
            {
                "_id": Eq(2),
                "score": Eq(rrf_score(1)),
                "sd": {
                    "value": Eq(rrf_score(1)),
                    "description": NonEmptyStr(),
                    "details": Eq(
                        [
                            {"inputPipelineName": "p1", "rank": "NA"},
                            {"inputPipelineName": "p2", "rank": 1, "weight": 1.0, "details": []},
                        ]
                    ),
                },
            },
        ),
        msg="$rankFusion scoreDetails should report rank NA and omit weight for a missing pipeline",
    ),
]

RANKFUSION_SCORE_DETAILS_STRUCTURE_ALL_TESTS = (
    RANKFUSION_SCORE_DETAILS_STRUCTURE_TESTS
    + RANKFUSION_SCORE_DETAILS_WEIGHT_TESTS
    + RANKFUSION_SCORE_DETAILS_NA_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(RANKFUSION_SCORE_DETAILS_STRUCTURE_ALL_TESTS))
def test_rankFusion_score_details_structure(collection, test_case: StageTestCase):
    """Test the structure of projected $rankFusion scoreDetails output."""
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
