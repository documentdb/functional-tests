"""Tests for $rankFusion score and scoreDetails metadata projection."""

from __future__ import annotations

from typing import Any, Dict

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.rankFusion.utils.rankFusion_common import (  # noqa: E501
    rrf_score,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    QUERY_METADATA_NOT_AVAILABLE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [scoreDetails Acceptance and No Auto-Output]: scoreDetails accepts
# both boolean true and false, and with true the scoreDetails metadata is not
# added to output documents unless a following stage projects it.
RANKFUSION_SCORE_DETAILS_ACCEPTANCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "score_details_false_accepted",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}},
                    "scoreDetails": False,
                }
            },
        ],
        expected=[{"_id": 1, "a": 1}],
        msg="$rankFusion should accept scoreDetails false and run the stage normally",
    ),
    StageTestCase(
        "score_details_true_not_auto_output",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}},
                    "scoreDetails": True,
                }
            },
        ],
        expected=[{"_id": 1, "a": 1}],
        msg="$rankFusion should not add scoreDetails metadata to output unless it is projected",
    ),
]

# Property [Score Metadata Availability]: the score metadata holds the RRF score
# and is projectable regardless of whether scoreDetails is true or false.
RANKFUSION_SCORE_META_AVAILABLE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "score_meta_score_details_true",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}},
                    "scoreDetails": True,
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[{"_id": 1, "score": rrf_score(1)}],
        msg="$rankFusion should expose the score metadata when scoreDetails is true",
    ),
    StageTestCase(
        "score_meta_score_details_false",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}},
                    "scoreDetails": False,
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[{"_id": 1, "score": rrf_score(1)}],
        msg="$rankFusion should expose the score metadata when scoreDetails is false",
    ),
]

# Property [Unpopulated Metadata Omitted]: requesting a metadata name that
# $rankFusion does not populate silently omits the projected field with no
# error, regardless of the scoreDetails setting.
_UNPOPULATED_PARAMS: list[tuple[str, str, Dict[str, Any]]] = [
    ("searchScore", "omitted", {}),
    ("searchScore", "true", {"scoreDetails": True}),
    ("searchScoreDetails", "omitted", {}),
    ("searchScoreDetails", "true", {"scoreDetails": True}),
    ("vectorSearchScore", "omitted", {}),
    ("vectorSearchScore", "true", {"scoreDetails": True}),
]
RANKFUSION_UNPOPULATED_META_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"unpopulated_{mname}_sd_{sd_id}",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}},
                    **score_details_spec,
                }
            },
            {"$project": {"_id": 1, "m": {"$meta": mname}}},
        ],
        expected=[{"_id": 1}],
        msg=f"$rankFusion should silently omit the unpopulated {mname} field when "
        f"scoreDetails is {sd_id}",
    )
    for mname, sd_id, score_details_spec in _UNPOPULATED_PARAMS
]

# Property [scoreDetails Metadata Not Available]: requesting
# { $meta: "scoreDetails" } when scoreDetails is not enabled produces a
# metadata-not-available error, unlike the unpopulated searchScore* names which
# are silently omitted.
RANKFUSION_SCORE_DETAILS_META_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "score_details_meta_unavailable_false",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}},
                    "scoreDetails": False,
                }
            },
            {"$project": {"_id": 1, "sd": {"$meta": "scoreDetails"}}},
        ],
        error_code=QUERY_METADATA_NOT_AVAILABLE_ERROR,
        msg="$rankFusion should reject a scoreDetails meta request when scoreDetails is false",
    ),
    StageTestCase(
        "score_details_meta_unavailable_null",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}},
                    "scoreDetails": None,
                }
            },
            {"$project": {"_id": 1, "sd": {"$meta": "scoreDetails"}}},
        ],
        error_code=QUERY_METADATA_NOT_AVAILABLE_ERROR,
        msg="$rankFusion should reject a scoreDetails meta request when scoreDetails is null",
    ),
    StageTestCase(
        "score_details_meta_unavailable_omitted",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}},
                }
            },
            {"$project": {"_id": 1, "sd": {"$meta": "scoreDetails"}}},
        ],
        error_code=QUERY_METADATA_NOT_AVAILABLE_ERROR,
        msg="$rankFusion should reject a scoreDetails meta request when scoreDetails is omitted",
    ),
]

RANKFUSION_METADATA_TESTS = (
    RANKFUSION_SCORE_DETAILS_ACCEPTANCE_TESTS
    + RANKFUSION_SCORE_META_AVAILABLE_TESTS
    + RANKFUSION_UNPOPULATED_META_TESTS
    + RANKFUSION_SCORE_DETAILS_META_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(RANKFUSION_METADATA_TESTS))
def test_rankFusion_metadata(collection, test_case: StageTestCase):
    """Test $rankFusion score and scoreDetails metadata projection."""
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
