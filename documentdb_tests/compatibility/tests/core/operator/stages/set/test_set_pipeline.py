from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.set.utils.set_common import (
    STAGE_NAMES,
    replace_stage_name,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Non-Existent Collection]: $set on a collection that does not exist
# returns an empty result set without error.
SET_NONEXISTENT_COLLECTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "nonexistent_collection",
        docs=None,
        pipeline=[{"$set": {"b": 1}}],
        expected=[],
        msg="$set on a non-existent collection should return empty result",
    ),
]

# Property [Empty Collection]: $set on a collection with no documents returns
# an empty result set without error.
SET_EMPTY_COLLECTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "empty_collection",
        docs=[],
        pipeline=[{"$set": {"b": 1}}],
        expected=[],
        msg="$set on an empty collection should return empty result",
    ),
]

# Property [Multiple Documents]: $set applies the specification to every
# document in the input independently.
SET_MULTIPLE_DOCUMENTS_TESTS: list[StageTestCase] = [
    StageTestCase(
        "multiple_documents",
        docs=[{"_id": 1, "a": 10}, {"_id": 2, "a": 20}, {"_id": 3, "a": 30}],
        pipeline=[{"$set": {"b": {"$add": ["$a", 1]}}}],
        expected=[
            {"_id": 1, "a": 10, "b": 11},
            {"_id": 2, "a": 20, "b": 21},
            {"_id": 3, "a": 30, "b": 31},
        ],
        msg="$set should apply to every document independently",
    ),
]

# Property [Consecutive Stages]: multiple $set stages compose sequentially,
# with each stage seeing the output of the previous one.
SET_CONSECUTIVE_STAGES_TESTS: list[StageTestCase] = [
    StageTestCase(
        "consecutive_stages",
        docs=[{"_id": 1, "a": 5}],
        pipeline=[
            {"$set": {"b": {"$add": ["$a", 10]}}},
            {"$set": {"c": {"$add": ["$b", 100]}}},
        ],
        expected=[{"_id": 1, "a": 5, "b": 15, "c": 115}],
        msg="$set second stage should see fields added by the first stage",
    ),
]

SET_PIPELINE_TESTS = (
    SET_NONEXISTENT_COLLECTION_TESTS
    + SET_EMPTY_COLLECTION_TESTS
    + SET_MULTIPLE_DOCUMENTS_TESTS
    + SET_CONSECUTIVE_STAGES_TESTS
)


@pytest.mark.parametrize("stage_name", STAGE_NAMES)
@pytest.mark.parametrize("test_case", pytest_params(SET_PIPELINE_TESTS))
def test_set_pipeline(collection, stage_name: str, test_case: StageTestCase):
    """Test $set / $addFields pipeline-level behavior cases."""
    populate_collection(collection, test_case)
    pipeline = replace_stage_name(test_case.pipeline, stage_name)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=f"{stage_name!r}: {test_case.msg!r}",
    )
