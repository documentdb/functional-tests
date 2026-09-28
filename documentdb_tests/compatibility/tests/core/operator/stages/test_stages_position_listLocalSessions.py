"""Tests for $listLocalSessions pipeline position, sub-pipeline placement, and composition."""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from pymongo.collection import Collection
from pymongo.database import Database

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    INVALID_NAMESPACE_ERROR,
    NOT_FIRST_STAGE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists, Gte, IsType, NotExists

# Property [Stage Position Errors]: $listLocalSessions must be the first pipeline stage,
# so it is rejected when any stage precedes it.
LISTLOCALSESSIONS_NOT_FIRST_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "after_documents",
        command={
            "aggregate": 1,
            "pipeline": [{"$documents": [{"a": 1}]}, {"$listLocalSessions": {}}],
            "cursor": {},
        },
        error_code=NOT_FIRST_STAGE_ERROR,
        msg="$listLocalSessions should be rejected when it follows another stage",
    ),
]

# Property [Sub-pipeline Placement Errors]: $listLocalSessions requires a collection-less
# namespace, so it is rejected as the first stage of a collection sub-pipeline
# which supplies a collection namespace.
LISTLOCALSESSIONS_SUB_PIPELINE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "union_with_coll_subpipeline",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$unionWith": {"coll": ctx.collection, "pipeline": [{"$listLocalSessions": {}}]}}
            ],
            "cursor": {},
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="$listLocalSessions should be rejected as the first stage of a "
        "$unionWith collection sub-pipeline",
    ),
    CommandTestCase(
        "facet_subpipeline",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$facet": {"f": [{"$listLocalSessions": {}}]}}],
            "cursor": {},
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="$listLocalSessions should be rejected as a $facet sub-pipeline first stage",
    ),
    CommandTestCase(
        "lookup_subpipeline",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$lookup": {
                        "from": ctx.collection,
                        "pipeline": [{"$listLocalSessions": {}}],
                        "as": "sessions",
                    }
                }
            ],
            "cursor": {},
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="$listLocalSessions should be rejected as a $lookup sub-pipeline first stage",
    ),
]

LISTLOCALSESSIONS_POSITION_TESTS = (
    LISTLOCALSESSIONS_NOT_FIRST_ERROR_TESTS + LISTLOCALSESSIONS_SUB_PIPELINE_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test", pytest_params(LISTLOCALSESSIONS_POSITION_TESTS))
def test_listLocalSessions_position(
    database_client: Database, collection: Collection, test: CommandTestCase
):
    """Test $listLocalSessions pipeline position and sub-pipeline placement errors."""
    target = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(target)
    result = execute_command(target, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


@dataclass(frozen=True)
class ListLocalSessionsCompositionTestCase(CommandTestCase):
    """Composition test case carrying its session requirement.

    Attributes:
        num_sessions: Number of explicit sessions to open before running the
            command, so the local session cache holds that many entries. The
            command runs inside the first session.
    """

    num_sessions: int = 1


# Property [Downstream Stage Composition]: as a first-stage source, $listLocalSessions
# emits a document stream that downstream stages transform like any other source. Each case
# runs inside one or more explicit sessions so the local session cache is populated, and
# asserts output that a no-op stage could not produce.
LISTLOCALSESSIONS_COMPOSITION_TESTS: list[ListLocalSessionsCompositionTestCase] = [
    ListLocalSessionsCompositionTestCase(
        "followed_by_match_none",
        command={
            "aggregate": 1,
            "pipeline": [{"$listLocalSessions": {}}, {"$match": {"_id": {"$exists": False}}}],
            "cursor": {},
        },
        expected=[],
        msg="a downstream $match with a filter matching no session should drop every document",
    ),
    ListLocalSessionsCompositionTestCase(
        "followed_by_project",
        command={
            "aggregate": 1,
            "pipeline": [{"$listLocalSessions": {}}, {"$project": {"lastUse": 1, "_id": 0}}],
            "cursor": {},
        },
        expected={"lastUse": IsType("date"), "_id": NotExists()},
        msg="a downstream $project should reshape each session to only the projected field",
    ),
    ListLocalSessionsCompositionTestCase(
        "followed_by_add_fields",
        command={
            "aggregate": 1,
            "pipeline": [{"$listLocalSessions": {}}, {"$addFields": {"marker": "present"}}],
            "cursor": {},
        },
        expected={"_id": Exists(), "lastUse": IsType("date"), "marker": Eq("present")},
        msg="a downstream $addFields should add a computed field while preserving originals",
    ),
    ListLocalSessionsCompositionTestCase(
        "followed_by_count",
        num_sessions=3,
        command={
            "aggregate": 1,
            "pipeline": [{"$listLocalSessions": {"allUsers": True}}, {"$count": "numSessions"}],
            "cursor": {},
        },
        expected={"numSessions": Gte(3)},
        msg="a downstream $count should collapse the multi-session stream into one count document",
    ),
    ListLocalSessionsCompositionTestCase(
        "followed_by_group",
        num_sessions=3,
        command={
            "aggregate": 1,
            "pipeline": [
                {"$listLocalSessions": {"allUsers": True}},
                {"$group": {"_id": None, "numSessions": {"$sum": 1}}},
            ],
            "cursor": {},
        },
        expected={"_id": Eq(None), "numSessions": Gte(3)},
        msg="a downstream $group should aggregate the multi-session stream into a single group",
    ),
    ListLocalSessionsCompositionTestCase(
        "followed_by_skip_limit",
        num_sessions=3,
        command={
            "aggregate": 1,
            "pipeline": [
                {"$listLocalSessions": {"allUsers": True}},
                {"$skip": 1},
                {"$limit": 1},
                {"$count": "numKept"},
            ],
            "cursor": {},
        },
        expected={"numKept": Eq(1)},
        msg="a downstream $skip and $limit should cap the multi-session stream to one document",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test", pytest_params(LISTLOCALSESSIONS_COMPOSITION_TESTS))
def test_listLocalSessions_composition(
    collection: Collection, test: ListLocalSessionsCompositionTestCase
):
    """Test downstream stages transform the $listLocalSessions source stream."""
    # Open the requested number of sessions so the local session cache is populated,
    # then run the command inside the first one.
    client = collection.database.client
    sessions = [client.start_session() for _ in range(test.num_sessions)]
    try:
        for session in sessions:
            collection.database.command("ping", session=session)
        ctx = CommandContext.from_collection(collection)
        result = execute_command(collection, test.build_command(ctx), session=sessions[0])
    finally:
        for session in sessions:
            session.end_session()
    assertResult(result, expected=test.build_expected(ctx), msg=test.msg)
