"""Tests for $querySettings returned document structure."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import pytest
from pymongo.collection import Collection

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, IsType, Len, NotExists


@dataclass(frozen=True)
class QuerySettingsStructureTestCase(StageTestCase):
    """Stage test case for $querySettings document-structure tests.

    Attributes:
        query_settings: Callable receiving the fixture collection,
            returning the settings to register via setQuerySettings
            before the stage runs.
        settings_comment: Optional comment to attach to each registered
            query setting.
    """

    query_settings: Callable[[Collection], list[dict[str, Any]]] = lambda ctx: []
    settings_comment: str | None = None
    raw_res: bool = False


# Property [Core Behavior - Document Structure]: each returned document
# describes one configured query setting and its query shape.
QUERYSETTINGS_CORE_STRUCTURE_TESTS: list[QuerySettingsStructureTestCase] = [
    QuerySettingsStructureTestCase(
        "core_structure_fields",
        pipeline=[{"$querySettings": {}}],
        query_settings=lambda ctx: [
            {"find": ctx.name, "filter": {"x": 1}, "$db": ctx.database.name}
        ],
        expected=lambda ctx: {
            "queryShapeHash": IsType("string"),
            "settings": {
                "indexHints": IsType("array"),
                "queryFramework": IsType("string"),
            },
            "representativeQuery": {
                "find": Eq(ctx.name),
                "filter": Eq({"x": 1}),
                "$db": Eq(ctx.database.name),
            },
        },
        msg=(
            "$querySettings should return one document per configured query"
            " setting describing its query shape"
        ),
    ),
]

# Property [Core Behavior - Optional Comment]: when a query setting is
# registered with a comment, the returned settings document includes the
# comment string.
QUERYSETTINGS_CORE_COMMENT_TESTS: list[QuerySettingsStructureTestCase] = [
    QuerySettingsStructureTestCase(
        "core_settings_comment",
        pipeline=[{"$querySettings": {}}],
        query_settings=lambda ctx: [
            {"find": ctx.name, "filter": {"x": 1}, "$db": ctx.database.name}
        ],
        settings_comment="qs comment value",
        expected={
            "settings": {
                "comment": Eq("qs comment value"),
            },
        },
        msg=(
            "$querySettings should include the comment string in settings"
            " when a comment was set on the query setting"
        ),
    ),
]

# Property [Core Behavior - Multiple Settings]: the stage returns one
# document per query setting previously added with setQuerySettings.
QUERYSETTINGS_CORE_MULTIPLE_TESTS: list[QuerySettingsStructureTestCase] = [
    QuerySettingsStructureTestCase(
        "core_multiple_settings",
        pipeline=[{"$querySettings": {}}],
        query_settings=lambda ctx: [
            {"find": ctx.name, "filter": {"x": 1}, "$db": ctx.database.name},
            {"find": ctx.name, "filter": {"y": 2}, "$db": ctx.database.name},
        ],
        expected={"cursor.firstBatch": Len(2)},
        raw_res=True,
        msg="$querySettings should return one document per configured query setting",
    ),
]

# Property [showDebugQueryShape Behavior]: when showDebugQueryShape is
# true, returned documents contain a debugQueryShape sub-document; when
# false or omitted, that field is absent.
QUERYSETTINGS_DEBUG_SHAPE_TESTS: list[QuerySettingsStructureTestCase] = [
    QuerySettingsStructureTestCase(
        "debug_shape_true_includes_field",
        pipeline=[{"$querySettings": {"showDebugQueryShape": True}}],
        query_settings=lambda ctx: [
            {"find": ctx.name, "filter": {"x": 1}, "sort": {"y": 1}, "$db": ctx.database.name}
        ],
        expected={
            "debugQueryShape": {
                "cmdNs": IsType("object"),
                "command": Eq("find"),
                "filter": IsType("object"),
                "sort": IsType("object"),
            },
        },
        msg=(
            "$querySettings with showDebugQueryShape true should include"
            " the debugQueryShape sub-document"
        ),
    ),
    QuerySettingsStructureTestCase(
        "debug_shape_false_omits_field",
        pipeline=[{"$querySettings": {"showDebugQueryShape": False}}],
        query_settings=lambda ctx: [
            {"find": ctx.name, "filter": {"x": 1}, "sort": {"y": 1}, "$db": ctx.database.name}
        ],
        expected={"debugQueryShape": NotExists()},
        msg=(
            "$querySettings with showDebugQueryShape false should omit"
            " the debugQueryShape field from returned documents"
        ),
    ),
    QuerySettingsStructureTestCase(
        "debug_shape_omitted_omits_field",
        pipeline=[{"$querySettings": {}}],
        query_settings=lambda ctx: [
            {"find": ctx.name, "filter": {"x": 1}, "sort": {"y": 1}, "$db": ctx.database.name}
        ],
        expected={"debugQueryShape": NotExists()},
        msg=(
            "$querySettings with showDebugQueryShape omitted should omit"
            " the debugQueryShape field from returned documents"
        ),
    ),
]

QUERYSETTINGS_STRUCTURE_TESTS = (
    QUERYSETTINGS_CORE_STRUCTURE_TESTS
    + QUERYSETTINGS_CORE_COMMENT_TESTS
    + QUERYSETTINGS_CORE_MULTIPLE_TESTS
    + QUERYSETTINGS_DEBUG_SHAPE_TESTS
)


def _setup_query_settings(
    collection: Collection,
    query_settings: list[dict[str, Any]],
    comment: str | None,
) -> None:
    """Register query settings via setQuerySettings."""
    db = collection.database
    admin = db.client.admin
    for query in query_settings:
        settings: dict[str, Any] = {
            "indexHints": [
                {
                    "ns": {"db": db.name, "coll": collection.name},
                    "allowedIndexes": ["_id_"],
                }
            ],
            "queryFramework": "classic",
        }
        if comment is not None:
            settings["comment"] = comment
        admin.command({"setQuerySettings": query, "settings": settings})


def _teardown_query_settings(collection: Collection, query_settings: list[dict[str, Any]]) -> None:
    """Remove previously registered query settings."""
    admin = collection.database.client.admin
    for query in query_settings:
        admin.command({"removeQuerySettings": query})


@pytest.mark.aggregate
@pytest.mark.requires(cluster_admin=True)
@pytest.mark.no_parallel
@pytest.mark.parametrize("test_case", pytest_params(QUERYSETTINGS_STRUCTURE_TESTS))
def test_querySettings_structure(collection: Collection, test_case: QuerySettingsStructureTestCase):
    """Test $querySettings returned document structure."""
    query_settings = test_case.query_settings(collection)
    # The $querySettings store is cluster-wide, so scope the read to this collection.
    pipeline = test_case.pipeline + [{"$match": {"representativeQuery.find": collection.name}}]
    try:
        _setup_query_settings(collection, query_settings, test_case.settings_comment)
        result = execute_admin_command(
            collection,
            {"aggregate": 1, "pipeline": pipeline, "cursor": {}},
        )
        expected = (
            test_case.expected(collection) if callable(test_case.expected) else test_case.expected
        )
        assertResult(
            result,
            expected=expected,
            msg=test_case.msg,
            raw_res=test_case.raw_res,
        )
    finally:
        _teardown_query_settings(collection, query_settings)
